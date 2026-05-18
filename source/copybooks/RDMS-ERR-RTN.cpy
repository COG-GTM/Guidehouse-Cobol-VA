      ******************************************************************
      *                          COMMENT SECTION                       *
      ******************************************************************
      * This proc is a subrountine to display the RDMS error message   *
      ******************************************************************
      *                          REVISION HISTORY                      *
      **************************** F O R M A T *************************
      *                                                                *
      * CHANGE CHANGE    CHANGED     RMIS                              *
      * NUMBER  DATE        BY        ID      DESCRIPTION OF CHANGE    *
      *------- ------ ------------- ------ --------------------------  *
      * CH-NNN MMDDYY FMLLLLLLLLLLL NNNNNN XXXXXXXXXXXXXXXXXXXXXXXXXX  *CHG-000 
      ******************************************************************CHG-END 
      *** RDMS-ERR-RTN.cpy COPYBOOK 
      *** FROM RDMS-ERR-RTN.txt UNISYS PROC 
    
       RDMS-ERR-RTN.
           INITIALIZE WS-RDMS-ERR-TBL.  
MIGRTN     MOVE SQLERRMC TO WS-RDMS-ERR-LINE(1).
MIGRTN*    EXEC SQL GETERROR INTO :WS-RDMS-ERR-LINE (1),
MIGRTN*                           :WS-RDMS-ERR-LINE (2),
MIGRTN*                           :WS-RDMS-ERR-LINE (3),
MIGRTN*                           :WS-RDMS-ERR-LINE (4),
MIGRTN*                           :WS-RDMS-ERR-LINE (5),
MIGRTN*                           :WS-RDMS-ERR-LINE (6),
MIGRTN*                           :WS-RDMS-ERR-LINE (7),
MIGRTN*                           :WS-RDMS-ERR-LINE (8),
MIGRTN*                           :WS-RDMS-ERR-LINE (9),
MIGRTN*                           :WS-RDMS-ERR-LINE (10)
MIGRTN*    END-EXEC.
           PERFORM VARYING WS-RDMS-INDEX
              FROM 1 BY 1 UNTIL WS-RDMS-INDEX > 10  
                IF WS-RDMS-ERR-LINE (WS-RDMS-INDEX) NOT = SPACES
                                                       AND ZEROES
                   DISPLAY WS-RDMS-ERR-LINE (WS-RDMS-INDEX) UPON PRINTER
                END-IF  
           END-PERFORM. 
       RDMS-ERR-RTN-X.  
           EXIT.
 END  *
