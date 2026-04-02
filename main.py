import ply.lex as lex
import ply.yacc as yacc

class Node:
    """Classe base genérica para todos os nós da AST."""
    def __init__(self):
        self.lineno = None

class ProgramaPrincipal(Node):
    def __init__(self, upper_functions, name, declarations, labeled_statements, bottom_functions):
        super().__init__()
        self.tipo_no = 'PROGRAMA_PRINCIPAL'
        self.upper_functions = upper_functions
        self.name = name
        self.declarations = declarations
        self.labeled_statements = labeled_statements
        self.bottom_functions = bottom_functions

    def __repr__(self):
        return (f" Funções(cima){self.upper_functions}\n"
                f"Programa({self.name})\n"
                f"  Declarações{self.declarations}\n"
                f"  LabeledStatements{self.labeled_statements}\n"
                f"  Funções(baixo){self.bottom_functions}")

class Funcao(Node):
    def __init__(self, return_type, name, arguments, declarations, labeled_statements):
        super().__init__()
        self.return_type = return_type
        self.name = name
        self.arguments = arguments
        self.declarations = declarations
        self.labeled_statements = labeled_statements
        
    def __repr__(self):
        return (f"Funcao({self.name}, TipoRetorno: {self.return_type})\n"
                f"  Argumentos: {self.arguments}\n"
                f"  {self.declarations}\n"
                f"  {self.labeled_statements}")

class DoublePrecisonComplexVal(Node):
    def __init__(self, elem1, elem2):
        super().__init__()
        self.elem1 = elem1
        self.elem2 = elem2
    def __repr__(self):
        return f"DoublePrecisionComplex({self.elem1},{self.elem2})"

class ComplexVal(Node):
    def __init__(self, elem1, elem2):
        super().__init__()
        self.elem1 = elem1
        self.elem2 = elem2
    def __repr__(self):
        return f"Complex({self.elem1},{self.elem2})"
    
class Print(Node):
    def __init__(self,format,iolist):
        super().__init__()
        self.format = format
        self.iolist = iolist
    def __repr__(self) -> str:
        return f"Print(Format: {self.format}, Items: {self.iolist})"

class BinOp(Node):
    """Nó para operações binárias (ex: A + B, NUM .GT. 5)"""
    def __init__(self, left, op, right):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right
        
    def __repr__(self):
        return f"({self.left} {self.op} {self.right})"

class UnOp(Node):
    """Nó para operações unárias (ex: -A, .NOT. ISPRIM)"""
    def __init__(self, op, expr):
        super().__init__()
        self.op = op
        self.expr = expr
        
    def __repr__(self):
        return f"({self.op} {self.expr})"

class Declaracao(Node):
    def __init__(self, tipo, ArrayIdList):
        super().__init__()
        self.tipo = tipo
        self.Ids = ArrayIdList
    
    def __repr__(self):
        str = f"Declaracao({self.tipo}"
        for elem in self.Ids:
            str += f" {elem.nome}"
            str += (f"[{elem.tamanho}]" if elem.tamanho > 0 else "")
            str += " / "
        return str + ")"



class ArrayId(Node):
    def __init__(self,nome,tamanho):
        super().__init__()
        self.nome = nome
        if(tamanho is None):
            self.tamanho = 0 # ou 1 caso se queira fazer singleton == array de 1 elemento 
        else:
            self.tamanho = tamanho
    def __repr__(self):
        # Faltava-te o __repr__ aqui! 
        # Assim ele distingue se é uma variável simples (N) ou um array (NUMS[5])
        if self.tamanho and self.tamanho != 0:
            return f"{self.nome}[{self.tamanho}]"
        return f"{self.nome}"        

class Statement(Node): #Representa uma ação
    pass

class Assignment(Statement):
    def __init__(self, name, index, value):
        super().__init__()
        self.name = name        # nome
        self.index = index      # None ou índice no array
        self.value = value      # expressão (valor)

    def __repr__(self):
        return f"{self.name}{''if self.index is None else f'[{self.index}]'} = {self.value}"

class Continue(Statement):
    def __init__(self, label):
        super().__init__()
        self.label = label  #label a acompanhar o continue
    
    def __repr__(self):
        return f"[{self.label}]CONTINUE"

class Mod(Statement):
    def __init__(self, left, right):
        super().__init__()
        self.left = left
        self.right = right

    def __repr__(self):
        return f"MOD({self.left}, {self.right})"

class LabeledStatement(Node):
    def __init__(self, label, statement):
        super().__init__()
        self.label = label      # int ou None
        self.statement = statement

    def __repr__(self):
        return f"{[{self.label}]if self.label!=None else ''} {self.statement}"

class LexError(Exception):
    pass

literals = "(),+-*/"
tokens = (
    'NEWLINE', 'PROGRAM', 'ID', 'END', 'FUNCTION', 'INTEGER', 'INTVAL', 
    'REAL', 'REALVAL', 'DOUBLEPRECISION', 'DOUBLEPRECISIONVAL', 'COMPLEX', 
    'DOUBLECOMPLEX', 'LOGICAL', 'LOGICALVAL', 
    'CHARACTER', 'CHARACTERVAL', 'HOLLERITH', 'HOLLERITHVAL', 'PRINT', 'READ', 
    'WRITE', 'DO', 'MOD', 'IF', 'THEN', 'ELSE', 'ENDIF', 'GOTO', 'CONTINUE', 
    'POWER', 'CONCAT', 'AND', 'OR', 'NOT', 'EQ', 'NE', 'LT', 'LE', 'GT', 'GE'
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
    'CONTINUE': 'CONTINUE'
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
    return t

def t_CONCAT(t):
    r'//'
    return t

def t_AND(t):
    r'\.AND\.|\.and\.'
    return t

def t_OR(t):
    r'\.or\.|\.OR\.'
    return t

def t_NOT(t):
    r'\.NOT\.|\.not\.'
    return t

def t_EQ(t):
    r'\.EQ\.|\.eq\.'
    return t

def t_NE(t):
    r'\.NE\.|\.ne\.'
    return t

def t_LT(t):
    r'\.LT\.|\.lt\.'
    return t

def t_LE(t):
    r'\.LE\.|\.le\.'
    return t

def t_GT(t):
    r'\.GT\.|\.gt\.'
    return t

def t_GE(t):
    r'\.GE\.|\.ge\.'
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

# p1: Main -> Functions PROGRAM ID\n Declaritions LabeledStatements END\n Functions
def p_main(p):
    '''Main : Functions PROGRAM ID NEWLINE Declarations LabeledStatements END NEWLINE Functions'''
    
    p[0] = ProgramaPrincipal(
        upper_functions=p[1],
        name=p[3],
        declarations=p[5],
        labeled_statements=p[6],
        bottom_functions=p[9]
    ) 

# p2: Functions -> FunctionType FUNCTION ID (ArgumentList)\n Declaritions LabeledStatements END\n Functions
# p3:            | Vazio
def p_functions(p):
    '''Functions : FunctionType FUNCTION ID '(' ArgumentList ')' NEWLINE Declarations LabeledStatements END NEWLINE Functions
                 | empty'''
    if len(p) > 2:
        nova_funcao = Funcao(return_type=p[1], name=p[3], arguments=p[5], declarations=p[8], labeled_statements=p[9])
        p[0] = [nova_funcao] + (p[12] if p[12] else [])
    else:
        p[0] = []
    
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
                    | HOLLERITH
                    | empty'''
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
# p24:     | COMPLEXVAL
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
    '''DoubleComplexVal : '(' DOUBLEPRECISIONVAL ',' DOUBLEPRECISIONVAL ')' '''
    doubleComplexValue = DoublePrecisonComplexVal(
        p[2],
        p[4]
    )
    p[0] = doubleComplexValue

def p_complex_val(p):
    '''ComplexVal : '(' REALVAL ',' REALVAL ')' '''
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
    '''Declaration : VarType ArrayIdList NEWLINE'''
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



#p42: LabeledStatements -> Label Statement \n LabeledStatements
#p43:                   | Vazio
def p_labeled_statements(p):
    '''LabeledStatements : Label Statement NEWLINE LabeledStatements
                         | empty'''
    if len(p) > 2:
        stmt = LabeledStatement(p[1], p[2])
        p[0] = [stmt] + p[4]
    else:
        p[0] = []

#p: Statement -> Atributions
#p        | Print
#p        | Read
#p        | Write
#p        | Do
#p        | Mod
#p        | If
#p        | Goto
#p        | Continue
def p_statement(p):
    '''Statement : Atributions
                 | Print
                 | Read
                 | Write
                 | Do
                 | Mod
                 | If
                 | Goto
                 | Continue'''
    p[0] = p[1]
    
#p: Atribution -> ID PosArray = VAL
def p_atribution(p):
    '''Atribution : ID PosArray '=' Val'''
    p[0] = Assignment(
        name=p[1],
        index=p[2] if p[2] else None,
        value=p[4]
    )

#p: PosArray -> (Pos)
#p        | Vazio
def p_pos_array(p):
    '''PosArray : '(' Pos ')'
                | empty'''

    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = []
    
#p: Pos -> INTVAL 
#p        | ID
def p_pos(p):
    '''Pos : INTVAL
           | ID'''
    p[0] = p[1]

#p: Mod -> MOD(SameTypePair)
def p_mod(p):
    '''Mod : MOD '(' SameTypePair ')' '''
    left, right = p[3]
    p[0] = Mod(left, right)

#p: SameTypePair -> INTVAL, INTVAL
#p                  | REALVAL, REALVAL
#p                  | COMPLEXVAL, COMPLEXVAL
#p                  |ID, ID 
#no caso de serem 2 ID, terá que se verificar se são do mesmo tipo...
def p_same_type_pair(p):
    '''SameTypePair : INTVAL ',' INTVAL
                    | REALVAL ',' REALVAL
                    | COMPLEXVAL ',' COMPLEXVAL
                    | ID ',' ID'''
    p[0] = (p[1], p[3])

#p: Continue -> Label CONTINUE
def p_continue (p):
    '''Continue : Label CONTINUE'''
    p[0] = ("continue", p[1])

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
    '''Expression : '(' Expression ')' '''
    p[0] = p[2]

def p_expression_val(p):
    '''Expression : Val'''
    p[0] = p[1]

#p: Label -> INTVAL
#p:      | Vazio
def p_label(p):
    '''Label : INTVAL
             | empty'''
    p[0] = p[1]

def p_error(p):
    if p:
        print(f"Erro de sintaxe próximo a '{p.value}' na linha {p.lineno}")
    else:
        print("Erro de sintaxe no final do ficheiro (Inesperado End Of File)")

def p_empty(p):
    'empty :'
    pass

parser = yacc.yacc()


if __name__ == '__main__':
    # 1. O código Fortran que queres testar
    # NOTA: Como a tua regra p_main exige um NEWLINE depois do END, 
    # é crucial deixar uma linha em branco no final da string!
    codigo_fortran = """PROGRAM HELLO
PRINT *, 'Ola, Mundo!'
END
"""

    print("A iniciar a análise (parsing) do código Fortran...\n")
    
    # 2. Chamar o parser
    # O PLY vai usar o 'lexer' automaticamente por trás dos panos
    ast = parser.parse(codigo_fortran)
    
    # 3. Imprimir o resultado (a tua Árvore de Sintaxe Abstrata)
    if ast:
        print("Sucesso! Aqui está a AST gerada:")
        print(ast)
    else:
        print("O parsing falhou e devolveu None. Verifica os erros acima.")