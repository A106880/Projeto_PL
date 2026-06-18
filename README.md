# Compilador Fortran 77 (standard ANSI X3.9-1978)
O objetivo deste projeto foi desenvolver um compilador para uma linguagem de programação simples, utilizando as técnicas aprendidas ao longo da Unidade Curricular de Processamento de Linguagens. O compilador foi implementado em Python e é capaz de traduzir código fonte escrito em Fortran 77 (standard ANSI X3.9-1978) para código máquina da máquina virtual disponibilizada.

Nota Final: 19

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

**Participantes:**  
- A106880 Afonso Quartas  
- A106885 José Rodrigues  
- A89467 Lucas Robertson  
