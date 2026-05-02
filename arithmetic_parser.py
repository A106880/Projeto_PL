import ply.yacc as yacc
from node_classes import ProgramaPrincipal, Funcao, Declaracao, Subroutine, BinOp, UnOp, ArrayId, DoublePrecisonComplexVal, ComplexVal, LabeledStatement, Assignment, Mod, Continue, Return, Goto, AssignedGoto, ComputedGoto, LabeledDO, BlockDO, ArithmeticIf, LogicIf, BlockIf, Print, Call, Label, FunctionCallorArraysAccess, Read
from arithmetic_lexer import tokens, lex


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
    p[0].lineno = p.lineno(1)

# p1: Main -> Functions PROGRAM ID\n Declaritions LabeledStatements END\n Functions
def p_main(p):
    '''Main : PROGRAM ID NewLines Declarations LabeledStatements END OptNewLines'''
    
    p[0] = ProgramaPrincipal(
        name=p[2],
        declarations=p[4],
        labeled_statements=p[5]
    )
    p[0].lineno = p.lineno(1) 

def p_newlines(p):
    '''NewLines : NEWLINE NewLines
                | NEWLINE'''
    pass

def p_opt_newlines(p):
    '''OptNewLines : NEWLINE OptNewLines
                   | empty'''
    pass

# p2: FunctionDef -> FunctionType FUNCTION ID (ArgumentList)\n Declaritions LabeledStatements END\n
def p_functions(p):
    '''FunctionDef : FunctionType FUNCTION ID '(' ArgumentList ')' NewLines Declarations LabeledStatements END OptNewLines'''
    p[0] = Funcao(return_type=p[1], name=p[3], arguments=p[5], declarations=p[8], labeled_statements=p[9])
    p[0].lineno = p.lineno(1)
    
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
    if p[0]:
        p[0].lineno = p.lineno(1)
    
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
    if not isinstance(p[0], (int, float, bool, str)):
        if p[0] is not None:
            p[0].lineno = p.lineno(1)

def p_double_complex_val(p):
    '''DoubleComplexVal : '(' DOUBLEPRECISIONVAL ',' DOUBLEPRECISIONVAL ')'  '''
    doubleComplexValue = DoublePrecisonComplexVal(
        p[2],
        p[4]
    )
    p[0] = doubleComplexValue
    p[0].lineno = p.lineno(1)

def p_complex_val(p):
    '''ComplexVal : '(' REALVAL ',' REALVAL ')'  '''
    complexValue = ComplexVal(
        p[2],
        p[4]
    )
    p[0] = complexValue
    p[0].lineno = p.lineno(1)
    
# p30: ArgumentList -> ID ArgumentRestList
# p31:     | Vazio
def p_argument_list(p):
    '''ArgumentList : ID ArgumentRestList
                    | empty'''
    if len(p) > 2:
        p[0] = [p[1]] + p[2] # Junta o primeiro argumento com o resto da lista
    else:
        p[0] = []
    if p[0] and len(p) > 2:
        p[0][0].lineno = p.lineno(1)
    
# p32: ArgumentRestList -> , ID ArgumentRestList
# p33:     | Vazio
def p_argument_rest_list(p):
    '''ArgumentRestList : ',' ID ArgumentRestList
                        | empty'''
    if len(p) > 2:
        p[0] = [p[2]] + p[3]
        p[0][0].lineno = p.lineno(1)
    else:
        p[0] = []


#p34: Declarations -> Declaration Declarations 
#p35:        | Vazio
def p_Declarations(p):
    '''Declarations : Declaration Declarations
                    | empty'''
    
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
        p[0][0].lineno = p.lineno(1)
    else:
        p[0] = []

#p36: Declaration -> VarType ArrayIdList\n
def p_Declaration(p):
    '''Declaration : VarType ArrayIdList NewLines'''
    nova_declaracao = Declaracao(p[1],p[2])
    p[0] = nova_declaracao
    p[0].lineno = p.lineno(1)




#p37: ArrayIdList -> ID ArraySize ArrayIdListRest
def p_ArrayIdList(p):
    '''ArrayIdList : ID ArraySize ArrayIdListRest'''
    p[0] = [ArrayId(p[1],p[2])] + p[3]
    p[0][0].lineno = p.lineno(1)


#p38: ArrayIdListRest -> ,ID ArraySize ArrayIdListRest
#p39:        |Vazio 
def p_ArrayIdListRest(p): 
    ''' ArrayIdListRest : ',' ID ArraySize ArrayIdListRest
                        | empty'''
    if len(p) > 2:
        p[0] = [ArrayId(p[2],p[3])] + p[4]
        p[0][0].lineno = p.lineno(1)
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
        p[0][0].lineno = p.lineno(1)
    else:
        p[0] = []

def p_labeled_statement(p):
    '''LabeledStatement : Label Statement NewLines
                        | Statement NewLines'''
    if len(p) > 3:
        p[0] = LabeledStatement(p[1], p[2])
    else:
        p[0] = LabeledStatement(None, p[1])
    p[0].lineno = p.lineno(1)

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
    p[0].lineno = p.lineno(1)
    
#NOTA: Em FORTRAN 77, as chamadas de funcoes e acessos a array(incluindo arrays de arrays) tem a mesma sintaxe
#p: Atribution -> FunctionCallorArraysAccess = VAL
def p_atribution(p):
    '''Atribution : FunctionCallorArraysAccess '=' Expression
                  | ID '=' Expression'''
    
    p[0] = Assignment(
        name=p[1],
        value=p[3]
    )
    p[0].lineno = p.lineno(1)

#p: Mod -> MOD(SameTypePair)
def p_mod(p):
    '''Mod : MOD '(' SameTypePair ')'  '''
    left, right = p[3]
    p[0] = Mod(left, right)
    p[0].lineno = p.lineno(1)

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
    p[0].lineno = p.lineno(1)

#p Return -> RETURN
def p_return(p):
    '''Return : RETURN'''
    p[0] = Return()
    p[0].lineno = p.lineno(1)

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
    p[0].lineno = p.lineno(1)

# p: LabelSeq -> Label
# p:           | Label ',' LabelSeq
def p_label_seq(p):
    '''LabelSeq : Label
                | Label ',' LabelSeq'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]
    if p[0]:
        p[0][0].lineno = p.lineno(1)

def p_labeledDo(p):
    '''Do : DO Label ID '=' Expression ',' Expression Step'''
    p[0] = LabeledDO(p[2], p[3], p[5], p[7], step=p[8]if p[8] is not None else 1)
    p[0].lineno = p.lineno(1)

def p_block_do(p):
    '''Do : DO ID '=' Expression ',' Expression Step NewLines LabeledStatements END DO'''
    p[0] = BlockDO(p[2], p[4], p[6], p[9], step = p[7]if p[7] is not None else 1)
    p[0].lineno = p.lineno(1)

def p_step(p):
    '''Step : ',' Expression
            | empty'''
    if len(p)>2:
        p[0] = p[2]
        if not isinstance(p[0], (int, float, bool, str)):
            if p[0] is not None:
                p[0].lineno = p.lineno(1)
    else:
        p[0] = p[1]

#p: If -> IF (Expression) Label ',' Label ',' Label
def p_if_arithmetic(p):
    '''If : IF '(' Expression ')' Label ',' Label ',' Label'''
    p[0] = ArithmeticIf(p[3], p[5], p[7], p[9])
    p[0].lineno = p.lineno(1)
#p:     | IF (Expression) Statement
def p_if_logic(p):
    '''If : IF '(' Expression ')' Statement'''
    p[0] = LogicIf(p[3], p[5])
    p[0].lineno = p.lineno(1)
#p:     | IF (Expression) THEN NewLines LabeledStatements ElseBlock ENDIF 
def p_if_block(p):
    '''If : IF '(' Expression ')' THEN NewLines LabeledStatements ElseBlock ENDIF'''
    p[0] = BlockIf(p[3], p[7], p[8])
    p[0].lineno = p.lineno(1)

#p: ElseBlock -> ELSE ElseBody 
#p: ElseBlock -> Vazio
def p_else_block(p):
    '''ElseBlock : ELSE ElseBody
                 | empty'''
    if len(p) > 2:
        p[0] = p[2]
        if p[0] is not None:
            p[0].lineno = p.lineno(1)
    else:
        p[0] = None

#p: ElseBody -> NewLines LabeledStatements
#p:           | IF (Expression) THEN NewLines LabeledStatements ElseBlock
def p_else_body(p):
    '''ElseBody : NewLines LabeledStatements
                | IF '(' Expression ')' THEN NewLines LabeledStatements ElseBlock ENDIF'''
    if (len(p) == 3):
        p[0] = p[2]
        if p[0]:
            p[0][0].lineno = p.lineno(1)
    else:
        p[0] = BlockIf(exp = p[3], thenBody = p[7], elseBody = p[8])
        p[0].lineno = p.lineno(1)

def p_print(p):
    '''Print : PRINT Format Iolist'''
    print = Print(
        format=p[2],
        iolist=p[3]
    )
    p[0] = print
    p[0].lineno = p.lineno(1)

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
    p[0].lineno = p.lineno(1)

def p_expression_unop(p):
    '''Expression : '-' Expression %prec UMINUS
                  | '+' Expression %prec UMINUS
                  | NOT Expression'''
    p[0] = UnOp(op=p[1], expr=p[2])
    p[0].lineno = p.lineno(1)

def p_expression_group(p):
    '''Expression : '(' Expression ')'  '''
    p[0] = p[2]
    if not isinstance(p[0], (int, float, bool, str)):
        if p[0] is not None:
            p[0].lineno = p.lineno(1)

def p_expression_val(p):
    '''Expression : Val
                  | Mod
                  | FunctionCallorArraysAccess'''
    p[0] = p[1]
    if not isinstance(p[0], (int, float, bool, str)):
        if p[0] is not None:
            p[0].lineno = p.lineno(1)

# Subroutine -> SUBROUTINE ID (ArgumentList)\n Declarations LabeledStatements END\n
def p_Subroutine(p):
    '''Subroutine :  SUBROUTINE ID '(' ArgumentList ')' NewLines Declarations LabeledStatements END OptNewLines'''
    p[0] = Subroutine(p[2],p[4],p[7],p[8])
    p[0].lineno = p.lineno(1)

#Call -> CALL ID (ArgumentList)
def p_Call(p):
    '''Call : CALL ID '(' ExpressionListStart ')' '''
    p[0] = Call(p[2], p[4])
    p[0].lineno = p.lineno(1)


def p_label(p):
    '''Label : INTVAL'''

    p[0] = Label(p[1])
    p[0].lineno = p.lineno(1)

def p_function_call_or_arrays_access(p):
    '''FunctionCallorArraysAccess : ID '(' Expression ExpressionList ')'  '''
    p[0] = FunctionCallorArraysAccess(p[1], [p[3]] + p[4])
    p[0].lineno = p.lineno(1)

def p_expression_list_start(p):
    '''ExpressionListStart : Expression ExpressionList
                      | empty'''
    if len(p) > 2:
        p[0] = [p[1]] + p[2]
        if p[0]:
            p[0][0].lineno = p.lineno(1)
    else:
        p[0] = []

def p_expression_list(p):
    '''ExpressionList : ',' Expression ExpressionList
                      | empty'''
    if len(p) > 2:
        p[0] = [p[2]] + p[3]
        if p[0]:
            p[0][0].lineno = p.lineno(1)
    else:
        p[0] = []

def p_read(p):
    '''Read : READ Format Iolist'''
    p[0] = Read(format=p[2], iolist=p[3])
    p[0].lineno = p.lineno(1)

def p_error(p):
    if p:
        print(f"Erro de sintaxe próximo a '{p.value}' na linha {p.lineno}")
    else:
        print("Erro de sintaxe no final do ficheiro (Inesperado End Of File)")

def p_empty(p):
    'empty :'
    pass


parser = yacc.yacc()