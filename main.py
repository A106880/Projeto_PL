import ply.lex as lex

class LexError(Exception):
    pass

literals = "()\n,\t"
tokens = ('PROGRAM', 'ID', 'END', 'FUNCTION', 'INTEGER', 'INTVAL', 'REAL', 'REALVAL', 'DOUBLEPRECISION', 'DOUBLEPRECISIONVAL', 'COMPLEX', 'COMPLEXVAL', 'DOUBLECOMPLEX', 'DOUBLECOMPLEXVAL', 'LOGICAL', 'LOGICALVAL', 'CHARACTER', 'CHARACTERVAL', 'HOLLERITH', 'HOLLERITHVAL', 'PRINT', 'READ', 'WRITE', 'DO', 'MOD', 'IF', 'THEN', 'ELSE', 'ENDIF', 'GOTO', 'CONTINUE')

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
    pass

def t_DOUBLECOMPLEXVAL(t):
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

t_ignore = ' \t\n'

def t_COMMENT(t):
    r'(^[Cc*].*)|(!.*)'
    pass


def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    raise LexError(f"Illegal character {t.value[0]}")


__file__ = "Untitled.ipynb"
lexer = lex.lex()


_lookahead = None


def next_token():
    global _lookahead
    _lookahead = lexer.token()


def lookahead():
    return (_lookahead.type, _lookahead.value, _lookahead.lineno, _lookahead.lexpos) if _lookahead else ('$', None, None, None)


class ParserError(Exception):
    pass


def recognize_terminal(expected_type):
    token_type, token_val, token_line, token_pos = lookahead()


    if(token_type == expected_type):
        next_token()
        return token_val
    else:
        raise ParserError(f'Unexpected token when recognizing terminal {expected_type}: {token_type}')





# p1: Main -> Functions PROGRAM ID\n Declaritions Statements END\n Functions
def recognize_Main():
    token_type, token_val, token_line, token_pos = lookahead()

    first_main = ['FUNCTION', 'PROGRAM', 'INTEGER', 'REAL', 'DOUBLEPRECISION', 'COMPLEX', 'DOUBLECOMPLEX', 'LOGICAL', 'CHARACTER', 'HOLLERITH']

    if token_type in first_main:
        recognize_Functions()
        recognize_terminal('PROGRAM')
        recognize_terminal('ID')
        recognize_terminal('\n')
        recognize_Declarations()
        recognize_Statements()
        recognize_terminal('END')
        recognize_terminal('\n')
        recognize_Functions()
    else:
        raise ParserError(f'Unexpected token when recognizing nonterminal \'Main\': {token_type}')
    

# p2: Functions -> FunctionType FUNCTION ID (ArgumentList)\n Declaritions Statements END\n Functions
# p3:            | Vazio
def recognize_Functions():
    token_type, token_val, token_line, token_pos = lookahead()

    first_functions = ['FUNCTION', 'INTEGER', 'REAL', 'DOUBLEPRECISION', 'COMPLEX', 'DOUBLECOMPLEX', 'LOGICAL', 'CHARACTER', 'HOLLERITH']
    follow_functions = ['PROGRAM', '$']

    if token_type in first_functions:
        recognize_FunctionType()
        recognize_terminal('FUNCTION')
        recognize_terminal('ID')
        recognize_terminal('(')
        recognize_ArgumentList()
        recognize_terminal(')')
        recognize_terminal('\n')
        recognize_Declarations()
        recognize_Statements()
        recognize_terminal('END')
        recognize_terminal('\n')
        recognize_Functions()
    elif token_type in follow_functions:
        pass
    else:
        raise ParserError(f'Unexpected token when recognizing nonterminal \'Functions\': {token_type}')
    
# p4: FunctionType -> INTEGER
# p5:     | REAL
# p6:     | DOUBLE PRECISION
# p7:     | COMPLEX
# p8:     | DOUBLE COMPLEX
# p9:     | LOGICAL
# p10:     | CHARACTER
# p11:     | HOLLERITH
# p12:     | Vazio
def recognize_FunctionType():
    token_type, token_val, token_line, token_pos = lookahead()

    first_functionType = ['INTEGER', 'REAL', 'DOUBLEPRECISION', 'COMPLEX', 'DOUBLECOMPLEX', 'LOGICAL', 'CHARACTER', 'HOLLERITH']
    follow_functionType = ['FUNCTION']

    if token_type in first_functionType:
        recognize_terminal(token_type)
    elif token_type in follow_functionType:
        pass
    else:
        raise ParserError(f'Unexpected token when recognizing nonterminal \'FunctionType\': {token_type}')
    
# p13: VarType -> INTEGER
# p14:     | REAL
# p15:     | DOUBL EPRECISION
# p16:     | COMPLEX
# p17:     | DOUBLECOMPLEX
# p18:     | LOGICAL
# p19:     | CHARACTER
# p20:     | HOLLERITH
def recognize_VarType():
    token_type, token_val, token_line, token_pos = lookahead()

    first_VarType = ['INTEGER', 'REAL', 'DOUBLEPRECISION', 'COMPLEX', 'DOUBLECOMPLEX', 'LOGICAL', 'CHARACTER', 'HOLLERITH']

    if token_type in first_VarType:
        recognize_terminal(token_type)
    else:
        raise ParserError(f'Unexpected token when recognizing nonterminal \'VarType\': {token_type}')

# p21: Val -> INTVAL
# p22:     | REALVAL
# p23:     | DOUBLEPRE
# p24:     | COMPLEXVAL
# p25:     | DOUBLECOMPLEXVAL
# p26:     | LOGICALVAL
# p27:     | CHARACTERVAL
# p28:     | HOLLERITHVAL
# p29:     | ID
def recognize_Val():
    token_type, token_val, token_line, token_pos = lookahead()

    first_Val = ['ID', 'INTVAL', 'REALVAL', 'DOUBLEPRECISIONVAL', 'COMPLEXVAL', 'DOUBLECOMPLEXVAL', 'LOGICALVAL', 'CHARACTERVAL', 'HOLLERITHVAL']

    if token_type in first_Val:
        recognize_terminal(token_type)
    else:
        raise ParserError(f'Unexpected token when recognizing nonterminal \'Val\': {token_type}')
    
# p30: ArgumentList -> ID ArgumentRestList
# p31:     | Vazio
def recognize_ArgumentList():
    token_type, token_val, token_line, token_pos = lookahead()

    first_argumentList = ['ID']
    follow_argumentList = [')']

    if token_type in first_argumentList:
        recognize_terminal('ID')
        recognize_ArgumentList()
    elif token_type in follow_argumentList:
        pass
    else:
        raise ParserError(f'Unexpected token when recognizing nonterminal \'ArgumentList\': {token_type}')
    
# p32: ArgumentRestList -> , ID ArgumentRestList
# p33:     | Vazio
def recognize_ArgumentRestList():
    token_type, token_val, token_line, token_pos = lookahead()

    first_argumentRestList = [',']
    follow_argumentRestList = [')']

    if token_type in first_argumentRestList:
        recognize_terminal(',')
        recognize_terminal('ID')
        recognize_ArgumentRestList()
    elif token_type in follow_argumentRestList:
        pass
    else:
        raise ParserError(f'Unexpected token when recognizing nonterminal \'ArgumentRestList\': {token_type}')