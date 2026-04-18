import os
from arithmetic_parser import parser
from node_classes import Assignment
translate = {
    "INTEGER": int,
    "REAL": float,
    "DOUBLEPRECISION": float,
    "COMPLEX": complex,
    "DOUBLECOMPLEX": complex,
    "LOGICAL": bool,
    "CHARACTER": str,
    'HOLLERITH': str}

declarations_dict = {}

def verify_declarations(declarations):
    for var in declarations[0].Ids:
        if var.nome in declarations_dict:
            print(f"Erro: Variável '{var.nome}' já declarada.")
            return False
        declarations_dict[var.nome] = declarations[0].tipo
    return True

def verify_statements(statements):
    for labeledstmt in statements:
        statement = labeledstmt.statement
        if isinstance(statement, Assignment):
            var_name = statement.name
            
            # 1. Verificar se a variável destino foi declarada
            if var_name not in declarations_dict:
                print(f"Erro: Variável '{var_name}' usada antes de ser declarada.")
                return False
            
            target_type = declarations_dict[var_name] # Ex: 'INTEGER'
            value = statement.value
            
            # 2. Se o valor for outra variável (uma string vinda do ID)
            if isinstance(value, str):
                if value not in declarations_dict:
                    print(f"Erro na linha {statement.lineno}: Variável '{value}' não declarada.")
                    return False
                
                source_type = declarations_dict[value]
                if source_type != target_type:
                    print(f"Erro na linha {statement.lineno}: Atribuição incompatível. "
                          f"'{var_name}' ({target_type}) recebeu '{value}' ({source_type}).")
                    return False
            
            # 3. Se o valor for um literal (int, float, etc.)
            else:
                expected_python_type = translate[target_type]
                if not isinstance(value, expected_python_type):
                    # Se for BinOp ou outro nó, precisas de uma lógica de eval() para saber o tipo resultante
                    pass 
    return True

def verify_program(ast):
    res1 = verify_declarations(ast[0].declarations)
    if not res1:
        return res1
    res2 = verify_statements(ast[0].labeled_statements)
    if not res2:
        return res2
    return True


if __name__ == '__main__':

    # for file in ("parser.out", "parsetab.py"):
    #     try:
    #         os.remove(file)
    #     except FileNotFoundError:
    #         pass

    codigo_fortran = ""
    ex_number = 2
    # for ex_number in range(1, 9):
    with open(f"exemplo{ex_number}.txt","r") as file:
        codigo_fortran = file.read()

    print(f"A iniciar a análise sintática do código Fortran de exemplo{ex_number}.txt\n")
    
    ast = parser.parse(codigo_fortran)
    
    if ast:
        print("Sucesso! Aqui está a AST gerada:")
        print(ast)
        res = verify_program(ast)
        print(res)
        print("\n\n\n")
    else:
        print("O parsing falhou e devolveu None. Verifica os erros acima.")


