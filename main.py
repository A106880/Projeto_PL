from arithmetic_parser import parser
from semantic_parser import SemanticParser
from ast_optimizer import ASTOptimizer
from code_generator import CodeGenerator

translate = {
    "INTEGER": int,
    "REAL": float,
    "DOUBLEPRECISION": float,
    "COMPLEX": complex,
    "DOUBLECOMPLEX": complex,
    "LOGICAL": bool,
    "CHARACTER": str,
    'HOLLERITH': str}



if __name__ == "__main__":
    # for file in ("parser.out", "parsetab.py"):
    #     try:
    #         os.remove(file)
    #     except FileNotFoundError:
    #         pass

    codigo_fortran = ""
    ex_number = 1
    # for ex_number in range(1, 9):
    with open(f"exemplo{ex_number}.txt", "r") as file:
        codigo_fortran = file.read()
    # with open("exemplo_otimizar.txt", "r") as file:
    #     codigo_fortran = file.read()
    # with open("exemplo_ref.txt", "r") as file:
    #     codigo_fortran = file.read()
    # with open("exemplo_erros.txt", "r") as file:
    #     codigo_fortran = file.read()

    print(
        f"A iniciar a análise sintática do código Fortran de exemplo{ex_number}.txt\n"
    )

    ast = parser.parse(codigo_fortran,tracking=True)

    if ast:
        print("Sucesso! Aqui está a AST gerada:")
        print(ast)
        
        
        
        # parser.symbols = SymbolTable()
        # res = verify_program(ast)
        # #print(res)
        # print("\n\n\n")

        print("\n--- Análise Semântica ---\n")
        semantic_parser = SemanticParser()
        semantic_parser.verify_program(ast)
        print(semantic_parser.errors.report())
        
        if len(semantic_parser.errors.errors) == 0:
            print("\n--- Otimização de AST ---\n")
            optimizer = ASTOptimizer()
            ast = optimizer.optimize_program(ast)
            print(f"Otimização concluída! {optimizer.optimized_nodes} nós modificados.")
            print("\nAST Otimizada:")
            print(ast)
            
            print("\n--- Geração de Código ---\n")
            generator = CodeGenerator()
            generator.set_semantic_info(semantic_parser)
            generator.generate_Program_Unit(ast)
            assembly_code = generator.get_assembly()
            
            with open("assembly.vm", "w") as f:
                f.write(assembly_code)
                
            print("Código máquina gerado com sucesso'!")
            print(assembly_code)
        else:
            print("\nOtimização e Geração de Código ignoradas devido a erros semânticos.")
        print("\n")
    else:
        print("O parsing falhou e devolveu None. Verifica os erros acima.")



