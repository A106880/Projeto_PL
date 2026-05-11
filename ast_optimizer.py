from node_classes import IntVal, RealVal, ProgramaPrincipal, Funcao, Subroutine, LabeledStatement, Assignment, Print, Write, BinOp, UnOp, Goto, Label
from semantic_parser import get_name

class ASTOptimizer:
    def __init__(self):
        self.optimized_nodes = 0

    def optimize_program(self, ast):
        if isinstance(ast, list):
            for i, unit in enumerate(ast):
                ast[i] = self.optimize_node(unit)
        return ast

    def optimize_node(self, node):
        if node is None:
            return None
        
        if isinstance(node, list):
            return [self.optimize_node(n) for n in node]
        
        class_name = type(node).__name__
        method_name = f"optimize_{class_name}"
        method = getattr(self, method_name, None)
        
        if method:
            return method(node)
        else:
            return node
            
    def optimize_ProgramaPrincipal(self, node):
        if hasattr(node, 'labeled_statements'):
            node.labeled_statements = self.optimize_statement_list(node.labeled_statements)
        return node

    def optimize_Funcao(self, node):
        if hasattr(node, 'labeled_statements'):
            node.labeled_statements = self.optimize_statement_list(node.labeled_statements)
        return node

    def optimize_Subroutine(self, node):
        if hasattr(node, 'labeled_statements'):
            node.labeled_statements = self.optimize_statement_list(node.labeled_statements)
        return node
        
    def optimize_LabeledStatement(self, node):
        if node.statement:
            node.statement = self.optimize_node(node.statement)
        return node

    def optimize_Assignment(self, node):
        if hasattr(node, 'value'):
            node.value = self.optimize_node(node.value)
        if hasattr(node, 'name') and hasattr(node.name, 'expressionList'):
            node.name.expressionList = [self.optimize_node(e) for e in node.name.expressionList]
        return node

    def optimize_Print(self, node):
        if hasattr(node, 'expressionList') and node.expressionList:
            node.expressionList = [self.optimize_node(e) for e in node.expressionList]
        return node
        
    def optimize_Write(self, node):
        if hasattr(node, 'iolist') and node.iolist:
            node.iolist = [self.optimize_node(e) for e in node.iolist]
        return node

    def optimize_BinOp(self, node):
        node.left = self.optimize_node(node.left)
        node.right = self.optimize_node(node.right)
        
        if type(node.left) in (IntVal, RealVal) and type(node.right) in (IntVal, RealVal):
            op = node.op
            v1 = node.left.value
            v2 = node.right.value
            
            try:
                res = None
                if op == '+':
                    res = v1 + v2
                elif op == '-':
                    res = v1 - v2
                elif op == '*':
                    res = v1 * v2
                elif op == '/':
                    if type(node.left) is IntVal and type(node.right) is IntVal:
                        res = v1 // v2
                    else:
                        res = v1 / v2
                elif op == '**':
                    res = v1 ** v2
                
                if res is not None:
                    self.optimized_nodes += 1
                    if isinstance(res, int) or (type(node.left) is IntVal and type(node.right) is IntVal and op != '/'):
                        new_node = IntVal(int(res))
                    else:
                        new_node = RealVal(float(res))
                    
                    if hasattr(node, 'expr_type'):
                        new_node.expr_type = node.expr_type
                    new_node.lineno = node.lineno
                    return new_node
            except Exception:
                pass
        return node

    def optimize_UnOp(self, node):
        node.expr = self.optimize_node(node.expr)
        
        if type(node.expr) in (IntVal, RealVal):
            op = node.op
            v = node.expr.value
            try:
                res = None
                if op == '+':
                    res = +v
                elif op == '-':
                    res = -v
                
                if res is not None:
                    self.optimized_nodes += 1
                    if isinstance(res, int) or type(node.expr) is IntVal:
                        new_node = IntVal(int(res))
                    else:
                        new_node = RealVal(float(res))
                    
                    if hasattr(node, 'expr_type'):
                        new_node.expr_type = node.expr_type
                    new_node.lineno = node.lineno
                    return new_node
            except Exception:
                pass
        return node

    def optimize_statement_list(self, lst):
        """Applies DCE and Jump-to-Jump to a list of LabeledStatement"""
        if not lst:
            return lst
            
        new_list = []
        dead_code = False
        
        for item in lst:
            if dead_code:
                if getattr(item, 'label', None) is not None:
                    dead_code = False
                else:
                    self.optimized_nodes += 1
                    continue
                    
            optimized_item = self.optimize_node(item)
            new_list.append(optimized_item)
            
            stmt = getattr(optimized_item, 'statement', None)
            if stmt:
                if type(stmt).__name__ in ('Goto', 'Return'):
                    dead_code = True
                
        label_targets = {}
        for item in new_list:
            if getattr(item, 'label', None) is not None:
                label_val = get_name(item.label)
                label_targets[label_val] = getattr(item, 'statement', None)
                
        replacements = {}
        for lbl, stmt in label_targets.items():
            if type(stmt).__name__ == 'Goto':
                target_lbl = get_name(stmt.label)
                if target_lbl != lbl:
                    replacements[lbl] = stmt.label 

        if replacements:
            self._apply_goto_replacements(new_list, replacements)
        
        return new_list

    def _apply_goto_replacements(self, nodes, replacements):
        for node in nodes:
            if isinstance(node, LabeledStatement):
                stmt = getattr(node, 'statement', None)
                if stmt and type(stmt).__name__ == 'Goto':
                    lbl_val = get_name(stmt.label)
                    if lbl_val in replacements:
                        stmt.label = replacements[lbl_val]
                        self.optimized_nodes += 1
