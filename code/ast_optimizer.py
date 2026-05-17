from __future__ import annotations

from typing import Any, Optional, Union, List

from node_classes import (
    Node, FunctionorArraysAccess, Call, Variable, Read, Declaration, ArrayId,
    IntVal, RealVal, MainProgram, Function, Subroutine,
    LabeledStatement, Assignment, Print, Write, BinOp, UnOp, Goto, Label,
    Expression, Statement, Program_Unit, LogicalVal, Return, Continue, Mod,
    LogicIf, BlockIf, BlockDO, LabeledDO, ArithmeticIf, ComputedGoto, AssignedGoto,
    StringVal, DoublePrecisionVal
)
from semantic_parser import get_name, SemanticParser

class ASTOptimizer:
    def __init__(self) -> None:
        self.optimized_nodes: int = 0
        self.semantic_info: Optional[SemanticParser] = None
        self.warnings: List[str] = []

    def set_semantic_info(self, semantic_info: SemanticParser) -> None:
        self.semantic_info = semantic_info

    def optimize_program(self, ast: List[Program_Unit]) -> List[Program_Unit]:
        if isinstance(ast, list):
            main_unit: Optional[MainProgram] = None
            units_by_name: dict[str, Program_Unit] = {}
            for unit in ast:
                if isinstance(unit, MainProgram):
                    main_unit = unit
                uname = get_name(unit.name) if getattr(unit, 'name', None) is not None else None
                if uname is not None:
                    units_by_name[uname] = unit

            if main_unit is None:
                for i, unit in enumerate(ast):
                    optimized_unit = self.optimize_node(unit)
                    if isinstance(optimized_unit, Program_Unit):
                        ast[i] = optimized_unit
                return ast

            reachable: set[str] = set()
            queue: List[Program_Unit] = []

            main_name = get_name(main_unit.name) if getattr(main_unit, 'name', None) is not None else "MAIN"
            reachable.add(main_name)
            queue.append(main_unit)

            while queue:
                current = queue.pop(0)
                called: set[str] = set()
                for stmt in getattr(current, 'labeled_statements', []) or []:
                    self._collect_called_units_from_node(stmt, called)

                for cname in called:
                    if cname in reachable:
                        continue
                    target: Optional[Program_Unit] = None
                    for unit in ast:
                        if getattr(unit, 'name', None) is None:
                            continue
                        if get_name(unit.name) == cname:
                            target = unit
                            break
                    if target is not None:
                        reachable.add(cname)
                        queue.append(target)

            new_ast: List[Program_Unit] = []
            for unit in ast:
                if isinstance(unit, MainProgram):
                    new_ast.append(unit)
                    continue
                if getattr(unit, 'name', None) is None:
                    new_ast.append(unit)
                    continue
                if get_name(unit.name) in reachable:
                    new_ast.append(unit)
                else:
                    self.optimized_nodes += 1

            ast[:] = new_ast

            for i, unit in enumerate(ast):
                optimized_unit = self.optimize_node(unit)
                if isinstance(optimized_unit, Program_Unit):
                    ast[i] = optimized_unit
        return ast

    def _collect_called_units_from_node(self, node: Union[Node, List[Node], None], called_set: set[str]) -> None:
        if node is None:
            return
        if isinstance(node, list):
            for n in node:
                self._collect_called_units_from_node(n, called_set)
            return

        if isinstance(node, FunctionorArraysAccess) and getattr(node, 'is_function', False):
            name = get_name(node.name)
            called_set.add(name)

        if isinstance(node, Call):
            called_set.add(get_name(node.subroutine))

        for attr in getattr(node, '__dict__', {}).values():
            if attr is None:
                continue
            if isinstance(attr, list) or isinstance(attr, tuple):
                for item in attr:
                    if hasattr(item, '__dict__') or isinstance(item, (FunctionorArraysAccess, Call)):
                        self._collect_called_units_from_node(item, called_set)
            elif hasattr(attr, '__dict__'):
                self._collect_called_units_from_node(attr, called_set)

    def optimize_node(self, node: Union[Node, List[Node], None]) -> Union[Node, List[Node], None]:
        if node is None:
            return None
        
        if isinstance(node, list):
            if node and isinstance(node[0], LabeledStatement):
                return self.optimize_statement_list(node)
            result: List[Node] = []
            for n in node:
                optimized = self.optimize_node(n)
                if isinstance(optimized, list):
                    result.extend(optimized)
                elif optimized is None:
                    continue
                else:
                    result.append(optimized)
            return result
        
        class_name = type(node).__name__
        method_name = f"optimize_{class_name}"
        method = getattr(self, method_name, None)
        
        if method:
            return method(node)
        else:
            if node is not None:
                print(f"ERROR: Optimization not implemented for: {method_name}")
            return node
            
    def optimize_MainProgram(self, node: MainProgram) -> MainProgram:
        if hasattr(node, 'labeled_statements') and node.labeled_statements:
            node.labeled_statements = self.optimize_statement_list(node.labeled_statements)
        self._remove_unused_declarations(node)
        return node

    def optimize_Function(self, node: Function) -> Function:
        if hasattr(node, 'labeled_statements') and node.labeled_statements:
            node.labeled_statements = self.optimize_statement_list(node.labeled_statements)
        self._remove_unused_declarations(node)
        return node

    def optimize_Subroutine(self, node: Subroutine) -> Subroutine:
        if hasattr(node, 'labeled_statements') and node.labeled_statements:
            node.labeled_statements = self.optimize_statement_list(node.labeled_statements)
        self._remove_unused_declarations(node)
        return node

    def optimize_LogicIf(self, node: LogicIf) -> LogicIf:
        node.exp = self.optimize_node(node.exp)
        node.statement = self.optimize_node(node.statement)
        return node

    def optimize_BlockIf(self, node: BlockIf) -> BlockIf:
        node.exp = self.optimize_node(node.exp)
        if node.thenBody:
            node.thenBody = self.optimize_statement_list(node.thenBody)
        if node.elseBody:
            if isinstance(node.elseBody, list):
                node.elseBody = self.optimize_statement_list(node.elseBody)
            else:
                node.elseBody = self.optimize_node(node.elseBody)
        return node

    def optimize_BlockDO(self, node: BlockDO) -> BlockDO:
        node.init_value = self.optimize_node(node.init_value)
        node.max_value = self.optimize_node(node.max_value)
        node.step = self.optimize_node(node.step)
        if node.labeled_statements:
            node.labeled_statements = self.optimize_statement_list(node.labeled_statements)
        return node

    def optimize_LabeledDO(self, node: LabeledDO) -> LabeledDO:
        node.control_var_init_value = self.optimize_node(node.control_var_init_value)
        node.iterations_number = self.optimize_node(node.iterations_number)
        node.step = self.optimize_node(node.step)
        if node.labeled_statements:
            node.labeled_statements = self.optimize_statement_list(node.labeled_statements)
        return node

    def optimize_ArithmeticIf(self, node: ArithmeticIf) -> ArithmeticIf:
        node.exp = self.optimize_node(node.exp)
        return node

    def optimize_Call(self, node: Call) -> Call:
        if node.arguments:
            node.arguments = [self.optimize_node(arg) for arg in node.arguments]
        return node

    def optimize_FunctionorArraysAccess(self, node: FunctionorArraysAccess) -> FunctionorArraysAccess:
        if node.expressionList:
            node.expressionList = [self.optimize_node(expr) for expr in node.expressionList]
        return node

    def optimize_Read(self, node: Read) -> Read:
        if node.iolist:
            node.iolist = [self.optimize_node(item) for item in node.iolist]
        return node

    def _collect_used_vars(self, node: Union[Node, List[Node], None], used: set[str]) -> None:
        if node is None:
            return
        if isinstance(node, list):
            for n in node:
                self._collect_used_vars(n, used)
            return

        if isinstance(node, Variable):
            used.add(node.name)
            return

        if isinstance(node, FunctionorArraysAccess):
            name = get_name(node.name)
            used.add(name)
            for expr in node.expressionList:
                self._collect_used_vars(expr, used)
            return

        for attr_name, attr_val in getattr(node, '__dict__', {}).items():
            if attr_val is None:
                continue
            if isinstance(attr_val, (list, tuple)):
                for item in attr_val:
                    if isinstance(item, Node):
                        self._collect_used_vars(item, used)
            elif isinstance(attr_val, Node):
                self._collect_used_vars(attr_val, used)

    def _remove_unused_declarations(self, unit: Program_Unit) -> None:
        used_vars: set[str] = set()
        for stmt in getattr(unit, 'labeled_statements', []) or []:
            self._collect_used_vars(stmt, used_vars)
        if isinstance(unit, (Function, Subroutine)):
            for arg in getattr(unit, 'arguments', []) or []:
                used_vars.add(get_name(arg))
            if isinstance(unit, Function):
                used_vars.add(get_name(unit.name))

        unit_name = get_name(unit.name) if getattr(unit, 'name', None) is not None else "MAIN"

        if hasattr(unit, 'declarations') and unit.declarations:
            new_declarations: List[Declaration] = []
            for decl in unit.declarations:
                new_ids: List[ArrayId] = []
                for array_id in decl.Ids:
                    var_name = get_name(array_id.name)
                    if var_name in used_vars:
                        new_ids.append(array_id)
                    else:
                        is_arr = array_id.tamanho > 0
                        tipo = "array" if is_arr else "variable"
                        self.warnings.append(f"[Warning] {unit_name}: {tipo} '{var_name}' declared but never used")
                        self.optimized_nodes += 1
                if new_ids:
                    decl.Ids = new_ids
                    new_declarations.append(decl)
            unit.declarations = new_declarations

        if self.semantic_info is not None:
            symbols = self.semantic_info.unit_symbols.get(unit_name, {})
            to_remove: List[str] = []
            for sym_name, sym_info in symbols.items():
                if sym_info.get('is_function') or sym_info.get('is_subroutine'):
                    continue
                if sym_name not in used_vars:
                    to_remove.append(sym_name)
            for sym_name in to_remove:
                del symbols[sym_name]
        
    def optimize_LabeledStatement(self, node: LabeledStatement) -> LabeledStatement:
        if node.statement:
            node.statement = self.optimize_node(node.statement)
        return node

    def optimize_Assignment(self, node: Assignment) -> Assignment:
        if hasattr(node, 'value'):
            node.value = self.optimize_node(node.value)
        if hasattr(node, 'name') and hasattr(node.name, 'expressionList'):
            node.name.expressionList = [self.optimize_node(e) for e in node.name.expressionList]
        return node

    def optimize_Print(self, node: Print) -> Print:
        if hasattr(node, 'iolist') and node.iolist:
            node.iolist = [self.optimize_node(e) for e in node.iolist]
        return node
        
    def optimize_Write(self, node: Write) -> Write:
        if hasattr(node, 'iolist') and node.iolist:
            node.iolist = [self.optimize_node(e) for e in node.iolist]
        return node

    def optimize_BinOp(self, node: BinOp) -> Union[BinOp, IntVal, RealVal, LogicalVal]:
        node.left = self.optimize_node(node.left)
        node.right = self.optimize_node(node.right)
        
        if getattr(node, 'expr_type', None) == "LOGICAL":
            if node.op == ".AND.":
                if isinstance(node.left, LogicalVal):
                    if not node.left.value:
                        return LogicalVal(False) 
                    return node.right 
                if isinstance(node.right, LogicalVal):
                    if not node.right.value:
                        return LogicalVal(False)
                    return node.left
            
            if node.op == ".OR.":
                if isinstance(node.left, LogicalVal):
                    if node.left.value:
                        return LogicalVal(True) 
                    return node.right 
                if isinstance(node.right, LogicalVal):
                    if node.right.value:
                        return LogicalVal(True)
                    return node.left

        if isinstance(node.left, (IntVal, RealVal, DoublePrecisionVal)) and isinstance(node.right, (IntVal, RealVal, DoublePrecisionVal)):
            op = node.op
            v1 = node.left.value
            v2 = node.right.value
            
            if op in ('.EQ.', '.NE.', '.LT.', '.LE.', '.GT.', '.GE.'):
                res_bool = False
                if op == '.EQ.':
                    res_bool = (v1 == v2)
                elif op == '.NE.':
                    res_bool = (v1 != v2)
                elif op == '.LT.':
                    res_bool = (v1 < v2)
                elif op == '.LE.':
                    res_bool = (v1 <= v2)
                elif op == '.GT.':
                    res_bool = (v1 > v2)
                elif op == '.GE.':
                    res_bool = (v1 >= v2)
                
                self.optimized_nodes += 1
                new_node = LogicalVal(res_bool)
                new_node.lineno = node.lineno
                return new_node

            try:
                res: Optional[Union[int, float]] = None
                if op == '+':
                    res = v1 + v2
                elif op == '-':
                    res = v1 - v2
                elif op == '*':
                    res = v1 * v2
                elif op == '/':
                    if v2 == 0:
                        if self.semantic_info is not None:
                            original_right = node.right
                            already_literal_zero = isinstance(original_right, (IntVal, RealVal, DoublePrecisionVal)) and original_right.value == 0
                            if already_literal_zero:
                                lineno = getattr(node, 'lineno', None)
                                self.semantic_info.errors.add_error("Division by zero detected", lineno)
                        return node
                    if type(node.left) is IntVal and type(node.right) is IntVal:
                        res = int(v1 / v2)
                    else:
                        res = v1 / v2
                elif op == '**':
                    if v1 == 0 and v2 < 0:
                        if self.semantic_info is not None:
                            original_left = node.left
                            original_right = node.right
                            already_literal = (isinstance(original_left, (IntVal, RealVal, DoublePrecisionVal)) and original_left.value == 0) and \
                                              (isinstance(original_right, (IntVal, RealVal, DoublePrecisionVal)) and original_right.value < 0)
                            if already_literal:
                                lineno = getattr(node, 'lineno', None)
                                self.semantic_info.errors.add_error("Zero raised to a negative power", lineno)
                        return node
                    res = v1 ** v2
                
                if res is not None:
                    self.optimized_nodes += 1
                    if isinstance(res, int) or (type(node.left) is IntVal and type(node.right) is IntVal and op != '/'):
                        new_node = IntVal(int(res))
                    elif type(node.left) is DoublePrecisionVal or type(node.right) is DoublePrecisionVal:
                        new_node = DoublePrecisionVal(float(res))
                    else:
                        new_node = RealVal(float(res))
                    
                    if hasattr(node, 'expr_type'):
                        new_node.expr_type = node.expr_type
                    new_node.lineno = node.lineno
                    return new_node
            except ZeroDivisionError:
                if self.semantic_info is not None:
                    lineno = getattr(node, 'lineno', None)
                    self.semantic_info.errors.add_error("Division by zero detected", lineno)
            except (OverflowError, ValueError) as e:
                if self.semantic_info is not None:
                    lineno = getattr(node, 'lineno', None)
                    self.semantic_info.errors.add_error(f"Arithmetic error detected after constant folding: {e}", lineno)
            except Exception:
                pass
        return node

    def optimize_UnOp(self, node: UnOp) -> Union[UnOp, IntVal, RealVal, LogicalVal]:
        node.expr = self.optimize_node(node.expr)
        
        if node.op == '.NOT.' and isinstance(node.expr, LogicalVal):
            self.optimized_nodes += 1
            new_node = LogicalVal(not node.expr.value)
            new_node.lineno = node.lineno
            return new_node

        if type(node.expr) in (IntVal, RealVal, DoublePrecisionVal):
            op = node.op
            v = node.expr.value
            try:
                res: Optional[Union[int, float]] = None
                if op == '+':
                    res = +v
                elif op == '-':
                    res = -v
                
                if res is not None:
                    self.optimized_nodes += 1
                    if isinstance(res, int) or type(node.expr) is IntVal:
                        new_node = IntVal(int(res))
                    elif type(node.expr) is DoublePrecisionVal:
                        new_node = DoublePrecisionVal(float(res))
                    else:
                        new_node = RealVal(float(res))
                    
                    if hasattr(node, 'expr_type'):
                        new_node.expr_type = node.expr_type
                    new_node.lineno = node.lineno
                    return new_node
            except Exception:
                pass
        return node

    def optimize_Mod(self, node: Mod) -> Union[Mod, IntVal]:
        node.left = self.optimize_node(node.left)
        node.right = self.optimize_node(node.right)

        if isinstance(node.right, IntVal):
            v2 = node.right.value
            if v2 == 0:
                if self.semantic_info is not None:
                    original_right = node.right
                    already_literal_zero = isinstance(original_right, IntVal) and original_right.value == 0
                    if already_literal_zero:
                        lineno = getattr(node, 'lineno', None)
                        self.semantic_info.errors.add_error("Modulo by zero detected", lineno)
                return node

        if isinstance(node.left, IntVal) and isinstance(node.right, IntVal):
            v1 = node.left.value
            v2 = node.right.value
            try:
                if v2 == 0:
                    
                    if self.semantic_info is not None:
                        original_right = node.right
                        already_literal_zero = isinstance(original_right, IntVal) and original_right.value == 0
                        if already_literal_zero:
                            lineno = getattr(node, 'lineno', None)
                            self.semantic_info.errors.add_error("Modulo by zero detected", lineno)
                    return node
                res = v1 % v2
                self.optimized_nodes += 1
                new_node = IntVal(int(res))
                if hasattr(node, 'expr_type'):
                    setattr(new_node, 'expr_type', node.expr_type)
                new_node.lineno = node.lineno
                return new_node
            except ZeroDivisionError:
                if self.semantic_info is not None:
                    lineno = getattr(node, 'lineno', None)
                    self.semantic_info.errors.add_error("Modulo by zero detected", lineno)
            except Exception:
                pass
        return node

    def optimize_statement_list(self, lst: List[LabeledStatement]) -> List[LabeledStatement]:
        if not lst:
            return lst
            
        new_list: List[LabeledStatement] = []
        dead_code: bool = False
        
        for item in lst:
            if dead_code:
                if getattr(item, 'label', None) is not None:
                    dead_code = False
                else:
                    self.optimized_nodes += 1
                    continue
                    
            optimized_item = self.optimize_node(item)
            if not isinstance(optimized_item, LabeledStatement):
                continue
            new_list.append(optimized_item)
            
            stmt = getattr(optimized_item, 'statement', None)
            if stmt:
                if type(stmt).__name__ in ('Goto', 'Return'):
                    dead_code = True
                
        label_targets: dict[str, Optional[Statement]] = {}
        for item in new_list:
            if getattr(item, 'label', None) is not None:
                label_val = get_name(item.label)
                label_targets[label_val] = getattr(item, 'statement', None)
                
        replacements: dict[str, Label] = {}
        for lbl, stmt in label_targets.items():
            if type(stmt).__name__ == 'Goto':
                target = getattr(stmt, 'label', None)
                if target is None:
                    continue
                target_lbl = get_name(target)
                if target_lbl != lbl:
                    replacements[lbl] = target

        if replacements:
            self._apply_goto_replacements(new_list, replacements)
        
        return new_list

    def _apply_goto_replacements(self, nodes: List[Node], replacements: dict[str, Label]) -> None:
        for node in nodes:
            if isinstance(node, LabeledStatement):
                stmt = getattr(node, 'statement', None)
                if stmt and type(stmt).__name__ == 'Goto':
                    lbl_val = get_name(stmt.label)
                    if lbl_val in replacements:
                        stmt.label = replacements[lbl_val]
                        self.optimized_nodes += 1

    def optimize_ComputedGoto(self, node: ComputedGoto) -> ComputedGoto:
        optimized_expr = self.optimize_node(node.expr)
        if isinstance(optimized_expr, Expression):
            node.expr = optimized_expr
        return node

    def optimize_AssignedGoto(self, node: AssignedGoto) -> AssignedGoto:
        node.var = self.optimize_node(node.var)
        return node




    def optimize_Goto(self, node: Goto) -> Goto:
        return node

    def optimize_IntVal(self, node: IntVal) -> IntVal:
        return node

    def optimize_RealVal(self, node: RealVal) -> RealVal:
        return node

    def optimize_DoublePrecisionVal(self, node: DoublePrecisionVal) -> DoublePrecisionVal:
        return node

    def optimize_StringVal(self, node: StringVal) -> StringVal:
        return node

    def optimize_LogicalVal(self, node: LogicalVal) -> LogicalVal:
        return node

    def optimize_Variable(self, node: Variable) -> Variable:
        return node

    def optimize_Label(self, node: Label) -> Label:
        return node

    def optimize_Return(self, node: Return) -> Return:
        return node

    def optimize_Continue(self, node: Continue) -> Continue:
        return node

    def optimize_Declaration(self, node: Declaration) -> Declaration:
        return node

    def optimize_ArrayId(self, node: ArrayId) -> ArrayId:
        return node
