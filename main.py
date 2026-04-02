import ply.lex as lex
import ply.yacc as yacc

class Node:
    """Classe base genérica para todos os nós da AST."""
    def __init__(self):
        self.lineno = None

class ProgramaPrincipal(Node):
    def __init__(self, funcoes_cima, nome, declaracoes, comandos, funcoes_baixo):
        super().__init__()
        self.tipo_no = 'PROGRAMA_PRINCIPAL'
        self.funcoes_cima = funcoes_cima
        self.nome = nome
        self.declaracoes = declaracoes
        self.comandos = comandos
        self.funcoes_baixo = funcoes_baixo

    def __repr__(self):
        return f"Programa({self.nome})"

class Funcao(Node):
    def __init__(self, tipo_retorno, nome, argumentos, declaracoes, comandos):
        super().__init__()
        self.tipo_retorno = tipo_retorno
        self.nome = nome
        self.argumentos = argumentos
        self.declaracoes = declaracoes
        self.comandos = comandos
        
    def __repr__(self):
        return f"Funcao({self.nome})"


class Declaracao(Node):
    def __init__(self, tipo, ArrayIdList):
        super().__init__()
        self.tipo = tipo
        self.Ids = ArrayIdList
    
    def __repr__(self):
        str = f"Declaracao({self.tipo}"
        for elem in self.ArrayIdList:
            str = str + f"{elem.nome}[{elem.tamanho}] / "
        return str + ")"



class ArrayId(Node):
    def __init__(self,nome,tamanho):
        super().__init__()
        self.nome = nome
        if(tamanho == None):
            self.tamanho = 0 # ou 1 caso se queira fazer singleton == array de 1 elemento 
        self.tamanho = tamanho


class LexError(Exception):
    pass

literals = "(),\t"
tokens = (
    'NEWLINE', 'PROGRAM', 'ID', 'END', 'FUNCTION', 'INTEGER', 'INTVAL', 
    'REAL', 'REALVAL', 'DOUBLEPRECISION', 'DOUBLEPRECISIONVAL', 'COMPLEX', 
    'COMPLEXVAL', 'DOUBLECOMPLEX', 'DOUBLECOMPLEXVAL', 'LOGICAL', 'LOGICALVAL', 
    'CHARACTER', 'CHARACTERVAL', 'HOLLERITH', 'HOLLERITHVAL', 'PRINT', 'READ', 
    'WRITE', 'DO', 'MOD', 'IF', 'THEN', 'ELSE', 'ENDIF', 'GOTO', 'CONTINUE'
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

def t_COMPLEXVAL(t):
    r'COMPLEXVAL_PLACEHOLDER'
    pass

def t_DOUBLECOMPLEXVAL(t):
    r'DOUBLECOMPLEXVAL_PLACEHOLDER'
    pass

def t_LOGICALVAL(t):
    r'\.(TRUE|true|FALSE|false)\.'
    t.value = True if 'true' in t.value.lower() else False
    return t

def t_CHARACTERVAL(t):
    r"'([^']|'')*'"
    t.value = t.value[1:-1].replace("''", "'")
    return t


def t_HOLLERITHVAL(t):
    r'HOLLERITHVAL_PLACEHOLDER'
    pass


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

def t_error(t):
    raise LexError(f"Illegal character {t.value[0]}")

lexer = lex.lex()

# p1: Main -> Functions PROGRAM ID\n Declaritions Statements END\n Functions
def p_main(p):
    '''Main : Functions PROGRAM ID NEWLINE Declarations Statements END NEWLINE Functions'''
    
    p[0] = ProgramaPrincipal(
        funcoes_cima=p[1],
        nome=p[3],
        declaracoes=p[5],
        comandos=p[6],
        funcoes_baixo=p[9]
    ) 

# p2: Functions -> FunctionType FUNCTION ID (ArgumentList)\n Declaritions Statements END\n Functions
# p3:            | Vazio
def p_functions(p):
    '''Functions : FunctionType FUNCTION ID '(' ArgumentList ')' NEWLINE Declarations Statements END NEWLINE Functions
                 | empty'''
    if len(p) > 2:
        nova_funcao = Funcao(tipo_retorno=p[1], nome=p[3], argumentos=p[5], declaracoes=p[8], comandos=p[9])
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
           | COMPLEXVAL
           | DOUBLECOMPLEXVAL
           | LOGICALVAL
           | CHARACTERVAL
           | HOLLERITHVAL
           | ID'''
    p[0] = p[1]
    
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
    """Declarations : Declaration Declarations"
                    | empty"""
    
    if len(p) > 2:
        p[0] = [p[1]] + p[2] 
    else:
        p[0] = []

#p36: Declaration -> VarType ArrayIdList\n
def p_Declaration(p):
    "Declaration : VarType ArrayIdList"
    nova_declaracao = Declaracao(p[1],p[2])
    p[0] = nova_declaracao




#p37: ArrayIdList -> ID ArraySize ArrayIdListRest
def p_ArrayIdList(p):
    "ArrayIdList : ID ArraySize ArrayIdListRest"
    p[0] = [ArrayId(p[1],p[2])] + p[3]


#p38: ArrayIdListRest -> ,ID ArraySize ArrayIdListRest
#p39:        |Vazio 
def p_ArrayIdListRest(p): 
    """ ArrayIdListRest : ',' ID ArraySize ArrayIDListRest
                        | empty"""
    if len(p) > 2:
        p[0] = [ArrayId(p[2],p[3])] + p[4]
    else:
        p[0] = []

#p40: ArraySize -> (INTVAL)
#p41:        | Vazio
def p_ArraySize(p):
    """ ArraySize : '(' INTVAL ')'
                  | empty """
    if len(p) > 2:
        p[0] = p[2]
    else:
        p[0] = None



#p42: Statements -> Label Statement \n Statements
#p43:                | Vazio
def p_Statements(p):
    """Statements : Label Statement '\n' Statements
                  | empty"""
    if len(p) > 2:
        p[0] = [(p[1],p[2])] + p[4]
    else:
        p[0] = []


def p_error(p):
    if p:
        print(f"Erro de sintaxe próximo a '{p.value}' na linha {p.lineno}")
    else:
        print("Erro de sintaxe no final do ficheiro (Inesperado End Of File)")

def p_empty(p):
    'empty :'
    pass

parser = yacc.yacc()