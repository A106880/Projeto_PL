from __future__ import annotations
from typing import Optional, Dict, List, Any
from node_classes import StringVal, Variable, FunctionorArraysAccess


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
            print(f"WARNING: Label generation ({node.label}) is not yet implemented in the CodeGen.")
        if node.statement:
            self.generate(node.statement)

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
        
        if t == "COMPLEX":
            l_type = getattr(node.left, "expr_type", "INTEGER")
            r_type = getattr(node.right, "expr_type", "INTEGER")
            
            self.generate(node.left)
            if l_type != "COMPLEX":
                self.instructions.append("PUSHF 0.0")
            
            self.generate(node.right)
            if r_type != "COMPLEX":
                self.instructions.append("PUSHF 0.0")
            
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

        self.generate(node.left)
        self.generate(node.right)
        
        # Determinar prefixo (F se algum for Real)
        l_type = getattr(node.left, "expr_type", "")
        r_type = getattr(node.right, "expr_type", "")
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
            l_type = getattr(node.left, "expr_type", "INTEGER")
            r_type = getattr(node.right, "expr_type", "INTEGER")
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
                    self.instructions.append("FEQ")
                    self.instructions.append("PUSHL -2")
                    self.instructions.append("PUSHL -4")
                    self.instructions.append("FEQ")
                    self.instructions.append("MUL") 
                    return
                self.instructions.append(f"{prefix}EQ")
            else: # .NE.
                if is_complex_comp:
                    self.instructions.append("STOREL -4")
                    self.instructions.append("STOREL -3")
                    self.instructions.append("STOREL -2")
                    self.instructions.append("STOREL -1")
                    self.instructions.append("PUSHL -1")
                    self.instructions.append("PUSHL -3")
                    self.instructions.append("FNE")
                    self.instructions.append("PUSHL -2")
                    self.instructions.append("PUSHL -4")
                    self.instructions.append("FNE")
                    self.instructions.append("ADD")
                    self.instructions.append("PUSHI 0")
                    self.instructions.append("GT")
                    return
                self.instructions.append(f"{prefix}NE")
        elif op == ".LT.":
            self.instructions.append(f"{prefix}LT")
        elif op == ".LE.":
            self.instructions.append(f"{prefix}LE")
        elif op == ".GT.":
            self.instructions.append(f"{prefix}GT")
        elif op == ".GE.":
            self.instructions.append(f"{prefix}GE")
        
        # Lógicos
        elif op in (".AND.", "AND"):
            self.instructions.append("MUL") 
        elif op in (".OR.", "OR"): 
            self.instructions.append("ADD")
            self.instructions.append("PUSHI 0")
            self.instructions.append("GT")

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
        elif op in (".NOT.", "NOT"):
            self.instructions.append("PUSHI 1")
            self.instructions.append("SWAP")
            self.instructions.append("SUB")

    def generate_Function(self, node: Any) -> None:
        func_name = node.name.name if hasattr(node.name, "name") else node.name
        self.instructions.append(f"{func_name}:")

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

    def get_assembly(self) -> str:
        return "\n".join(self.instructions)
