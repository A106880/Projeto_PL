from error_classes import SemanticErrorCollector, SemanticError
from node_classes import (
    Node, Program_Unit, ProgramaPrincipal, Funcao, Subroutine, Declaracao, ArrayId,
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

 
        return None

    def verify_program(self, ast):
        if isinstance(ast, list):
            self.verify_global_names(ast)


            for unit in ast:
                if isinstance(unit, Funcao):
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

    def verify_ProgramaPrincipal(self, node):
        self._current_unit_name = node.name
        self._defined_labels.clear()
        self._used_labels.clear()
        self.symbols.push_scope()
        self.process_declarations(node.declarations, node)
        self.labels = []
        self.process_labeled_statements(node.labeled_statements)
        self.check_labels()
        self.collect_labeled_do_bodies(node.labeled_statements)
        # Salvar tabela de símbolos da unidade
        unit_name = get_name(node.name) if node.name else "MAIN"
        self.unit_symbols[unit_name] = dict(self.symbols._scopes[-1])
        self.symbols.pop_scope()
        self._current_unit_name = None

    def verify_Funcao(self, node):
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
        self.collect_labeled_do_bodies(node.labeled_statements)
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

    def verify_Declaracao(self, node):
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
        name = node.name.name 
        info = self.symbols.lookup(name)
        if info is None:
            if hasattr(node.name, 'name') and node.name in self.program_units:
                func_unit = self.program_units[node.name]
                if isinstance(func_unit, Funcao):
                    node.is_function = True
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
            
        current_lineno = getattr(expr, 'lineno', lineno)
            
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
        print(self.program_units)
        for program_unit in ast:
            print(program_unit.name)
        
            if program_unit.name in self.program_units:
                self.errors.add_error(f"Name {program_unit.name.name} already used", program_unit.lineno)                
            else:
                self.program_units[program_unit.name] = program_unit

        print("\n\n",self.program_units.keys())

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
        new_list = []
        while i < n:
            stmt = labeled_statements[i]
            real_stmt = getattr(stmt, 'statement', None)
            if isinstance(real_stmt, LabeledDO) and real_stmt.labeled_statements is None:
                target_label = real_stmt.label.value
                body = []
                j = i+1
                while j < n:
                    s = labeled_statements[j]
                    body.append(s)
                    if s.label and getattr(s.label, 'value', None) == target_label:
                        break
                    j += 1
                real_stmt.labeled_statements = body
                new_list.append(stmt)
                i = j+1
            else:
                new_list.append(stmt)
                i += 1
        labeled_statements[:] = new_list

    def verify_LabeledDO(self, node):
        allowed_numeric_types = {"INTEGER", "REAL", "DOUBLEPRECISION"}
        lineno = getattr(node, "lineno", None)
        var_name = node.control_var.name
        var_info = self.symbols.lookup(var_name)
        if not var_info:
            self.errors.add_error(f"Labeled DO loop control variable '{var_name}' is not declared.", lineno)
        elif var_info.get("type") not in allowed_numeric_types:
            self.errors.add_error(f"Labeled DO loop control variable '{var_name}' must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {var_info.get('type')}.", lineno)
        
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
        elif var_info.get("type") not in allowed_numeric_types:
            self.errors.add_error(f"Block DO loop control variable '{var_name}' must be numeric (INTEGER, REAL, DOUBLEPRECISION), got {var_info.get('type')}.", lineno)

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



