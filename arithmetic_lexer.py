import ply.lex as lex
from node_classes import Variable
import re


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
    'SUBROUTINE': 'SUBROUTINE',
    'CALL': 'CALL',
    'RETURN': 'RETURN'
}


def t_HOLLERITHVAL(t):
    r'\d+[Hh]\w+'
    match = re.match(r'(\d+)[Hh](.*)', t.value)
    if match:
        n = int(match.group(1))
        text = match.group(2)[:n]
        t.value = text
    t.lineno = t.lexer.lineno
    return t


def t_DOUBLEPRECISIONVAL(t):
    r'\d+\.\d*(?:[Dd][+-]?\d+)?|\.\d+(?:[Dd][+-]?\d+)?|\d+[Dd][+-]?\d+'
    t.value = float(t.value.lower().replace('d', 'e'))
    t.lineno = t.lexer.lineno
    return t


def t_REALVAL(t):
    r'\d+\.\d*(?:[Ee][+-]?\d+)?|\.\d+(?:[Ee][+-]?\d+)?|\d+[Ee][+-]?\d+'
    t.value = float(t.value)
    t.lineno = t.lexer.lineno
    return t


def t_INTVAL(t):
    r'\d+'
    t.value = int(t.value)
    t.lineno = t.lexer.lineno
    return t


def t_LOGICALVAL(t):
    r'\.(TRUE|true|FALSE|false)\.'
    t.value = True if 'true' in t.value.lower() else False
    t.lineno = t.lexer.lineno
    return t


def t_CHARACTERVAL(t):
    r''([^']|'')*''
    t.value = t.value[1:-1].replace('''', ''')
    t.lineno = t.lexer.lineno
    return t


def t_ID(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    t.type = reserved.get(t.value.upper(), 'ID')
    t.value = Variable(t.value.upper())
    t.value.lineno = t.lexer.lineno
    t.lineno = t.lexer.lineno
    return t


t_ignore = ' \t'


def preprocess_fortran(source):
    lines = source.split('\n')
    for i, line in enumerate(lines):
        if line and line[0] in ('C', 'c', '*'):
            lines[i] = ''
    return '\n'.join(lines)


def t_COMMENT(t):
    r'!.*'
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
