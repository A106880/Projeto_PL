from node_classes import ProgramaPrincipal, Funcao, StringVal, Expression, Variable, FunctionorArraysAccess


class EnvVar:
    def __init__(self, name, scope, offset, var_type, is_ref=False):
        self.name = name
        self.scope = scope  # 'GLOBAL' ou 'LOCAL'
        self.offset = offset
        self.type = var_type
        self.is_ref = is_ref


class CodeGenerator:
    def __init__(self):
        self.instructions = []
        self.globals = {}
        self.locals = {}
        self.gp_offset = 0
        self.fp_offset = 0
        self.semantic_info = None

    def set_semantic_info(self, parser):
        self.semantic_info = parser

    def add_global(self, name, var_type, size=1):
        var = EnvVar(name, "GLOBAL", self.gp_offset, var_type)
        self.globals[name] = var
        self.gp_offset += size
        return var

    def add_local(self, name, var_type, is_ref=False, size=1):
        var = EnvVar(name, "LOCAL", self.fp_offset, var_type, is_ref)
        self.locals[name] = var
        self.fp_offset += size
        return var

    def lookup(self, name):
        if name in self.locals:
            return self.locals[name]
        return self.globals.get(name)

    def generate(self, node):
        if node is None:
            return

        if isinstance(node, list):
            for n in node:
                self.generate(n)
            return

        class_name = type(node).__name__
        method_name = f"generate_{class_name}"
        method = getattr(self, method_name, None)

        if method:
            method(node)
        else:
            # Fallback para nós ainda não implementados
            pass

    def generate_Program_Unit(self, ast):
        if isinstance(ast, list):
            for unit in ast:
                self.generate(unit)
        else:
            self.generate(ast)

    def generate_ProgramaPrincipal(self, node):
        self.instructions.append("START")
        
        unit_name = node.name.name if hasattr(node.name, "name") else (node.name or "MAIN")
        symbols = self.semantic_info.unit_symbols.get(unit_name, {})
        
        for name, info in symbols.items():
            if not info.get("is_function") and not info.get("is_subroutine"):
                size = info.get("array_size", 1) if info.get("is_array") else 1
                self.add_global(name, info.get("type"), size)

        if self.gp_offset > 0:
            self.instructions.append(f"PUSHN {self.gp_offset}")

        self.generate(node.labeled_statements)
        self.instructions.append("STOP")

    def generate_LabeledStatement(self, node):
        # Ignorando GOTO/Labels para já. Só gera a statement.
        if node.statement:
            self.generate(node.statement)

    def generate_Assignment(self, node):
        var_name = node.name.name if hasattr(node.name, "name") else node.name
        
        # Se for atribuição a um array ARR(I) = valor
        if isinstance(node.name, FunctionorArraysAccess): ## and node.name.is_array :
            # 1. Calcular endereço base
            var = self.lookup(var_name.name if hasattr(node.name, "name") else node.name)
            if var:
                if var.scope == "GLOBAL":
                    self.instructions.append("PUSHGP")
                else:
                    self.instructions.append("PUSHFP")
                self.instructions.append(f"PUSHI {var.offset}")
                self.instructions.append("PADD")

                # 2. Calcular Offset (Índice - 1)
                self.generate(node.name.expressionList[0])
                self.instructions.append("PUSHI 1")
                self.instructions.append("SUB")
                self.instructions.append("PADD") # Endereço final do elemento

                # 3. Gerar o valor a ser guardado e fazer STORE 0
                self.generate(node.value)
                self.instructions.append("STORE 0")
            return

        # Atribuição normal a variável
        self.generate(node.value)
        var = self.lookup(var_name)

        if var:
            if var.is_ref:
                self.instructions.append(f"PUSHL {var.offset}")
                self.instructions.append("SWAP")
                self.instructions.append("STORE 0")
            elif var.scope == "GLOBAL":
                self.instructions.append(f"STOREG {var.offset}")
            else:
                self.instructions.append(f"STOREL {var.offset}")
        else:
            print(f"DEBUG: Variable {var_name} not found in environment!")

    def generate_Print(self, node):
        if node.iolist:
            for item in node.iolist:
                self.generate(item)
                t = getattr(item, "expr_type", "INTEGER")
                if isinstance(item, StringVal):
                    self.instructions.append("WRITES")
                elif t == "INTEGER":
                    self.instructions.append("WRITEI")
                elif t == "REAL":
                    self.instructions.append("WRITEF")
                else:
                    self.instructions.append("WRITEI")  # Fallback
        self.instructions.append("WRITELN")

    def generate_IntVal(self, node):
        self.instructions.append(f"PUSHI {node.value}")

    def generate_RealVal(self, node):
        self.instructions.append(f"PUSHF {node.value}")

    def generate_StringVal(self, node):
        self.instructions.append(f'PUSHS "{node.value}"')

    def generate_Variable(self, node):
        var = self.lookup(node.name)
        if var:
            if var.is_ref:
                self.instructions.append(f"PUSHL {var.offset}")
                self.instructions.append("LOAD 0")
            elif var.scope == "GLOBAL":
                self.instructions.append(f"PUSHG {var.offset}")
            else:
                self.instructions.append(f"PUSHL {var.offset}")

    def generate_BinOp(self, node):
        self.generate(node.left)
        self.generate(node.right)

        op = node.op
        t = getattr(node, "expr_type", "INTEGER")
        prefix = "F" if t == "REAL" else ""

        if op == "+":
            self.instructions.append(f"{prefix}ADD")
        elif op == "-":
            self.instructions.append(f"{prefix}SUB")
        elif op == "*":
            self.instructions.append(f"{prefix}MUL")
        elif op == "/":
            self.instructions.append(f"{prefix}DIV")

    def generate_Funcao(self, node):
        func_name = node.name.name if hasattr(node.name, "name") else node.name
        self.instructions.append(f"{func_name}:")

        # Salvar scope anterior
        old_locals = self.locals
        old_fp_offset = self.fp_offset
        self.locals = {}

        symbols = self.semantic_info.unit_symbols.get(func_name, {})
        n_args = len(node.arguments)

        # O nome da função atua como uma variável local para o valor de retorno (offset -n_args)
        ret_var = EnvVar(func_name, "LOCAL", -n_args, node.return_type, is_ref=True)
        self.locals[func_name] = ret_var

        # 1. Mapear Argumentos
        for i, arg in enumerate(node.arguments):
            offset = -n_args + 1 + i
            arg_name = arg.name if hasattr(arg, "name") else arg
            info = symbols.get(arg_name, {})
            var = EnvVar(arg_name, "LOCAL", offset, info.get("type"), is_ref=True)
            self.locals[arg_name] = var

        self.fp_offset = 1

        # 2. Mapear Variáveis Locais
        for name, info in symbols.items():
            if name not in self.locals and not info.get("is_function") and not info.get("is_subroutine"):
                size = info.get("array_size", 1) if info.get("is_array") else 1
                self.add_local(name, info.get("type"), False, size)

        # Alocar espaço para as variáveis locais (se houver)
        num_locals = self.fp_offset - 1
        if num_locals > 0:
            self.instructions.append(f"PUSHN {num_locals}")

        self.generate(node.labeled_statements)
        self.instructions.append("RETURN")

        # Restaurar scope
        self.locals = old_locals
        self.fp_offset = old_fp_offset

    def generate_Return(self, node):
        self.instructions.append("RETURN")

    def generate_FunctionorArraysAccess(self, node):
        name = node.name.name if hasattr(node.name, "name") else node.name
        
        if node.is_array:
            # 1. Obter endereço base
            var = self.lookup(name)
            if var:
                if var.scope == "GLOBAL":
                    self.instructions.append("PUSHGP")
                else:
                    self.instructions.append("PUSHFP")
                self.instructions.append(f"PUSHI {var.offset}")
                self.instructions.append("PADD")

                # 2. Calcular Offset (Índice - 1)
                # Fortran é 1-indexed. Assumimos 1D.
                self.generate(node.expressionList[0])
                self.instructions.append("PUSHI 1")
                self.instructions.append("SUB")
                
                # 3. Somar ao base e carregar valor
                self.instructions.append("PADD")
                self.instructions.append("LOAD 0")
            else:
                print(f"DEBUG: Array {name} not found in environment!")

        elif node.is_function:
            # 1. Reservar espaço para o retorno
            self.instructions.append("PUSHI 0")

            # 2. Empilhar argumentos por referência
            for arg in node.expressionList:
                if isinstance(arg, Variable):
                    arg_var = self.lookup(arg.name)
                    if arg_var:
                        if arg_var.scope == "GLOBAL":
                            self.instructions.append("PUSHGP")
                        else:
                            self.instructions.append("PUSHFP")
                        self.instructions.append(f"PUSHI {arg_var.offset}")
                        self.instructions.append("PADD")
                    else:
                        self.generate(arg)
                else:
                    self.generate(arg)

            # 3. Chamar a função
            self.instructions.append(f"PUSHA {name}")
            self.instructions.append("CALL")

            # 4. Limpar argumentos da pilha
            if node.expressionList:
                self.instructions.append(f"POP {len(node.expressionList)}")
        
        else:
            print(f"DEBUG: {name} is neither marked as array nor function!")


    def emit(self, line):
        self.instructions.append(line)

    def emit_label(self, label):
        self.instructions.append(f"{label}:")

    def new_label(self, prefix='LABEL'):
        name = f"{prefix.upper()}{getattr(self, 'label_counter', 0)}"
        self.label_counter = getattr(self, 'label_counter', 0) + 1
        return name

    def get_var_name(self, variable):
        if hasattr(variable, 'name'):
            return variable.name
        return str(variable)

    def generate_expression(self, expr):
        if isinstance(expr, int):
            return str(expr)
        if hasattr(expr, 'name'):
            return expr.name
        if hasattr(expr, 'value'):
            return str(expr.value)
        self.generate(expr)
        return "" 

    def generate_Goto(self, node):
        label = f"label_{node.label.value}"
        self.emit(f"JUMP {label}")

    def generate_ComputedGoto(self, node):
        index = self.generate_expression(node.expr)
        num_labels = len(node.labels)
        for idx, label in enumerate(node.labels, 1):
            self.emit("DUP 0")
            self.emit(f"PUSHI {idx}")
            self.emit("EQUAL")
            next_label = self.new_label("after_case")
            self.emit(f"JZ {next_label}")
            self.emit(f"JUMP label{label.value}")
            self.emit_label(next_label)
        self.emit("POP 1")

    def generate_AssignedGoto(self, node):
        var = self.get_var_name(node.var)
        self.generate_expression(node.var)
        for label in node.labels:
            self.emit("DUP 0")
            self.emit(f"PUSHI {label.value}")
            self.emit("EQUAL")
            next_label = self.new_label("after_case")
            self.emit(f"JZ {next_label}")
            self.emit(f"JUMP label{label.value}")
            self.emit_label(next_label)
        self.emit("POP 1")


    def generate_BlockDO(self, node):
        var = self.get_var_name(node.control_var)
        loop_label = self.new_label('doStart')
        end_label = self.new_label('doEnd')
        self.generate(node.init_value)
        var_obj = self.lookup(var)
        if var_obj.scope == "GLOBAL":
            self.emit(f"STOREG {var_obj.offset}")
        else:
            self.emit(f"STOREL {var_obj.offset}")

        self.emit_label(loop_label)
        if var_obj.scope == "GLOBAL":
            self.emit(f"PUSHG {var_obj.offset}")
        else:
            self.emit(f"PUSHL {var_obj.offset}")
        self.generate(node.max_value)
        self.emit("INFEQ")
        self.emit(f"JZ {end_label}")

        for stmt in node.labeled_statements:
            self.generate(stmt)

        if var_obj.scope == "GLOBAL":
            self.emit(f"PUSHG {var_obj.offset}")
        else:
            self.emit(f"PUSHL {var_obj.offset}")
        self.generate(node.step)
        self.emit("ADD")
        if var_obj.scope == "GLOBAL":
            self.emit(f"STOREG {var_obj.offset}")
        else:
            self.emit(f"STOREL {var_obj.offset}")

        self.emit(f"JUMP {loop_label}")
        self.emit_label(end_label)

    def generate_LabeledDO(self, node):
        var = self.get_var_name(node.control_var)
        var_obj = self.lookup(var)
        loop_start = self.new_label("loopStart")
        loop_end = self.new_label("loopEnd")
        user_label = f"label{node.label.value}"

        self.generate(node.control_var_init_value)
        if var_obj.scope == "GLOBAL":
            self.emit(f"STOREG {var_obj.offset}")
        else:
            self.emit(f"STOREL {var_obj.offset}")

        self.emit_label(loop_start)
        if var_obj.scope == "GLOBAL":
            self.emit(f"PUSHG {var_obj.offset}")
        else:
            self.emit(f"PUSHL {var_obj.offset}")
        self.generate(node.iterations_number)
        self.emit("INFEQ")
        self.emit(f"JZ {loop_end}")

        for stmt in node.labeled_statements:
            self.generate(stmt)

        if var_obj.scope == "GLOBAL":
            self.emit(f"PUSHG {var_obj.offset}")
        else:
            self.emit(f"PUSHL {var_obj.offset}")
        self.generate(node.step)
        self.emit("ADD")
        if var_obj.scope == "GLOBAL":
            self.emit(f"STOREG {var_obj.offset}")
        else:
            self.emit(f"STOREL {var_obj.offset}")

        self.emit(f"JUMP {loop_start}")
        self.emit_label(loop_end)
        self.emit(f"JUMP {user_label}")

        self.emit_label(user_label) 

    def generate_ArithmeticIf(self, node):
        self.generate(node.exp)
        self.emit("DUP 0")
        self.emit("PUSHI 0")
        self.emit("INF")
        self.emit(f"JZ NEXT1{node.lineno}")
        self.emit(f"JUMP label{node.labeln.value}")

        self.emit_label(f"NEXT1{node.lineno}")
        self.emit("DUP 0")
        self.emit("PUSHI 0")
        self.emit("EQUAL")
        self.emit(f"JZ NEXT2{node.lineno}")
        self.emit(f"JUMP label{node.labelz.value}")

        self.emit_label(f"NEXT2{node.lineno}")
        self.emit(f"JUMP label    {node.labelp.value}")

    def generate_LogicIf(self, node):
        endif_label = self.new_label("endif")
        self.generate_expression(node.exp)
        self.emit(f"JZ {endif_label}")
        self.generate(node.statement)
        self.emit_label(endif_label)

    def generate_BlockIf(self, node):
        else_label = self.new_label('else')
        end_label = self.new_label('endif')
        self.generate(node.exp)
        self.emit(f"JZ {else_label}")
        for stmt in node.thenBody:
            self.generate(stmt)
        self.emit(f"JUMP {end_label}")
        self.emit_label(else_label)
        if node.elseBody:
            for stmt in node.elseBody:
                self.generate(stmt)
        self.emit_label(end_label)

    

    def get_assembly(self):
        return "\n".join(self.instructions)
