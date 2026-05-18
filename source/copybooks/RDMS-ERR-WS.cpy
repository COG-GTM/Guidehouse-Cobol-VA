      ******************************************************************
      *                          COMMENT SECTION                       *
      ******************************************************************
      * This proc is working storage area for RDMS-ERR-RTN             *
      ******************************************************************
      *                          REVISION HISTORY                      *
      **************************** F O R M A T *************************
      *                                                                *
      * CHANGE CHANGE    CHANGED     RMIS                              *
      * NUMBER  DATE        BY        ID      DESCRIPTION OF CHANGE    *
      *------- ------ ------------- ------ --------------------------  *
      * CH-NNN MMDDYY FMLLLLLLLLLLL NNNNNN XXXXXXXXXXXXXXXXXXXXXXXXXX  *CHG-000 
      ******************************************************************CHG-END 
      *** RDMS-ERR-WS.cpy COPYBOOK 
      *** FROM RDMS-ERR-WS.txt UNISYS PROC 
       01  WS-RDMS-INDEX               PIC 9(02).   
       01  WS-RDMS-ERR-TBL. 
           05  WS-RDMS-ERR-LINE OCCURS 10 TIMES.
               10                      PIC X(132).  
 END  *
