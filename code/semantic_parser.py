from __future__ import annotations
from typing import Any, Optional, Dict, List, Tuple, Set

#from sympy import arg
from error_classes import SemanticErrorCollector
from node_classes import (
    Node, Program_Unit, MainProgram, Function, Subroutine, Declaration,
    LabeledStatement, Assignment, Print, Write, Read, Call,
    BinOp, UnOp, Mod, FunctionorArraysAccess, Variable,
    Goto, AssignedGoto, ComputedGoto,
    ArithmeticIf, LogicIf, BlockIf, LabeledDO, BlockDO,
    ComplexVal, DoublePrecisionComplexVal, Label,
    IntVal, RealVal, StringVal, LogicalVal, Expression,
    Statement, Return, Continue
)

translate: Dict[str, type] = {
                "INTEGER": int,
                "REAL": float,
                "DOUBLEPRECISION": float,
                "LOGICAL": bool,
                "CHARACTER": str,
                "COMPLEX": complex,
                "DOUBLECOMPLEX": complex,
                "HOLLERITH": str,
            }

class SymbolTable:
    _scopes: List[Dict[str, Any]]

    def __init__(self) -> None:
        self._scopes = [{}]

    def push_scope(self) -> None:
        self._scopes.append({})

    def pop_scope(self) -> None:
        if len(self._scopes) > 1:
            self._scopes.pop()

    def declare(self, name: str, var_type: Optional[str], is_array: bool = False, array_size: int = 0) -> Tuple[bool, str]:
        scope = self._scopes[-1]
        
        # Se estamos num escopo local (len > 1), verificar se não choca com nome de subrotina/função global
        if len(self._scopes) > 1:
            global_scope = self._scopes[0]
            if name in global_scope:
                info = global_scope[name]
                if info.get("is_function"):
                    global_type = info.get("type")
                    if global_type is None and var_type is not None:
                        info["type"] = var_type
                        return True, ""
                    elif global_type is not None and var_type is not None and global_type != var_type:
                        return False, f"Conflicting type declaration for function: '{name}'"
                    return True, ""
                elif info.get("is_subroutine"):
                    return False, f"Name '{name}' already used as a subroutine"

        if name in scope:
            if scope[name].get("type") is None and var_type is not None:
                scope[name]["type"] = var_type
                scope[name]["is_array"] = is_array
                scope[name]["array_size"] = array_size
                return True, ""
            return False, f"Duplicate declaration: '{name}'"
        
        scope[name] = {
            "type": var_type,
            "initialized": False,
            "is_array": is_array,
            "array_size": array_size,
        }
        return True, ""

    def lookup(self, name: str) -> Optional[Dict[str, Any]]:
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def initialize(self, name: str) -> bool:
        for scope in reversed(self._scopes):
            if name in scope:
                scope[name]["initialized"] = True
                return True
        return False

    def is_declared(self, name: str) -> bool:
        return self.lookup(name) is not None

    def declare_function(self, name: Any, return_type: Optional[Any], params: List[Any]) -> Tuple[bool, str]:
        name_str = get_name(name)
        ret_type_str = get_name(return_type) if return_type else None
        params_str = [get_name(p) for p in params]
        scope = self._scopes[0]

        if name_str in scope:
            return False, f"Duplicate program unit name: '{name_str}'"

        scope[name_str] = {
            "type": ret_type_str,
            "initialized": True,
            "is_function": True,
            "params": params_str,
        }
        return True, ""

    def declare_subroutine(self, name: Any, params: List[Any]) -> Tuple[bool, str]:
        name_str = get_name(name)
        params_str = [get_name(p) for p in params]
        scope = self._scopes[0]

        if name_str in scope:
            return False, f"Duplicate program unit name: '{name_str}'"

        scope[name_str] = {
            "type": None,
            "initialized": True,
            "is_subroutine": True,
            "params": params_str,
        }
        return True, ""


def get_name(obj: Any) -> Any:
    if isinstance(obj, Variable):
        return obj.name
    if isinstance(obj, Label):
        return obj.value
    if isinstance(obj, str):
        return obj
    if isinstance(obj, FunctionorArraysAccess):
        return get_name(obj.name)
    return obj


class SemanticParser:
    symbols: SymbolTable
    errors: SemanticErrorCollector
    _defined_labels: Dict[Any, Any]
    _used_labels: List[Any]
    _current_unit_name: Optional[str]
    _in_function: bool
    _in_subroutine: bool
    _in_do_loop: bool
    program_units: Dict[str, Program_Unit]
    unit_symbols: Dict[str, Dict[str, Any]]

    def __init__(self) -> None:
        self.symbols = SymbolTable()
        self.errors = SemanticErrorCollector()
        self._defined_labels = {}
        self._used_labels = []
        self._current_unit_name = None
        self._in_function = False
        self._in_subroutine = False
        self._in_do_loop = False
        self.program_units = {}
        self.unit_symbols = {} # Guarda a tabela de símbolos de cada unidade
        
    def get_implicit_type(self, name: str) -> str:
        if name and name[0].upper() in 'IJKLMN':
            return "INTEGER"
        return "REAL"

    def apply_implicit_typing(self) -> None:
        # Aplica regra I-N a todos os símbolos do escopo atual que não têm tipo
        scope = self.symbols._scopes[-1]
        for name, info in scope.items():
            if not info.get("is_subroutine") and info.get("type") is None:
                info["type"] = self.get_implicit_type(name)

    def verify(self, node: Any) -> Any:
        if node is None:
            
            return None
        if isinstance(node, list):
            for item in node:
                self.verify(item)
   
            return None
        class_name = type(node).__name__
        method_name = f"verify_{class_name}"
        method = getattr(self, method_name, None)
        if method:
            return method(node)
        
        if node is not None:
            print(f"ERROR: Semantic verification not implemented: {method_name}")
 
        return None

    def verify_program(self, ast: List[Program_Unit]) -> None:
        if isinstance(ast, list):
            self.verify_global_names(ast)


            for unit in ast:
                if isinstance(unit, Function):
                    self.symbols.declare_function(
                        unit.name, unit.return_type,
                        [get_name(a) for a in unit.arguments]
                    )
                elif isinstance(unit, Subroutine):
                    self.symbols.declare_subroutine(
                        unit.name,
                        [get_name(a) for a in unit.arguments]
                    )

            for unit in ast:
                self.verify(unit)

    def verify_MainProgram(self, node: MainProgram) -> None:
        self._current_unit_name = get_name(node.name)
        self._defined_labels.clear()
        self._used_labels.clear()
        self.symbols.push_scope()
        self.process_declarations(node.declarations)
        self.apply_implicit_typing() # Aplica regra I-N após declarações explícitas
        self.labels = []
        self.process_labeled_statements(node.labeled_statements)
        self.collect_labeled_do_bodies(node.labeled_statements)
        self.check_labels()
        # Salvar tabela de símbolos da unidade
        unit_name = get_name(node.name) if node.name else "MAIN"
        self.unit_symbols[unit_name] = dict(self.symbols._scopes[-1])
        self.symbols.pop_scope()
        self._current_unit_name = None

    def verify_Function(self, node: Function) -> None:
        func_name = get_name(node.name)
        ret_type = get_name(node.return_type)
        self._current_unit_name = func_name
        self._in_function = True
        self._defined_labels.clear()
        self._used_labels.clear()
        self.symbols.push_scope()

        seen_args = set()
        for arg in node.arguments:
            name = get_name(arg)
            if name in seen_args:
                self.errors.add_error(f"Duplicate argument name in function {func_name}: {name}", node.lineno)
            else:
                seen_args.add(name)
                self.symbols.declare(name, None)
                self.symbols.initialize(name) # Argumentos são considerados inicializados pela chamada

        self.symbols.declare(func_name, ret_type)
        self.process_declarations(node.declarations)
        self.apply_implicit_typing() # Aplica regra I-N após declarações explícitas

        # Verificar atribuição de retorno
        local_scope = self.symbols._scopes[-1]
        func_symbol = local_scope.get(func_name)
        if func_symbol:
            func_symbol["initialized"] = False

        self.labels = []
        self.process_labeled_statements(node.labeled_statements)
        self.collect_labeled_do_bodies(node.labeled_statements)
        self.check_labels()

        # Verificar se houve atribuição ao nome da função
        if func_symbol and not func_symbol.get("initialized"):
            lineno = node.lineno if hasattr(node, "lineno") else 0
            self.errors.add_error(f"Return variable '{func_name}' is not assigned a value in function", lineno)

        # Garantir que a função fica marcada como inicializada para os chamadores
        if func_symbol:
            func_symbol["initialized"] = True

        # Salvar tabela de símbolos da unidade (incluindo acesso a globais se necessário para debug)
        self.unit_symbols[func_name] = {**self.symbols._scopes[0], **self.symbols._scopes[-1]}
        self.symbols.pop_scope()
        self._in_function = False
        self._current_unit_name = None


    def verify_Subroutine(self, node: Subroutine) -> None:
        subroutine_name = get_name(node.name)
        self._current_unit_name = subroutine_name
        self._in_subroutine = True
        self._defined_labels.clear()
        self._used_labels.clear()
        self.symbols.push_scope()

        seen_args = set()
        for arg in node.arguments:
            name = get_name(arg)
            if name in seen_args:
                self.errors.add_error(f"Duplicate argument name in subroutine {subroutine_name}: {name}", node.lineno)
            else:
                seen_args.add(name)
                self.symbols.declare(name, None)
                self.symbols.initialize(name) # Argumentos inicializados pela chamada

        self.process_declarations(node.declarations)

        global_scope = self.symbols._scopes[0]
        subroutine_symbol = global_scope.get(subroutine_name)
        if subroutine_symbol:
            subroutine_symbol["initialized"] = False

        self.labels = []
        self.process_labeled_statements(node.labeled_statements)
        self.check_labels()

        # Garantir que a subrotina fica marcada como inicializada para os chamadores
        if subroutine_symbol:
            subroutine_symbol["initialized"] = True

        # Salvar tabela de símbolos da unidade
        self.unit_symbols[subroutine_name] = dict(self.symbols._scopes[-1])
        self.symbols.pop_scope()
        self._in_subroutine = False
        self._current_unit_name = None

    def check_labels(self) -> None:
        defined_values = set(self._defined_labels.keys())
        for label_node in self._used_labels:
            label_val = get_name(label_node)
            if label_val not in defined_values:
                lineno = label_node.lineno if hasattr(label_node, 'lineno') else 0
                self.errors.add_error(f"Label {label_val} referenced but not defined", lineno)

    def verify_Declaration(self, node: Declaration) -> None:
        lineno = node.lineno
        tipo = get_name(node.tipo)
        for var in node.Ids:
            name = get_name(var.name)
            is_array = var.tamanho > 0
            ok, msg = self.symbols.declare(name, tipo, is_array, var.tamanho)
            if not ok:
                self.errors.add_error(msg, lineno)

    def verify_Assignment(self, node: Assignment) -> None:
        lineno = node.lineno
        assign = node
                        
        target_name = get_name(assign.name)
        
        info = self.symbols.lookup(target_name)
        if not info:
            self.errors.add_error(f"Undeclared variable: {target_name}", lineno)
            return

        if info.get("is_subroutine"):
            self.errors.add_error(f"Cannot assign to subroutine name: {target_name}", lineno)
            return
        if isinstance(assign.name, FunctionorArraysAccess):
            if info.get("is_function"):
                self.errors.add_error(f"Cannot assign to function call: {target_name}", lineno)
                return
            if not info.get("is_array"):
                self.errors.add_error(f"Variable is not an array: {target_name}", lineno)
                return
            for idx_expr in assign.name.expressionList:
                self.verify_expression(idx_expr, lineno)

        else:
            if info.get("is_function"):
                if target_name != self._current_unit_name:
                    self.errors.add_error(f"Cannot assign to function name: {target_name}", lineno)
                    return
            elif info.get("is_array"):
                self.errors.add_error(f"Cannot assign to array without index: {target_name}", lineno)
                return

        assign_type = info.get("type")
        assign_type_translated = translate.get(assign_type) if assign_type else None
        
        value_result = self.verify_expression(assign.value, lineno)
        if isinstance(value_result, str):
            value_type = translate.get(value_result)
        else:
            value_type = None
        
        if assign_type and assign_type_translated is None:
            self.errors.add_error(f"Unknown type for variable {target_name}: {assign_type}", lineno)
        elif assign_type_translated != value_type and value_type is not None:
            self.errors.add_error(f"Type mismatch in assignment to {target_name}: expected {assign_type}, got {value_result}", lineno)
        elif value_type is None:
            self.errors.add_error(f"Type error, assinging no type to variable of type {assign_type} ")

        self.symbols.initialize(target_name)


    def verify_Print(self, node: Print) -> None:
        lineno = node.lineno
        for item in node.iolist:
            self.verify_expression(item, lineno)

    def verify_Write(self, node: Write) -> None:
        lineno = node.lineno
        unit = node.unit
        if unit != '*':
            self.errors.add_error(
                f"WRITE para ficheiro (unit={unit}) não suportado, apenas escrita para ecrã (unit=*)",
                lineno
            )
        for item in node.iolist:
            self.verify_expression(item, lineno)

    def verify_Read(self, node: Read) -> None:
        lineno = node.lineno
        for item in node.iolist:
            if isinstance(item, Variable):
                name = item.name
                info = self.symbols.lookup(name)
                if info is None:
                    self.errors.add_error(f"Undeclared variable in READ: '{name}'", lineno)
                else:
                    self.symbols.initialize(name)
                    item.expr_type = info.get("type")
            elif isinstance(item, FunctionorArraysAccess):
                name = get_name(item.name)
                info = self.symbols.lookup(name)
                if info is None:
                    self.errors.add_error(f"Undeclared variable in READ: '{name}'", lineno)
                else:
                    self.symbols.initialize(name)
                    item.expr_type = info.get("type")
                for expr in item.expressionList:
                    self.verify_expression(expr, lineno)

    def verify_FunctionorArraysAccess(self, node: FunctionorArraysAccess) -> Optional[str]:
        lineno = node.lineno
        name = get_name(node.name)
        info = self.symbols.lookup(name)
        
        if info is None:
            if name in self.program_units:
                func_unit = self.program_units[name]
                if isinstance(func_unit, Function):
                    node.is_function = True
                    node.is_array = False
                    expected = len(func_unit.arguments)
                    actual = len(node.expressionList)
                    if expected != actual:
                        self.errors.add_error(f"Wrong number of arguments calling function {name}; expected {expected}, got {actual}", lineno)
                    
                    # Verificação de tipos dos argumentos
                    for i, expr in enumerate(node.expressionList):
                        expr_type = self.verify_expression(expr, lineno)
                        if i < expected:
                            arg_name = get_name(func_unit.arguments[i])
                            # Procurar tipo na declaração da função chamada
                            expected_type = None
                            for decl in func_unit.declarations:
                                for decl_id in decl.Ids:
                                    if get_name(decl_id.name) == arg_name:
                                        expected_type = get_name(decl.tipo)
                                        break
                                if expected_type:
                                    break
                            
                            if expr_type and expected_type and expr_type != expected_type:
                                self.errors.add_error(f"Type mismatch for argument {i+1} of function {name}: expected {expected_type}, got {expr_type}", lineno)
                    
                    return get_name(func_unit.return_type)
            
            self.errors.add_error(f"Undeclared function or array: {name}", lineno)
            for expr in node.expressionList:
                self.verify_expression(expr, lineno)
            return None

        if info.get("is_function"):
            node.is_function = True
            expected_params = info.get("params", [])
            if len(node.expressionList) != len(expected_params):
                exp_len = len(expected_params)
                exprLis = len(node.expressionList)
                self.errors.add_error(f"Wrong number of arguments calling function {name}; expected {exp_len}, got {exprLis}", lineno)
            
            # Verificação de tipos dos argumentos (procurar na unidade correspondente se disponível)
            func_unit = self.program_units.get(name)
            for i, expr in enumerate(node.expressionList):
                expr_type = self.verify_expression(expr, lineno)
                if func_unit and isinstance(func_unit, Function) and i < len(expected_params):
                    arg_name = expected_params[i]
                    expected_type = None
                    for decl in func_unit.declarations:
                        for decl_id in decl.Ids:
                            if get_name(decl_id.name) == arg_name:
                                expected_type = get_name(decl.tipo)
                                break
                        if expected_type:
                            break
                    if expr_type and expected_type and expr_type != expected_type:
                        self.errors.add_error(f"Type mismatch for argument {i+1} of function {name}: expected {expected_type}, got {expr_type}", lineno)
            return info.get("type")

        elif info.get("is_array"):
            node.is_array = True
            arraySize = info.get("array_size", 0)
            if node.expressionList and isinstance(node.expressionList[0], IntVal):
                accessIndex = node.expressionList[0].value
                if (accessIndex > arraySize or accessIndex < 1):
                    self.errors.add_error(f"Index {accessIndex} is out of bounds for array {name} with size {arraySize}", lineno)
        else:
            self.errors.add_error(f"{name} is not a function nor an array.")
            return None
        for expr in node.expressionList:
            self.verify_expression(expr, lineno)
        return info.get("type")


    _arithmetic_ops: Set[str] = {'+', '-', '*', '/', '**'}

    _comparison_ops: Set[str] = {'.EQ.', '.NE.', '.LT.', '.LE.', '.GT.', '.GE.'}

    _logical_ops: Set[str] = {'.AND.', '.OR.', '.EQV.', '.NEQV.'}

    _numeric_types: Set[str] = {'INTEGER', 'REAL', 'DOUBLEPRECISION', 'COMPLEX', 'DOUBLECOMPLEX'}

    def verify_BinOp(self, node: BinOp) -> Optional[str]:
        lineno = node.lineno
        left_type = self.verify_expression(node.left, lineno)
        right_type = self.verify_expression(node.right, lineno)
        op = node.op

        if left_type is None:
            self.errors.add_error(f"Left operand of '{op}' must doesn't have a type", lineno)
            return None
        if right_type is None:
            self.errors.add_error(f"Right operand of '{op}' must doesn't have a type", lineno)
            return None

        if op in self._arithmetic_ops:
            if left_type not in self._numeric_types:
                self.errors.add_error(f"Left operand of '{op}' must be numeric, got {left_type}", lineno)
                return None
            if right_type not in self._numeric_types:
                self.errors.add_error(f"Right operand of '{op}' must be numeric, got {right_type}", lineno)
                return None

            # if op == '/':
            #     if isinstance(node.right, IntVal) and node.right.value == 0:
            #         self.errors.add_error("Division by zero", lineno)
            #     elif isinstance(node.right, RealVal) and node.right.value == 0.0:
            #         self.errors.add_error("Division by zero", lineno)

            # if op == '**':
            #     left_is_zero = (isinstance(node.left, IntVal) and node.left.value == 0) or \
            #                    (isinstance(node.left, RealVal) and node.left.value == 0.0)
            #     right_is_neg = (isinstance(node.right, IntVal) and node.right.value < 0) or \
            #                    (isinstance(node.right, RealVal) and node.right.value < 0.0)
            #     if left_is_zero and right_is_neg:
            #         self.errors.add_error("Zero raised to a negative power", lineno)

            if left_type == right_type:
                return left_type
            type_priority = ['INTEGER', 'REAL', 'DOUBLEPRECISION', 'COMPLEX', 'DOUBLECOMPLEX']
            left_p = type_priority.index(left_type) if left_type in type_priority else 0
            right_p = type_priority.index(right_type) if right_type in type_priority else 0
            return type_priority[max(left_p, right_p)]

        elif op in self._comparison_ops:
            if left_type not in self._numeric_types or right_type not in self._numeric_types:
                self.errors.add_error(f"Comparison operator '.{op}.' requires numeric operands, got {left_type} and {right_type}", lineno)
                return None
            
            # Impedir comparação de ordem em complexos
            if left_type == "COMPLEX" or right_type == "COMPLEX":
                if op in (".LT.", ".LE.", ".GT.", ".GE.", "LT", "LE", "GT", "GE"):
                    self.errors.add_error(f"Operadores relacionais de ordem ({op}) nao sao permitidos para numeros complexos.", lineno)

            return "LOGICAL"

        elif op in self._logical_ops:
            if left_type != 'LOGICAL':
                self.errors.add_error(f"Left operand of '.{op}.' must be LOGICAL, got {left_type}", lineno)
                return None
            if right_type != 'LOGICAL':
                self.errors.add_error(f"Right operand of '.{op}.' must be LOGICAL, got {right_type}", lineno)
                return None
            return "LOGICAL"

        elif op == 'CONCAT':
            if left_type != 'CHARACTER':
                self.errors.add_error(f"Left operand of '//' must be CHARACTER, got {left_type}", lineno)
                return None
            if right_type != 'CHARACTER':
                self.errors.add_error(f"Right operand of '//' must be CHARACTER, got {right_type}", lineno)
                return None
            return "CHARACTER"

        return None

    def verify_UnOp(self, node: UnOp) -> Optional[str]:
        lineno = node.lineno
        expr_type = self.verify_expression(node.expr, lineno)
        op = node.op

        if expr_type is None:
            return None

        if op in ('+', '-'):
            if expr_type not in self._numeric_types:
                self.errors.add_error(f"Unary '{op}' requires numeric operand, got {expr_type}", lineno)
                return None
            return expr_type
        
        elif op == ".NOT.":
            if expr_type != "LOGICAL":
                self.errors.add_error(f"Operand of '.NOT.' must be LOGICAL, got {expr_type}", lineno)
                return None
            return "LOGICAL"

        return None

        return None

    def process_declarations(self, declarations: List[Declaration]) -> None:
        if declarations:
            for decl in declarations:
                self.verify(decl)

    def process_labeled_statements(self, stmts: List[LabeledStatement]) -> None:
        if stmts:
            for stmt in stmts:
                self.verify(stmt)

    def verify_LabeledStatement(self, node: LabeledStatement) -> None:
        if node.label is not None:
            label_name = get_name(node.label)
            if label_name in self._defined_labels:
                self.errors.add_error(f"Duplicate label: {label_name}", node.lineno)
            else:
                self._defined_labels[label_name] = node.label
        if getattr(node, 'statement', None) and node.statement:
            self.verify(node.statement)

    def verify_expression(self, expr: Expression, lineno: Optional[int] = None) -> Optional[str]:
        if expr is None:
            
            return None
            
        current_lineno = getattr(expr, 'lineno', lineno)
            
        def _get_type() -> Optional[str]:
            if isinstance(expr, LogicalVal):
                return "LOGICAL"
            if isinstance(expr, IntVal):
                return "INTEGER"
            if isinstance(expr, RealVal):
                return "REAL"
            if isinstance(expr, StringVal):
                return "CHARACTER"
            if isinstance(expr, Variable):
                name = expr.name
                info = self.symbols.lookup(name)
                if info is None:
                    self.errors.add_error(f"Undeclared variable: '{name}'", current_lineno)
                    return None
                
                # Verificar se a variável foi inicializada (exceto se for argumento de função, mas por agora check básico)
                if not info.get("initialized"):
                    # Evitar erro se estivermos numa função e o nome for o da própria função (valor de retorno)
                    if not (self._in_function and name == self._current_unit_name):
                        self.errors.add_error(f"Usage of uninitialized variable: '{name}'", current_lineno)
                
                return info.get("type")
            if isinstance(expr, ComplexVal):
                return "COMPLEX"
            if isinstance(expr, DoublePrecisionComplexVal):
                return "DOUBLECOMPLEX"
            if isinstance(expr, Node):
                print(expr)
                r = self.verify(expr)
                print(r)
                return r
            return None
        
        t = _get_type()


        if isinstance(expr, Node):
            expr.expr_type = t
        return t

    def verify_global_names(self, ast: List[Program_Unit]) -> None:
        # print(self.program_units)
        for program_unit in ast:
            name = get_name(program_unit.name)
            if name in self.program_units:
                self.errors.add_error(f"Name {name} already used", program_unit.lineno)                
            else:
                self.program_units[name] = program_unit

        # print("\n\n",self.program_units.keys())

    def verify_Call(self, node: Call) -> None:
            call_statement = node
            sub_name = get_name(call_statement.subroutine)
            if sub_name in self.program_units:
                subroutine = self.program_units[sub_name]
                if not isinstance(subroutine, Subroutine):
                    self.errors.add_error(f"{sub_name} is not a subroutine", call_statement.lineno)
                elif len(call_statement.arguments) != len(subroutine.arguments):
                    expected_args = len(subroutine.arguments)
                    actual_args = len(call_statement.arguments)
                    self.errors.add_error(f"Wrong number of arguments calling SUBROUTINE {sub_name}; expected {expected_args}, got {actual_args}", call_statement.lineno)


    def verify_Mod(self, node: Mod) -> Optional[str]:
        lineno = node.lineno
        left_type = self.verify_expression(node.left, lineno)
        right_type = self.verify_expression(node.right, lineno)
        if not (left_type == "INTEGER"):
            self.errors.add_error(f"Left side of Mod is not an Integer, is actually {left_type}", lineno)
        if not (right_type == "INTEGER"):
            self.errors.add_error(f"Right side of Mod is not an Integer, is actually {right_type}", lineno)
        if left_type == "INTEGER" and right_type == "INTEGER":
            return "INTEGER"
        elif left_type and right_type and left_type != right_type:
            self.errors.add_error(f"Different types on Mod, left type = {left_type} and right type = {right_type}", lineno)
        return None

    def verify_Return(self, node: Return) -> None:
        if not self._in_function and not self._in_subroutine:
            self.errors.add_error("RETURN statement outside of FUNCTION or SUBROUTINE", node.lineno)

    def verify_Continue(self, node: Continue) -> None:
        pass

    def verify_Statement(self, node: Statement) -> None:
        if isinstance(node, Goto):
            self.verify_Goto(node)
        elif isinstance(node, AssignedGoto):
            self.verify_AssignedGoto(node)
        elif isinstance(node, ComputedGoto):
            self.verify_ComputedGoto(node)
        elif isinstance(node, ArithmeticIf):
            self.verify_ArithmeticIf(node)
        elif isinstance(node, LogicIf):
            self.verify_LogicIf(node)
        elif isinstance(node, BlockIf):
            self.verify_BlockIf(node)
        elif isinstance(node, LabeledDO):
            self.verify_LabeledDO(node)
        elif isinstance(node, BlockDO):
            self.verify_BlockDO(node)
        if getattr(node, 'statement', None):
            self.verify(node.statement)   
    
    def verify_Goto(self, node:Goto):
        self._used_labels.append(node.label)

    def verify_ComputedGoto(self, node:ComputedGoto):
        for label in node.labels:
            self._used_labels.append(label)
        expr_type = self.verify_expression(node.expr, node.lineno)
        if expr_type != "INTEGER" or expr_type!= "REAL":
            self.errors.add_error(f"Computed GOTO index (expression) must be INTEGER/REAL, got {expr_type}", node.lineno)

    def verify_AssignedGoto(self, node:AssignedGoto):
        var_name = node.var.name
        var_info = self.symbols.lookup(var_name)
        if not var_info:
            self.errors.add_error(f"Assigned GOTO variable '{var_name}' is not declared", getattr(node, 'leneno', None))
        elif var_info.get("type") != "INTEGER":
            self.errors.add_error(f"Assigned GOTO variable '{var_name}' must be of type INTEGER, got {var_info.get('type')}",getattr(node, 'lineno', None))
        
        if node.labels:
            for label in node.labels:
                self._used_labels.append(label)
    

    def collect_labeled_do_bodies(self, labeled_statements):
        i = 0
        n = len(labeled_statements)
        result = []
        while i < n:
            stmt = labeled_statements[i]
            if isinstance(stmt.statement, LabeledDO) and stmt.statement.labeled_statements is None:
                loop = stmt.statement
                loop_body = []
                i += 1
                while i < n:
                    next_stmt = labeled_statements[i]
                    if (next_stmt.label is not None
                        and next_stmt.label.value == loop.label.value):
                        break
                    loop_body.append(next_stmt)
                    i += 1
                loop.labeled_statements = loop_body
                result.append(stmt)
                if i < n:
                    result.append(labeled_statements[i])
                i += 1
            else:
                result.append(stmt)
                i += 1
        return result

    def verify_LabeledDO(self, node):
        allowed_numeric_types = {"INTEGER", "REAL", "DOUBLEPRECISION"}
        lineno = getattr(node, "lineno", None)
        var_name = node.control_var.name
        var_info = self.symbols.lookup(var_name)
        if not var_info:
            self.errors.add_error(f"Labeled DO loop control variable '{var_name}' is not declared.", lineno)
        else:
            if var_info.get("type") not in allowed_numeric_types:
                self.errors.add_error(f"Labeled DO loop control variable '{var_name}' must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {var_info.get('type')}.", lineno)
            self.symbols.initialize(var_name) # Inicializada pelo ciclo DO

        init_type = self.verify_expression(node.control_var_init_value, lineno)
        if init_type not in allowed_numeric_types:
            self.errors.add_error(f"Labeled DO loop initial value must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {init_type}.", lineno)
        
        final_type = self.verify_expression(node.iterations_number, lineno)
        if final_type not in allowed_numeric_types:
            self.errors.add_error(f"Labeled DO loop final value must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {final_type}.", lineno)
        
        if getattr(node, 'step', None) is not None:
            step_type = self.verify_expression(node.step, lineno)
            if step_type not in allowed_numeric_types:
                self.errors.add_error(f"Labeled DO loop step value must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {step_type}.", lineno)
        
        if node.label is not None:
            self._used_labels.append(node.label)
    
    def verify_BlockDO(self, node:BlockDO):
        allowed_numeric_types = {"INTEGER", "REAL", "DOUBLEPRECISION"}
        lineno = getattr(node, "lineno", None)
        var_name = node.control_var.name
        var_info = self.symbols.lookup(var_name)
        if not var_info:
            self.errors.add_error(f"Block DO loop control variable '{var_name}' is not declared.", lineno)
        else:
            if var_info.get("type") not in allowed_numeric_types:
                self.errors.add_error(f"Block DO loop control variable '{var_name}' must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {var_info.get('type')}.", lineno)
            self.symbols.initialize(var_name) # Inicializada pelo ciclo DO

        init_type = self.verify_expression(node.init_value, lineno)
        if init_type not in allowed_numeric_types:
            self.errors.add_error(f"Block DO loop initial value must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {init_type}.", lineno)

        final_type = self.verify_expression(node.max_value, lineno)
        if final_type not in allowed_numeric_types:
            self.errors.add_error(f"Block DO loop final value must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {final_type}.", lineno)

        if getattr(node, "step", None) is not None:
            step_type = self.verify_expression(node.step, lineno)
            if step_type not in allowed_numeric_types:
                self.errors.add_error(f"Block DO loop step value must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {step_type}.", lineno)

        if getattr(node, "labeled_statements", None):
            for labeled_stmt in node.labeled_statements:
                self.verify(labeled_stmt)

    def verify_ArithmeticIf(self, node:ArithmeticIf):
        allowed_types = {"INTEGER", "REAL", "DOUBLEPRECISION"}
        lineno = getattr(node, "lineno", None)
        expr_type = self.verify_expression(node.exp, lineno)

        if expr_type not in allowed_types:
            self.errors.add_error(f"Arithmetic IF condition must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {expr_type}.", lineno)
            
        self._used_labels.append(node.labeln)
        self._used_labels.append(node.labelz)
        self._used_labels.append(node.labelp)

    def verify_LogicIf(self, node:LogicIf):
        cond_type = self.verify_expression(node.exp, node.lineno)
        if cond_type != "LOGICAL":
            self.errors.add_error(f"Logical IF condition must be LOGICAL, got {cond_type}", node.lineno)
        self.verify(node.statement)

    def verify_BlockIf(self, node:BlockIf):
        cond_type = self.verify_expression(node.exp, node.lineno)
        if cond_type != "LOGICAL":
            self.errors.add_error(f"Block IF condition must be LOGICAL, got {cond_type}", node.lineno)

        for stmt in node.thenBody:
            self.verify(stmt)

        if node.elseBody:#!=None
            if isinstance(node.elseBody, list):#==[LabeledStatement]
                for stmt in node.elseBody:
                    self.verify(stmt)
            else:#==outro BlockIf
                self.verify(node.elseBody)



