      PROGRAM TESTTYPES
C     Output Esperado:
C     Soma Complexa: (4.0, 6.0)
C     Double Precision: 123.456 456.789
C     Tipificacao Implicita (I, R): 10 20.5
      COMPLEX C1, C2, C3
      DOUBLE PRECISION DP1, DP2
      INTEGER I
      REAL R

      C1 = (1.0, 2.0)
      C2 = (3.0, 4.0)
      C3 = C1 + C2
      PRINT *, 'Soma Complexa: ', C3

      DP1 = 123.456D0
      DP2 = 456.789D0
      PRINT *, 'Double Precision: ', DP1, DP2

      I = 10
      R = 20.5
      PRINT *, 'Tipificacao Implicita (I, R): ', I, R

      END
