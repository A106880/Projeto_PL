from __future__ import annotations
import os

import ply.lex as lex
import ply.yacc as yacc

class Node:
    """Classe base genérica para todos os nós da AST."""
    def __init__(self):
        self.lineno = None
    
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0)->str:
        return ""
    
def print_indented_list(nome:str, list:list, indent:int = 0):
    space0 = '  '*indent
    space1 = '  '*(indent+1)
    if any(isinstance(elem, Node) for elem in list):
        return f"{space0}{nome}{{\n"+"\n".join(elem.repr(indent+1) for elem in list)+f"\n{space0}}}"
    else:
        return f"{space0}{nome}{{\n"+"\n".join(f'{space1}{elem}' for elem in list)+f"\n{space0}}}"

def printIfNotNone(conteudo, limitadorEsq:str, limitadorDir:str)->str:
    return f"{limitadorEsq}{str(conteudo)}{limitadorDir}" if conteudo is not None else "" 

class ArrayId(Node):
    def __init__(self, nome:str, tamanho:int):
        super().__init__()
        self.nome = nome
        if(tamanho is None):
            self.tamanho = 0 # ou 1 caso se queira fazer singleton == array de 1 elemento 
        else:
            self.tamanho = tamanho

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return f"{space}{self.nome}{f'[{self.tamanho}]' if self.tamanho != 0 else ''}" 

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
            elems.append(f"{elem.nome}"+(f"[{elem.tamanho}]" if elem.tamanho > 0 else ""))
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


class ProgramaPrincipal(Node):
    def __init__(self, name:str, declarations:list[Declaracao], labeled_statements:list[LabeledStatement]):
        super().__init__()
        self.tipo_no = 'PROGRAMA_PRINCIPAL'
        self.name = name
        self.declarations = declarations
        self.labeled_statements = labeled_statements

    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space0 = '  '*indent
        space1 = '  '*(indent+1)
        return (f"Programa{printIfNotNone(self.name, '(', ')')}\n"
                f"{print_indented_list('Declarações', self.declarations, indent+1)}\n"
                f"{print_indented_list('LabeledStatements', self.labeled_statements, indent+1)}\n"
                f"{space0}END Programa{printIfNotNone(self.name, '(', ')')}\n")
    
class Funcao(Node):
    def __init__(self, return_type:str, name:str, arguments:list[str] 
                ,declarations:list[Declaracao], labeled_statements:list[LabeledStatement]):
        super().__init__()
        self.return_type = return_type
        self.name = name
        self.arguments = arguments
        self.declarations = declarations
        self.labeled_statements = labeled_statements
        
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return (f"Funcao({self.name}, TipoRetorno: {self.return_type})\n"
                f"{print_indented_list('Argumentos', self.arguments, indent+1)}\n"
                f"{print_indented_list('Declarações', self.declarations, indent+1)}\n"
                f"{print_indented_list('LabeledStatements', self.labeled_statements, indent+1)}\n"
                f"{space}END Funcao({self.name})\n")

class DoublePrecisonComplexVal(Node):
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

class Assignment(Statement):
    def __init__(self, name, value):
        super().__init__()
        self.name = name        # nome
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

#NOTA: Em FORTRAN 77, as chamadas de funcoes e acessos a array(incluindo arrays de arrays) tem a mesma sintaxe
class FunctionCallorArraysAccess(Node):
    def __init__(self, name:str, expressionList):
        super().__init__()
        self.name = name
        self.expressionList = expressionList

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

class Subroutine(Node):
    def __init__(self, name, arguments, declarations, labeled_statements):
        super().__init__()
        self.name = name
        self.arguments = arguments
        self.declarations = declarations
        self.labeled_statements = labeled_statements
        
    def __repr__(self):
        return self.repr(0)

    def repr(self, indent = 0):
        space = '  '*indent
        return (f"{space}Subrotina({self.name},\n"
                f"{print_indented_list('Argumentos',self.arguments, indent+1)}\n"
                f"{print_indented_list('Declarações',self.declarations, indent+1)}\n"
                f"{print_indented_list('LabeledStatements',self.labeled_statements, indent+1)}\n")
    
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

class LexError(Exception):
    pass

literals = "(),+-*/="
tokens = (
    'NEWLINE', 'PROGRAM', 'ID', 'END', 'FUNCTION', 'INTEGER', 'INTVAL', 
    'REAL', 'REALVAL', 'DOUBLEPRECISION', 'DOUBLEPRECISIONVAL', 'COMPLEX', 
    'DOUBLECOMPLEX', 'LOGICAL', 'LOGICALVAL', 
    'CHARACTER', 'CHARACTERVAL', 'HOLLERITH', 'HOLLERITHVAL', 'PRINT', 'READ', 
    'WRITE', 'DO', 'MOD', 'IF', 'THEN', 'ELSE', 'ENDIF', 'GOTO', 'CONTINUE', 'SUBROUTINE', 'CALL',
    'POWER', 'CONCAT', 'AND', 'OR', 'NOT', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
    'RETURN'
)

reserved = {
    'PROGRAM': 'PROGRAM', 
    'END': 'END', 
    'FUNCTION': 'FUNCTION', 
    'INTEGER': 'INTEGER', 
    'REAL': 'REAL', 
    'DOUBLEPRECISION': 'DOUBLEPRECISION',
    'COMPLEX': 'COMPLEX', 
    'DOUBLECOMPLEX': 'DOUBLECOMPLEX', 
    'LOGICAL': 'LOGICAL', 
    'CHARACTER': 'CHARACTER', 
    'HOLLERITH': 'HOLLERITH', 
    'PRINT': 'PRINT', 
    'READ': 'READ', 
    'WRITE': 'WRITE', 
    'DO': 'DO', 
    'MOD': 'MOD', 
    'IF': 'IF', 
    'THEN': 'THEN', 
    'ELSE': 'ELSE', 
    'ENDIF': 'ENDIF', 
    'GOTO': 'GOTO', 
    'CONTINUE': 'CONTINUE',
    'SUBROUTINE' : 'SUBROUTINE',
    'CALL' : 'CALL',
    'RETURN' : 'RETURN'
}

def t_INTVAL(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_DOUBLEPRECISIONVAL(t):
    r'\d+\.\d*(?:[Dd][+-]?\d+)?|\.\d+(?:[Dd][+-]?\d+)?|\d+[Dd][+-]?\d+'
    t.value = float(t.value.lower().replace('d', 'e'))
    return t

def t_REALVAL(t):
    r'\d+\.\d*(?:[Ee][+-]?\d+)?|\.\d+(?:[Ee][+-]?\d+)?|\d+[Ee][+-]?\d+'
    t.value = float(t.value)
    return t

def t_LOGICALVAL(t):
    r'\.(TRUE|true|FALSE|false)\.'
    t.value = True if 'true' in t.value.lower() else False
    return t

def t_CHARACTERVAL(t):
    r"'([^']|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t


def t_HOLLERITHVAL(t):
    r'\d+[Hh]\w*'
    pass


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value.upper(), 'ID')
    return t

t_ignore = ' \t'

def t_COMMENT(t):
    r'(^[Cc*].*)|(!.*)'
    pass


def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += len(t.value)
    t.type = 'NEWLINE'
    return t

def t_POWER(t):
    r'\*\*'
    t.type = reserved.get(t.value.upper(),'POWER')
    return t

def t_CONCAT(t):
    r'//'
    t.type = reserved.get(t.value.upper(),'CONCAT')
    return t

def t_AND(t):
    r'\.AND\.|\.and\.'
    t.type = reserved.get(t.value.upper(),'AND')
    return t

def t_OR(t):
    r'\.or\.|\.OR\.'
    t.type = reserved.get(t.value.upper(),'OR')
    return t

def t_NOT(t):
    r'\.NOT\.|\.not\.'
    t.type = reserved.get(t.value.upper(),'NOT')
    return t

def t_EQ(t):
    r'\.EQ\.|\.eq\.'
    t.type = reserved.get(t.value.upper(),'EQ')
    return t

def t_NE(t):
    r'\.NE\.|\.ne\.'
    t.type = reserved.get(t.value.upper(),'NE')
    return t

def t_LT(t):
    r'\.LT\.|\.lt\.'
    t.type = reserved.get(t.value.upper(),'LT')
    return t

def t_LE(t):
    r'\.LE\.|\.le\.'
    t.type = reserved.get(t.value.upper(),'LE')
    return t

def t_GT(t):
    r'\.GT\.|\.gt\.'
    t.type = reserved.get(t.value.upper(),'GT')
    return t

def t_GE(t):
    r'\.GE\.|\.ge\.'
    t.type = reserved.get(t.value.upper(),'GE')
    return t

def t_error(t):
    raise LexError(f"Illegal character {t.value[0]}")

lexer = lex.lex()

precedence = (
    ('left', 'OR'),            # .OR.
    ('left', 'AND'),           # .AND.
    ('right', 'NOT'),          # .NOT.
    ('left', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'), # Relacionais
    ('left', 'CONCAT'),        # //
    ('left', '+', '-'),        # Adição e Subtração
    ('left', '*', '/'),        # Multiplicação e Divisão
    ('right', 'POWER'),        # ** (Exponenciação)
    ('right', 'UMINUS'),       # Operador Unário (Negativo)
)

#Program -> ProgramUnit Program |
#               Vazio
def p_Program(p):
    '''Program : ProgramUnit Program
               | empty'''
    if len(p) > 2:
        p[0] = [p[1]] + p[2] 
    else:
        p[0] = []

# ProgramUnit -> FunctionDef | Main | Subroutine
def p_ProgramUnit(p):
    '''ProgramUnit : FunctionDef 
                   | Main
                   | Subroutine'''
    p[0] = p[1]

# p1: Main -> Functions PROGRAM ID\n Declaritions LabeledStatements END\n Functions
def p_main(p):
    '''Main : PROGRAM ID NewLines Declarations LabeledStatements END OptNewLines'''
    
    p[0] = ProgramaPrincipal(
        name=p[2],
        declarations=p[4],
        labeled_statements=p[5]
    ) 

def p_newlines(p):
    '''NewLines : NEWLINE NewLines
                | NEWLINE'''

def p_opt_newlines(p):
    '''OptNewLines : NEWLINE OptNewLines
                   | empty'''

# p2: FunctionDef -> FunctionType FUNCTION ID (ArgumentList)\n Declaritions LabeledStatements END\n
def p_functions(p):
    '''FunctionDef : FunctionType FUNCTION ID '(' ArgumentList ')' NewLines Declarations LabeledStatements END OptNewLines'''
    p[0] = Funcao(return_type=p[1], name=p[3], arguments=p[5], declarations=p[8], labeled_statements=p[9])
    
# p4: FunctionType -> INTEGER
# p5:     | REAL
# p6:     | DOUBLE PRECISION
# p7:     | COMPLEX
# p8:     | DOUBLE COMPLEX
# p9:     | LOGICAL
# p10:     | CHARACTER
# p11:     | HOLLERITH
# p12:     | Vazio
def p_function_type(p):
    '''FunctionType : INTEGER
                    | REAL
                    | DOUBLEPRECISION
                    | COMPLEX
                    | DOUBLECOMPLEX
                    | LOGICAL
                    | CHARACTER
                    | HOLLERITH'''
    p[0] = p[1] if len(p) > 1 else None
    
# p13: VarType -> INTEGER
# p14:     | REAL
# p15:     | DOUBL EPRECISION
# p16:     | COMPLEX
# p17:     | DOUBLECOMPLEX
# p18:     | LOGICAL
# p19:     | CHARACTER
# p20:     | HOLLERITH
def p_var_type(p):
    '''VarType : INTEGER
               | REAL
               | DOUBLEPRECISION
               | COMPLEX
               | DOUBLECOMPLEX
               | LOGICAL
               | CHARACTER
               | HOLLERITH'''
    p[0] = p[1]

# p21: Val -> INTVAL
# p22:     | REALVAL
# p23:     | DOUBLEPRE
# p24:     | ComplexVal
# p25:     | DOUBLECOMPLEXVAL
# p26:     | LOGICALVAL
# p27:     | CHARACTERVAL
# p28:     | HOLLERITHVAL
# p29:     | ID
def p_val(p):
    '''Val : INTVAL
           | REALVAL
           | DOUBLEPRECISIONVAL
           | ComplexVal
           | DoubleComplexVal
           | LOGICALVAL
           | CHARACTERVAL
           | HOLLERITHVAL
           | ID '''
    p[0] = p[1]

def p_double_complex_val(p):
    '''DoubleComplexVal : '(' DOUBLEPRECISIONVAL ',' DOUBLEPRECISIONVAL ')'  '''
    doubleComplexValue = DoublePrecisonComplexVal(
        p[2],
        p[4]
    )
    p[0] = doubleComplexValue

def p_complex_val(p):
    '''ComplexVal : '(' REALVAL ',' REALVAL ')'  '''
    complexValue = ComplexVal(
        p[2],
        p[4]
    )
    p[0] = complexValue
    
# p30: ArgumentList -> ID ArgumentRestList
# p31:     | Vazio
def p_argument_list(p):
    '''ArgumentList : ID ArgumentRestList
                    | empty'''
    if len(p) > 2:
        p[0] = [p[1]] + p[2] # Junta o primeiro argumento com o resto da lista
    else:
        p[0] = []
    
# p32: ArgumentRestList -> , ID ArgumentRestList
# p33:     | Vazio
def p_argument_rest_list(p):
    '''ArgumentRestList : ',' ID ArgumentRestList
                        | empty'''
    if len(p) > 2:
        p[0] = [p[2]] + p[3]
    else:
        p[0] = []


#p34: Declarations -> Declaration Declarations 
#p35:        | Vazio
def p_Declarations(p):
    '''Declarations : Declaration Declarations
                    | empty'''
    
    if len(p) > 2:
        p[0] = [p[1]] + p[2] 
    else:
        p[0] = []

#p36: Declaration -> VarType ArrayIdList\n
def p_Declaration(p):
    '''Declaration : VarType ArrayIdList NewLines'''
    nova_declaracao = Declaracao(p[1],p[2])
    p[0] = nova_declaracao




#p37: ArrayIdList -> ID ArraySize ArrayIdListRest
def p_ArrayIdList(p):
    '''ArrayIdList : ID ArraySize ArrayIdListRest'''
    p[0] = [ArrayId(p[1],p[2])] + p[3]


#p38: ArrayIdListRest -> ,ID ArraySize ArrayIdListRest
#p39:        |Vazio 
def p_ArrayIdListRest(p): 
    ''' ArrayIdListRest : ',' ID ArraySize ArrayIdListRest
                        | empty'''
    if len(p) > 2:
        p[0] = [ArrayId(p[2],p[3])] + p[4]
    else:
        p[0] = []

#p40: ArraySize -> (INTVAL)
#p41:        | Vazio
def p_ArraySize(p):
    ''' ArraySize : '(' INTVAL ')'
                  | empty '''
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = None



def p_labeled_statements(p):
    '''LabeledStatements : LabeledStatement LabeledStatements
                         | empty'''
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
    else:
        p[0] = []

def p_labeled_statement(p):
    '''LabeledStatement : Label Statement NewLines
                        | Statement NewLines'''
    if len(p) > 3:
        p[0] = LabeledStatement(p[1], p[2])
    else:
        p[0] = LabeledStatement(None, p[1])

#p: Statement -> Atribution
#p        | Print
#p        | Read
#p        | Write
#p        | Do
#p        | Mod
#p        | If
#p        | Goto
#p        | Continue
def p_statement(p):
    '''Statement : Atribution
                 | Print
                 | Read
                 | If
                 | Do
                 | Mod
                 | Goto
                 | Continue
                 | Call
                 | Return'''
    p[0] = p[1]
    
#NOTA: Em FORTRAN 77, as chamadas de funcoes e acessos a array(incluindo arrays de arrays) tem a mesma sintaxe
#p: Atribution -> FunctionCallorArraysAccess = VAL
def p_atribution(p):
    '''Atribution : FunctionCallorArraysAccess '=' Expression
                  | ID '=' Expression'''
    
    p[0] = Assignment(
        name=p[1],
        value=p[3]
    )

#p: Mod -> MOD(SameTypePair)
def p_mod(p):
    '''Mod : MOD '(' SameTypePair ')'  '''
    left, right = p[3]
    p[0] = Mod(left, right)

#p: SameTypePair -> INTVAL, INTVAL
#p                  | REALVAL, REALVAL
#p                  | ComplexVal, ComplexVal
#p                  |ID, ID 
#no caso de serem 2 ID, terá que se verificar se são do mesmo tipo...
def p_same_type_pair(p):
    '''SameTypePair : INTVAL ',' INTVAL
                    | REALVAL ',' REALVAL
                    | ComplexVal ',' ComplexVal
                    | ID ',' ID'''
    p[0] = (p[1], p[3])

#p: Continue -> Label CONTINUE
def p_continue (p):
    '''Continue : CONTINUE'''
    p[0] = Continue()

#p Return -> RETURN
def p_return(p):
    '''Return : RETURN'''
    p[0] = Return()

# p: GoTo -> GOTO Label
# p:       | GOTO '(' LabelSeq ')'  ',' Expression
# p:       | GOTO ID
# p:       | GOTO ID '(' LabelSeq ')'
def p_goto(p):
    '''Goto : GOTO Label
            | GOTO '(' LabelSeq ')'  ',' Expression
            | GOTO ID
            | GOTO ID '(' LabelSeq ')'  '''
    
    if len(p) == 3:
        if isinstance(p[2], int):
            p[0] = Goto(label=p[2])
        else:
            p[0] = AssignedGoto(var=p[2])

    elif len(p) == 7:
        p[0] = ComputedGoto(labels=p[3], expr=p[6])

    elif len(p) == 6:
        p[0] = AssignedGoto(var=p[2], labels=p[4])

# p: LabelSeq -> Label
# p:           | Label ',' LabelSeq
def p_label_seq(p):
    '''LabelSeq : Label
                | Label ',' LabelSeq'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_labeledDo(p):
    '''Do : DO Label ID '=' Expression ',' Expression Step'''
    p[0] = LabeledDO(p[2], p[3], p[5], p[7], step=p[8]if p[8] is not None else 1)

def p_block_do(p):
    '''Do : DO ID '=' Expression ',' Expression Step NewLines LabeledStatements END DO'''
    p[0] = BlockDO(p[2], p[4], p[6], p[9], step = p[7]if p[7] is not None else 1)

def p_step(p):
    '''Step : ',' Expression
            | empty'''
    if len(p)>2:
        p[0] = p[2]
    else:
        p[0] = p[1]

#p: If -> IF (Expression) Label ',' Label ',' Label
def p_if_arithmetic(p):
    '''If : IF '(' Expression ')' Label ',' Label ',' Label'''
    p[0] = ArithmeticIf(p[3], p[5], p[7], p[9])
#p:     | IF (Expression) Statement
def p_if_logic(p):
    '''If : IF '(' Expression ')' Statement'''
    p[0] = LogicIf(p[3], p[5])
#p:     | IF (Expression) THEN NewLines LabeledStatements ElseBlock ENDIF 
def p_if_block(p):
    '''If : IF '(' Expression ')' THEN NewLines LabeledStatements ElseBlock ENDIF'''
    p[0] = BlockIf(p[3], p[7], p[8])

#p: ElseBlock -> ELSE ElseBody 
#p: ElseBlock -> Vazio
def p_else_block(p):
    '''ElseBlock : ELSE ElseBody
                 | empty'''
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = None

#p: ElseBody -> NewLines LabeledStatements
#p:           | IF (Expression) THEN NewLines LabeledStatements ElseBlock
def p_else_body(p):
    '''ElseBody : NewLines LabeledStatements
                | IF '(' Expression ')' THEN NewLines LabeledStatements ElseBlock ENDIF'''
    if (len(p) == 3):
        p[0] = p[2]
    else:
        p[0] = BlockIf(exp = p[3], thenBody = p[7], elseBody = p[8])

def p_print(p):
    '''Print : PRINT Format Iolist'''
    print = Print(
        format=p[2],
        iolist=p[3]
    )
    p[0] = print

def p_format(p):
    '''Format : '*'
              | INTVAL'''
    p[0] = p[1]

def p_iolist(p):
    '''Iolist : ',' Expression Iolist
              | empty'''
    if len(p)>2:
        p[0] = [p[2]]+p[3]
    else:
        p[0] = []

def p_expression_binop(p):
    '''Expression : Expression '+' Expression
                  | Expression '-' Expression
                  | Expression '*' Expression
                  | Expression '/' Expression
                  | Expression POWER Expression
                  | Expression CONCAT Expression
                  | Expression EQ Expression
                  | Expression NE Expression
                  | Expression LT Expression
                  | Expression LE Expression  
                  | Expression GT Expression
                  | Expression GE Expression
                  | Expression AND Expression
                  | Expression OR Expression'''
    p[0] = BinOp(left=p[1], op=p[2], right=p[3])

def p_expression_unop(p):
    '''Expression : '-' Expression %prec UMINUS
                  | '+' Expression %prec UMINUS
                  | NOT Expression'''
    p[0] = UnOp(op=p[1], expr=p[2])

def p_expression_group(p):
    '''Expression : '(' Expression ')'  '''
    p[0] = p[2]

def p_expression_val(p):
    '''Expression : Val
                  | Mod
                  | FunctionCallorArraysAccess'''
    p[0] = p[1]

# Subroutine -> SUBROUTINE ID (ArgumentList)\n Declarations LabeledStatements END\n
def p_Subroutine(p):
    '''Subroutine :  SUBROUTINE ID '(' ArgumentList ')' NewLines Declarations LabeledStatements END OptNewLines'''
    p[0] = Subroutine(p[2],p[4],p[7],p[8])

#Call -> CALL ID (ArgumentList)
def p_Call(p):
    '''Call : CALL ID '(' ArgumentList ')'  '''
    p[0] = Call(p[2], p[4])


def p_label(p):
    '''Label : INTVAL'''

    p[0] = Label(p[1])

def p_function_call_or_arrays_access(p):
    '''FunctionCallorArraysAccess : ID '(' Expression ExpressionList ')'  '''
    p[0] = FunctionCallorArraysAccess(p[1], [p[3]] + p[4])


def p_expression_list(p):
    '''ExpressionList : ',' Expression ExpressionList
                      | empty'''
    if len(p) > 2:
        p[0] = [p[2]] + p[3]
    else:
        p[0] = []

def p_read(p):
    '''Read : READ Format Iolist'''
    p[0] = Read(format=p[2], iolist=p[3])

def p_error(p):
    if p:
        print(f"Erro de sintaxe próximo a '{p.value}' na linha {p.lineno}")
    else:
        print("Erro de sintaxe no final do ficheiro (Inesperado End Of File)")

def p_empty(p):
    'empty :'
    pass


if __name__ == '__main__':

    for file in ("parser.out", "parsetab.py"):
        try:
            os.remove(file)
        except FileNotFoundError:
            pass

    parser = yacc.yacc()


    codigo_fortran = ""
    for ex_number in range(1, 9):
        with open(f"exemplo{ex_number}.txt","r") as file:
            codigo_fortran = file.read()

        print(f"A iniciar a análise sintática do código Fortran de exemplo{ex_number}.txt\n")
        
        ast = parser.parse(codigo_fortran)
        
        if ast:
            print("Sucesso! Aqui está a AST gerada:")
            print(ast)
            print("\n\n\n")
        else:
            print("O parsing falhou e devolveu None. Verifica os erros acima.")