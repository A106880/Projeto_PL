      PROGRAM TESTOPT
      INTEGER X, Y, Z, UNUSED
      X = 10 + 20 * 2
      PRINT *, 'Constant Folding (10 + 20 * 2 = 50): ', X
      
      GOTO 10
      PRINT *, 'DCE: Isto nao deve ser gerado'
10    CONTINUE

      IF (.TRUE. .OR. (5 .EQ. 0)) THEN
         PRINT *, 'Short-circuit OR funciona'
      ENDIF

      END
