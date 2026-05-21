      *** DATECONV-WS.cpy COPYBOOK 
      *** FROM DATECONV-WS.txt UNISYS PROC 
      ***************************************************************** 
      *                       REVISION HISTORY                        * 
      ***************************************************************** 
      *                                                               * 
      * ------------------------F O R M A T-------------------------- * 
      * CHANGE CHANGE CHANGED        RMIS                             * 
      * NUMBER  DATE    BY          NUMBER   DESCRIPTION OF CHANGE    * 
      * ------ ------ ------------- ------ -------------------------  * 
      * CH-NNN MMDDYY FMLLLLLLLLLLL NNNNNN XXXXXXXXXXXXXXXXXXXXXXXXX  * 
      * ------------------------------------------------------------- * 
 
      ***************************************************************** 
      ***   
      *** Convert a date to julian day number ("INT") or vice versa.
      *** Convert a date to julian day or vice versa.   
      *** Input dates are FROM, output dates are TO.
      *** Compute differences and Add days. 
      *** The date can be Julian (YYDDD), YYMMDD, YYYYMMDD, or MMDDYY.  
      *** If the input is invalid, the output is zero and   
      *** DATE-CONVERT-ERR-IND and DATE-ERR-IND is set to "Y".  
      *** Also requires proc DATECONV-PD.   
      ***   
       01  CONV-DATES.  
           05  ABORT-ON-DATE-ERR          PIC X VALUE ZEROS.            CH-001  
           05  DATESUB-FUNC               PIC 9(2) VALUE ZEROS.         CH-001  
           05  FROM-INT-DT                PIC 9(10) COMP VALUE ZEROS.   CH-001  
           05  FROM-INT-DT-X REDEFINES FROM-INT-DT. 
               10  CONV-INT               PIC 9(10) COMP.   
           05  FROM-JUL-DT                PIC 9(5) VALUE ZEROS.         CH-001  
           05  FROM-JUL-DT-X REDEFINES FROM-JUL-DT. 
               10  CONV-JUL-DT            PIC 9(5). 
           05  FROM-CYMD-DT               PIC 9(8) VALUE ZEROS.         CH-001  
           05  FROM-CYMD-DT-X REDEFINES FROM-CYMD-DT.   
               10  FROM-CYMD-YYYY         PIC 9(4). 
               10  FROM-CYMD-YYYY-X REDEFINES FROM-CYMD-YYYY.   
                   15  FROM-CYMD-CENTURY  PIC 99.                       CH-001  
                   15  FROM-CYMD-YY       PIC 99.                       CH-001  
               10  FROM-CYMD-MM           PIC 99.   
               10  FROM-CYMD-DD           PIC 99.   
           05  FROM-YMD-DT                PIC 9(6) VALUE ZEROS.         CH-002  
           05  FROM-YMD-DT-X REDEFINES FROM-YMD-DT.                     CH-002  
               10 FROM-YMD-YY             PIC 99.                       CH-001  
               10 FROM-YMD-MM             PIC 99.                       CH-001  
               10 FROM-YMD-DD             PIC 99.                       CH-001  
           05  FROM-YMD-DT-C REDEFINES FROM-YMD-DT. 
               10 CONV-YMD-DT             PIC 9(6). 
           05  FROM-MDY-DT                PIC 9(6) VALUE ZEROS.         CH-002  
           05  FROM-MDY-DT-X REDEFINES FROM-MDY-DT.                     CH-002  
               10  FROM-MDY-MM            PIC 99.                       CH-001  
               10  FROM-MDY-DD            PIC 99.                       CH-001  
               10  FROM-MDY-YY            PIC 99.                       CH-001  
           05  FROM-MDY-DT-C REDEFINES FROM-MDY-DT. 
               10 CONV-MDY-DT             PIC 9(6). 
           05  MONTHS-TO-ADD              PIC S9(5) VALUE ZEROS.        CH-001  
           05  BETWEEN-JUL-DT             PIC 9(5) VALUE ZEROS.         CH-003  
           05  BETWEEN-YMD-DT             PIC 9(6) VALUE ZEROS.         CH-003  
           05  BETWEEN-YMD-DT-X REDEFINES BETWEEN-YMD-DT.               CH-003  
               10 BETWEEN-YMD-YY          PIC 99.                       CH-003  
               10 BETWEEN-YMD-MM          PIC 99.                       CH-003  
               10 BETWEEN-YMD-DD          PIC 99.                       CH-003  
           05  BETWEEN-YMD-MDY-DT-X REDEFINES BETWEEN-YMD-DT.           CH-003  
               10  BETWEEN-MDY-DT         PIC 9(6).                     CH-003  
               10  BETWEEN-MDY-DT-X REDEFINES BETWEEN-MDY-DT.           CH-003  
                   15  BETWEEN-MDY-MM     PIC 99.                       CH-003  
                   15  BETWEEN-MDY-DD     PIC 99.                       CH-003  
                   15  BETWEEN-MDY-YY     PIC 99.                       CH-003  
           05  TO-INT-DT                  PIC 9(10) COMP VALUE ZEROS.   CH-002  
           05  TO-JUL-DT                  PIC 9(5) VALUE ZEROS. 
           05  TO-CYMD-DT                 PIC 9(8) VALUE ZEROS.         CH-001  
           05  TO-CYMD-DT-X REDEFINES TO-CYMD-DT.                       CH-003  
               10  TO-CYMD-YYYY           PIC 9(4).                     CH-003  
               10  TO-CYMD-YYYY-X REDEFINES TO-CYMD-YYYY.               CH-002  
                   15  TO-CYMD-CENTURY    PIC 99.                       CH-002  
                   15  TO-CYMD-YY         PIC 99.   
               10  TO-CYMD-MM             PIC 99.                       CH-002  
               10  TO-CYMD-DD             PIC 99.   
           05  TO-YMD-DT                  PIC 9(6) VALUE ZEROS.         CH-002  
           05  TO-YMD-DT-X REDEFINES TO-YMD-DT.                         CH-002  
               10 TO-YMD-YY               PIC 99.                       CH-001  
               10 TO-YMD-MM               PIC 99.                       CH-001  
               10 TO-YMD-DD               PIC 99.                       CH-001  
           05  TO-MDCY-DT                 PIC 9(8) VALUE ZEROS.         CH-005  
           05  TO-MDCY-DT-X REDEFINES TO-MDCY-DT.                       CH-005  
               10  TO-MDCY-MM             PIC 99.   
               10  TO-MDCY-DD             PIC 99.   
               10  TO-MDCY-YYYY           PIC 9(4).                     CH-005  
               10  TO-MDCY-YYYY-X REDEFINES TO-MDCY-YYYY.               CH-005  
                   15  TO-MDCY-CENTURY    PIC 99.                       CH-005  
                   15  TO-MDCY-YY         PIC 99.                       CH-005  
           05  TO-MDY-DT                  PIC 9(6) VALUE ZEROS.         CH-002  
           05  TO-MDY-DT-X REDEFINES TO-MDY-DT.                         CH-002  
               10  TO-MDY-MM              PIC 99.                       CH-001  
               10  TO-MDY-DD              PIC 99.                       CH-001  
               10  TO-MDY-YY              PIC 99.                       CH-001  
           05  DAYS-DIF                   PIC S9(5) VALUE ZEROS.        CH-001  
               88  FROM-DT-EQ-TO-DT       VALUE 0.                      CH-001  
               88  FROM-DT-LT-TO-DT       VALUE 1 THRU 99999.           CH-001  
               88  FROM-DT-LE-TO-DT       VALUE 0 THRU 99999.           CH-001  
               88  FROM-DT-GT-TO-DT       VALUE -99999 THRU -1.         CH-001  
               88  FROM-DT-GE-TO-DT       VALUE -99999 THRU 0.          CH-001  
               88  TO-DT-LT-FROM-DT       VALUE -99999 THRU -1.         CH-004  
               88  TO-DT-LE-FROM-DT       VALUE -99999 THRU 0.          CH-004  
               88  TO-DT-GT-FROM-DT       VALUE 1 THRU 99999.           CH-004  
               88  TO-DT-GE-FROM-DT       VALUE 0 THRU 99999.           CH-004  
               88  BETWEEN-DT-WITHIN      VALUE 88888.                  CH-003  
               88  BETWEEN-DT-OUTSIDE     VALUE 77777.                  CH-003  
           05  DAYS-DIF-UNSIGNED          PIC 9(5) VALUE ZEROS. 
           05  DATE-ERR-IND               PIC X VALUE ZEROS.            CH-001  
               88  DATE-ERR               VALUE 'Y'.                    CH-001  
               88  DATE-IS-VALID          VALUE 'N'.                    CH-001  
           05  DATE-ERR-IND-X REDEFINES DATE-ERR-IND.   
               10  DATE-CONVERT-ERR-IND   PIC X.
                   88  DATE-CONVERT-ERR   VALUE 'Y'.
           05  DATE-ERR-REASON            PIC 9(2) COMP VALUE ZEROS.    CH-004  
               88  NON-NUMERIC-DD         VALUE 2.  
               88  NON-NUMERIC-DDD        VALUE 3.  
               88  NON-NUMERIC-MM         VALUE 4.  
               88  NON-NUMERIC-YYYY       VALUE 5.  
               88  OUT-OF-RANGE-DD        VALUE 7.  
               88  OUT-OF-RANGE-DDD       VALUE 8.  
               88  OUT-OF-RANGE-INT       VALUE 9.  
               88  OUT-OF-RANGE-MM        VALUE 10. 
               88  OUT-OF-RANGE-YYYY      VALUE 11. 
 END  *
