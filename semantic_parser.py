from error_classes import SemanticErrorCollector, SemanticError
from node_classes import (
    Node, Program_Unit, MainProgram, Function, Subroutine, Declaration, ArrayId,
    LabeledStatement, Assignment, Print, Write, Read, Call,
    BinOp, UnOp, Mod, FunctionorArraysAccess, Variable,
    Continue, Return, Goto, AssignedGoto, ComputedGoto,
    ArithmeticIf, LogicIf, BlockIf, LabeledDO, BlockDO,
    ComplexVal, DoublePrecisionComplexVal, Label,
    IntVal, RealVal, StringVal, LogicalVal
)

translate = {
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

    def __init__(self):
        self._scopes = [{}]

    def push_scope(self):
        self._scopes.append({})

    def pop_scope(self):
        if len(self._scopes) > 1:
            self._scopes.pop()

    def declare(self, name, var_type, is_array=False, array_size=0):
        scope = self._scopes[-1]
        if len(self._scopes) > 1:
            global_scope = self._scopes[0]
            if name in global_scope and global_scope[name].get("is_function"):
                if not is_array:
                    global_type = global_scope[name].get("type")
                    if global_type is None and var_type is not None:
                        global_scope[name]["type"] = var_type
                    elif global_type is not None and var_type is not None and global_type != var_type:
                        return False, f"Conflicting type declaration for function: '{name}'"
                    return True, ""

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

    def lookup(self, name):
        for scope in reversed(self._scopes):
            if name in scope:
                return scope[name]
        return None

    def initialize(self, name):
        for scope in reversed(self._scopes):
            if name in scope:
                scope[name]["initialized"] = True
                return True
        return False

    def is_declared(self, name):
        return self.lookup(name) is not None

    def declare_function(self, name, return_type, params):
        name = get_name(name)
        return_type = get_name(return_type) if return_type else return_type
        params = [get_name(p) for p in params]
        scope = self._scopes[0]

        scope[name] = {
            "type": return_type,
            "initialized": True,
            "is_function": True,
            "params": params,
        }
        return True, ""

    def declare_subroutine(self, name, params):
        name = get_name(name)
        params = [get_name(p) for p in params]
        scope = self._scopes[0]
        scope[name] = {
            "type": None,
            "initialized": True,
            "is_subroutine": True,
            "params": params,
        }
        return True, ""


def get_name(obj):
    if isinstance(obj, Variable):
        return obj.name
    if isinstance(obj, Label):
        return obj.value
    if isinstance(obj, str):
        return obj
    if isinstance(obj, FunctionorArraysAccess):
        return obj.name.name
    return obj


class SemanticParser:

    def __init__(self):
        self.symbols = SymbolTable()
        self.errors = SemanticErrorCollector()
        self._defined_labels = {}
        self._used_labels = []
        self._current_unit_name = None
        self._in_function = False
        self._in_do_loop = False
        self.program_units = {}
        self.unit_symbols = {} # Guarda a tabela de símbolos de cada unidade
        



    def verify(self, node):
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

    def verify_program(self, ast):
        if isinstance(ast, list):
            self.verify_global_names(ast)


            for unit in ast:
                if isinstance(unit, Function):
                    self.symbols.declare_function(
                        unit.name, unit.return_type,
                        [a.name if isinstance(a, Variable) else a for a in unit.arguments]
                    )
                elif isinstance(unit, Subroutine):
                    self.symbols.declare_subroutine(
                        unit.name,
                        [a.name if isinstance(a, Variable) else a for a in unit.arguments]
                    )

            for unit in ast:
                self.verify(unit)

    def verify_MainProgram(self, node):
        self._current_unit_name = node.name
        self._defined_labels.clear()
        self._used_labels.clear()
        self.symbols.push_scope()
        self.process_declarations(node.declarations, node)
        self.labels = []
        self.process_labeled_statements(node.labeled_statements)
        self.check_labels()
        # Salvar tabela de símbolos da unidade
        unit_name = get_name(node.name) if node.name else "MAIN"
        self.unit_symbols[unit_name] = dict(self.symbols._scopes[-1])
        self.symbols.pop_scope()
        self._current_unit_name = None

    def verify_Function(self, node):
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

        self.symbols.declare(func_name, ret_type)
        self.process_declarations(node.declarations, node)
        self.labels = []
        self.process_labeled_statements(node.labeled_statements)
        self.check_labels()
        # Salvar tabela de símbolos da unidade
        self.unit_symbols[func_name] = dict(self.symbols._scopes[-1])
        self.symbols.pop_scope()
        self._in_function = False
        self._current_unit_name = None

    def check_labels(self):
        defined_values = set(self._defined_labels.keys())
        for label_node in self._used_labels:
            label_val = get_name(label_node)
            if label_val not in defined_values:
                lineno = label_node.lineno if hasattr(label_node, 'lineno') else 0
                self.errors.add_error(f"Label {label_val} referenced but not defined", lineno)

    def verify_Declaration(self, node):
        lineno = node.lineno
        tipo = get_name(node.tipo)
        for var in node.Ids:
            name = get_name(var.name)
            is_array = var.tamanho > 0
            ok, msg = self.symbols.declare(name, tipo, is_array, var.tamanho)
            if not ok:
                self.errors.add_error(msg, lineno)

    def verify_Assignment(self, node):
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
        assign_type_translated = translate.get(assign_type)
        
        value_type_str = self.verify_expression(assign.value, lineno)
        if isinstance(value_type_str, str):
            value_type = translate.get(value_type_str)
        else:
            value_type = None
        
        if assign_type_translated is None:
            self.errors.add_error(f"Unknown type for variable {target_name}: {assign_type}", lineno)
        elif assign_type_translated != value_type and value_type is not None:
            self.errors.add_error(f"Type mismatch in assignment to {target_name}: expected {assign_type}, got {value_type_str}", lineno)

        self.symbols.initialize(target_name)


    def verify_Print(self, node):
        lineno = node.lineno
        for item in node.iolist:
            self.verify_expression(item, lineno)

    def verify_Write(self, node):
        lineno = node.lineno
        unit = node.unit
        if unit != '*':
            self.errors.add_error(
                f"WRITE para ficheiro (unit={unit}) não suportado, apenas escrita para ecrã (unit=*)",
                lineno
            )
        for item in node.iolist:
            self.verify_expression(item, lineno)

    def verify_Read(self, node):
        lineno = node.lineno
        for item in node.iolist:
            if isinstance(item, Variable):
                name = item.name
                if not self.symbols.is_declared(name):
                    self.errors.add_error(f"Undeclared variable in READ: '{name}'", lineno)
                else:
                    self.symbols.initialize(name)
            elif isinstance(item, FunctionorArraysAccess):
                name = item.name
                if isinstance(name, Variable):
                    name = name.name
                if not self.symbols.is_declared(name):
                    self.errors.add_error(f"Undeclared variable in READ: '{name}'", lineno)
                else:
                    self.symbols.initialize(name)
                for expr in item.expressionList:
                    self.verify_expression(expr, lineno)

    def verify_FunctionorArraysAccess(self, node):
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
                    for expr in node.expressionList:
                        self.verify_expression(expr, lineno)
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
        elif info.get("is_array"):
            node.is_array = True
            arraySize = info.get("array_size", 0)
            if isinstance(node.expressionList[0], IntVal):
                accessIndex = node.expressionList[0].value
                if (accessIndex > arraySize or accessIndex < 1):
                    self.errors.add_error(f"Index {accessIndex} is out of bounds for array {name} with size {arraySize}", lineno)

        for expr in node.expressionList:
            self.verify_expression(expr, lineno)
        return info.get("type")


    _arithmetic_ops = {'+', '-', '*', '/', '**'}

    _comparison_ops = {'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'}

    _logical_ops = {'AND', 'OR'}

    _numeric_types = {'INTEGER', 'REAL', 'DOUBLEPRECISION', 'COMPLEX', 'DOUBLECOMPLEX'}

    def verify_BinOp(self, node):
        lineno = node.lineno
        left_type = self.verify_expression(node.left, lineno)
        right_type = self.verify_expression(node.right, lineno)
        op = node.op


        if left_type is None or right_type is None:
            return None

        if op in self._arithmetic_ops:
            if left_type not in self._numeric_types:
                self.errors.add_error(f"Left operand of '{op}' must be numeric, got {left_type}", lineno)
                return None
            if right_type not in self._numeric_types:
                self.errors.add_error(f"Right operand of '{op}' must be numeric, got {right_type}", lineno)
                return None

            if op == '/':
                if isinstance(node.right, IntVal) and node.right.value == 0:
                    self.errors.add_error("Division by zero", lineno)
                elif isinstance(node.right, RealVal) and node.right.value == 0.0:
                    self.errors.add_error("Division by zero", lineno)

            if op == '**':
                left_is_zero = (isinstance(node.left, IntVal) and node.left.value == 0) or \
                               (isinstance(node.left, RealVal) and node.left.value == 0.0)
                right_is_neg = (isinstance(node.right, IntVal) and node.right.value < 0) or \
                               (isinstance(node.right, RealVal) and node.right.value < 0.0)
                if left_is_zero and right_is_neg:
                    self.errors.add_error("Zero raised to a negative power", lineno)

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

    def verify_UnOp(self, node):
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

        elif op == 'NOT':
            if expr_type != 'LOGICAL':
                self.errors.add_error(f"'.NOT.' requires LOGICAL operand, got {expr_type}", lineno)
                return None
            return "LOGICAL"

        return None

    def process_declarations(self, declarations, parent_node=None):
        if declarations:
            for decl in declarations:
                self.verify(decl)

    def process_labeled_statements(self, stmts:list[LabeledStatement]):
        if stmts:
            for stmt in stmts:
                self.verify(stmt)

    def verify_LabeledStatement(self, node):
        if node.label is not None:
            label_name = get_name(node.label)
            if label_name in self._defined_labels:
                self.errors.add_error(f"Duplicate label: {label_name}", node.lineno)
            else:
                self._defined_labels[label_name] = node.label
        if getattr(node, 'statement', None):
            self.verify(node.statement)

    def verify_expression(self, expr, lineno=None):
        if expr is None:
             
            return None
            
        current_lineno = expr.lineno if expr.lineno is not None else lineno
            
        def _get_type():
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
                return info.get("type")
            if isinstance(expr, ComplexVal):
                return "COMPLEX"
            if isinstance(expr, DoublePrecisionComplexVal):
                return "DOUBLECOMPLEX"
            if isinstance(expr, Node):
                return self.verify(expr)
            return None

        t = _get_type()
        if isinstance(expr, Node):
            expr.expr_type = t
        return t

    def verify_global_names(self,ast:list[Program_Unit]):
        # print(self.program_units)
        for program_unit in ast:
            name = get_name(program_unit.name)
            if name in self.program_units:
                self.errors.add_error(f"Name {name} already used", program_unit.lineno)                
            else:
                self.program_units[name] = program_unit

        # print("\n\n",self.program_units.keys())

    def verify_Call(self,node):
            call_statement = node
            if call_statement.subroutine in self.program_units:
                subroutine = self.program_units[call_statement.subroutine]
                if not isinstance(subroutine, Subroutine):
                    self.errors.add_error(f"{call_statement.subroutine.name} is not a subroutine", call_statement.lineno)
                elif len(call_statement.arguments) != len(subroutine.arguments):
                    expected_args = len(subroutine.arguments)
                    actual_args = len(call_statement.arguments)
                    self.errors.add_error(f"Wrong number of arguments calling SUBROUTINE {call_statement.subroutine.name}; expected {expected_args}, got {actual_args}", call_statement.lineno)


    def verify_Mod(self,node:Mod):
        left_type = self.verify_expression(node.left)
        print(node.right)
        right_type = self.verify_expression(node.right)
        if not (left_type == "INTEGER"):
            self.errors.add_error(f"Left side of Mod is not an Integer, is actually {left_type}")
        if not (right_type == "INTEGER"):
            self.errors.add_error(f"Right side of Mod is not an Integer, is actually {right_type}")
        if not (right_type == left_type):
            self.errors.add_error(f"Diferent types on Mod, left type = {left_type} and right type = {right_type}")
        return
        
    def verify_Statement(self, node):
        if isinstance(node, Goto):
            self._used_labels.append(node.label)
        elif isinstance(node, AssignedGoto):
            if node.labels:
                for label in node.labels:
                    self._used_labels.append(label)
        elif isinstance(node, ComputedGoto):
            for label in node.labels:
                self._used_labels.append(label)
        elif isinstance(node, ArithmeticIf):
            self._used_labels.append(node.labeln)
            self._used_labels.append(node.labelz)
            self._used_labels.append(node.labelp)
        elif isinstance(node, LogicIf):
            print("WARNING: Semantic verification for LogicIf not yet implemented.")
        elif isinstance(node, BlockIf):
            print("WARNING: Semantic verification for BlockIf not yet implemented.")
        elif isinstance(node, LabeledDO):
            if node.label:
                self._used_labels.append(node.label)
        elif isinstance(node, BlockDO):
            print("WARNING: Semantic verification for BlockDO not yet implemented.")
        if getattr(node, 'statement', None):
            self.verify(node.statement)    
