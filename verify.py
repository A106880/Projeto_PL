from node_classes import Program_Unit
from error_classes import SemanticError
from node_classes import Call,LabeledStatement,Subroutine,Funcao,Declaracao,ProgramaPrincipal
from enum import Enum

# class syntax
class Program_Unit_Type(Enum):
    PROGRAM = 0
    FUNCTION = 1
    SUBROUTINE = 2



class Semantic_Program_Unit():
    def __init__(self,parser_program_unit:Program_Unit):
        self.variables = {} # key = variable, value = type
        
        if isinstance(parser_program_unit,ProgramaPrincipal):
            self.type = Program_Unit_Type.PROGRAM
        elif isinstance(parser_program_unit,Funcao):
            self.type = Program_Unit_Type.FUNCTION
        elif isinstance(parser_program_unit,Subroutine):
            self.type = Program_Unit_Type.SUBROUTINE
        
        if self.type != Program_Unit_Type.PROGRAM:
            self.verify_arguments(parser_program_unit.arguments)
    
        if self.type == Program_Unit_Type.FUNCTION:
            self.variables[parser_program_unit.name.nome] = parser_program_unit.return_type

    def verify_arguments(self,arguments:list[str]):
        self.arguments = {}
        for argument in arguments:
            self.arguments[argument] = "INTEGER"

    def verify_declarations(self,declarations:list[Declaracao]):
        for declaration in declarations:
            for id in declaration.Ids:
                if id.nome.nome in self.variables:
                    raise SemanticError(f": Variable {id.nome.nome} declared multiple times")
                self.variables[id.nome.nome] = (declaration.tipo.nome,id.tamanho)
    
    def verify_statements(self,labeled_statements:list[LabeledStatement],program_units):
        for labeled_statement in labeled_statements:
            statement = labeled_statement.statement
            if isinstance(statement,Call):
                self.verify_call(statement,program_units)

    def verify_call(self,call_statement:Call,program_units):
        if call_statement.subroutine.nome in program_units:
            if not program_units[call_statement.subroutine.nome].type == Program_Unit_Type.SUBROUTINE:
                raise SemanticError(f":{call_statement.subroutine.nome} is not a subroutine")
            if not len(call_statement.arguments) == len(program_units[call_statement.subroutine.nome].arguments):
                raise SemanticError(f":Wrong number of arguments calling {call_statement.subroutine.nome}; expected {len(program_units[call_statement.subroutine.nome].arguments)}, got {len(call_statement.arguments)}")




class Verifier():
    def __init__(self):
        self.program_units = {}
        self.functions = {}

    def verify_global_names(self,ast:list[Program_Unit]):
        for program_unit in ast:
            if program_unit.name.nome in self.program_units:
                raise SemanticError(f":Global name {program_unit.name.nome} already used")
            else:
                self.program_units[program_unit.name.nome] = Semantic_Program_Unit(program_unit)
    

    def verify_declarations(self,declarations:list[Declaracao],program_unit_name:str):
        self.program_units[program_unit_name].verify_declarations(declarations)
        print(self.program_units[program_unit_name].variables)


    def verify_statements(self,labeled_statements:list[LabeledStatement],program_unit_name:str):
        self.program_units[program_unit_name].verify_statements(labeled_statements,self.program_units)
