from __future__ import annotations
from typing import Any, Union, Optional, List

class Node:
    """Classe base genérica para todos os nós da AST."""
    lineno: Optional[int]

    def __init__(self) -> None:
        self.lineno = None
    
    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent: int = 0)->str:
        return ""
    
def print_indented_list(name:str, list_to_print:List[Any], indent:int = 0) -> str:
    space0 = '  '*indent
    space1 = '  '*(indent+1)
    if any(isinstance(elem, Node) for elem in list_to_print):
        return f"{space0}{name}{{\n"+"\n".join(elem.repr(indent+1) if isinstance(elem, Node) else str(elem) for elem in list_to_print)+f"\n{space0}}}"
    else:
        return f"{space0}{name}{{\n"+"\n".join(f'{space1}{elem}' for elem in list_to_print)+f"\n{space0}}}"

def printIfNotNone(conteudo: Any, limitadorEsq:str, limitadorDir:str)->str:
    return f"{limitadorEsq}{str(conteudo)}{limitadorDir}" if conteudo is not None else "" 

class ArrayId(Node):
    name: str
    tamanho: int

    def __init__(self, name:str, tamanho:Optional[int]):
        super().__init__()
        self.name = name
        if(tamanho is None):
            self.tamanho = 0 
        else:
            self.tamanho = tamanho

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"{space}{self.name}{f'[{self.tamanho}]' if self.tamanho != 0 else ''}" 

class Declaration(Node):
    tipo: str
    Ids: List[ArrayId]

    def __init__(self, tipo:str, ArrayIdList:List[ArrayId]):
        super().__init__()
        self.tipo = tipo
        self.Ids = ArrayIdList
    
    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        elems = []
        for elem in self.Ids:
            elems.append(f"{elem.name}"+(f"[{elem.tamanho}]" if elem.tamanho > 0 else ""))
        return f"{space}Declaration({self.tipo} {' / '.join(elems)})"

class Label(Node):
    value: int

    def __init__(self, value:int):
        super().__init__()
        self.value = value

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"{space}Label({self.value})"

class Statement(Node):
    pass

class LabeledStatement(Node):
    label: Optional[Label]
    statement: Statement

    def __init__(self, label:Label|None, statement:Statement):
        super().__init__()
        self.label = label      # Label com int ||  um None
        self.statement = statement

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return f"{printIfNotNone(self.label, '[', '] ')}{self.statement.repr(indent)}"


class Program_Unit(Node):
    name: str
    declarations: List[Declaration]
    labeled_statements: List[LabeledStatement]

    def __init__(self,name:str,declarations:List[Declaration],labeled_statements:List[LabeledStatement]):
        super().__init__()
        self.name = name
        self.declarations = declarations
        self.labeled_statements = labeled_statements
    


class MainProgram(Program_Unit):
    tipo_no: str
    node_type: str

    def __init__(self, name:str, declarations:List[Declaration], labeled_statements:List[LabeledStatement]):
        super().__init__(name,declarations,labeled_statements)
        self.tipo_no = 'MAIN_PROGRAM'
        self.node_type = 'MAIN_PROGRAM'

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space0 = '  '*indent
        return (f"Program{printIfNotNone(self.name, '(', ')')}\n"
                f"{print_indented_list('Declarations', self.declarations, indent+1)}\n"
                f"{print_indented_list('LabeledStatements', self.labeled_statements, indent+1)}\n"
                f"{space0}END Program{printIfNotNone(self.name, '(', ')')}\n")
    
class Function(Program_Unit):
    arguments: List[Union[Variable, str]]
    return_type: str

    def __init__(self, return_type:Optional[str], name:str, arguments:List[Union[Variable, str]]
        ,declarations:List[Declaration], labeled_statements:List[LabeledStatement]):
        super().__init__(name,declarations,labeled_statements)
        self.arguments = arguments
        if return_type is None:
            n_name = name if isinstance(name, str) else str(name)
            if n_name.startswith(('N', 'I')):
                self.return_type = "INTEGER"
            else:
                self.return_type = "REAL"
        else:
            self.return_type = return_type

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return (f"Function({self.name}, Return Type: {self.return_type})\n"
                f"{print_indented_list('Arguments', self.arguments, indent+1)}\n"
                f"{print_indented_list('Declarations', self.declarations, indent+1)}\n"
                f"{print_indented_list('LabeledStatements', self.labeled_statements, indent+1)}\n"
                f"{space}END Function({self.name})\n")





class Subroutine(Program_Unit):
    arguments: List[Union[Variable, str]]

    def __init__(self, name:str, arguments:List[Union[Variable, str]], 
                 declarations:List[Declaration], labeled_statements:List[LabeledStatement]):
        super().__init__(name,declarations,labeled_statements)
        self.arguments = arguments
        
    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return (f"Subroutine({self.name},\n"
                f"{print_indented_list('Arguments',self.arguments, indent+1)}\n"
                f"{print_indented_list('Declarations',self.declarations, indent+1)}\n"
                f"{print_indented_list('LabeledStatements',self.labeled_statements, indent+1)}\n")
    

class DoublePrecisionComplexVal(Node):
    elem1: Any
    elem2: Any

    def __init__(self, elem1: Any, elem2: Any):
        super().__init__()
        self.elem1 = elem1
        self.elem2 = elem2

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"{space}DoublePrecisionComplex({self.elem1},{self.elem2})"

class ComplexVal(Node):
    elem1: Any
    elem2: Any

    def __init__(self, elem1: Any, elem2: Any):
        super().__init__()
        self.elem1 = elem1
        self.elem2 = elem2

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"{space}Complex({self.elem1},{self.elem2})"
    
class Expression(Node):
    expr_type: Optional[str]

    def __init__(self):
        super().__init__()
        self.expr_type = None

class BinOp(Expression):
    left: Any
    op: str
    right: Any

    def __init__(self, left, op:str, right):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"{space}({self.left} {self.op} {self.right})"

class UnOp(Expression):
    op: str
    expr: Any

    def __init__(self, op:str, expr):
        super().__init__()
        self.op = op
        self.expr = expr
        
    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"{space}({self.op} {self.expr})"

class Print(Statement):
    format: str
    iolist: List[Expression]

    def __init__(self,format:str,iolist:List[Expression]):
        super().__init__()
        self.format = format
        self.iolist = iolist

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return f"Print(Format: {self.format}, Items: {self.iolist})"

class Write(Statement):
    unit: Any
    format: str
    iolist: List[Expression]

    def __init__(self, unit, format:str, iolist:List[Expression]):
        super().__init__()
        self.unit = unit
        self.format = format
        self.iolist = iolist

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return f"Write(Unit: {self.unit}, Format: {self.format}, Items: {self.iolist})"

class Assignment(Statement):
    name: Any
    value: Any

    def __init__(self, name, value):
        super().__init__()
        self.name = name        # name
        self.value = value      # expressão (valor)

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return f"{self.name} = {self.value}"

class Continue(Statement):
    def __init__(self):
        super().__init__()
    
    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return "CONTINUE"

class Return(Statement):
    def __init__(self):
        super().__init__()

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent=0) -> str:
        return "RETURN"

class Goto(Statement):
    label: Any

    def __init__(self, label:Label):
        super().__init__()
        self.label = label
    
    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return f"GOTO {self.label}"

class ComputedGoto(Statement):
    labels: List[Any]
    expr: Expression

    def __init__(self, labels:List[Label], expr:Expression):
        super().__init__()
        self.labels = labels
        self.expr = expr

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self,indent = 0) -> str:
        return f"GOTO ({', '.join(str(label) for label in self.labels)}) , {self.expr}"

class AssignedGoto(Statement):
    var: Any
    labels: Optional[List[Any]]

    def __init__(self, var, labels=None):
        super().__init__()
        self.var = var
        self.labels = labels

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        if self.labels:
            return f"GOTO {self.var} ({', '.join(str(label) for label in self.labels)})"
        else:
            return f"GOTO {self.var}"

class ArithmeticIf(Statement):
    exp: Expression
    labeln: Any
    labelz: Any
    labelp: Any

    def __init__(self, exp, labeln, labelz, labelp):
        super().__init__()
        self.exp = exp
        self.labeln = labeln # exp < 0, usa esta label
        self.labelz = labelz # exp == 0, usa esta label
        self.labelp = labelp # exp > 0, usa esta label

    def __repr__(self) -> str:
        return self.repr(0)
    
    def repr(self, indent = 0) -> str:
        return f"IF ({self.exp}) {self.labeln}, {self.labelz}, {self.labelp}"

class LogicIf(Statement):
    exp: Expression
    statement: Statement

    def __init__(self, exp, statement):
        super().__init__()
        self.exp = exp
        self.statement = statement
    
    def __repr__(self) -> str:
        return self.repr(0)
    
    def repr(self, indent = 0) -> str:
        return f"IF ({self.exp})\n{self.statement.repr(indent+1)}"

class BlockIf(Statement):
    exp: Expression
    thenBody: List[LabeledStatement]
    elseBody: Optional[Union[List[LabeledStatement], BlockIf]]

    def __init__(self, exp:Expression, thenBody:List[LabeledStatement], elseBody:Optional[Union[List[LabeledStatement], BlockIf]] = None):
        super().__init__()
        self.exp = exp #condição
        self.thenBody = thenBody #conjunto de statements
        self.elseBody = elseBody #Pode ñ existir(None), ser uma lista de statements(else) ou outro BlockIf(kinda q1 elif)

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space0 = '  '*indent
        
        elseBodyText = ""
        if isinstance(self.elseBody, list):
            elseBodyText = f"{print_indented_list('ELSE', self.elseBody, indent+1)}\n"
        elif self.elseBody is not None:
            elseBodyText = self.elseBody.repr(indent+1)
        
        end_endif = f"{space0}}}ENDIF"

        return (f"IF ({self.exp}){{\n"
                f"{print_indented_list('THEN', self.thenBody, indent+1)}\n"
                f"{elseBodyText}{end_endif}")

class Mod(Statement):
    left: Expression
    right: Expression

    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return f"MOD({self.left}, {self.right})"


class Call(Statement):
    subroutine: Subroutine
    arguments: List[Expression]

    def __init__(self, subroutine,arguments):
        super().__init__()
        self.subroutine = subroutine
        self.arguments = arguments
    
    def __eq__(self, other: object) -> bool:
        if isinstance(other, Call):
            return self.subroutine == other.subroutine and self.arguments == other.arguments
        return False
    
    def __hash__(self) -> int:
        return hash((self.subroutine, tuple(self.arguments)))

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return f"Call(Subroutine: {self.subroutine}, Arguments: {self.arguments})"

#NOTA: Em FORTRAN 77, as chamadas de funcoes e acessos a array(incluindo arrays de arrays) tem a mesma sintaxe
class FunctionorArraysAccess(Expression):
    name: str
    expressionList: List[Expression]
    is_array: bool
    is_function: bool

    def __init__(self, name:str, expressionList):
        super().__init__()
        self.name = name
        self.expressionList = expressionList
        self.is_array = False
        self.is_function = False

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FunctionorArraysAccess):
            return self.name == other.name and self.expressionList == other.expressionList
        return False

    def __hash__(self) -> int:
        return hash((self.name, tuple(self.expressionList)))

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"{space}Function or Array Access ({self.name}, {self.expressionList})"
    
class Read(Statement):
    format: str
    iolist: List[Any]

    def __init__(self, format:str, iolist):
        super().__init__()
        self.format = format
        self.iolist = iolist
    
    def __repr__(self) -> str:
        return self.repr(0)
    
    def repr(self, indent = 0) -> str:
        return f"Read(Format: {self.format}, Items: {self.iolist})"

class LabeledDO(Statement):
    label: Label
    control_var: str
    control_var_init_value: Any
    iterations_number: Any
    labeled_statements: Optional[List[LabeledStatement]]
    step: Any

    def __init__(self, label:Label, control_var:str, control_var_init_value, iterations_number, labeled_statements = None, step = 1):
        super().__init__()
        self.label = label
        self.control_var = control_var
        self.control_var_init_value = control_var_init_value
        self.iterations_number = iterations_number
        self.labeled_statements = labeled_statements #temporariamente a none
        self.step = step

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        return (f"DO {self.label} (INIT = {self.control_var} = {self.control_var_init_value}, LIMIT = {self.iterations_number}, STEP = {self.step})")

class BlockDO(Statement):
    control_var: str
    init_value: Any
    max_value: Any
    labeled_statements: List[LabeledStatement]
    step: Any

    def __init__(self, control_var:str, init_value, max_value, labeled_statements:List[LabeledStatement], step = 1):
        super().__init__()
        self.control_var = control_var
        self.init_value = init_value
        self.max_value = max_value
        self.labeled_statements = labeled_statements
        self.step = step
    
    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return (f"DO (INIT = {self.control_var} = {self.init_value}, LIMIT = {self.max_value}, STEP = {self.step}){{\n"
                f"{print_indented_list('LabeledStatements', self.labeled_statements, indent+1)}\n"
                f"{space}}}END DO")










class Variable(Node):
    name: str

    def __init__(self, name:str):
        super().__init__()
        self.name = name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Variable):
            return self.name == other.name
        return False

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"{space}Variable({self.name})"

class IntVal(Node):
    value: int

    def __init__(self, value: int):
        super().__init__()
        self.value = value

    def __repr__(self) -> str: return self.repr(0)

    def repr(self, indent=0) -> str:
        return f"{'  '*indent}IntVal({self.value})"

class RealVal(Node):
    value: float

    def __init__(self, value: float):
        super().__init__()
        self.value = value

    def __repr__(self) -> str: return self.repr(0)

    def repr(self, indent=0) -> str:
        return f"{'  '*indent}RealVal({self.value})"

class StringVal(Node):
    value: str

    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __repr__(self) -> str: return self.repr(0)

    def repr(self, indent=0) -> str:
        return f"{'  '*indent}StringVal('{self.value}')"

class LogicalVal(Node):
    value: bool

    def __init__(self, value: bool):
        super().__init__()
        self.value = value

    def __repr__(self) -> str: return self.repr(0)

    def repr(self, indent=0) -> str:
        return f"{'  '*indent}LogicalVal({self.value})"
