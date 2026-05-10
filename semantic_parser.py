from error_classes import SemanticErrorCollector, SemanticError
from node_classes import (
    Node, Program_Unit, ProgramaPrincipal, Funcao, Subroutine, Declaracao, ArrayId,
    LabeledStatement, Assignment, Print, Read, Call,
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
        self._defined_labels = set()
        self._used_labels = []
        self._current_unit_name = None
        self._in_function = False
        self._in_do_loop = False
        self.program_units = {}
        self.labels = []
        



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
        self.symbols.pop_scope()
        self._current_unit_name = None

    def verify_Funcao(self, node):
        self._current_unit_name = get_name(node.name)
        self._in_function = True
        self._defined_labels.clear()
        self._used_labels.clear()
        self.symbols.push_scope()

        for arg in node.arguments:
            name = get_name(arg)
            self.symbols.declare(name, None)

        func_name = get_name(node.name)
        ret_type = get_name(node.return_type)
        self.symbols.declare(func_name, ret_type)
        self.process_declarations(node.declarations, node)
        self.labels = []
        self.process_labeled_statements(node.labeled_statements)
        self.symbols.pop_scope()
        self._in_function = False
        self._current_unit_name = None

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
        if info.get("is_function"):
            self.errors.add_error(f"Cannot assign to function name: {target_name}", lineno)
            return
        if info.get("is_subroutine"):
            self.errors.add_error(f"Cannot assign to subroutine name: {target_name}", lineno)
            return
        if info.get("is_array"):
            self.errors.add_error(f"Cannot assign to array name without index: {target_name}", lineno)
            return
        if not info.get("is_array") and isinstance(node.name, FunctionorArraysAccess):
            self.errors.add_error(f"This variable is not an array: {target_name}", lineno)
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
        #FIXME
        info = self.symbols.lookup(name)
        if info is None:
            self.errors.add_error(f"Undeclared function or array: {name}", lineno)
        if info and info.get("is_function"):
            expected_params = info.get("params", [])
            if len(node.expressionList) != len(expected_params):
                exp_len = len(expected_params)
                exprLis = len(node.expressionList)
                self.errors.add_error(f"Wrong number of arguments calling function {name}; expected {exp_len}, got {exprLis}", lineno)
        


        for expr in node.expressionList:
            self.verify_expression(expr, lineno)
        if info:
            return info.get("type")
        return None

    def process_declarations(self, declarations, parent_node=None):
        if declarations:
            for decl in declarations:
                self.verify(decl)

    def process_labeled_statements(self, stmts:list[LabeledStatement]):
        if stmts:
            for stmt in stmts:

                if not stmt.label:
                    pass
                elif stmt.label.value in self.labels:
                    return self.errors.add_error(f"Duplicate label: '{stmt.label}'")
                elif not stmt.label is None:
                    self.labels.append(stmt.label.value)

            for stmt in stmts:
                self.verify(stmt)

    def verify_LabeledStatement(self, node):
        if getattr(node, 'statement', None):
            self.verify(node.statement)

    def verify_expression(self, expr, lineno=None):
        if expr is None:
             
            return None
            
        current_lineno = expr.lineno if expr.lineno is not None else lineno
            
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
        if isinstance(expr,UnOp):
            expr_type = self.verify_expression(expr.expr)
            return self.verify_UnOP(expr.op,expr_type)

        if isinstance(expr,BinOp):
            left_type = self.verify_expression(expr.left)
            right_type = self.verify_expression(expr.right)
            return self.verify_BinOP(expr.op,left_type,right_type)


        if isinstance(expr, Node):
            return self.verify(expr)
        return None

    def verify_UnOP(self,op,expr_type):
        if op == "NOT" and expr_type == "LOGICAL":
            return "LOGICAL"
        #To do : Other UnOps
        return None

    def verify_BinOP(self,op,left_type,right_type):
        print(op)
        if (op in ["+","-","*","/","POWER"]):
            if (left_type in ["INTEGER","REAL"] and left_type == right_type):
                return left_type
            else:
                if not (left_type in ["INTEGER","REAL"]):
                    self.errors.add_error(f"Wrong left type, expected either INTEGER or REAL, got {left_type}")
                if not (right_type in ["INTEGER","REAL"]):
                    self.errors.add_error(f"Wrong right type, expected either INTEGER or REAL, got {right_type}")
                if not (right_type == left_type):
                    self.errors.add_error(f"Types don't match, got {left_type}, {right_type}")                
                return None


        if (op in ["CONCAT"]):
            if (left_type == "CHARACTER" and left_type == right_type):
                return left_type
                
                if not (left_type in ["CHARACTER"]):
                    self.errors.add_error(f"Wrong left type, expected CHARACTER, got {left_type}")
                if (right_type in ["CHARACTER"]):
                    self.errors.add_error(f"Wrong right type, expected CHARACTER, got {right_type}")
                if not (right_type == left_type):
                    self.errors.add_error(f"Types don't match, got {left_type}, {right_type}")          
        
        if (op in [".AND.",".OR."]):
            
            if (left_type == "LOGICAL" and left_type == right_type):
                return left_type

            if not (left_type in ["LOGICAL"]):
                self.errors.add_error(f"Wrong left type, expected LOGICAL, got {left_type}")
            if not(right_type in ["LOGICAL"]):
                self.errors.add_error(f"Wrong right type, expected LOGICAL, got {right_type}")
            if not (right_type == left_type):
                self.errors.add_error(f"Types don't match, got {left_type}, {right_type}")          
        
        if (op in [".EQ.",".NE.",".LT.",".LE.",".GT.",".GE."]):
            if (left_type == right_type):
                return "LOGICAL"

            if not (right_type == left_type):
                self.errors.add_error(f"Types don't match, got {left_type}, {right_type}")          
        
        
        


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
        if not (left_type == "INTEGER" or left_type == "REAL"):
            self.errors.add_error(f"Left side of Mod is not a Number, is actually {left_type}")
        if not (right_type == "INTEGER" or right_type == "REAL"):
            self.errors.add_error(f"Right side of Mod is not a Number, is actually {right_type}")
        if not (right_type == left_type):
            self.errors.add_error(f"Diferent types on Mod, left type = {left_type} and right type = {right_type}")
        return
        