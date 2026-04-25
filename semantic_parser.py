from error_classes import SemanticError

# A simple symbol table, but now registers whether the variable has been initialized and its type
class SymbolTable():
  def __init__(self):
    self.__table = {}

  # return whether initialized and its type, but only if declared
  def lookup(self, id):
    if id not in self.__table:
      for item in self.__table:
        print(item)
        print(type(item))
        print((isinstance(item,str)) )
      print((isinstance(id,str)) )
      raise SemanticError(f"Undeclared variable: {id}")
    else:
      return self.__table.get(id)

  # declare an identifier and its type
  # since declaration and assignment are separated, do not allow duplicate declarations
  def declare(self, id, tpe):
    if id in self.__table:
      raise SemanticError(f"Duplicate declaration: {id}")
    self.__table[id] = (tpe, False)

  # mark a variable as initialized, but only if declared
  def initialize(self, id):
    if id not in self.__table:
      raise SemanticError(f"Undeclared variable: {id}")
    self.__table[id] = (self.__table[id][0], True)