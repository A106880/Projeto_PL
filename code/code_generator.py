from __future__ import annotations
from typing import Optional, Dict, List, Any
from node_classes import (
    Node, Call, StringVal, Variable, FunctionorArraysAccess,
    IntVal, RealVal, LogicalVal, ComplexVal, DoublePrecisionComplexVal,
    BlockDO, AssignedGoto, ComputedGoto, Goto, Expression, BinOp, LabeledDO,
    MainProgram, Program_Unit, Print, Read, Write, DoublePrecisionVal
)
from semantic_parser import SemanticParser


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
        self.semantic_info: Optional[SemanticParser] = None
        self._label_count: int = 0
        self._literals: Dict[Any, tuple[EnvVar, Any]] = {}

    def set_semantic_info(self, parser: SemanticParser) -> None:
        self.semantic_info = parser

    def _setup_scratch_vars(self) -> None:
        if self.semantic_info is None:
            return
        
        if self.semantic_info.has_complex:
            self.add_local("__comp_r1", "REAL")
            self.add_local("__comp_i1", "REAL")
            self.add_local("__comp_r2", "REAL")
            self.add_local("__comp_i2", "REAL")
            self.add_local("__comp_temp", "REAL")

        if self.semantic_info.has_power:
            self.add_local("__pow_base_i", "INTEGER")
            self.add_local("__pow_exp_i", "INTEGER")
            self.add_local("__pow_res_i", "INTEGER")

        max_args = self.semantic_info.max_literal_args if hasattr(self.semantic_info, 'max_literal_args') else 0
        for i in range(max_args):
            self.add_local(f"__arg_temp_{i}", "DOUBLECOMPLEX", size=2)

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

    def _emit_store(self, var: Optional[EnvVar]) -> None:
        if var is None:
            print("DEBUG: _emit_store called with None")
            return
        self.instructions.append(f"STORE{'G' if var.scope == 'GLOBAL' else 'L'} {var.offset}")

    def _emit_push(self, var: Optional[EnvVar]) -> None:
        if var is None:
            print("DEBUG: _emit_push called with None")
            return
        self.instructions.append(f"PUSH{'G' if var.scope == 'GLOBAL' else 'L'} {var.offset}")

    def _generate_array_addr(self, node: FunctionorArraysAccess) -> None:
        node_name = getattr(node, "name", None)
        var_name = getattr(node_name, "name", node_name)
        if not isinstance(var_name, str):
            print(f"DEBUG: Array name {var_name} is not a valid string!")
            return
        var = self.lookup(var_name)
        if not var:
            print(f"DEBUG: Array {var_name} not found in environment!")
            return

        # 1. Endereço base
        self.instructions.append("PUSHGP" if var.scope == "GLOBAL" else "PUSHFP")
        self.instructions.append(f"PUSHI {var.offset}")
        self.instructions.append("PADD")

        # 2. Offset (Índice - 1)
        self.generate(node.expressionList[0])
        self.instructions.append("PUSHI 1")
        self.instructions.append("SUB")
        
        # 3. Escalar se for complexo (2 slots por elemento)
        if var.type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION"):
            self.instructions.append("PUSHI 2")
            self.instructions.append("MUL")
        
        self.instructions.append("PADD")

    def _collect_literals(self, node: Any) -> None:
        if node is None:
            return
        if isinstance(node, list):
            for n in node:
                self._collect_literals(n)
            return

        literal_types = (IntVal, RealVal, StringVal, LogicalVal, ComplexVal, DoublePrecisionComplexVal, DoublePrecisionVal)
        if isinstance(node, literal_types):
            if isinstance(node, (ComplexVal, DoublePrecisionComplexVal)):
                key = (type(node).__name__, node.elem1.value, node.elem2.value)
            else:
                key = (type(node).__name__, node.value)
            
            if key not in self._literals:
                t_name = "COMPLEX" if isinstance(node, (ComplexVal, DoublePrecisionComplexVal)) else \
                         "DOUBLEPRECISION" if isinstance(node, DoublePrecisionVal) else \
                         "INTEGER" if isinstance(node, (IntVal, LogicalVal)) else \
                         "REAL" if isinstance(node, RealVal) else "CHARACTER"
                size = 2 if t_name in ("COMPLEX", "DOUBLEPRECISION") else 1
                var_name = f"__lit_{len(self._literals)}"
                self._literals[key] = (self.add_global(var_name, t_name, size), node)
            return
        
        if isinstance(node, (Write, Print)):
            for attr_name, attr_value in getattr(node, "__dict__", {}).items():
                if attr_name == 'iolist' and attr_value:
                    for item in attr_value:
                        if not isinstance(item, literal_types):
                            self._collect_literals(item)
                elif isinstance(attr_value, (Node, list)):
                    self._collect_literals(attr_value)
            return

        for attr in getattr(node, "__dict__", {}).values():
            if isinstance(attr, (Node, list)):
                self._collect_literals(attr)

    def _get_literal_addr_instrs(self, node: Any) -> List[str]:
        literal_types = (IntVal, RealVal, StringVal, LogicalVal, ComplexVal, DoublePrecisionComplexVal, DoublePrecisionVal)
        if not isinstance(node, literal_types):
            return []

        if isinstance(node, (ComplexVal, DoublePrecisionComplexVal)):
            key = (type(node).__name__, node.elem1.value, node.elem2.value)
        else:
            key = (type(node).__name__, node.value)
        
        entry = self._literals.get(key)
        if entry:
            var, _ = entry
            return ["PUSHGP", f"PUSHI {var.offset}", "PADD"]
        return []

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
        unit_name = node.name.name if hasattr(node.name, "name") else (node.name or "MAIN")
        self.curr_unit = unit_name

        # 1. Recolher todos os literais da AST para alocar globais
        self._collect_literals(node)

        symbols = getattr(self.semantic_info, "unit_symbols", {}).get(unit_name, {}) if self.semantic_info else {}
        
        # 2. Declarar Globais
        for name, info in symbols.items():
            if not info.get("is_function") and not info.get("is_subroutine"):
                var_type = info.get("type")
                is_array = info.get("is_array")
                base_size = 2 if var_type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION") else 1
                size = (info.get("array_size", 1) if is_array else 1) * base_size
                self.add_global(name, var_type, size)

        # 3. Alocar Globais na Stack
        if self.gp_offset > 0:
            self.instructions.append(f"PUSHN {self.gp_offset}")

        # 4. Definir FP para o início do Activation Record do Main
        self.instructions.append("START")

        # 5. Inicializar Variáveis de Literais
        for var, lit_node in self._literals.values():
            if isinstance(lit_node, (ComplexVal, DoublePrecisionComplexVal, DoublePrecisionVal)):
                if isinstance(lit_node, DoublePrecisionVal):
                    self.instructions.append(f"PUSHF {lit_node.value}")
                    self.instructions.append(f"STOREG {var.offset}")
                    self.instructions.append(f"PUSHF 0.0")
                    self.instructions.append(f"STOREG {var.offset + 1}")
                else:
                    self.instructions.append(f"PUSHF {lit_node.elem1.value}")
                    self.instructions.append(f"STOREG {var.offset}")
                    self.instructions.append(f"PUSHF {lit_node.elem2.value}")
                    self.instructions.append(f"STOREG {var.offset + 1}")
            elif isinstance(lit_node, RealVal):
                self.instructions.append(f"PUSHF {lit_node.value}")
                self.instructions.append(f"STOREG {var.offset}")
            elif isinstance(lit_node, StringVal):
                self.instructions.append(f'PUSHS "{lit_node.value}"')
                self.instructions.append(f"STOREG {var.offset}")
            elif isinstance(lit_node, LogicalVal):
                val = 1 if lit_node.value else 0
                self.instructions.append(f"PUSHI {val}")
                self.instructions.append(f"STOREG {var.offset}")
            else: # IntVal
                self.instructions.append(f"PUSHI {lit_node.value}")
                self.instructions.append(f"STOREG {var.offset}")

        self.fp_offset = 0
        self.locals = {} # Limpar locals para o Main
        self._setup_scratch_vars()
        num_locals = self.fp_offset
        if num_locals > 0:
            self.instructions.append(f"PUSHN {num_locals}")

        self.generate(node.labeled_statements)
        self.instructions.append("STOP")

    def generate_LabeledStatement(self, node: Any) -> None:
        if node.label:
            # Não emitir label se a instrução for um LabeledDO, pois o generate_LabeledDO já a trata.
            if not isinstance(node.statement, LabeledDO):
                self.emit_label(self.get_full_label(node.label.value))
        if node.statement:
            self.generate(node.statement)

    def generate_Assignment(self, node: Any) -> None:
        var_name = node.name.name if hasattr(node.name, "name") else node.name
        
        if isinstance(node.name, FunctionorArraysAccess):
            var = self.lookup(var_name)
            if var:
                # 1. Calcular endereço do elemento
                self._generate_array_addr(node.name)

                # 2. Gerar o valor a ser guardado
                is_2slot_arr = var.type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION")
                if is_2slot_arr:
                    self.instructions.append("DUP 1")
                
                self.generate(node.value)
                val_type = getattr(node.value, "expr_type", "INTEGER")

                # Conversão implícita
                if var.type in ("REAL", "DOUBLEPRECISION") and val_type == "INTEGER":
                    self.instructions.append("ITOF")
                    if var.type == "DOUBLEPRECISION":
                        self.instructions.append("PUSHF 0.0")
                elif var.type == "INTEGER" and val_type in ("REAL", "DOUBLEPRECISION"):
                    if val_type == "DOUBLEPRECISION":
                        self.instructions.append("POP 1")
                    self.instructions.append("FTOI")

                if is_2slot_arr and val_type not in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION"):
                    self.instructions.append("PUSHF 0.0")
                
                if is_2slot_arr:
                    self.instructions.append("STORE 1")
                    self.instructions.append("STORE 0")
                else:
                    self.instructions.append("STORE 0")
            return

        # Atribuição normal a variável
        self.generate(node.value)
        var = self.lookup(var_name)
        if var:
            val_type = getattr(node.value, "expr_type", "INTEGER")
            
            # Conversão implícita
            if var.type in ("REAL", "DOUBLEPRECISION") and val_type == "INTEGER":
                self.instructions.append("ITOF")
                if var.type == "DOUBLEPRECISION":
                    self.instructions.append("PUSHF 0.0")
            elif var.type == "INTEGER" and val_type in ("REAL", "DOUBLEPRECISION"):
                if val_type == "DOUBLEPRECISION":
                    self.instructions.append("POP 1")
                self.instructions.append("FTOI")

            is_2slot = var.type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION")
            if is_2slot and val_type not in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION"):
                self.instructions.append("PUSHF 0.0")
            
            if var.is_ref:
                if is_2slot:
                    self.instructions.append(f"PUSHL {var.offset}") # Endereço base
                    self.instructions.append("PUSHI 1")
                    self.instructions.append("PADD")
                    self.instructions.append("SWAP")
                    self.instructions.append("STORE 0") # Guarda Parte 2 em Addr+1
                    self.instructions.append(f"PUSHL {var.offset}")
                    self.instructions.append("SWAP")
                    self.instructions.append("STORE 0") # Guarda Parte 1 em Addr
                else:
                    self.instructions.append(f"PUSHL {var.offset}")
                    self.instructions.append("SWAP")
                    self.instructions.append("STORE 0")
            elif var.scope == "GLOBAL":
                if is_2slot:
                    self.instructions.append(f"STOREG {var.offset + 1}")
                    self.instructions.append(f"STOREG {var.offset}")
                else:
                    self.instructions.append(f"STOREG {var.offset}")
            else:
                if is_2slot:
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
                elif t in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION"):
                    if t == "DOUBLEPRECISION":
                        self.instructions.append("WRITEF")
                        self.instructions.append("WRITEF")
                    else:
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
                elif t == "CHARACTER" or t == "HOLLERITH":
                    self.instructions.append("WRITES")
                else:
                    self.instructions.append("WRITEI")
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
                elif t in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION"):
                    if t == "DOUBLEPRECISION":
                        self.instructions.append("WRITEF")
                        self.instructions.append("WRITEF")
                    else:
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
                elif t == "CHARACTER" or t == "HOLLERITH":
                    self.instructions.append("WRITES")
                else:
                    self.instructions.append("WRITEI")
        self.instructions.append("WRITELN")

    def generate_Read(self, node: Any) -> None:
        if node.iolist:
            for item in node.iolist:
                # 1. Determinar o tipo do destino
                t = getattr(item, "expr_type", "INTEGER")
                
                # 2. Tratar destino
                if isinstance(item, Variable):
                    var_name = item.name
                    var = self.lookup(var_name)
                    if var:
                        self.instructions.append("READ")
                        if t == "INTEGER":
                            self.instructions.append("ATOI")
                        elif t == "REAL":
                            self.instructions.append("ATOF")
                        
                        if var.scope == "GLOBAL":
                            self.instructions.append(f"STOREG {var.offset}")
                        else:
                            self.instructions.append(f"STOREL {var.offset}")
                
                elif isinstance(item, FunctionorArraysAccess):
                    name_attr = getattr(item, "name", None)
                    var_name = getattr(name_attr, "name", name_attr)
                    var = self.lookup(var_name)
                    if var:
                        # Calcular endereço primeiro
                        self._generate_array_addr(item)
                        
                        # Ler e converter
                        self.instructions.append("READ")
                        if t == "INTEGER":
                            self.instructions.append("ATOI")
                        elif t == "REAL":
                            self.instructions.append("ATOF")
                        
                        # Guardar no endereço que está na stack
                        self.instructions.append("STORE 0")

    def generate_IntVal(self, node: Any) -> None:
        self.instructions.append(f"PUSHI {node.value}")

    def generate_RealVal(self, node: Any) -> None:
        self.instructions.append(f"PUSHF {node.value}")

    def generate_DoublePrecisionVal(self, node: Any) -> None:
        self.instructions.append(f"PUSHF {node.value}")
        self.instructions.append("PUSHF 0.0")

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
            is_2slot = var.type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION")
            if var.is_ref:
                self.instructions.append(f"PUSHL {var.offset}")
                self.instructions.append("LOAD 0")
                if is_2slot:
                    self.instructions.append(f"PUSHL {var.offset}")
                    self.instructions.append("PUSHI 1")
                    self.instructions.append("PADD")
                    self.instructions.append("LOAD 0")
            elif var.scope == "GLOBAL":
                self.instructions.append(f"PUSHG {var.offset}")
                if is_2slot:
                    self.instructions.append(f"PUSHG {var.offset + 1}")
            else:
                self.instructions.append(f"PUSHL {var.offset}")
                if is_2slot:
                    self.instructions.append(f"PUSHL {var.offset + 1}")

    def generate_BinOp(self, node: Any) -> None:
        op = node.op
        t = getattr(node, "expr_type", "INTEGER")
        l_type = getattr(node.left, "expr_type", "INTEGER")
        r_type = getattr(node.right, "expr_type", "INTEGER")
        
        complex_types = ("COMPLEX", "DOUBLECOMPLEX")
        is_any_complex = (l_type in complex_types or r_type in complex_types)
        is_any_float = (l_type in ("REAL", "DOUBLEPRECISION") or r_type in ("REAL", "DOUBLEPRECISION"))
        
        self.generate(node.left)
        if is_any_complex and l_type not in complex_types:
            self.instructions.append("PUSHF 0.0")
        elif is_any_float and l_type == "INTEGER":
            self.instructions.append("ITOF")
            
        if op not in (".AND.", ".OR."):
            self.generate(node.right)
            if is_any_complex and r_type not in complex_types:
                self.instructions.append("PUSHF 0.0")
            elif is_any_float and r_type == "INTEGER":
                self.instructions.append("ITOF")

        if t in complex_types:
            r1_var = self.lookup("__comp_r1")
            i1_var = self.lookup("__comp_i1")
            r2_var = self.lookup("__comp_r2")
            i2_var = self.lookup("__comp_i2")
            temp_var = self.lookup("__comp_temp")

            if op in ("+", "-"):
                prefix = "F"
                # Stack: R1, I1, R2, I2
                self._emit_store(i2_var)
                self._emit_store(r2_var)
                self._emit_store(i1_var)
                self._emit_store(r1_var)
                
                # Real: R1 +/- R2
                self._emit_push(r1_var)
                self._emit_push(r2_var)
                self.instructions.append(f"{prefix}{'ADD' if op == '+' else 'SUB'}")
                
                # Imag: I1 +/- I2
                self._emit_push(i1_var)
                self._emit_push(i2_var)
                self.instructions.append(f"{prefix}{'ADD' if op == '+' else 'SUB'}")
                return
            
            elif op == "*":
                # (R1, I1) * (R2, I2) -> (R1*R2 - I1*I2), (R1*I2 + I1*R2)
                self._emit_store(i2_var)
                self._emit_store(r2_var)
                self._emit_store(i1_var)
                self._emit_store(r1_var)
                
                # Real: R1*R2 - I1*I2
                self._emit_push(r1_var)
                self._emit_push(r2_var)
                self.instructions.append("FMUL")
                self._emit_push(i1_var)
                self._emit_push(i2_var)
                self.instructions.append("FMUL")
                self.instructions.append("FSUB")
                
                # Imag: R1*I2 + I1*R2
                self._emit_push(r1_var)
                self._emit_push(i2_var)
                self.instructions.append("FMUL")
                self._emit_push(i1_var)
                self._emit_push(r2_var)
                self.instructions.append("FMUL")
                self.instructions.append("FADD")
                return

            elif op == "/":
                # (R1, I1) / (R2, I2) -> [(ac+bd)/D] + [(bc-ad)/D]i onde D = c^2+d^2
                self._emit_store(i2_var)
                self._emit_store(r2_var)
                self._emit_store(i1_var)
                self._emit_store(r1_var)

                # 1. Calcular Denominador D = c^2 + d^2
                self._emit_push(r2_var)
                self._emit_push(r2_var)
                self.instructions.append("FMUL")
                self._emit_push(i2_var)
                self._emit_push(i2_var)
                self.instructions.append("FMUL")
                self.instructions.append("FADD")
                self._emit_store(temp_var)

                # 2. Parte Real: (ac + bd) / D
                self._emit_push(r1_var)
                self._emit_push(r2_var)
                self.instructions.append("FMUL")
                self._emit_push(i1_var)
                self._emit_push(i2_var)
                self.instructions.append("FMUL")
                self.instructions.append("FADD")
                self._emit_push(temp_var)
                self.instructions.append("FDIV")

                # 3. Parte Imag: (bc - ad) / D
                self._emit_push(i1_var)
                self._emit_push(r2_var)
                self.instructions.append("FMUL")
                self._emit_push(r1_var)
                self._emit_push(i2_var)
                self.instructions.append("FMUL")
                self.instructions.append("FSUB")
                self._emit_push(temp_var)
                self.instructions.append("FDIV")
                return

        # Determinar prefixo
        prefix = "F" if (l_type in ("REAL", "DOUBLEPRECISION") or r_type in ("REAL", "DOUBLEPRECISION")) else ""
        
        if op == "+":
            self.instructions.append(f"{prefix}ADD")
        elif op == "-":
            self.instructions.append(f"{prefix}SUB")
        elif op == "*":
            self.instructions.append(f"{prefix}MUL")
        elif op == "/":
            self.instructions.append(f"{prefix}DIV")
        
        # Relacionais
        elif op in (".EQ.", ".NE.", ".LT.", ".LE.", ".GT.", ".GE."):
            is_complex_comp = (l_type in complex_types or r_type in complex_types)
            is_float_comp = (l_type in ("REAL", "DOUBLEPRECISION") or r_type in ("REAL", "DOUBLEPRECISION"))
            prefix = "F" if is_float_comp else ""

            if op == ".EQ.":
                if is_complex_comp:
                    r1_var = self.lookup("__comp_r1")
                    i1_var = self.lookup("__comp_i1")
                    r2_var = self.lookup("__comp_r2")
                    i2_var = self.lookup("__comp_i2")
                    
                    self._emit_store(i2_var)
                    self._emit_store(r2_var)
                    self._emit_store(i1_var)
                    self._emit_store(r1_var)
                    
                    self._emit_push(r1_var)
                    self._emit_push(r2_var)
                    self.instructions.append("EQUAL")
                    
                    self._emit_push(i1_var)
                    self._emit_push(i2_var)
                    self.instructions.append("EQUAL")
                    
                    self.instructions.append("AND") 
                    return
                self.instructions.append("EQUAL")
            elif op == ".NE.":
                if is_complex_comp:
                    r1_var = self.lookup("__comp_r1")
                    i1_var = self.lookup("__comp_i1")
                    r2_var = self.lookup("__comp_r2")
                    i2_var = self.lookup("__comp_i2")

                    self._emit_store(i2_var)
                    self._emit_store(r2_var)
                    self._emit_store(i1_var)
                    self._emit_store(r1_var)
                    
                    self._emit_push(r1_var)
                    self._emit_push(r2_var)
                    self.instructions.append("EQUAL")
                    self.instructions.append("NOT")
                    
                    self._emit_push(i1_var)
                    self._emit_push(i2_var)
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
        
        elif op == '//':
            self.instructions.append("CONCAT")
        
        elif op == '**' or op == 'POWER':
            lbl_start = self.new_label("powStart")
            lbl_end = self.new_label("powEnd")
            
            var_base = self.lookup("__pow_base_i")
            var_exp = self.lookup("__pow_exp_i")
            var_res = self.lookup("__pow_res_i")
            
            self._emit_store(var_exp)
            self._emit_store(var_base)
            self.instructions.append("PUSHI 1")
            self._emit_store(var_res)
            
            self.instructions.append(f"{lbl_start}:")
            self._emit_push(var_exp)
            self.instructions.append("PUSHI 0")
            self.instructions.append("SUP")
            self.instructions.append(f"JZ {lbl_end}")
            
            self._emit_push(var_res)
            self._emit_push(var_base)
            self.instructions.append("MUL")
            self._emit_store(var_res)
            
            self._emit_push(var_exp)
            self.instructions.append("PUSHI 1")
            self.instructions.append("SUB")
            self._emit_store(var_exp)
            
            self.instructions.append(f"JUMP {lbl_start}")
            self.instructions.append(f"{lbl_end}:")
            self._emit_push(var_res)
        
        # Lógicos com Curto-circuito
        elif op == ".AND.":
            lbl_false = self.new_label("andFalse")
            lbl_end = self.new_label("andEnd")
            
            self.instructions.append("DUP 1")
            self.instructions.append(f"JZ {lbl_false}")
            self.instructions.append("POP 1")
            self.generate(node.right)
            self.instructions.append(f"JUMP {lbl_end}")
            
            self.instructions.append(f"{lbl_false}:")
            self.instructions.append(f"{lbl_end}:")
            return

        elif op == ".OR.": 
            lbl_true = self.new_label("orTrue")
            lbl_end = self.new_label("orEnd")
            
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
            prefix = "F" if t in ("REAL", "DOUBLEPRECISION") else ""
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
        self.instructions.append("MOD") 

    def generate_Function(self, node: Any) -> None:
        func_name = node.name.name if hasattr(node.name, "name") else node.name
        self.instructions.append(f"{func_name}:")
        self.curr_unit = func_name

        # Salvar scope anterior
        old_locals = self.locals
        old_fp_offset = self.fp_offset
        self.locals = {}

        symbols = self.semantic_info.unit_symbols.get(func_name, {}) if self.semantic_info else {}
        n_args = len(node.arguments)

        # O nome da função atua como uma variável local para o valor de retorno
        # No EWVM, CALL coloca o FP no slot logo acima dos argumentos.
        # Logo, os argumentos estão em fp[-1], fp[-2], ...
        # O RetVal está abaixo dos argumentos, em fp[-(n_args + base_size)]
        ret_type_name = node.return_type.name if hasattr(node.return_type, 'name') else str(node.return_type)
        is_complex_ret = ret_type_name in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION")
        base_size = 2 if is_complex_ret else 1
        ret_offset = -(n_args + base_size)
        ret_var = EnvVar(func_name, "LOCAL", ret_offset, ret_type_name, is_ref=False)
        self.locals[func_name] = ret_var

        self.fp_offset = 0 # Inicia em 0: locais começam em fp[0]
        self._setup_scratch_vars()

        # 1. Mapear Argumentos
        for i, arg in enumerate(node.arguments):
            offset = -n_args + i
            arg_name = arg.name if hasattr(arg, "name") else arg
            info = symbols.get(arg_name, {})
            var = EnvVar(arg_name, "LOCAL", offset, info.get("type"), is_ref=True)
            self.locals[arg_name] = var

        # 2. Mapear Variáveis Locais
        for name, info in symbols.items():
            if name not in self.locals and not info.get("is_function") and not info.get("is_subroutine"):
                var_type = info.get("type")
                is_array = info.get("is_array")
                base_size_var = 2 if var_type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION") else 1
                size = (info.get("array_size", 1) if is_array else 1) * base_size_var
                self.add_local(name, var_type, False, size)

        # Alocar espaço para as variáveis locais
        num_locals = self.fp_offset
        if num_locals > 0:
            self.instructions.append(f"PUSHN {num_locals}")

        self.generate(node.labeled_statements)
        
        # Limpar lixo local ANTES do return implícito
        if self.fp_offset > 0:
            self.instructions.append(f"POP {self.fp_offset}")

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

        self.fp_offset = 0 # Inicia em 0
        self._setup_scratch_vars()

        symbols = self.semantic_info.unit_symbols.get(sub_name, {})
        n_args = len(node.arguments)

        # 1. Mapear Argumentos (todos por referência)
        for i, arg in enumerate(node.arguments):
            offset = -n_args + i
            arg_name = arg.name if hasattr(arg, "name") else arg
            info = symbols.get(arg_name, {})
            var = EnvVar(arg_name, "LOCAL", offset, info.get("type"), is_ref=True)
            self.locals[arg_name] = var

        # 2. Mapear Variáveis Locais (apenas variáveis locais, não argumentos nem funções/subrotinas)
        for name, info in symbols.items():
            if name not in self.locals and not info.get("is_function") and not info.get("is_subroutine"):
                var_type = info.get("type")
                is_array = info.get("is_array")
                base_size_var = 2 if var_type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION") else 1
                size = (info.get("array_size", 1) if is_array else 1) * base_size_var
                self.add_local(name, var_type, False, size)

        num_locals = self.fp_offset
        if num_locals > 0:
            self.instructions.append(f"PUSHN {num_locals}")

        # 3. Gerar código da subrotina
        self.generate(node.labeled_statements)
        
        if self.fp_offset > 0:
            self.instructions.append(f"POP {self.fp_offset}")
        
        # 4. Retornar sem valor
        self.instructions.append("RETURN")

        # Restaurar scope
        self.locals = old_locals
        self.fp_offset = old_fp_offset

    def generate_Return(self, node: Any) -> None:
        if self.fp_offset > 0:
            self.instructions.append(f"POP {self.fp_offset}")
        self.instructions.append("RETURN")

    def generate_FunctionorArraysAccess(self, node: Any) -> None:
        name = node.name.name if hasattr(node.name, "name") else node.name
        
        if node.is_array:
            # 1. Obter endereço do elemento
            self._generate_array_addr(node)
            var_name = node.name.name if hasattr(node.name, "name") else node.name
            var = self.lookup(var_name)

            # 2. Carregar valor
            is_2slot_arr = var.type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION")
            if is_2slot_arr:
                self.instructions.append("DUP 1")
                self.instructions.append("LOAD 0")
                self.instructions.append("SWAP")
                self.instructions.append("LOAD 1")
            else:
                self.instructions.append("LOAD 0")

        elif node.is_function:
            # 1. Reservar espaço para o retorno
            ret_type = getattr(node, "expr_type", "INTEGER")
            if ret_type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION"):
                self.instructions.append("PUSHI 0")
                self.instructions.append("PUSHI 0")
            else:
                self.instructions.append("PUSHI 0")

            # 2. Empilhar argumentos por referência
            for i, arg in enumerate(node.expressionList):
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
                elif isinstance(arg, FunctionorArraysAccess) and arg.is_array:
                    self._generate_array_addr(arg)
                else:
                    addr_instrs = self._get_literal_addr_instrs(arg)
                    if addr_instrs:
                        self.instructions.extend(addr_instrs)
                    else:
                        self.generate(arg)
                        temp_name = f"__arg_temp_{i % 10}"
                        temp_var = self.lookup(temp_name)
                        if temp_var is None:
                            continue
                        arg_type = getattr(arg, "expr_type", "INTEGER")
                        if arg_type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION"):
                            self.instructions.append(f"STOREL {temp_var.offset + 1}")
                            self.instructions.append(f"STOREL {temp_var.offset}")
                        else:
                            self.instructions.append(f"STOREL {temp_var.offset}")
                        
                        # Passar endereço do temporário
                        self.instructions.append("PUSHFP")
                        self.instructions.append(f"PUSHI {temp_var.offset}")
                        self.instructions.append("PADD")

            # 3. Chamar a função
            self.instructions.append(f"PUSHA {name}")
            self.instructions.append("CALL")

            # 4. Limpar argumentos da pilha
            total_arg_slots = 0
            for arg in node.expressionList:
                t = getattr(arg, "expr_type", "INTEGER")
                # Em Fortran todos os argumentos são passados por referência (1 slot de endereço)
                # No entanto, se o compilador passasse o valor diretamente, isto seria necessário.
                # Mas espera! Nosso compilador PASSA O ENDEREÇO para todos os argumentos.
                # Um endereço ocupa sempre 1 SLOT.
                total_arg_slots += 1
            
            if total_arg_slots > 0:
                self.instructions.append(f"POP {total_arg_slots}")
        
        else:
            print(f"DEBUG: {name} is neither marked as array nor function!")

    def generate_Call(self, node: Call) -> None:
        name = node.subroutine.name if hasattr(node.subroutine, "name") else node.subroutine

        # 1. Empilhar argumentos por referência
        for i, arg in enumerate(node.arguments):
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
            elif isinstance(arg, FunctionorArraysAccess) and arg.is_array:
                self._generate_array_addr(arg)
            else:
                addr_instrs = self._get_literal_addr_instrs(arg)
                if addr_instrs:
                    self.instructions.extend(addr_instrs)
                else:
                    self.generate(arg)
                    temp_name = f"__arg_temp_{i % 10}"
                    temp_var = self.lookup(temp_name)
                    if temp_var is None:
                        continue
                    arg_type = getattr(arg, "expr_type", "INTEGER")
                    if arg_type in ("COMPLEX", "DOUBLECOMPLEX", "DOUBLEPRECISION"):
                        self.instructions.append(f"STOREL {temp_var.offset + 1}")
                        self.instructions.append(f"STOREL {temp_var.offset}")
                    else:
                        self.instructions.append(f"STOREL {temp_var.offset}")
                    
                    # Passar endereço do temporário
                    self.instructions.append("PUSHFP")
                    self.instructions.append(f"PUSHI {temp_var.offset}")
                    self.instructions.append("PADD")

        # 2. Chamar a subrotina
        self.instructions.append(f"PUSHA {name}")
        self.instructions.append("CALL")

        # 3. Limpar argumentos da pilha
        total_arg_slots = 0
        for arg in node.arguments:
            total_arg_slots += 1
        
        if total_arg_slots > 0:
            self.instructions.append(f"POP {total_arg_slots}")
        

    def emit(self, line):
        self.instructions.append(line)

    def emit_label(self, label):
        self.instructions.append(f"{label}:")

    def get_full_label(self, label_val: Any) -> str:
        """Retorna o nome da label prefixado pela unidade atual para evitar colisões."""
        prefix = f"{self.curr_unit}" if hasattr(self, 'curr_unit') and self.curr_unit else ""
        return f"{prefix}LABEL{label_val}"

    def new_label(self, prefix='LABEL'):
        unit_prefix = f"{self.curr_unit}" if hasattr(self, 'curr_unit') and self.curr_unit else ""
        name = f"{unit_prefix}{prefix.upper()}{getattr(self, 'label_counter', 0)}"
        self.label_counter = getattr(self, 'label_counter', 0) + 1
        return name

    def get_var_name(self, variable: Any) -> str:
        if hasattr(variable, 'name'):
            return variable.name
        return str(variable)

    def generate_expression(self, expr: Expression) -> str:
        if isinstance(expr, int):
            return str(expr)
        if hasattr(expr, 'name'):
            return expr.name
        if hasattr(expr, 'value'):
            return str(expr.value)
        self.generate(expr)
        return "" 

    def generate_Goto(self, node:Goto) -> None:
        label = self.get_full_label(node.label.value)
        self.emit(f"JUMP {label}")

    def generate_ComputedGoto(self, node:ComputedGoto) -> None:
        self.generate(node.expr)
        for idx, label in enumerate(node.labels, 1):
            self.emit("DUP 0")
            self.emit(f"PUSHI {idx}")
            self.emit("EQUAL")
            next_label = self.new_label("afterCase")
            self.emit(f"JZ {next_label}")
            self.emit("POP 1")
            self.emit(f"JUMP {self.get_full_label(label.value)}")
            self.emit_label(next_label)
        self.emit("POP 1")

    def generate_AssignedGoto(self, node:AssignedGoto) -> None:
        self.generate(node.var)
        if node.labels is None:
            self.emit("POP 1")
            return
        for label in node.labels:
            self.emit("DUP 0")
            self.emit(f"PUSHI {label.value}")
            self.emit("EQUAL")
            next_label = self.new_label("AfterCase")
            self.emit(f"JZ {next_label}")
            self.emit("POP 1")
            self.emit(f"JUMP {self.get_full_label(label.value)}")
            self.emit_label(next_label)
        self.emit("POP 1")


    def generate_BlockDO(self, node:BlockDO) -> None:
        var = self.get_var_name(node.control_var)
        loop_label = self.new_label('doStart')
        end_label = self.new_label('doEnd')
        self.generate(node.init_value)
        var_obj = self.lookup(var)
        if var_obj is None:
            return
        prefix = "F" if var_obj.type in ("REAL", "DOUBLEPRECISION") else ""
        
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
        self.emit(f"{prefix}INFEQ")
        self.emit(f"JZ {end_label}")

        for stmt in (node.labeled_statements or []):
            self.generate(stmt)

        if var_obj.scope == "GLOBAL":
            self.emit(f"PUSHG {var_obj.offset}")
        else:
            self.emit(f"PUSHL {var_obj.offset}")
        self.generate(node.step)
        self.emit(f"{prefix}ADD")
        if var_obj.scope == "GLOBAL":
            self.emit(f"STOREG {var_obj.offset}")
        else:
            self.emit(f"STOREL {var_obj.offset}")

        self.emit(f"JUMP {loop_label}")
        self.emit_label(end_label)

    def generate_LabeledDO(self, node: LabeledDO) -> None:
        var = self.get_var_name(node.control_var)
        var_obj = self.lookup(var)
        if var_obj is None:
            return
        loop_start = self.new_label("loopStart")
        loop_end = self.new_label("loopEnd")
        user_label = self.get_full_label(node.label.value)
        prefix = "F" if var_obj.type in ("REAL", "DOUBLEPRECISION") else ""

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
        self.emit(f"{prefix}INFEQ")
        self.emit(f"JZ {loop_end}")

        for stmt in (node.labeled_statements or []):
            self.generate(stmt)

        if var_obj.scope == "GLOBAL":
            self.emit(f"PUSHG {var_obj.offset}")
        else:
            self.emit(f"PUSHL {var_obj.offset}")
        self.generate(node.step)
        self.emit(f"{prefix}ADD")
        if var_obj.scope == "GLOBAL":
            self.emit(f"STOREG {var_obj.offset}")
        else:
            self.emit(f"STOREL {var_obj.offset}")

        self.emit(f"JUMP {loop_start}")
        self.emit_label(loop_end)

    def generate_Continue(self, node: Any) -> None:
        self.emit("NOP")

    def generate_ArithmeticIf(self, node):
        self.generate(node.exp)
        t = getattr(node.exp, "expr_type", "INTEGER")
        prefix = "F" if t in ("REAL", "DOUBLEPRECISION") else ""
        zero_instr = "PUSHF 0.0" if prefix == "F" else "PUSHI 0"
        
        next1 = self.new_label("arithNext")
        next2 = self.new_label("arithNext")

        self.emit("DUP 0")
        self.emit(zero_instr)
        self.emit(f"{prefix}INF")
        self.emit(f"JZ {next1}")
        self.emit("POP 1")
        self.emit(f"JUMP {self.get_full_label(node.labeln.value)}")

        self.emit_label(next1)
        self.emit("DUP 0")
        self.emit(zero_instr)
        self.emit("EQUAL")
        self.emit(f"JZ {next2}")
        self.emit("POP 1") # Limpa
        self.emit(f"JUMP {self.get_full_label(node.labelz.value)}")

        self.emit_label(next2)
        self.emit("POP 1") # Limpa
        self.emit(f"JUMP {self.get_full_label(node.labelp.value)}")

    def generate_LogicIf(self, node):
        endif_label = self.new_label("endIf")
        self.generate(node.exp)
        self.emit(f"JZ {endif_label}")
        self.generate(node.statement)
        self.emit_label(endif_label)

    def generate_BlockIf(self, node):
        else_label = self.new_label('else')
        end_label = self.new_label('endIf')
        self.generate(node.exp)
        self.emit(f"JZ {else_label}")
        
        self.generate(node.thenBody)
        
        self.emit(f"JUMP {end_label}")
        self.emit_label(else_label)
        
        if node.elseBody:
            self.generate(node.elseBody)
            
        self.emit_label(end_label)

    def get_assembly(self) -> str:
        return "\n".join(self.instructions)
