      PROGRAM TESTCONTROL
      INTEGER I, J, K
      
      I = 2
      GOTO (10, 20, 30), I
10    PRINT *, 'Nao deve imprimir isto'
20    PRINT *, 'Computed GOTO: Saltou para 20'
30    CONTINUE

      J = 0
      IF (J) 40, 50, 60
40    PRINT *, 'Arithmetic IF: < 0'
50    PRINT *, 'Arithmetic IF: == 0'
60    CONTINUE

      PRINT *, 'DO Labeled:'
      DO 100 K = 1, 3
         PRINT *, 'K = ', K
100   CONTINUE

      PRINT *, 'DO Block:'
      DO J = 1, 2
         PRINT *, 'J = ', J
      ENDDO

      END
