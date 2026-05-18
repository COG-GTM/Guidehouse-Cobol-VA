MIGRTN***DMCAERR COPYBOOK
       DMCA-ERRFLDS.
      *** MOVE VALUES TO DMCA ERROR FIELDS ***
      *
           MOVE DB-RTNCODE-DMS TO ERROR-NUM.
           MOVE DB-RTNCODE-DMS (3:2) TO ERROR-CODE.
           MOVE DB-SQLCODE-NUM TO DB-SQLCODE-DISP.
	   IF DB-OK
	       MOVE ZEROS TO ERROR-STATUS
	       GO TO DMCA-ERRFLDS-EXIT
	   END-IF.

           MOVE DB-TABLE-NAME  TO ERROR-RECORD
           IF DB-FUNCTION      = 'DELETE'
           OR DB-FUNCTION-TYPE = 'DELETE'
               MOVE '02'       TO ERROR-FUNCTION
           ELSE
           IF DB-FUNCTION           = 'SELECT'
           OR DB-FUNCTION-TYPE(1:4) = 'FIND'
           OR DB-FUNCTION-TYPE(1:5) = 'FETCH'
               MOVE '03'       TO ERROR-FUNCTION
           ELSE
           IF DB-FUNCTION      = 'UPDATE'
           OR DB-FUNCTION-TYPE = 'MODIFY'
               MOVE '08'       TO ERROR-FUNCTION
           ELSE
           IF DB-FUNCTION      = 'INSERT'
           OR DB-FUNCTION-TYPE = 'STORE'
               MOVE '12'       TO ERROR-FUNCTION
           END-IF
           END-IF
           END-IF
           END-IF
           IF DB-DEADLOCK
               MOVE '02' TO RB-ERROR-CODE
           END-IF
      ***  IF (NOT DB-OK) AND (NOT DB-NOT-FND) AND (NOT DB-DUP-REC)
           IF (DB-SQLCODE-NUM = +0)
           OR (DB-SQLCODE-NUM = +100)
           OR (DB-SQLCODE-NUM = +1403)
           OR (DB-SQLCODE-NUM = -0001)
	       CONTINUE
           ELSE
               DISPLAY '!!! ORACLE DATABASE ERROR!!!' UPON PRINTER
               IF DB-FUNCTION = SPACES
                 DISPLAY DB-TABLE-NAME ' ' DB-FUNCTION-TYPE ' '
                     DB-SQLCODE-DISP UPON PRINTER
                 DISPLAY DB-MESSAGE UPON PRINTER
                 DISPLAY DB-DATA UPON PRINTER
               ELSE
                 DISPLAY DB-TABLE-NAME ' ' DB-FUNCTION ' '
                     DB-SQLCODE-DISP UPON PRINTER
                 DISPLAY DB-MESSAGE UPON PRINTER
                 DISPLAY DB-DATA UPON PRINTER
               END-IF
           END-IF.
       DMCA-ERRFLDS-EXIT.
           EXIT.
