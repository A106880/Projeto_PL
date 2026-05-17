      PROGRAM TESTSUB
      INTEGER A, B, RES, ADD
      A = 5
      B = 10
      CALL MYSUB(A, B)
      RES = ADD(A, B)
      PRINT *, 'Resultado Funcao ADD: ', RES
      END

      SUBROUTINE MYSUB(X, Y)
      INTEGER X, Y
      PRINT *, 'Subrotina recebeu: ', X, Y
      RETURN
      END

      INTEGER FUNCTION ADD(X, Y)
      INTEGER X, Y
      ADD = X + Y
      RETURN
      END
