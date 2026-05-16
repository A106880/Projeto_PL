from __future__ import annotations
from typing import Optional, Dict, List, Any
from node_classes import Call, StringVal, Variable, FunctionorArraysAccess


class EnvVar:
    def __init__(self, name: str, scope: str, offset: int, var_type: str, is_ref: bool = False) -> None:
        self.name: str = name
        self.scope: str = scope  # 'GLOBAL' ou 'LOCAL'
        self.offset: int = offset
        self.type: str = var_type
        self.is_ref: bool = is_ref
        


class CodeGenerator:
    def __init__(self) -> None:
        self.instructions: List[str] = []
        self.globals: Dict[str, EnvVar] = {}
        self.locals: Dict[str, EnvVar] = {}
        self.gp_offset: int = 0
        self.fp_offset: int = 0
        self.semantic_info: Optional[Any] = None
        self._label_count: int = 0

    def set_semantic_info(self, parser: Any) -> None:
        self.semantic_info = parser

    def add_global(self, name: str, var_type: str, size: int = 1) -> EnvVar:
        var = EnvVar(name, "GLOBAL", self.gp_offset, var_type)
        self.globals[name] = var
        self.gp_offset += size
        return var

    def add_local(self, name: str, var_type: str, is_ref: bool = False, size: int = 1) -> EnvVar:
        var = EnvVar(name, "LOCAL", self.fp_offset, var_type, is_ref)
        self.locals[name] = var
        self.fp_offset += size
        return var

    def lookup(self, name: str) -> Optional[EnvVar]:
        if name in self.locals:
            return self.locals[name]
        return self.globals.get(name)

    def generate(self, node: Any) -> None:
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
            # Fallback para funções não implementadas
            if node is not None:
                print(f"ERROR: Generation function not implemented: {method_name}")

    def generate_Program_Unit(self, ast: Any) -> None:
        if isinstance(ast, list):
            for unit in ast:
                self.generate(unit)
        else:
            self.generate(ast)

    def generate_MainProgram(self, node: Any) -> None:
        self.instructions.append("START")
        
        unit_name = node.name.name if hasattr(node.name, "name") else (node.name or "MAIN")
        
        self.curr_unit = unit_name

        symbols = self.semantic_info.unit_symbols.get(unit_name, {})
        
        for name, info in symbols.items():
            if not info.get("is_function") and not info.get("is_subroutine"):
                var_type = info.get("type")
                is_array = info.get("is_array")
                base_size = 2 if var_type == "COMPLEX" else 1
                size = (info.get("array_size", 1) if is_array else 1) * base_size
                self.add_global(name, var_type, size)

        if self.gp_offset > 0:
            self.instructions.append(f"PUSHN {self.gp_offset}")

        self.generate(node.labeled_statements)
        self.instructions.append("STOP")

    def generate_LabeledStatement(self, node: Any) -> None:
        if node.label:
            self.instructions.append(f"LABEL{node.label.value}:")
            print(f"WARNING: Label generation ({node.label}) is not yet implemented in the CodeGen.")
        if node.statement:
            self.generate(node.statement)

   # def generate_Goto(self,node : Any) -> None:
    #    self.instructions.append(f"JUMP {self.curr_unit}{node.label.value}")

    def generate_Assignment(self, node: Any) -> None:
        var_name = node.name.name if hasattr(node.name, "name") else node.name
        
        # Se for atribuição a um array ARR(I) = valor
        if isinstance(node.name, FunctionorArraysAccess):
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
                val_type = getattr(node.value, "expr_type", "INTEGER")
                if var.type == "COMPLEX" and val_type != "COMPLEX":
                    self.instructions.append("PUSHF 0.0")
                self.instructions.append("STORE 0")
            return

        # Atribuição normal a variável
        self.generate(node.value)
        var = self.lookup(var_name)
        if var:
            val_type = getattr(node.value, "expr_type", "INTEGER")
            if var.type == "COMPLEX" and val_type != "COMPLEX":
                self.instructions.append("PUSHF 0.0")
            is_complex = var.type == "COMPLEX"
            if var.is_ref:
                if is_complex:
                    # Guardar Imaginário em base+1
                    self.instructions.append("DUP 1") # Duplica o endereço
                    self.instructions.append("PUSHI 1")
                    self.instructions.append("PADD")
                    self.instructions.append("PUSHFP") 
                    self.instructions.append("LOAD 1") 
                    
                    pass # TODO: Refinar isto para referências complexas
                self.instructions.append(f"PUSHL {var.offset}")
                self.instructions.append("SWAP")
                self.instructions.append("STORE 0")
            elif var.scope == "GLOBAL":
                if is_complex:
                    self.instructions.append(f"STOREG {var.offset + 1}")
                    self.instructions.append(f"STOREG {var.offset}")
                else:
                    self.instructions.append(f"STOREG {var.offset}")
            else:
                if is_complex:
                    self.instructions.append(f"STOREL {var.offset + 1}")
                    self.instructions.append(f"STOREL {var.offset}")
                else:
                    self.instructions.append(f"STOREL {var.offset}")
        else:
            print(f"DEBUG: Variable {var_name} not found in environment!")

    def generate_Print(self, node: Any) -> None:
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
                elif t == "COMPLEX":
                    self.instructions.append('PUSHS "("')
                    self.instructions.append("WRITES")
                    self.instructions.append("SWAP") 
                    self.instructions.append("WRITEF")
                    self.instructions.append('PUSHS ", "')
                    self.instructions.append("WRITES")
                    self.instructions.append("WRITEF")
                    self.instructions.append('PUSHS ")"')
                    self.instructions.append("WRITES")
                elif t == "LOGICAL":
                    self.instructions.append("WRITEI") # Imprime 0 ou 1
                else:
                    self.instructions.append("WRITEI")  # Fallback
        self.instructions.append("WRITELN")

    def generate_Write(self, node: Any) -> None:
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
                elif t == "COMPLEX":
                    self.instructions.append('PUSHS "("')
                    self.instructions.append("WRITES")
                    self.instructions.append("SWAP") 
                    self.instructions.append("WRITEF")
                    self.instructions.append('PUSHS ", "')
                    self.instructions.append("WRITES")
                    self.instructions.append("WRITEF")
                    self.instructions.append('PUSHS ")"')
                    self.instructions.append("WRITES")
                elif t == "LOGICAL":
                    self.instructions.append("WRITEI")
                else:
                    self.instructions.append("WRITEI")
        self.instructions.append("WRITELN")

    def generate_Read(self, node: Any) -> None:
        if node.iolist:
            for item in node.iolist:
                # 1. Ler da entrada (instrução READ da VM coloca endereço da string na stack)
                self.instructions.append("READ")
                
                # 2. Determinar o tipo do destino
                t = getattr(item, "expr_type", "INTEGER")
                
                # 3. Converter se necessário
                if t == "INTEGER":
                    self.instructions.append("ATOI")
                elif t == "REAL":
                    self.instructions.append("ATOF")
                
                # 4. Armazenar no destino
                if isinstance(item, Variable):
                    var_name = item.name
                    var = self.lookup(var_name)
                    if var:
                        if var.scope == "GLOBAL":
                            self.instructions.append(f"STOREG {var.offset}")
                        else:
                            self.instructions.append(f"STOREL {var.offset}")
                elif isinstance(item, FunctionorArraysAccess):
                    var_name = item.name.name if hasattr(item.name, "name") else item.name
                    var = self.lookup(var_name)
                    if var:
                        # Precisamos do endereço base + (índice - 1)
                        # Como já temos o valor convertido no topo da stack, 
                        # vamos guardá-lo temporariamente ou preparar o endereço primeiro.
                        
                        # 1. Calcular Endereço (precisamos fazer isso ANTES do READ ou usar SWAP)
                        # Vamos reformular:
                        # 1. Calcular Endereço e colocar na pilha
                        # 2. READ
                        # 3. ATOI/ATOF
                        # 4. STORE 0
                        
                        # Voltamos atrás no READ para este item:
                        self.instructions.pop() # remove converter se houver
                        if t in ("INTEGER", "REAL"):
                            self.instructions.pop() # remove converter
                        self.instructions.pop() # remove READ
                        
                        # Agora sim:
                        if var.scope == "GLOBAL":
                            self.instructions.append("PUSHGP")
                        else:
                            self.instructions.append("PUSHFP")
                        self.instructions.append(f"PUSHI {var.offset}")
                        self.instructions.append("PADD")
                        
                        self.generate(item.expressionList[0])
                        self.instructions.append("PUSHI 1")
                        self.instructions.append("SUB")
                        self.instructions.append("PADD") # Endereço final na pilha
                        
                        # Agora o READ
                        self.instructions.append("READ")
                        if t == "INTEGER":
                            self.instructions.append("ATOI")
                        elif t == "REAL":
                            self.instructions.append("ATOF")
                        
                        self.instructions.append("STORE 0")

    def generate_IntVal(self, node: Any) -> None:
        self.instructions.append(f"PUSHI {node.value}")

    def generate_RealVal(self, node: Any) -> None:
        self.instructions.append(f"PUSHF {node.value}")

    def generate_ComplexVal(self, node: Any) -> None:
        self.generate(node.elem1)
        self.generate(node.elem2)

    def generate_DoublePrecisionComplexVal(self, node: Any) -> None:
        self.generate_ComplexVal(node)

    def generate_StringVal(self, node: Any) -> None:
        self.instructions.append(f'PUSHS "{node.value}"')

    def generate_LogicalVal(self, node: Any) -> None:
        val = 1 if node.value else 0
        self.instructions.append(f"PUSHI {val}")

    def generate_Variable(self, node: Any) -> None:
        var = self.lookup(node.name)
        if var:
            is_complex = var.type == "COMPLEX"
            if var.is_ref:
                self.instructions.append(f"PUSHL {var.offset}")
                self.instructions.append("LOAD 0")
                if is_complex:
                    self.instructions.append(f"PUSHL {var.offset}")
                    self.instructions.append("PUSHI 1")
                    self.instructions.append("PADD")
                    self.instructions.append("LOAD 0")
            elif var.scope == "GLOBAL":
                self.instructions.append(f"PUSHG {var.offset}")
                if is_complex:
                    self.instructions.append(f"PUSHG {var.offset + 1}")
            else:
                self.instructions.append(f"PUSHL {var.offset}")
                if is_complex:
                    self.instructions.append(f"PUSHL {var.offset + 1}")

    def generate_BinOp(self, node: Any) -> None:
        op = node.op
        t = getattr(node, "expr_type", "INTEGER")
        l_type = getattr(node.left, "expr_type", "INTEGER")
        r_type = getattr(node.right, "expr_type", "INTEGER")
        
        # Se algum dos lados for COMPLEX, ambos devem ser tratados como tal na stack
        is_any_complex = (l_type == "COMPLEX" or r_type == "COMPLEX")
        
        # Gerar o Lado Esquerdo (sempre necessário)
        self.generate(node.left)
        if is_any_complex and l_type != "COMPLEX":
            self.instructions.append("PUSHF 0.0")
            
        # Para operadores lógicos (.AND., .OR.), o Lado Direito é gerado lá dentro (Curto-circuito)
        if op not in (".AND.", ".OR."):
            self.generate(node.right)
            if is_any_complex and r_type != "COMPLEX":
                self.instructions.append("PUSHF 0.0")

        # 1. Aritmética Complexa
        if t == "COMPLEX":
            if op in ("+", "-"):
                prefix = "F"
                self.instructions.append("SWAP")
                self.instructions.append("STOREL -1")   
                self.instructions.append(f"{prefix}{'ADD' if op == '+' else 'SUB'}")
                self.instructions.append("STOREL -2")
                self.instructions.append("PUSHL -1")    
                self.instructions.append(f"{prefix}{'ADD' if op == '+' else 'SUB'}")    
                self.instructions.append("PUSHL -2")    
                return
            
            elif op == "*":
                # (R1, I1) * (R2, I2) -> (R1*R2 - I1*I2), (R1*I2 + I1*R2)
                # Stack inicial: R1, I1, R2, I2
                self.instructions.append("STOREL -4") # I2
                self.instructions.append("STOREL -3") # R2
                self.instructions.append("STOREL -2") # I1
                self.instructions.append("STOREL -1") # R1
                
                # Real: R1*R2 - I1*I2
                self.instructions.append("PUSHL -1")
                self.instructions.append("PUSHL -3")
                self.instructions.append("FMUL")
                self.instructions.append("PUSHL -2")
                self.instructions.append("PUSHL -4")
                self.instructions.append("FMUL")
                self.instructions.append("FSUB")
                
                # Imag: R1*I2 + I1*R2
                self.instructions.append("PUSHL -1")
                self.instructions.append("PUSHL -4")
                self.instructions.append("FMUL")
                self.instructions.append("PUSHL -2")
                self.instructions.append("PUSHL -3")
                self.instructions.append("FMUL")
                self.instructions.append("FADD")
                return

            elif op == "/":
                # (R1, I1) / (R2, I2) -> [(ac+bd)/D] + [(bc-ad)/D]i onde D = c^2+d^2
                self.instructions.append("STOREL -4") # I2 (d)
                self.instructions.append("STOREL -3") # R2 (c)
                self.instructions.append("STOREL -2") # I1 (b)
                self.instructions.append("STOREL -1") # R1 (a)

                # 1. Calcular Denominador D = c^2 + d^2
                self.instructions.append("PUSHL -3")
                self.instructions.append("PUSHL -3")
                self.instructions.append("FMUL")
                self.instructions.append("PUSHL -4")
                self.instructions.append("PUSHL -4")
                self.instructions.append("FMUL")
                self.instructions.append("FADD")
                self.instructions.append("STOREL -5") # D

                # 2. Parte Real: (ac + bd) / D
                self.instructions.append("PUSHL -1")
                self.instructions.append("PUSHL -3")
                self.instructions.append("FMUL")
                self.instructions.append("PUSHL -2")
                self.instructions.append("PUSHL -4")
                self.instructions.append("FMUL")
                self.instructions.append("FADD")
                self.instructions.append("PUSHL -5")
                self.instructions.append("FDIV")

                # 3. Parte Imag: (bc - ad) / D
                self.instructions.append("PUSHL -2")
                self.instructions.append("PUSHL -3")
                self.instructions.append("FMUL")
                self.instructions.append("PUSHL -1")
                self.instructions.append("PUSHL -4")
                self.instructions.append("FMUL")
                self.instructions.append("FSUB")
                self.instructions.append("PUSHL -5")
                self.instructions.append("FDIV")
                return

        # Determinar prefixo (F se algum for Real)
        prefix = "F" if (l_type == "REAL" or r_type == "REAL") else ""
        
        if op == "+":
            self.instructions.append(f"{prefix}ADD")
        elif op == "-":
            self.instructions.append(f"{prefix}SUB")
        elif op == "*":
            self.instructions.append(f"{prefix}MUL")
        elif op == "/":
            self.instructions.append(f"{prefix}DIV")
        
        # Relacionais
        elif op in (".EQ.", ".NE."):
            is_complex_comp = (l_type == "COMPLEX" or r_type == "COMPLEX")

            if op == ".EQ.":
                if is_complex_comp:
                    # R1, I1, R2, I2
                    self.instructions.append("STOREL -4")
                    self.instructions.append("STOREL -3")
                    self.instructions.append("STOREL -2")
                    self.instructions.append("STOREL -1")
                    self.instructions.append("PUSHL -1")
                    self.instructions.append("PUSHL -3")
                    self.instructions.append("EQUAL")
                    self.instructions.append("PUSHL -2")
                    self.instructions.append("PUSHL -4")
                    self.instructions.append("EQUAL")
                    self.instructions.append("AND") 
                    return
                self.instructions.append("EQUAL")
            else: # .NE.
                if is_complex_comp:
                    self.instructions.append("STOREL -4")
                    self.instructions.append("STOREL -3")
                    self.instructions.append("STOREL -2")
                    self.instructions.append("STOREL -1")
                    self.instructions.append("PUSHL -1")
                    self.instructions.append("PUSHL -3")
                    self.instructions.append("EQUAL")
                    self.instructions.append("NOT")
                    self.instructions.append("PUSHL -2")
                    self.instructions.append("PUSHL -4")
                    self.instructions.append("EQUAL")
                    self.instructions.append("NOT")
                    self.instructions.append("OR")
                    return
                self.instructions.append("EQUAL")
                self.instructions.append("NOT")
        elif op == ".LT.":
            self.instructions.append(f"{prefix}INF")
        elif op == ".LE.":
            self.instructions.append(f"{prefix}INFEQ")
        elif op == ".GT.":
            self.instructions.append(f"{prefix}SUP")
        elif op == ".GE.":
            self.instructions.append(f"{prefix}SUPEQ")
        
        elif op == ".EQV.":
            self.instructions.append("EQUAL")
        elif op == ".NEQV.":
            self.instructions.append("EQUAL")
            self.instructions.append("NOT")
        
        # Lógicos com Curto-circuito
        elif op == ".AND.":
            self._label_count += 1
            lbl_false = f"scf{self._label_count}"
            lbl_end = f"sce{self._label_count}"
            
            # Já temos o resultado do Left na stack
            self.instructions.append("DUP 1")
            self.instructions.append(f"JZ {lbl_false}")
            self.instructions.append("POP 1")
            self.generate(node.right)
            self.instructions.append(f"JUMP {lbl_end}")
            
            self.instructions.append(f"{lbl_false}:")
            
            self.instructions.append(f"{lbl_end}:")
            return

        elif op == ".OR.": 
            self._label_count += 1
            lbl_true = f"sct{self._label_count}"
            lbl_end = f"soe{self._label_count}"
            
            self.instructions.append("DUP 1")
            self.instructions.append("NOT")
            self.instructions.append(f"JZ {lbl_true}")
            self.instructions.append("POP 1")
            self.generate(node.right)
            self.instructions.append(f"JUMP {lbl_end}")
            
            self.instructions.append(f"{lbl_true}:")
            
            self.instructions.append(f"{lbl_end}:")
            return

    def generate_UnOp(self, node: Any) -> None:
        self.generate(node.expr)
        op = node.op
        if op == "-":
            t = getattr(node.expr, "expr_type", "INTEGER")
            prefix = "F" if t == "REAL" else ""
            if prefix == "F":
                self.instructions.append("PUSHF -1.0")
                self.instructions.append("FMUL")
            else:
                self.instructions.append("PUSHI -1")
                self.instructions.append("MUL")
        elif op in (".NOT."):
            self.instructions.append("PUSHI 1")
            self.instructions.append("SWAP")
            self.instructions.append("SUB")

    def generate_Mod(self, node):
        self.generate(node.left)
        self.generate(node.right)
        self.instructions.append(f"MOD") 

    def generate_Function(self, node: Any) -> None:
        func_name = node.name.name if hasattr(node.name, "name") else node.name
        self.instructions.append(f"{func_name}:")
        self.curr_unit = func_name

        # Salvar scope anterior
        old_locals = self.locals
        old_fp_offset = self.fp_offset
        self.locals = {}

        symbols = self.semantic_info.unit_symbols.get(func_name, {})
        n_args = len(node.arguments)

        # O nome da função atua como uma variável local para o valor de retorno
        ret_var = EnvVar(func_name, "LOCAL", -(n_args + 1), node.return_type, is_ref=False)
        self.locals[func_name] = ret_var

        # 1. Mapear Argumentos
        for i, arg in enumerate(node.arguments):
            offset = -n_args + i
            arg_name = arg.name if hasattr(arg, "name") else arg
            info = symbols.get(arg_name, {})
            var = EnvVar(arg_name, "LOCAL", offset, info.get("type"), is_ref=True)
            self.locals[arg_name] = var

        self.fp_offset = 1

        # 2. Mapear Variáveis Locais
        for name, info in symbols.items():
            if name not in self.locals and not info.get("is_function") and not info.get("is_subroutine"):
                var_type = info.get("type")
                is_array = info.get("is_array")
                base_size = 2 if var_type == "COMPLEX" else 1
                size = (info.get("array_size", 1) if is_array else 1) * base_size
                self.add_local(name, var_type, False, size)

        # Alocar espaço para as variáveis locais (se houver)
        num_locals = self.fp_offset - 1
        if num_locals > 0:
            self.instructions.append(f"PUSHN {num_locals}")

        self.generate(node.labeled_statements)
        self.instructions.append("RETURN")

        # Restaurar scope
        self.locals = old_locals
        self.fp_offset = old_fp_offset
    
    def generate_Subroutine(self, node: Any) -> None:
        sub_name = node.name.name if hasattr(node.name, "name") else node.name
        self.curr_unit = sub_name
        self.instructions.append(f"{sub_name}:")

        # Salvar scope anterior
        old_locals = self.locals
        old_fp_offset = self.fp_offset
        self.locals = {}

        symbols = self.semantic_info.unit_symbols.get(sub_name, {})
        n_args = len(node.arguments)

        # 1. Mapear Argumentos (todos por referência)
        for i, arg in enumerate(node.arguments):
            offset = -n_args + i
            arg_name = arg.name if hasattr(arg, "name") else arg
            info = symbols.get(arg_name, {})
            var = EnvVar(arg_name, "LOCAL", offset, info.get("type"), is_ref=True)
            self.locals[arg_name] = var

        self.fp_offset = 1

        # 2. Mapear Variáveis Locais (apenas variáveis locais, não argumentos nem funções/subrotinas)
        for name, info in symbols.items():
            if name not in self.locals and not info.get("is_function") and not info.get("is_subroutine"):
                var_type = info.get("type")
                is_array = info.get("is_array")
                base_size = 2 if var_type == "COMPLEX" else 1
                size = (info.get("array_size", 1) if is_array else 1) * base_size
                self.add_local(name, var_type, False, size)

        # Alocar espaço para as variáveis locais (se houver)
        num_locals = self.fp_offset - 1
        if num_locals > 0:
            self.instructions.append(f"PUSHN {num_locals}")

        # 3. Gerar código da subrotina
        self.generate(node.labeled_statements)
        
        # 4. Retornar sem valor
        self.instructions.append("RETURN")

        # Restaurar scope
        self.locals = old_locals
        self.fp_offset = old_fp_offset

    def generate_Return(self, node: Any) -> None:
        self.instructions.append("RETURN")

    def generate_FunctionorArraysAccess(self, node: Any) -> None:
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

                # 2. Calcular Offset
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

    def generate_Call(self, node: Call) -> None:
        name = node.subroutine.name if hasattr(node.subroutine, "name") else node.subroutine

        # 1. Empilhar argumentos por referência
        for arg in node.arguments:
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

        # 2. Chamar a subrotina
        self.instructions.append(f"PUSHA {name}")
        self.instructions.append("CALL")

        # 3. Limpar argumentos da pilha
        if node.arguments:
            self.instructions.append(f"POP {len(node.arguments)}")
        

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
        label = f"LABEL{node.label.value}"
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
            next_label = self.new_label("AFTERCASE")
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

    def get_assembly(self) -> str:
        return "\n".join(self.instructions)
