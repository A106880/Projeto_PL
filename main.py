from arithmetic_parser import parser
from arithmetic_lexer import preprocess_fortran
from semantic_parser import SemanticParser
from ast_optimizer import ASTOptimizer
from code_generator import CodeGenerator
import sys

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
    if len(sys.argv) < 2:
        print("Usage: python main.py <fortran_code_file>")
        sys.exit(1)
    filename = sys.argv[1] 

    
    with open(filename, "r") as file:
        codigo_fortran = file.read()

    print(
        f"Starting syntactic analysis of Fortran code from {filename}\n"
    )

    codigo_fortran = preprocess_fortran(codigo_fortran)

    ast = parser.parse(codigo_fortran,tracking=True)

    if ast:
        print("Success! Here is the generated AST:")
        print(ast)
        
        
        
        # parser.symbols = SymbolTable()
        # res = verify_program(ast)
        # #print(res)
        # print("\n\n\n")

        print("\n--- Semantic Analysis ---\n")
        semantic_parser = SemanticParser()
        semantic_parser.verify_program(ast)
        
        print("\n--- AST Optimization ---\n")
        optimizer = ASTOptimizer()
        optimizer.set_semantic_info(semantic_parser)
        ast = optimizer.optimize_program(ast)
        print(f"Optimization completed! {optimizer.optimized_nodes} node(s) modified.")
        if optimizer.warnings:
            print(f"\n  Warnings ({len(optimizer.warnings)}):")
            for w in optimizer.warnings:
                print(f"    {w}")
        print("\nOptimized AST:")
        print(ast)

        print("\n--- Error Report ---\n")
        print(semantic_parser.errors.report())

        if not semantic_parser.errors.has_errors():
            print("\n--- Code Generation ---\n")
            generator = CodeGenerator()
            generator.set_semantic_info(semantic_parser)
            generator.generate_Program_Unit(ast)
            assembly_code = generator.get_assembly()
            
            with open("assembly.vm", "w") as f:
                f.write(assembly_code)
                
            print("Machine code generated successfully!")
            print(assembly_code)
        else:
            print("\nCode Generation skipped due to errors.")
        print("\n")
    else:
        print("Parsing failed and returned None. Check the errors above.")



