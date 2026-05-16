# Relatório do Projeto de Processamento de Linguagens
## Introdução
O objetivo deste projeto foi desenvolver um compilador para uma linguagem de programação simples, utilizando as técnicas aprendidas ao longo da Unidade Curricular de Processamento de Linguagens. O compilador foi implementado em Python e é capaz de traduzir código fonte escrito em Fortran 77 (standard ANSI X3.9-1978) para código máquina da máquina virtual disponibilizada.

## Estrutura do Compilador
O compilador é composto por várias fases, cada uma responsável por uma etapa do processo de compilação:
1. **Análise Léxica (Lexer)**: Responsável por tokenizar o código fonte, identificando palavras-chave, identificadores, literais e símbolos.
2. **Análise Sintática (Parser)**: Constrói uma árvore de sintaxe abstrata (AST) a partir dos tokens gerados pelo lexer, verificando a estrutura gramatical do código.
3. **Análise Semântica**: Verifica a semântica do código, garantindo que as operações sejam válidas e que as variáveis sejam usadas corretamente.
4. **Otimização**: Realiza otimizações na representação intermediária para melhorar a eficiência do código gerado.
5. **Geração de Código**: Traduz a AST otimizada para código máquina da máquina virtual.

## Análise Léxica
A análise léxica foi implementada utilizando expressões regulares para identificar os diferentes tipos de tokens no código fonte. O lexer é capaz de reconhecer palavras-chave, identificadores, literais numéricos e de string, bem como símbolos de pontuação e operadores.

Nesta fase foram implementados os seguintes tokens:

**Palavras-Chave e Estruturas de Controlo**

Estes foram reservados para que não seja possível usá-los como identificadores, e para que seja possível identificar a estrutura do programa.
- `PROGRAM`: Representa o início de um programa.
- `END`: Representa o fim de uma unidade de programa.
- `FUNCTION`: Representa o início de uma função.
- `SUBROUTINE`: Representa o início de uma subrotina.
- `RETURN`: Representa a instrução de retorno de uma função ou subrotina.
- `CALL`: Representa a instrução de chamada de subrotina.
- `IF`: Representa a estrutura condicional.
- `THEN`: Representa o bloco de código executado quando a condição é verdadeira.
- `ELSE`: Representa o bloco de código executado quando a condição é falsa.
- `ENDIF`: Representa o fim da estrutura condicional.
- `DO`: Representa o laço de repetição.
- `CONTINUE`: Representa a instrução de continuação do laço.
- `GOTO`: Representa a instrução de salto incondicional.

**Tipos de Dados**

Estes também foram reservados para que não seja possível usá-los como identificadores, e para que seja possível identificar o tipo de dados das variáveis.
- `INTEGER`: Representa o tipo de dados inteiro (declaração).
- `REAL`: Representa o tipo de dados real (declaração).
- `DOUBLEPRECISION`: Representa o tipo de dados de precisão dupla (declaração).
- `COMPLEX`: Representa o tipo de dados complexo (declaração).
- `DOUBLECOMPLEX`: Representa o tipo de dados complexo de precisão dupla (declaração).
- `LOGICAL`: Representa o tipo de dados lógico (declaração).
- `CHARACTER`: Representa o tipo de dados caractere (declaração).
- `HOLLERITH`: Representa o tipo de dados Hollerith (declaração).

**Literais**

Representam os literais usados no código fonte, e são importantes para a geração de código, pois permitem que o compilador saiba como representar esses valores na máquina virtual.
- `INTVAL`: Representa um literal inteiro.
- `REALVAL`: Representa um literal real.
- `DOUBLEPRECISIONVAL`: Representa um literal de precisão dupla.
- `LOGICALVAL`: Representa um literal lógico.
- `CHARACTERVAL`: Representa um literal de caractere.
- `HOLLERITHVAL`: Representa um literal Hollerith.

**Identificadores e Operações I/O**

Representam os identificadores usados no código fonte, e as operações de entrada e saída, que são fundamentais para a interação do programa com o usuário.
- `ID`: Representa um identificador (variável, função, subrotina, etc.).
- `NEWLINE`: Representa uma nova linha no código fonte.
- `PRINT`: Representa a instrução de impressão formatada.
- `READ`: Representa a instrução de leitura.
- `WRITE`: Representa a instrução de escrita.

**Operadores Aritméticos**

Representam os operadores aritméticos usados no código fonte, e são essenciais para a realização de cálculos e manipulações de dados.
- `ADD`: Representa o operador de adição (`+`).
- `SUB`: Representa o operador de subtração (`-`).
- `MUL`: Representa o operador de multiplicação (`*`).
- `DIV`: Representa o operador de divisão (`/`).
- `POWER`: Representa o operador de potência (`**`).
- `MOD`: Representa o operador módulo.
- `CONCAT`: Representa o operador de concatenação (`//`).

**Operadores Relacionais**

Representam os operadores relacional usados no código fonte, e são essenciais para a realização de comparações e manipulações de dados.
- `EQ`: Representa o operador relacional IGUAL A (`.EQ.`).
- `NE`: Representa o operador relacional NÃO IGUAL A (`.NE.`).
- `LT`: Representa o operador relacional MENOR QUE (`.LT.`).
- `LE`: Representa o operador relacional MENOR OU IGUAL A (`.LE.`).
- `GT`: Representa o operador relacional MAIOR QUE (`.GT.`).
- `GE`: Representa o operador relacional MAIOR OU IGUAL A (`.GE.`).

**Operadores Lógicos**
Representam os operadores lógicos usados no código fonte, e são essenciais para a realização de operações lógicas e manipulações de dados.
- `AND`: Representa o operador lógico E (`.AND.`).
- `OR`: Representa o operador lógico OU (`.OR.`).
- `NOT`: Representa o operador lógico NÃO (`.NOT.`).

## Análise Sintática
A análise sintática foi implementada utilizando uma abordagem de análise descendente recursiva. O parser é capaz de construir uma árvore de sintaxe abstrata (AST) a partir da analise do codigo fonte, utilizando como regra as producoes que contruímos. Para uma melhor organizacao da arvore decimos fazer com que cada nodo da arvore seja constituido por uma classe que representa o tipo do nodo. Cada classe é constituida por atributos que auxiliam na recolha de informacao do nodo.

A nossa gramatica é composta por várias produções, que definem a estrutura do código fonte.

Como em fortran 77 os acessos a arrays e funcoes tem o mesmo formato, decidimos criar uma producao `FunctionorArraysAccess` para representar ambos os casos, e depois na analise semantica decidir se estamos a aceder a um array ou a uma funcao.

As producoes contruidas foram as seguintes:

**Estrutura do Programa**
- `Program` → OptNewLines ProgramUnit Program | OptNewLines
- `ProgramUnit` → FunctionDef | Main | Subroutine
- `Main` → PROGRAM ID NewLines Declarations LabeledStatements END
- `FunctionDef` → FunctionType FUNCTION ID '(' ArgumentList ')' NewLines Declarations LabeledStatements END
- `Subroutine` → SUBROUTINE ID '(' ArgumentList ')' NewLines Declarations LabeledStatements END

**Utilidades**
- `NewLines` → NEWLINE NewLines | NEWLINE
- `OptNewLines` → NewLines | ε

**Tipos de Dados**
- `FunctionType` → INTEGER | REAL | DOUBLEPRECISION | COMPLEX | DOUBLECOMPLEX | LOGICAL | CHARACTER | HOLLERITH | ε
- `VarType` → INTEGER | REAL | DOUBLEPRECISION | COMPLEX | DOUBLECOMPLEX | LOGICAL | CHARACTER | HOLLERITH

**Declarações**
- `Declarations` → Declaration Declarations | ε
- `Declaration` → VarType ArrayIdList NewLines
- `ArrayIdList` → ID ArraySize ArrayIdListRest
- `ArrayIdListRest` → ',' ID ArraySize ArrayIdListRest | ε
- `ArraySize` → '(' INTVAL ')' | ε

**Argumentos**
- `ArgumentList` → ID ArgumentRestList | ε
- `ArgumentRestList` → ',' ID ArgumentRestList | ε

**Valores e Literais**
- `Val` → INTVAL | REALVAL | DOUBLEPRECISIONVAL | ComplexVal | DoubleComplexVal | LOGICALVAL | CHARACTERVAL | HOLLERITHVAL | ID
- `ComplexVal` → '(' REALVAL ',' REALVAL ')'
- `DoubleComplexVal` → '(' DOUBLEPRECISIONVAL ',' DOUBLEPRECISIONVAL ')'

**Instruções**
- `LabeledStatements` → LabeledStatement LabeledStatements | ε
- `LabeledStatement` → Label Statement NewLines | Statement NewLines
- `Statement` → Atribution | Print | Read | Write | If | Do | Mod | Goto | Continue | Call | Return

**Atribuição**
- `Atribution` → FunctionorArraysAccess '=' Expression | ID '=' Expression

**Operações Aritméticas e de Módulo**
- `Mod` → MOD '(' SameTypePair ')'
- `SameTypePair` → Expression ',' Expression

**Controlo de Fluxo**
- `Continue` → CONTINUE
- `Return` → RETURN
- `Goto` → GOTO Label | GOTO '(' LabelSeq ')' ',' Expression | GOTO ID | GOTO ID '(' LabelSeq ')'
- `Label` → INTVAL
- `LabelSeq` → Label | Label ',' LabelSeq

**Estruturas de Repetição**
- `Do` → DO Label ID '=' Expression ',' Expression Step | DO ID '=' Expression ',' Expression Step NewLines LabeledStatements END DO
- `Step` → ',' Expression | ε

**Estruturas Condicionais**
- `If` → IF '(' Expression ')' Label ',' Label ',' Label | IF '(' Expression ')' Statement | IF '(' Expression ')' THEN NewLines LabeledStatements ElseBlock ENDIF
- `ElseBlock` → ELSE ElseBody | ε
- `ElseBody` → NewLines LabeledStatements | IF '(' Expression ')' THEN NewLines LabeledStatements ElseBlock ENDIF

**Operações de Entrada/Saída**
- `Print` → PRINT Format Iolist
- `Read` → READ Format Iolist
- `Write` → WRITE '(' Format ',' Format ')' Iolist
- `Format` → '*' | INTVAL
- `Iolist` → ',' Expression Iolist | ε

**Chamadas de Subrotinas e Acesso a Funções/Arrays**
- `Call` → CALL ID '(' ExpressionListStart ')'
- `FunctionorArraysAccess` → ID '(' Expression ExpressionList ')'

**Expressões**

- `Expression` → Expression '+' Expression | Expression '-' Expression | Expression '*' Expression | Expression '/' Expression | Expression POWER Expression | Expression CONCAT Expression
- `Expression` → Expression EQ Expression | Expression NE Expression | Expression LT Expression | Expression LE Expression | Expression GT Expression | Expression GE Expression
- `Expression` → Expression AND Expression | Expression OR Expression
- `Expression` → '-' Expression | '+' Expression | NOT Expression
- `Expression` → '(' Expression ')'
- `Expression` → Val | Mod | FunctionorArraysAccess

Como nas expressoes existe o conceito de precedencia, nós optamos por definir uma estrutura de precedencia para as expressoes, de forma a garantir que as expressoes sejam avaliadas corretamente. A precedencia definida foi a seguinte (de menor para maior prioridade):

**OR** (esq) → **AND** (esq) → **NOT** (dir) → **Relacionais** (esq) → **Concatenação** (esq) → **Adição/Subtração** (esq) → **Multiplicação/Divisão** (esq) → **Potência** (dir) → **Unário** (dir)

**Listas de Expressões**
- `ExpressionListStart` → Expression ExpressionList | ε
- `ExpressionList` → ',' Expression ExpressionList | ε


## Análise Semântica
Nesta fase decimos contruir uma análise semântica que efetue verificacoes em cada nodo relevante da arvore e que constua a uma estrutura que siva de guia para as fases, seguintes. Durante a nossa análise semântica, sempre que acontece um erro este é adicionado a uma lista de erros que no final será apresentada ao utilizador.

As verificacoes efetuadas pelo nosso compilador nesta fase são as seguintes:
