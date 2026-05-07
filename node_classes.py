from __future__ import annotations

class Node:
    """Classe base genérica para todos os nós da AST."""
    def __init__(self):
        self.lineno = None
    
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0)->str:
        return ""
    
def print_indented_list(name:str, list:list, indent:int = 0):
    space0 = '  '*indent
    space1 = '  '*(indent+1)
    if any(isinstance(elem, Node) for elem in list):
        return f"{space0}{name}{{\n"+"\n".join(elem.repr(indent+1) for elem in list)+f"\n{space0}}}"
    else:
        return f"{space0}{name}{{\n"+"\n".join(f'{space1}{elem}' for elem in list)+f"\n{space0}}}"

def printIfNotNone(conteudo, limitadorEsq:str, limitadorDir:str)->str:
    return f"{limitadorEsq}{str(conteudo)}{limitadorDir}" if conteudo is not None else "" 

class ArrayId(Node):
    def __init__(self, name:str, tamanho:int):
        super().__init__()
        self.name = name
        if(tamanho is None):
            self.tamanho = 0 # ou 1 caso se queira fazer singleton == array de 1 elemento 
        else:
            self.tamanho = tamanho

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{space}{self.name}{f'[{self.tamanho}]' if self.tamanho != 0 else ''}" 

class Declaracao(Node):
    def __init__(self, tipo:str, ArrayIdList:list[ArrayId]):
        super().__init__()
        self.tipo = tipo
        self.Ids = ArrayIdList
    
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        elems = []
        for elem in self.Ids:
            elems.append(f"{elem.name}"+(f"[{elem.tamanho}]" if elem.tamanho > 0 else ""))
        return f"{space}Declaracao({self.tipo} {' / '.join(elems)})"

class Label(Node):
    def __init__(self, value:int):
        super().__init__()
        self.value = value

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{space}Label({self.value})"

class Statement(Node):
    pass

class LabeledStatement(Node):
    def __init__(self, label:Label|None, statement:Statement):
        super().__init__()
        self.label = label      # Label com int ||  um None
        self.statement = statement

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{space}{printIfNotNone(self.label, '[', '] ')}{self.statement.repr(indent)}"


class Program_Unit(Node):
    def __init__(self,name:str,declarations:list[Declaracao],labeled_statements:list[LabeledStatement]):
        super().__init__()
        self.name = name
        self.declarations = declarations
        self.labeled_statements = labeled_statements
    


class ProgramaPrincipal(Program_Unit):
    def __init__(self, name:str, declarations:list[Declaracao], labeled_statements:list[LabeledStatement]):
        super().__init__(name,declarations,labeled_statements)
        self.tipo_no = 'PROGRAMA_PRINCIPAL'

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space0 = '  '*indent
        space1 = '  '*(indent+1)
        return (f"Programa{printIfNotNone(self.name, '(', ')')}\n"
                f"{print_indented_list('Declarações', self.declarations, indent+1)}\n"
                f"{print_indented_list('LabeledStatements', self.labeled_statements, indent+1)}\n"
                f"{space0}END Programa{printIfNotNone(self.name, '(', ')')}\n")
    
class Funcao(Program_Unit):
    def __init__(self, return_type:str, name:str, arguments:list[str] 
                ,declarations:list[Declaracao], labeled_statements:list[LabeledStatement]):
        super().__init__(name,declarations,labeled_statements)
        self.arguments = arguments
        if return_type == None:
            if name.name[0] == 'N' or name.name[0] == 'I':
                self.return_type = "INTEGER"
            else:
                self.return_type = "REAL"
        else:
            self.return_type = return_type

        # self.variables = {}
        # for dec in declarations:
        #     self.variables[dec.Ids] = dec.tipo


        
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return (f"Funcao({self.name}, TipoRetorno: {self.return_type})\n"
                f"{print_indented_list('Argumentos', self.arguments, indent+1)}\n"
                f"{print_indented_list('Declarações', self.declarations, indent+1)}\n"
                f"{print_indented_list('LabeledStatements', self.labeled_statements, indent+1)}\n"
                f"{space}END Funcao({self.name})\n")




class Subroutine(Program_Unit):
    def __init__(self, name, arguments, declarations, labeled_statements):
        super().__init__(name,declarations,labeled_statements)
        self.arguments = arguments
        
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return (f"{space}Subrotina({self.name},\n"
                f"{print_indented_list('Argumentos',self.arguments, indent+1)}\n"
                f"{print_indented_list('Declarações',self.declarations, indent+1)}\n"
                f"{print_indented_list('LabeledStatements',self.labeled_statements, indent+1)}\n")
    

class DoublePrecisionComplexVal(Node):
    def __init__(self, elem1, elem2):
        super().__init__()
        self.elem1 = elem1
        self.elem2 = elem2

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{space}DoublePrecisionComplex({self.elem1},{self.elem2})"

class ComplexVal(Node):
    def __init__(self, elem1, elem2):
        super().__init__()
        self.elem1 = elem1
        self.elem2 = elem2

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{space}Complex({self.elem1},{self.elem2})"
    
class Expression(Node):
    pass

class BinOp(Expression):
    """Nó para operações binárias (ex: A + B, NUM .GT. 5)"""
    def __init__(self, left, op:str, right):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{space}({self.left} {self.op} {self.right})"

class UnOp(Expression):
    """Nó para operações unárias (ex: -A, .NOT. ISPRIM)"""
    def __init__(self, op:str, expr):
        super().__init__()
        self.op = op
        self.expr = expr
        
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{space}({self.op} {self.expr})"

class Print(Statement):
    def __init__(self,format:str,iolist:list[Expression]):
        super().__init__()
        self.format = format
        self.iolist = iolist

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"Print(Format: {self.format}, Items: {self.iolist})"

class Write(Statement):
    def __init__(self, unit, format:str, iolist:list[Expression]):
        super().__init__()
        self.unit = unit
        self.format = format
        self.iolist = iolist

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"Write(Unit: {self.unit}, Format: {self.format}, Items: {self.iolist})"

class Assignment(Statement):
    def __init__(self, name, value):
        super().__init__()
        self.name = name        # name
        self.value = value      # expressão (valor)

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{self.name} = {self.value}"

class Continue(Statement):
    def __init__(self):
        super().__init__()
    
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"CONTINUE"

class Return(Statement):
    def __init__(self):
        super().__init__()

    def repr(self, indent=0):
        space = '  ' * indent
        return f"RETURN"

class Goto(Statement):
    def __init__(self, label:Label):
        self.label = label
    
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"GOTO {self.label}"

class ComputedGoto(Statement):
    def __init__(self, labels:list[Label], expr:Expression):
        self.labels = labels
        self.expr = expr

    def __repr__(self,indent = 0):
        space = '  '*indent
        return f"GOTO ({', '.join(str(label) for label in self.labels)}) , {self.expr}"

class AssignedGoto(Statement):
    def __init__(self, var, labels=None):
        self.var = var
        self.labels = labels

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        if self.labels:
            return f"GOTO {self.var} ({', '.join(str(label) for label in self.labels)})"
        else:
            return f"GOTO {self.var}"

class ArithmeticIf(Statement):
    def __init__(self, exp, labeln, labelz, labelp):
        super().__init__()
        self.exp = exp
        self.labeln = labeln # exp < 0, usa esta label
        self.labelz = labelz # exp == 0, usa esta label
        self.labelp = labelp # exp > 0, usa esta label

    def __repr__(self):
        return self.repr(0)
    
    def repr(self, indent = 0):
        return f"IF ({self.exp}) {self.labeln}, {self.labelz}, {self.labelp}"

class LogicIf(Statement):
    def __init__(self, exp, statement):
        super().__init__()
        self.exp = exp
        self.statement = statement
    
    def __repr__(self):
        return self.repr(0)
    
    def repr(self, indent = 0):
        return f"IF ({self.exp})\n{self.statement.repr(indent+1)}"

class BlockIf(Statement):
    def __init__(self, exp:Expression, thenBody:list[LabeledStatement], elseBody:list[LabeledStatement]|BlockIf|None = None):
        super().__init__()
        self.exp = exp #condição
        self.thenBody = thenBody #conjunto de statements
        self.elseBody = elseBody #Pode ñ existir(None), ser uma lista de statements(else) ou outro BlockIf(kinda q1 elif)

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space0 = '  '*indent
        space1 = '  '*(indent+1)

        elseBodyText = ""
        if isinstance(self.elseBody, list):
            elseBodyText = f"{print_indented_list('ELSE', self.elseBody, indent+1)}\n"
        elif self.elseBody is not None:
            elseBodyText = self.elseBody.repr(indent+1)
        elseBodyText += f"{space0}}}ENDIF"

        return (f"IF ({self.exp}){{\n"
                f"{print_indented_list('THEN', self.thenBody, indent+1)}\n"
                f"{elseBodyText}")

class Mod(Statement):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"MOD({self.left}, {self.right})"


class Call(Statement):
    def __init__(self, subroutine,arguments):
        super().__init__()
        self.subroutine = subroutine
        self.arguments = arguments
    
    def __eq__(self, other):
        if isinstance(other, Call):
            return self.subroutine == other.subroutine and self.arguments == other.arguments
        return False
    
    def __hash__(self):
        return hash((self.subroutine, tuple(self.arguments)))

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = ' '*indent
        return f"Call(Subroutine: {self.subroutine}, Arguments: {self.arguments})"

#NOTA: Em FORTRAN 77, as chamadas de funcoes e acessos a array(incluindo arrays de arrays) tem a mesma sintaxe
class FunctionorArraysAccess(Node):
    def __init__(self, name:str, expressionList):
        super().__init__()
        self.name = name
        self.expressionList = expressionList

    def __eq__(self, other):
        if isinstance(other, FunctionorArraysAccess):
            return self.name == other.name and self.expressionList == other.expressionList
        return False

    def __hash__(self):
        return hash((self.name, tuple(self.expressionList)))

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"{space}Chamada da funcao/array {self.name} com/em {self.expressionList}"
    
class Read(Statement):
    def __init__(self, format:str, iolist):
        super().__init__()
        self.format = format
        self.iolist = iolist
    
    def __repr__(self):
        return self.repr(0)
    
    def repr(self, indent = 0) -> str:
        space = '  '*indent
        return f"Read(Format: {self.format}, Items: {self.iolist})"

class LabeledDO(Statement):
    def __init__(self, label:Label, control_var:str, control_var_init_value, iterations_number, labeled_statements = None, step = 1):
        super().__init__()
        self.label = label
        self.control_var = control_var
        self.control_var_init_value = control_var_init_value
        self.iterations_number = iterations_number
        self.labeled_statements = labeled_statements #temporariamente a none
        self.step = step

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return (f"DO {self.label} (INIT = {self.control_var} = {self.control_var_init_value}, LIMIT = {self.iterations_number}, STEP = {self.step})"
                # f"  LabeledStatements: {self.labeled_statements}\n"
                # f"{self.label} END DO"
                )

class BlockDO(Statement):
    def __init__(self, control_var:str, init_value, max_value, labeled_statements:list[LabeledStatement], step = 1):
        super().__init__()
        self .control_var = control_var
        self.init_value = init_value
        self.max_value = max_value
        self.labeled_statements = labeled_statements
        self.step = step
    
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return (f"DO (INIT = {self.control_var} = {self.init_value}, LIMIT = {self.max_value}, STEP = {self.step}){{\n"
                f"{print_indented_list('LabeledStatements', self.labeled_statements, indent+1)}\n"
                f"{space}}}END DO")










class Variable(Node):
    def __init__(self, name:str):
        super().__init__()
        self.name = name

    def __eq__(self, other):
        if isinstance(other, Variable):
            return self.name == other.name
        return False

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{space}Variable({self.name})"

class IntVal(Node):
    def __init__(self, value: int):
        super().__init__()
        self.value = value
    def __repr__(self): return self.repr(0)
    def repr(self, indent=0):
        return f"{'  '*indent}IntVal({self.value})"

class RealVal(Node):
    def __init__(self, value: float):
        super().__init__()
        self.value = value
    def __repr__(self): return self.repr(0)
    def repr(self, indent=0):
        return f"{'  '*indent}RealVal({self.value})"

class StringVal(Node):
    def __init__(self, value: str):
        super().__init__()
        self.value = value
    def __repr__(self): return self.repr(0)
    def repr(self, indent=0):
        return f"{'  '*indent}StringVal('{self.value}')"

class LogicalVal(Node):
    def __init__(self, value: bool):
        super().__init__()
        self.value = value
    def __repr__(self): return self.repr(0)
    def repr(self, indent=0):
        return f"{'  '*indent}LogicalVal({self.value})"