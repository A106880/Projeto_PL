**Unidade Curricular:** Processamento de Linguagens  
**Projeto:** Construção de um Compilador para Fortran 77 Standard  
**Grupo G31**  
**Integrantes:**  
- A106880 Afonso Quartas  
- A106885 José Rodrigues  
- A89467 Lucas Robertson  


# Relatório do Projeto de Processamento de Linguagens
## Introdução
O objetivo deste projeto foi desenvolver um compilador para uma linguagem de programação simples, utilizando as técnicas aprendidas ao longo da Unidade Curricular de Processamento de Linguagens. O compilador foi implementado em Python e é capaz de traduzir código fonte escrito em Fortran 77 (standard ANSI X3.9-1978) para código máquina da máquina virtual disponibilizada.

## Instruções de Execução
Para executar o compilador.

1. **Compilação de um ficheiro Fortran:**
   Para compilar um ficheiro, execute o seguinte comando na raiz do projeto:
   ```bash
   python3 code/f77compiler.py <caminho_do_ficheiro>
   ```

   Este comando irá gerar um ficheiro com extensão `.vm` no diretório atual.

## Estrutura do Compilador
O compilador é composto por várias fases, cada uma responsável por uma etapa do processo de compilação:
1. **Análise Léxica (Lexer)**: Responsável por tokenizar o código fonte, identificando palavras-chave, identificadores, literais e símbolos.
2. **Análise Sintática (Parser)**: Constrói uma árvore de sintaxe abstrata (AST) a partir dos tokens gerados pelo lexer, verificando a estrutura gramatical do código.
3. **Análise Semântica**: Verifica a semântica do código, garantindo que as operações sejam válidas e que as variáveis sejam usadas corretamente.
4. **Otimização**: Realiza otimizações na representação intermediária para melhorar a eficiência do código gerado.
5. **Geração de Código**: Traduz a AST otimizada para código máquina da máquina virtual.

## Análise Léxica
A análise léxica foi implementada utilizando o módulo `ply.lex` e expressões regulares para identificar os tokens. 

**Pré-processamento**

Uma característica importante do Fortran 77 é a sua insensibilidade a espaços em branco em palavras-chave. Para lidar com isto de forma robusta, o compilador inclui uma fase de pré-processamento (`preprocess_fortran`) que:
- Remove comentários de linha (iniciados por `C`, `c`, `*` na primeira coluna ou `!`).
- Normaliza keywords compostas, removendo espaços em branco internos (ex: `DOUBLE PRECISION` torna-se `DOUBLEPRECISION`, `END IF` torna-se `ENDIF`, `GO TO` torna-se `GOTO`).

Após o pré-processamento, o lexer identifica os seguintes tokens:

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
- `ENDDO`: Representa o fim de um bloco `DO` (modernização).

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
- `EQV`: Representa a equivalência lógica (`.EQV.`).
- `NEQV`: Representa a não-equivalência lógica (`.NEQV.`).

## Análise Sintática
A análise sintática foi implementada utilizando uma abordagem de análise descendente recursiva. O parser é capaz de construir uma árvore de sintaxe abstrata (AST) a partir da analise do codigo fonte, utilizando como regra as producoes que contruímos. Para uma melhor organizacao da arvore decimos fazer com que cada nodo da arvore seja constituido por uma classe que representa o tipo do nodo. Cada classe é constituida por atributos que auxiliam na recolha de informacao do nodo.

A nossa gramatica é composta por várias produções, que definem a estrutura do código fonte.

Como em fortran 77 os acessos a arrays e funcoes tem o mesmo formato, decidimos criar uma producao `FunctionorArraysAccess` para representar ambos os casos, e depois na analise semantica decidir se estamos a aceder a um array ou a uma funcao.

As producoes contruidas foram as seguintes:

**Estrutura do Programa**
- `Program` → OptNewLines ProgramUnit Program | OptNewLines
- `ProgramUnit` → FunctionDef | Main | Subroutine
- `Main` → PROGRAM ID NewLines Declarations LabeledStatements OptNewLines END
- `FunctionDef` → FunctionType FUNCTION ID '(' ArgumentList ')' NewLines Declarations LabeledStatements END
- `Subroutine` → SUBROUTINE ID '(' ArgumentList ')' NewLines Declarations LabeledStatements OptNewLines END | SUBROUTINE ID NewLines Declarations LabeledStatements OptNewLines END

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
- `Do` → DO Label ID '=' Expression ',' Expression Step | DO ID '=' Expression ',' Expression Step NewLines LabeledStatements ENDDO
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
Nesta fase, o compilador realiza verificações em cada nodo da árvore sintática para garantir a coerência lógica do programa.

**Sistema de Erros e Avisos**

O compilador utiliza um coletor centralizado (`SemanticErrorCollector`). Distinguimos dois tipos de mensagens:
- **Erros Semânticos:** Impedem a geração de código. Ocorrem em caso de tipos incompatíveis, variáveis não declaradas ou erros de sintaxe em subprogramas.
- **Avisos (Warnings):** Não impedem a compilação. São gerados principalmente pelo otimizador quando deteta variáveis declaradas mas nunca utilizadas.

**Verificações Implementadas**

- **Regra de Tipificação Implícita (I-N):** Seguindo o standard Fortran 77, variáveis não declaradas explicitamente são tipificadas com base na sua primeira letra: `I` a `N` são `INTEGER`, as restantes são `REAL`.
- **Rastreio de Inicialização:** O compilador mantém um estado de inicialização para cada variável, lançando um erro se uma variável for lida antes de lhe ser atribuído um valor.
- **Validação de Limites (Bounds Checking):** Para índices constantes em arrays, o compilador verifica se o acesso está dentro do intervalo declarado (1 a N).
- **Assinaturas de Subprogramas:** Validação rigorosa do número e tipo de argumentos em chamadas de `FUNCTION` e `SUBROUTINE`.
- **Verificação de Retorno de Funções:** Garante que, dentro de uma função, existe pelo menos uma atribuição ao nome da função antes do `RETURN`.
- **Validação de Ciclos DO:** Verifica se a label de término de um ciclo `DO` existe e se aponta para um statement válido (evitando saltos para instruções de controlo inválidas).

## Otimização de AST
Antes da geração de código, a AST sofre uma fase de otimização (`ASTOptimizer`) para melhorar a eficiência da tradução:

- **Constant Folding:** Avaliação de expressões constantes em tempo de compilação. Suporta aritmética, operadores lógicos (com *short-circuit*) e relacionais. Inclui deteção preventiva de erros como divisão por zero.
- **Dead Code Elimination (DCE):** 
  - Remoção de instruções inalcançáveis posicionadas após um `GOTO` ou `RETURN`.
  - Remoção de blocos inteiros de funções ou subrotinas que nunca são invocadas a partir do programa principal.
- **Jump Threading:** Otimização de saltos em cadeia, onde um `GOTO` aponta para outro `GOTO`.
- **Remoção de Declarações Inúteis:** Variáveis declaradas mas não utilizadas são removidas da tabela de símbolos e das instruções `PUSH` iniciais, gerando o respetivo aviso.

## Geração de Código
A fase final traduz a AST otimizada para o assembly da máquina virtual EWVM.

**Peculiaridades da Implementação**

- **Gestão de Memória (GP vs FP):** O compilador separa explicitamente o acesso a globais (`PUSHGP`/`PUSHG`) e locais (`PUSHFP`/`PUSHL`). As globais são alocadas antes da instrução `START`, enquanto locais e variáveis temporárias de rascunho são alocadas após o `START`.
- **Passagem por Referência para Literais:** Como o Fortran exige passagem por referência, ao passar um literal (ex: `10`) para uma função, o compilador aloca-o numa variável global temporária e passa o endereço desta, evitando falhas na VM.
- **Tipos de 2-Slots (DOUBLE e COMPLEX):** Tipos de precisão dupla ou complexos ocupam dois slots na stack. O gerador de código gere esta duplicidade em todas as operações de carga, armazenamento e aritmética.
- **Limpeza da Stack (Workaround VM):** Devido a uma limitação da VM `ewvm` onde a instrução `RETURN` não limpa as variáveis locais, o compilador injeta automaticamente instruções `POP` dinâmicas antes de cada retorno para garantir a integridade da stack do chamador.
- **Cast Implícito:** O gerador injeta instruções `ITOF` (Integer to Float) ou `FTOI` conforme necessário durante atribuições entre `INTEGER` e `REAL`.
- **Aritmética Complexa e Potências:** Operações como a divisão de números complexos ou a exponenciação inteira (`**`) são traduzidas em sequências complexas de assembly, incluindo loops de multiplicação para potências.

## Dificuldades Encontradas
Durante o desenvolvimento do projeto, foram enfrentados diversos desafios técnicos que exigiram soluções criativas e uma compreensão profunda tanto da linguagem Fortran 77 como da arquitetura da máquina virtual alvo.

*   **Conflitos Shift/Reduce com NEWLINE:** A gestão do token `NEWLINE` foi um dos maiores desafios no parser. A sua inclusão em múltiplas produções criava ambiguidades onde o parser não conseguia decidir se uma quebra de linha terminava uma instrução ou iniciava a próxima, resultando em conflitos de leitura. Resolvemos isto centralizando a gestão de linhas opcionais na estrutura de topo do programa.
*   **Implementação de Literais Hollerith:** Estes literais têm uma estrutura complexa (`nH<texto>`), onde o número `n` dita o comprimento exato da string a ler. Como isto foge às regras de parsing padrão, tivemos de implementar uma lógica manual no Lexer para capturar o conteúdo textual após o `H`, saltando o número correto de caracteres no buffer.
*   **Terminação de Ciclos DO com Labels:** Para permitir que um ciclo `DO` terminasse corretamente mesmo com múltiplos statements e labels (como vários `CONTINUE`) no seu corpo, adotámos uma abordagem em duas fases: o parser lê o cabeçalho como uma instrução comum e o corpo é posteriormente identificado e estruturado durante a fase de **Análise Semântica**.
*   **Deteção de Equações Impossíveis:** Inicialmente, tínhamos dificuldades em decidir onde validar operações inválidas (como divisões por zero). Algumas eram detetadas na análise semântica e outras apenas durante a otimização de constantes. Para uniformizar o comportamento, movemos este grupo de verificações para o otimizador, garantindo que qualquer expressão constante que resulte num erro aritmético seja reportada consistentemente.
*   **Entendimento da Máquina Virtual (EWVM):** Grande parte do esforço não foi apenas a escrita do compilador, mas a compreensão profunda do funcionamento da máquina virtual alvo. Entender como a stack, os registadores de controlo e as instruções de I/O operam foi fundamental para garantir que o assembly gerado fosse funcional.
*   **Gestão de Tipos de 2-Slots:** A manipulação de tipos como `COMPLEX` e `DOUBLE PRECISION` exigiu uma lógica extra no gerador de código, pois cada valor ocupa dois slots de memória, obrigando a sequências complexas de operações para manter a integridade dos dados na stack.

## Suite de Testes
Para validar as funcionalidades do compilador, foi desenvolvida uma suite de testes localizada no diretório `testes/`. Abaixo descrevemos os novos testes principais:

1.  **`test_types.f77`**: Demonstra o suporte a tipos de dados avançados (`COMPLEX`, `DOUBLE PRECISION`) e a aplicação da regra de tipificação implícita (I-N).
2.  **`test_control.f77`**: Testa estruturas de controlo complexas, incluindo `Computed GOTO`, `Assigned GOTO`, `Arithmetic IF` e as duas variantes de ciclos `DO` (Block e Labeled).
3.  **`test_subprograms.f77`**: Valida a definição e chamada de `FUNCTION` e `SUBROUTINE`, focando na passagem de argumentos por referência e no retorno de valores complexos.
4.  **`test_optimizations.f77`**: Desenhado especificamente para validar a fase de otimização, contendo expressões constantes para *folding*, código inalcançável para eliminação e variáveis declaradas mas não usadas para geração de avisos.

## Conclusão
Em conclusão, o compilador cumpre e excede os requisitos base, oferecendo um sistema robusto de análise e otimização que garante a geração de código eficiente e seguro para a máquina virtual alvo. A modularidade da implementação permite que o compilador seja facilmente estendido para suportar mais características do standard Fortran.
