from arithmetic_parser import parser
from node_classes import Assignment
from semantic_parser import SymbolTable
from error_classes import SemanticError
from node_classes import Variable
from verify import Verifier

translate = {
    "INTEGER": int,
    "REAL": float,
    "DOUBLEPRECISION": float,
    "COMPLEX": complex,
    "DOUBLECOMPLEX": complex,
    "LOGICAL": bool,
    "CHARACTER": str,
    'HOLLERITH': str}


def verify_declarations(declarations):
    for i in range(len(declarations)):
        for var in declarations[i].Ids:
            parser.symbols.declare(var.nome.nome, declarations[i].tipo.nome)

def verify_statements(statements):
    for statement in statements:
        assign = statement.statement
        if isinstance(assign, Assignment):
            assign_type = parser.symbols.lookup(assign.name.nome)[0]
            assign_type_translated = None
            if isinstance(assign.value, Variable):
                value_type = parser.symbols.lookup(assign.value.nome)[0]
                value_type = translate.get(value_type)
            else:
                value_type = type(assign.value)
            
            assign_type_translated = translate.get(assign_type)
            
            if assign_type_translated is None:
                raise SemanticError(f"Unknown type for variable {assign.name.nome}: {translate.get(assign_type)}")
            if assign_type_translated != value_type:
                raise SemanticError(f"Type mismatch in assignment to {assign.name.nome}: expected {translate.get(assign_type)}, got {value_type}")

            parser.symbols.initialize(assign.name.nome)

def verify_program(ast):

    verifier = Verifier()
    verifier.verify_global_names(ast)
    for program_unit in ast:
        program_unit_name = program_unit.name.nome
        verifier.verify_declarations(program_unit.declarations,program_unit_name)
        verifier.verify_statements(program_unit.labeled_statements,program_unit_name)

    verify_declarations(ast[0].declarations)
    verify_statements(ast[0].labeled_statements)


if __name__ == '__main__':
from semantic_parser import SemanticParser


if __name__ == "__main__":
    # for file in ("parser.out", "parsetab.py"):
    #     try:
    #         os.remove(file)
    #     except FileNotFoundError:
    #         pass

    codigo_fortran = ""
    ex_number = 8
    # for ex_number in range(1, 9):
    with open(f"exemplo{ex_number}.txt", "r") as file:
        codigo_fortran = file.read()

    print(
        f"A iniciar a análise sintática do código Fortran de exemplo{ex_number}.txt\n"
    )

    ast = parser.parse(codigo_fortran)

    if ast:
        print("Sucesso! Aqui está a AST gerada:")
        print(ast)
        
        
        
        parser.symbols = SymbolTable()
        res = verify_program(ast)
        #print(res)
        print("\n\n\n")
        print("\n--- Análise Semântica ---\n")
        semantic_parser = SemanticParser()
        semantic_parser.verify_program(ast)
        print(semantic_parser.errors.report())
        print("\n")
    else:
        print("O parsing falhou e devolveu None. Verifica os erros acima.")



