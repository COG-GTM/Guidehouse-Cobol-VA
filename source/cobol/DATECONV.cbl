       IDENTIFICATION DIVISION. 
       PROGRAM-ID.  DATECONV.   
MIGRTN*----------------------------------------------------------*
MIGRTN*  PROGRAM CONVERTED BY INFORMATION ANALYSIS INCORPORATED  *
MIGRTN*  DATE:  7/3/2012       TIME:  18:28:29                   *
MIGRTN*----------------------------------------------------------*
      *DATE-WRITTEN.  1994. 
      ********************************************************************  
      * This subprogram provides the logic to implement various         CH-001  
      * date-handling functions.  The main program which calls          CH-001  
      * this subprogram must include copybooks DATECONV-PD and          CH-001  
      * DATECONV-WS.  DATECONV contains paragraphs which define         CH-001  
      * the various functions which are available and which call this   CH-001  
      * subprogram to accomplish these functions.  See the copybooks    CH-001  
      * for more information.                                           CH-001  
      *                                                                 CH-001  
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
      ***************************************************************** CHG-END
    
       ENVIRONMENT DIVISION.
       CONFIGURATION SECTION.   
       SPECIAL-NAMES.  PRINTER IS PRT  CONSOLE IS CON.  
       DATA DIVISION.   
    
       WORKING-STORAGE SECTION. 
       01  WRK-CYMD-DT                   PIC 9(8).                      CH-001  
       01  WRK-CYMD-YYYY-X REDEFINES WRK-CYMD-DT.   
           05  WRK-CYMD-YYYY             PIC 9(4).                      CH-001  
           05  WRK-CYMD-MMDD             PIC 9(4).                      CH-001  
       01  WRK-CYMD-DT-X REDEFINES WRK-CYMD-DT. 
           05  WRK-CYMD-CENTURY          PIC 99.                        CH-001  
           05  WRK-CYMD-YMD-DT           PIC 9(6).  
           05  WRK-CYMD-YMD-X REDEFINES WRK-CYMD-YMD-DT.
               10  WRK-CYMD-YY           PIC 99.                        CH-001  
               10  WRK-CYMD-MM           PIC 99.                        CH-001  
               10  WRK-CYMD-DD           PIC 99.                        CH-001  
       01  WRK-CYMD-CJUL-X REDEFINES WRK-CYMD-DT.                       CH-004  
           05  WRK-CJUL-DT               PIC 9(7).                      CH-004  
           05  WRK-CJUL-DT-X REDEFINES WRK-CJUL-DT.                     CH-004  
               10  FILLER                PIC 99.                        CH-004  
               10  WRK-CJUL-JUL-DT       PIC 9(5).                      CH-004  
               10  WRK-CJUL-JUL-X REDEFINES WRK-CJUL-JUL-DT.            CH-004  
                   15  WRK-CJUL-JUL-YY   PIC 99.                        CH-004  
                   15  WRK-CJUL-JUL-DDD  PIC 999.                       CH-004  
           05  FILLER                    PIC 9.                         CH-004  
       01  HLD-CYMD-DT                   PIC 9(8).                      CH-004  
       01  HLD-CYMD-YYYY-X REDEFINES HLD-CYMD-DT.                       CH-004  
           05  HLD-CYMD-YYYY             PIC 9(4).                      CH-004  
           05  HLD-CYMD-MMDD             PIC 9(4).                      CH-004  
       01  HLD-CYMD-DT-X REDEFINES HLD-CYMD-DT.                         CH-004  
           05  HLD-CYMD-CENTURY          PIC 99.                        CH-004  
           05  HLD-CYMD-YMD-DT           PIC 9(6).                      CH-004  
           05  HLD-CYMD-YMD-X REDEFINES HLD-CYMD-YMD-DT.                CH-004  
               10  HLD-CYMD-YY           PIC 99.                        CH-004  
               10  HLD-CYMD-MM           PIC 99.                        CH-004  
               10  HLD-CYMD-DD           PIC 99.                        CH-004  
       01  HLD-CYMD-CJUL-X REDEFINES HLD-CYMD-DT.                       CH-004  
           05  HLD-CJUL-DT               PIC 9(7).                      CH-004  
           05  HLD-CJUL-DT-X REDEFINES HLD-CJUL-DT.                     CH-004  
               10  FILLER                PIC 99.                        CH-004  
               10  HLD-CJUL-JUL-DT       PIC 9(5).                      CH-004  
               10  HLD-CJUL-JUL-X REDEFINES HLD-CJUL-JUL-DT.            CH-004  
                   15  HLD-CJUL-JUL-YY   PIC 99.                        CH-004  
                   15  HLD-CJUL-JUL-DDD  PIC 999.                       CH-004  
           05  FILLER                    PIC 9.                         CH-004  
       01  HOLD-JUL-DT-YYYYDDD           PIC 9(07).                     CH-645

       01  BAD-FUNC-MSG.                                                CH-001  
           05  FILLER                    PIC X(45) VALUE                CH-001  
               'DATECONV CALLED WITH INVALID DATESUB-FUNC = '.          CH-001  
           05  PRT-DATECONV-FUNC         PIC 99.                        CH-001  
       01  MONTHS-TO-ADD-UNSIGNED        PIC 9(5) COMP.                 CH-001  
       01  YEARS-TO-ADD                  PIC 9(5) COMP.                 CH-001  
       01  MONTHS-ONLY-TO-ADD            PIC 9(5) COMP.                 CH-001  
       01  DAYS-TO-ADD                   PIC S9(5) COMP.
       01  LEAP-YEAR                     PIC 9(1) COMP.                 CH-003  
       01  MONTH-END-SWITCH              PIC 9(1) COMP. 
       01  DAY-TABLE-VALUES.                                            CH-003  
           05  FILLER                    PIC X(39) VALUE                CH-003  
               '31,29,31,30,31,30,31,31,30,31,30,31,366'.               CH-003  
           05  FILLER                    PIC X(39) VALUE                CH-003  
               '31,28,31,30,31,30,31,31,30,31,30,31,365'.               CH-003  
       01  DAY-TABLES  REDEFINES  DAY-TABLE-VALUES.                     CH-003  
           05  LPYR  OCCURS 2.                                          CH-003  
               10  DAYS-OF-MONTH OCCURS 13.                             CH-003  
                   15  DAYS-IN-YY        PIC 9(03).                     CH-004  
                   15  DAYS-IN-MM REDEFINES DAYS-IN-YY.                 CH-004  
                       20  NBRDAYS       PIC 9(02).                     CH-003  
                       20  FILLER        PIC X(01).                     CH-003  
    
       COPY JDN-CONSTANTS-WS.               
       COPY JDN-PACKET-WS.              
       COPY JDN-RECORD-WS.              
    
       LINKAGE SECTION. 
       COPY DATECONV-WS             
            REPLACING ==VALUE ZEROS.== BY ==.==.
    
       PROCEDURE DIVISION USING CONV-DATES. 
    
       000-MAIN SECTION.
       000-SELECT.                                                      CH-001 
            IF DATESUB-FUNC = 1  
               PERFORM 100-CHECK-CYMD-DT                                CH-632
           ELSE IF DATESUB-FUNC = 2                                     CH-001  
               PERFORM 200-YMD-TO-JUL                                   CH-001  
           ELSE IF DATESUB-FUNC = 3                                     CH-001  
               PERFORM 300-JUL-TO-YMD                                   CH-001  
           ELSE IF DATESUB-FUNC = 4                                     CH-001  
               PERFORM 400-DIF-JUL                                      CH-001  
           ELSE IF DATESUB-FUNC = 5                                     CH-001  
               PERFORM 500-DIF-YMD                                      CH-001  
           ELSE IF DATESUB-FUNC = 6                                     CH-004  
               PERFORM 600-DIF-CYMD-30                                  CH-645  
           ELSE IF DATESUB-FUNC = 7                                     CH-001  
               PERFORM 700-ADD-JUL                                      CH-001  
           ELSE IF DATESUB-FUNC = 8                                     CH-001  
               PERFORM 800-ADD-YMD                                      CH-001  
           ELSE IF DATESUB-FUNC = 9                                     CH-001  
               PERFORM 900-CHECK-MDY-DT                                 CH-001  
           ELSE IF DATESUB-FUNC = 10                                    CH-001  
               PERFORM 1000-MDY-TO-JUL                                  CH-001  
           ELSE IF DATESUB-FUNC = 11                                    CH-001  
               PERFORM 1100-JUL-TO-MDY                                  CH-001  
           ELSE IF DATESUB-FUNC = 12                                    CH-001  
               PERFORM 1200-MDY-TO-YMD                                  CH-001  
           ELSE IF DATESUB-FUNC = 13                                    CH-001  
               PERFORM 1300-YMD-TO-MDY                                  CH-001  
           ELSE IF DATESUB-FUNC = 14                                    CH-001  
               PERFORM 1400-DIF-MDY                                     CH-001  
           ELSE IF DATESUB-FUNC = 15                                    CH-004  
               PERFORM 1500-DIF-JUL-30                                  CH-004  
           ELSE IF DATESUB-FUNC = 16                                    CH-004  
               PERFORM 1600-DIF-MDY-30                                  CH-004  
           ELSE IF DATESUB-FUNC = 17                                    CH-001  
               PERFORM 1700-ADD-MDY                                     CH-001  
           ELSE IF DATESUB-FUNC = 18                                    CH-001  
               PERFORM 1800-YMD-TO-CYMD                                 CH-001  
           ELSE IF DATESUB-FUNC = 19                                    CH-001  
               PERFORM 1900-DIF-CYMD                                    CH-001  
           ELSE IF DATESUB-FUNC = 20                                    CH-001  
               PERFORM 2000-ADD-CYMD                                    CH-001  
           ELSE IF DATESUB-FUNC = 21                                    CH-001  
               PERFORM 2100-ADD-MONTHS-TO-YMD                           CH-001  
           ELSE IF DATESUB-FUNC = 22                                    CH-001  
               PERFORM 2200-ADD-MONTHS-TO-CYMD                          CH-001  
           ELSE IF DATESUB-FUNC = 23                                    CH-001  
               PERFORM 2300-JUL-TO-CYMD                                 CH-001  
           ELSE IF DATESUB-FUNC = 24                                    CH-001  
               PERFORM 2400-CYMD-TO-JUL                                 CH-001  
           ELSE IF DATESUB-FUNC = 25                                    CH-001  
               PERFORM 2500-CYMD-TO-INT                                 CH-001  
           ELSE IF DATESUB-FUNC = 26                                    CH-001  
               PERFORM 2600-INT-TO-CYMD                                 CH-001  
           ELSE IF DATESUB-FUNC = 27                                    CH-006  
               PERFORM 2700-MDY-TO-MDCY                                 CH-006  
           ELSE IF DATESUB-FUNC = 28                                    CH-006  
               PERFORM 2800-DIF-JUL-NO-CHECK                            CH-006  
           ELSE IF DATESUB-FUNC = 31                                    CH-001  
               PERFORM 3100-JUL-TO-INT                                  CH-001  
           ELSE IF DATESUB-FUNC = 32                                    CH-001  
               PERFORM 3200-INT-TO-JUL                                  CH-001  
           ELSE IF DATESUB-FUNC = 33                                    CH-001  
               PERFORM 3300-YMD-TO-INT                                  CH-001  
           ELSE IF DATESUB-FUNC = 34                                    CH-001  
               PERFORM 3400-INT-TO-YMD                                  CH-001  
           ELSE IF DATESUB-FUNC = 35                                    CH-001  
               PERFORM 3500-MDY-TO-INT                                  CH-001  
           ELSE IF DATESUB-FUNC = 36                                    CH-001  
               PERFORM 3600-INT-TO-MDY                                  CH-001  
           ELSE IF DATESUB-FUNC = 37                                    CH-002  
               PERFORM 4000-DIF-FY                                      CH-002  
           ELSE IF DATESUB-FUNC = 38                                    CH-002  
               PERFORM 4100-RANGE-JUL                                   CH-002  
           ELSE IF DATESUB-FUNC = 39                                    CH-002  
               PERFORM 4200-RANGE-YMD                                   CH-002  
           ELSE IF DATESUB-FUNC = 40                                    CH-002  
               PERFORM 4300-RANGE-MDY                                   CH-002  
           ELSE IF DATESUB-FUNC = 41
               PERFORM 4400-ADD-MONTHS-TO-MDY   
           ELSE IF DATESUB-FUNC = 42
               PERFORM 4500-ADD-MONTHS-END-JUL  
           ELSE 
               MOVE DATESUB-FUNC TO PRT-DATECONV-FUNC                   CH-001  
               DISPLAY BAD-FUNC-MSG UPON PRT                            CH-001  
               DISPLAY BAD-FUNC-MSG UPON CON                            CH-001
MIGRTN*        CALL 'ABORTRUN'.                                         CH-001  
MIGRTN         MOVE 99 TO RETURN-CODE
MIGRTN         STOP RUN.
                                                                        CH-001  
           IF DATE-ERR-IND = 'Y' AND ABORT-ON-DATE-ERR = 'Y'            CH-001  
               IF DATESUB-FUNC = 1 OR 9                                 CH-001  
                   NEXT SENTENCE                                        CH-001  
               ELSE                                                     CH-001  
                   DISPLAY 'DATECONV CALLED WITH INVALID INPUT DATE '   CH-001  
                       'WITH ABORT-ON-DATE-ERR = "Y"' UPON PRT          CH-001  
                   DISPLAY 'FROM-JUL-DT: ' FROM-JUL-DT                  CH-001  
                       '  TO-JUL-DT: ' TO-JUL-DT                        CH-001  
                       '  FROM-MDY-DT: ' FROM-MDY-DT                    CH-001  
                       '  TO-MDY-DT: ' TO-MDY-DT                        CH-001  
                       '  FROM-YMD-DT: ' FROM-YMD-DT                    CH-001  
                       UPON PRT                                         CH-001  
                   DISPLAY 'TO-YMD-DT: ' TO-YMD-DT                      CH-001  
                       '   FROM-CYMD-DT: ' FROM-CYMD-DT                 CH-001  
                       '   TO-CYMD-DT: ' TO-CYMD-DT                     CH-001  
                       UPON PRT                                         CH-001  
                   DISPLAY 'DATESUB-FUNC: ' DATESUB-FUNC UPON PRT       CH-001  
                   DISPLAY 'DATECONV CALLED WITH INVALID INPUT DATE'    CH-001  
                        UPON CON                                        CH-001
                   MOVE 99 TO RETURN-CODE
                   STOP RUN.
    
       000-EXIT.
           EXIT PROGRAM.
    
       100-CHECK-CYMD-DT.                                               CH-632
           MOVE FROM-CYMD-DT TO WRK-CYMD-DT.                            CH-632  
           PERFORM 9950-VALIDATE-YYYY THROUGH 9960-VALIDATE-EXIT.       CH-003  
       110-CHECK-YMD-DT-EXIT.   
           EXIT PROGRAM.
    
       200-YMD-TO-JUL.                                                  CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-YMD-DT TO JDN-YYMMDD.                              CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM 3200-INT-TO-JUL                                  CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-JUL-DT.                                 CH-001  
       210-YMD-TO-JUL-EXIT.                                             CH-001  
           EXIT PROGRAM.
    
       300-JUL-TO-YMD.                                                  CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-JUL-DT TO JDN-YYDDD.                               CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DAY.                                  CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM 3400-INT-TO-YMD                                  CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-YMD-DT.                                 CH-001  
       310-JUL-TO-YMD-EXIT.                                             CH-001  
           EXIT PROGRAM.
    
       400-DIF-JUL. 
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-JUL-DT TO JDN-YYDDD.                               CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DAY.                                  CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM JDN-ACC-SELF-INIT                                CH-001  
               MOVE TO-JUL-DT TO JDN-YYDDD                              CH-001  
               MOVE ZERO TO JDN-CC                                      CH-001  
               PERFORM JDN-ACC-INT-OF-DAY                               CH-001  
               MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                   CH-005  
               IF JDN-PKT-STATUS = JDN-CON-NOERR                        CH-001  
                   SUBTRACT FROM-INT-DT FROM JDN-INT GIVING DAYS-DIF    CH-001  
                   MOVE DAYS-DIF TO DAYS-DIF-UNSIGNED                   CH-005  
               ELSE                                                     CH-001  
                   MOVE 'Y' TO DATE-ERR-IND                             CH-001  
                   MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED             CH-005  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED.                CH-005  
       410-DIF-JUL-EXIT.
           EXIT PROGRAM.
    
       500-DIF-YMD.                                                     CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-YMD-DT TO JDN-YYMMDD.                              CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM JDN-ACC-SELF-INIT                                CH-001  
               MOVE TO-YMD-DT TO JDN-YYMMDD                             CH-001  
               MOVE ZERO TO JDN-CC                                      CH-001  
               PERFORM JDN-ACC-INT-OF-DATE                              CH-001  
               MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                   CH-005  
               IF JDN-PKT-STATUS = JDN-CON-NOERR                        CH-001  
                   SUBTRACT FROM-INT-DT FROM JDN-INT GIVING DAYS-DIF    CH-001  
                   MOVE DAYS-DIF TO DAYS-DIF-UNSIGNED                   CH-005  
               ELSE                                                     CH-001  
                   MOVE 'Y' TO DATE-ERR-IND                             CH-001  
                   MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED             CH-005  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED.                CH-005  
       510-DIF-YMD-EXIT.                                                CH-001  
           EXIT PROGRAM.
    
       600-DIF-CYMD-30.                                                 CH-645  
           PERFORM 2400-CYMD-TO-JUL.                                    CH-645  
           IF DATE-IS-VALID                                             CH-004  
               MOVE HOLD-JUL-DT-YYYYDDD   TO WRK-CJUL-DT                CH-645  
               PERFORM 9940-CONV-JUL-30 THRU 9945-CONV-JUL-EXIT         CH-004  
               MOVE WRK-CJUL-DT           TO HLD-CJUL-DT                CH-004  
               MOVE TO-CYMD-DT            TO FROM-CYMD-DT               CH-645  
               PERFORM 2400-CYMD-TO-JUL                                 CH-645  
               IF DATE-IS-VALID                                         CH-004  
                   MOVE HOLD-JUL-DT-YYYYDDD   TO WRK-CJUL-DT            CH-645  
                   PERFORM 9940-CONV-JUL-30 THRU 9945-CONV-JUL-EXIT     CH-004  
                   PERFORM 9930-CALC-JUL-30-DIF THRU                    CH-004  
                           9935-CALC-JUL-30-DIF-EXIT                    CH-004  
               ELSE                                                     CH-004  
                   MOVE 'Y' TO DATE-ERR-IND                             CH-004  
                   MOVE ZERO TO DAYS-DIF DAYS-DIF-UNSIGNED              CH-005  
           ELSE                                                         CH-004  
               MOVE 'Y'  TO DATE-ERR-IND                                CH-004  
               MOVE ZERO TO DAYS-DIF DAYS-DIF-UNSIGNED.                 CH-005  
       610-DIF-CYMD-30-EXIT.                                            CH-645
           EXIT PROGRAM.
    
       700-ADD-JUL.                                                     CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-JUL-DT TO JDN-YYDDD.                               CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DAY.                                  CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               ADD JDN-INT DAYS-DIF GIVING FROM-INT-DT                  CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM 3200-INT-TO-JUL                                  CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-JUL-DT.                                 CH-001  
       710-ADD-JUL-EXIT.                                                CH-001  
           EXIT PROGRAM.
    
       800-ADD-YMD.                                                     CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-YMD-DT TO JDN-YYMMDD.                              CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               ADD JDN-INT DAYS-DIF GIVING FROM-INT-DT                  CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM 3400-INT-TO-YMD                                  CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-YMD-DT.                                 CH-001  
       810-ADD-YMD-EXIT.                                                CH-001  
           EXIT PROGRAM.
    
       900-CHECK-MDY-DT.
           MOVE FROM-MDY-MM TO WRK-CYMD-MM.                             CH-003  
           MOVE FROM-MDY-DD TO WRK-CYMD-DD.                             CH-003  
           MOVE FROM-MDY-YY TO WRK-CYMD-YY.                             CH-003  
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-003  
           PERFORM 9950-VALIDATE-YYYY THROUGH 9960-VALIDATE-EXIT.       CH-003  
       910-CHECK-MDY-DT-EXIT.   
           EXIT PROGRAM.
    
       1000-MDY-TO-JUL.                                                 CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-MDY-YY TO JDN-YY.                                  CH-001  
           MOVE FROM-MDY-MM TO JDN-MM.                                  CH-001  
           MOVE FROM-MDY-DD TO JDN-DD.                                  CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM 3200-INT-TO-JUL                                  CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-JUL-DT.                                 CH-001  
       1010-MDY-TO-JUL-EXIT.                                            CH-001  
           EXIT PROGRAM.
    
       1100-JUL-TO-MDY. 
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-JUL-DT TO JDN-YYDDD.                               CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DAY.                                  CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM 3600-INT-TO-MDY                                  CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-MDY-DT.                                 CH-001  
       1110-JUL-TO-MDY-EXIT.
           EXIT PROGRAM.
    
       1200-MDY-TO-YMD.                                                 CH-001  
           MOVE FROM-MDY-MM TO TO-YMD-MM.                               CH-001  
           MOVE FROM-MDY-DD TO TO-YMD-DD.                               CH-001  
           MOVE FROM-MDY-YY TO TO-YMD-YY.                               CH-001  
           MOVE 'N' TO DATE-ERR-IND.                                    CH-001  
       1210-MDY-TO-YMD-EXIT.                                            CH-001  
           EXIT PROGRAM.
    
       1300-YMD-TO-MDY.                                                 CH-001  
           MOVE FROM-YMD-MM TO TO-MDY-MM.                               CH-001  
           MOVE FROM-YMD-DD TO TO-MDY-DD.                               CH-001  
           MOVE FROM-YMD-YY TO TO-MDY-YY.                               CH-001  
           MOVE 'N' TO DATE-ERR-IND.                                    CH-001  
       1310-YMD-TO-MDY-EXIT.                                            CH-001  
           EXIT PROGRAM.
    
       1400-DIF-MDY.                                                    CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-MDY-YY TO JDN-YY.                                  CH-001  
           MOVE FROM-MDY-MM TO JDN-MM.                                  CH-001  
           MOVE FROM-MDY-DD TO JDN-DD.                                  CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM JDN-ACC-SELF-INIT                                CH-001  
               MOVE TO-MDY-YY TO JDN-YY                                 CH-001  
               MOVE TO-MDY-MM TO JDN-MM                                 CH-001  
               MOVE TO-MDY-DD TO JDN-DD                                 CH-001  
               MOVE ZERO TO JDN-CC                                      CH-001  
               PERFORM JDN-ACC-INT-OF-DATE                              CH-001  
               MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                   CH-005  
               IF JDN-PKT-STATUS = JDN-CON-NOERR                        CH-001  
                   SUBTRACT FROM-INT-DT FROM JDN-INT GIVING DAYS-DIF    CH-001  
                   MOVE DAYS-DIF TO DAYS-DIF-UNSIGNED                   CH-005  
               ELSE                                                     CH-001  
                   MOVE 'Y' TO DATE-ERR-IND                             CH-001  
                   MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED             CH-005  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED.                CH-005  
       1410-DIF-MDY-EXIT.                                               CH-001  
           EXIT PROGRAM.
    
       1500-DIF-JUL-30. 
           MOVE FROM-JUL-DT TO WRK-CJUL-JUL-DT.                         CH-004  
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-004  
           PERFORM 9950-VALIDATE-YYYY.                                  CH-004  
           PERFORM 9956-VALIDATE-DDD.                                   CH-004  
           IF DATE-IS-VALID                                             CH-004  
               PERFORM 9940-CONV-JUL-30 THRU 9945-CONV-JUL-EXIT         CH-004  
               MOVE WRK-CJUL-DT TO HLD-CJUL-DT                          CH-004  
               MOVE TO-JUL-DT TO WRK-CJUL-JUL-DT                        CH-004  
               PERFORM 9920-CALC-YY-TO-YYYY                             CH-004  
               PERFORM 9950-VALIDATE-YYYY                               CH-004  
               PERFORM 9956-VALIDATE-DDD                                CH-004  
               IF DATE-IS-VALID                                         CH-004  
                   PERFORM 9940-CONV-JUL-30 THRU 9945-CONV-JUL-EXIT     CH-004  
                   PERFORM 9930-CALC-JUL-30-DIF THRU                    CH-004  
                           9935-CALC-JUL-30-DIF-EXIT                    CH-004  
               ELSE                                                     CH-004  
                   MOVE 'Y' TO DATE-ERR-IND                             CH-004  
                   MOVE ZERO TO DAYS-DIF DAYS-DIF-UNSIGNED              CH-005  
           ELSE                                                         CH-004  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-004  
               MOVE ZERO TO DAYS-DIF DAYS-DIF-UNSIGNED.                 CH-005  
       1510-DIF-JUL-30-EXIT.
           EXIT PROGRAM.
    
       1600-DIF-MDY-30. 
           PERFORM 1000-MDY-TO-JUL.                                     CH-004  
           IF DATE-IS-VALID                                             CH-004  
               MOVE TO-JUL-DT TO WRK-CJUL-JUL-DT                        CH-004  
               PERFORM 9940-CONV-JUL-30 THRU 9945-CONV-JUL-EXIT         CH-004  
               MOVE WRK-CJUL-DT TO HLD-CJUL-DT                          CH-004  
               MOVE TO-MDY-DT TO FROM-MDY-DT                            CH-004  
               PERFORM 1000-MDY-TO-JUL                                  CH-004  
               IF DATE-IS-VALID                                         CH-004  
                   MOVE TO-JUL-DT TO WRK-CJUL-JUL-DT                    CH-004  
                   PERFORM 9940-CONV-JUL-30 THRU 9945-CONV-JUL-EXIT     CH-004  
                   PERFORM 9930-CALC-JUL-30-DIF THRU                    CH-004  
                           9935-CALC-JUL-30-DIF-EXIT                    CH-004  
               ELSE                                                     CH-004  
                   MOVE 'Y' TO DATE-ERR-IND                             CH-004  
                   MOVE ZERO TO DAYS-DIF DAYS-DIF-UNSIGNED              CH-005  
           ELSE                                                         CH-004  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-004  
               MOVE ZERO TO DAYS-DIF DAYS-DIF-UNSIGNED.                 CH-005  
       1610-DIF-MDY-30-EXIT.
           EXIT PROGRAM.
    
       1700-ADD-MDY.
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-MDY-YY TO JDN-YY.                                  CH-001  
           MOVE FROM-MDY-MM TO JDN-MM.                                  CH-001  
           MOVE FROM-MDY-DD TO JDN-DD.                                  CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               ADD JDN-INT DAYS-DIF GIVING FROM-INT-DT                  CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM 3600-INT-TO-MDY                                  CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-MDY-DT.                                 CH-001  
       1710-ADD-MDY-EXIT.   
           EXIT PROGRAM.
    
       1800-YMD-TO-CYMD.                                                CH-001  
           MOVE FROM-YMD-DT TO WRK-CYMD-YMD-DT.                         CH-003  
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-003  
           PERFORM 9950-VALIDATE-YYYY THRU 9960-VALIDATE-EXIT.          CH-003  
           IF DATE-IS-VALID                                             CH-003  
               MOVE WRK-CYMD-DT TO TO-CYMD-DT                           CH-003  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-CYMD-DT.                                CH-001  
       1810-YMD-TO-CYMD-EXIT.                                           CH-001  
           EXIT PROGRAM.
    
       1900-DIF-CYMD.                                                   CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-CYMD-DT TO JDN-YYYYMMDD.                           CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM JDN-ACC-SELF-INIT                                CH-001  
               MOVE TO-CYMD-DT TO JDN-YYYYMMDD                          CH-001  
               PERFORM JDN-ACC-INT-OF-DATE                              CH-001  
               MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                   CH-005  
               IF JDN-PKT-STATUS = JDN-CON-NOERR                        CH-001  
                   SUBTRACT FROM-INT-DT FROM JDN-INT GIVING DAYS-DIF    CH-001  
                   MOVE DAYS-DIF TO DAYS-DIF-UNSIGNED                   CH-005  
               ELSE                                                     CH-001  
                   MOVE 'Y' TO DATE-ERR-IND                             CH-001  
                   MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED             CH-005  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED.                CH-005  
       1910-DIF-CYMD-EXIT.                                              CH-001  
           EXIT PROGRAM.
    
       2000-ADD-CYMD.                                                   CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-CYMD-DT TO JDN-YYYYMMDD.                           CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               ADD JDN-INT DAYS-DIF GIVING FROM-INT-DT                  CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM 3400-INT-TO-YMD                                  CH-001  
               MOVE JDN-YYYYMMDD TO TO-CYMD-DT                          CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-CYMD-DT.                                CH-001  
       2010-ADD-CYMD-EXIT.                                              CH-001  
           EXIT PROGRAM.
    
       2100-ADD-MONTHS-TO-YMD.                                          CH-001  
           MOVE ZEROS TO MONTH-END-SWITCH.  
           MOVE FROM-YMD-DT TO WRK-CYMD-YMD-DT.                         CH-003  
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-003  
           PERFORM 9950-VALIDATE-YYYY THRU 9960-VALIDATE-EXIT.          CH-003  
           IF DATE-IS-VALID                                             CH-001  
               PERFORM 9910-ADD-MONTHS                                  CH-001  
               MOVE WRK-CYMD-YMD-DT TO TO-YMD-DT                        CH-003  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-YMD-DT.                                 CH-001  
       2110-ADD-MONTHS-TO-YMD-EXIT.                                     CH-001  
           EXIT PROGRAM.
    
       2200-ADD-MONTHS-TO-CYMD.                                         CH-001  
           MOVE ZEROS TO MONTH-END-SWITCH.  
           MOVE FROM-CYMD-DT TO WRK-CYMD-DT.                            CH-003  
           PERFORM 9950-VALIDATE-YYYY THRU 9960-VALIDATE-EXIT.          CH-003  
           IF DATE-IS-VALID                                             CH-001  
               PERFORM 9910-ADD-MONTHS                                  CH-001  
               MOVE WRK-CYMD-DT TO TO-CYMD-DT                           CH-003  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-YMD-DT.                                 CH-001  
       2210-ADD-MONTHS-TO-CYMD-EXIT.                                    CH-001  
           EXIT PROGRAM.
    
       2300-JUL-TO-CYMD.                                                CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-JUL-DT TO JDN-YYDDD.                               CH-001  
           MOVE ZERO TO JDN-CC.                                         CH-001  
           PERFORM JDN-ACC-INT-OF-DAY.                                  CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               PERFORM 3400-INT-TO-YMD                                  CH-001  
               MOVE JDN-YYYYMMDD TO TO-CYMD-DT                          CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-CYMD-DT.                                CH-001  
       2310-JUL-TO-CYMD-EXIT.                                           CH-001  
           EXIT PROGRAM.
    
       2400-CYMD-TO-JUL.                                                CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-CYMD-DT TO JDN-YYYYMMDD.                           CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO FROM-INT-DT                              CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
               PERFORM 3200-INT-TO-JUL                                  CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-JUL-DT.                                 CH-001  
       2410-CYMD-TO-JUL-EXIT.                                           CH-001  
           EXIT PROGRAM.
    
       2500-CYMD-TO-INT.                                                CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-CYMD-DT TO JDN-YYYYMMDD.                           CH-001  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
               MOVE JDN-INT TO TO-INT-DT                                CH-001  
               MOVE 'N' TO DATE-ERR-IND                                 CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-INT-DT.                                 CH-001  
       2510-CYMD-TO-INT-EXIT.                                           CH-001  
           EXIT PROGRAM.
    
       2600-INT-TO-CYMD.                                                CH-001  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-001  
           MOVE FROM-INT-DT TO JDN-INT.                                 CH-001  
           PERFORM JDN-ACC-DATE-OF-INT.                                 CH-001  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-001  
              IF JDN-YYYY >= 1953                                       CH-645  
                  MOVE JDN-YYYYMMDD TO TO-CYMD-DT                       CH-001  
                  MOVE 'N' TO DATE-ERR-IND                              CH-001  
              ELSE                                                      CH-001  
                  MOVE 'Y' TO DATE-ERR-IND                              CH-001  
                  MOVE 11 TO DATE-ERR-REASON                            CH-005  
                  MOVE ZEROS TO TO-CYMD-DT                              CH-001  
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-CYMD-DT.                                CH-001  
       2610-INT-TO-CYMD-EXIT.                                           CH-001  
           EXIT PROGRAM.
                                                                        CH-006  
       2700-MDY-TO-MDCY.                                                CH-006  
           MOVE FROM-MDY-MM TO WRK-CYMD-MM.                             CH-006  
           MOVE FROM-MDY-DD TO WRK-CYMD-DD.                             CH-006  
           MOVE FROM-MDY-YY TO WRK-CYMD-YY.                             CH-006  
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-006  
           PERFORM 9950-VALIDATE-YYYY THRU 9960-VALIDATE-EXIT.          CH-006  
           IF DATE-IS-VALID                                             CH-006  
               MOVE WRK-CYMD-YYYY TO TO-MDCY-YYYY                       CH-006  
               MOVE WRK-CYMD-MM   TO TO-MDCY-MM                         CH-006  
               MOVE WRK-CYMD-DD   TO TO-MDCY-DD                         CH-006  
           ELSE                                                         CH-006  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-006  
               MOVE ZEROS TO TO-MDCY-DT.                                CH-006  
       2710-MDY-TO-MDCY-EXIT.                                           CH-006  
           EXIT PROGRAM.                                                CH-006  
                                                                        CH-006  
       2800-DIF-JUL-NO-CHECK.                                           CH-006  
           MOVE FROM-JUL-DT TO WRK-CJUL-JUL-DT.                         CH-006  
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-006  
           PERFORM 9950-VALIDATE-YYYY.                                  CH-006  
           PERFORM 9956-VALIDATE-DDD.                                   CH-006  
           MOVE ZEROS TO DAYS-TO-ADD.   
           IF DATE-IS-VALID                                             CH-006  
               PERFORM JDN-ACC-SELF-INIT                                CH-006  
               MOVE FROM-JUL-DT TO JDN-YYDDD                            CH-006  
               MOVE ZERO TO JDN-CC                                      CH-006  
               PERFORM JDN-ACC-INT-OF-DAY                               CH-006  
               MOVE JDN-INT TO FROM-INT-DT                              CH-006  
           ELSE                                                         CH-006  
               IF NON-NUMERIC-YYYY OR NON-NUMERIC-DDD OR                CH-006  
                  FROM-JUL-DT = ZEROS   
                   MOVE ZEROS TO FROM-INT-DT                            CH-006  
               ELSE                                                     CH-006  
                   SUBTRACT 365 FROM WRK-CJUL-JUL-DDD GIVING
                         DAYS-TO-ADD
                   MOVE 365 TO WRK-CJUL-JUL-DDD 
                   PERFORM JDN-ACC-SELF-INIT
                   MOVE WRK-CJUL-JUL-DT TO JDN-YYDDD                    CH-006  
                   MOVE ZERO TO JDN-CC  
                   PERFORM JDN-ACC-INT-OF-DAY   
                   ADD JDN-INT, DAYS-TO-ADD GIVING FROM-INT-DT. 
           MOVE TO-JUL-DT TO WRK-CJUL-JUL-DT.                           CH-006  
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-006  
           PERFORM 9950-VALIDATE-YYYY.                                  CH-006  
           PERFORM 9956-VALIDATE-DDD.                                   CH-006  
           MOVE ZEROS TO DAYS-TO-ADD.   
           IF DATE-IS-VALID                                             CH-006  
               PERFORM JDN-ACC-SELF-INIT                                CH-006  
               MOVE TO-JUL-DT TO JDN-YYDDD                              CH-006  
               MOVE ZERO TO JDN-CC                                      CH-006  
               PERFORM JDN-ACC-INT-OF-DAY                               CH-006  
               MOVE JDN-INT TO TO-INT-DT                                CH-006  
           ELSE                                                         CH-006  
               IF NON-NUMERIC-YYYY OR NON-NUMERIC-DDD OR
                  TO-JUL-DT = ZEROS 
                   MOVE ZEROS TO TO-INT-DT  
               ELSE 
                   SUBTRACT 365 FROM WRK-CJUL-JUL-DDD GIVING
                         DAYS-TO-ADD
                   MOVE 365 TO WRK-CJUL-JUL-DDD 
                   PERFORM JDN-ACC-SELF-INIT
                   MOVE WRK-CJUL-JUL-DT TO JDN-YYDDD
                   MOVE ZERO TO JDN-CC  
                   PERFORM JDN-ACC-INT-OF-DAY   
                   ADD JDN-INT, DAYS-TO-ADD GIVING TO-INT-DT.   
           SUBTRACT FROM-INT-DT FROM TO-INT-DT GIVING DAYS-DIF.         CH-006  
           MOVE DAYS-DIF TO DAYS-DIF-UNSIGNED.                          CH-006  
           MOVE ZEROS TO DATE-ERR-REASON.                               CH-006  
           MOVE 'N' TO DATE-ERR-IND.                                    CH-006  
       2810-DIF-JUL-NO-CHECK-EXIT.                                      CH-006  
           EXIT PROGRAM.                                                CH-006  
    
       3100-JUL-TO-INT. 
           PERFORM JDN-ACC-SELF-INIT.   
           MOVE FROM-JUL-DT TO JDN-YYDDD.   
           MOVE ZERO TO JDN-CC. 
           PERFORM JDN-ACC-INT-OF-DAY.  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR
               MOVE 'N' TO DATE-ERR-IND 
               MOVE JDN-INT TO TO-INT-DT CONV-INT   
           ELSE 
               MOVE 'Y' TO DATE-ERR-IND 
               MOVE ZEROS TO TO-INT-DT CONV-INT.
       3110-JUL-TO-INT-EXIT.
           EXIT PROGRAM.
    
       3200-INT-TO-JUL. 
           PERFORM JDN-ACC-SELF-INIT.   
           MOVE FROM-INT-DT TO JDN-INT. 
           PERFORM JDN-ACC-DAY-OF-INT.  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR
              IF JDN-YYYY >= 1953                                       CH-645
                  MOVE JDN-YYDDD   TO TO-JUL-DT, CONV-JUL-DT   
                  MOVE JDN-YYYYDDD TO HOLD-JUL-DT-YYYYDDD               CH-645
                  MOVE 'N' TO DATE-ERR-IND  
              ELSE  
                  MOVE 'Y' TO DATE-ERR-IND  
                  MOVE 11 TO DATE-ERR-REASON                            CH-005  
                  MOVE ZEROS TO TO-JUL-DT CONV-JUL-DT   
           ELSE 
               MOVE 'Y' TO DATE-ERR-IND 
               MOVE ZEROS TO TO-JUL-DT CONV-JUL-DT. 
       3210-INT-TO-JUL-EXIT.
           EXIT PROGRAM.
    
       3300-YMD-TO-INT. 
           PERFORM JDN-ACC-SELF-INIT.   
           MOVE FROM-YMD-DT TO JDN-YYMMDD.  
           MOVE ZERO TO JDN-CC. 
           PERFORM JDN-ACC-INT-OF-DATE. 
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR
               MOVE JDN-INT TO TO-INT-DT CONV-INT   
               MOVE 'N' TO DATE-ERR-IND 
           ELSE 
               MOVE 'Y' TO DATE-ERR-IND 
               MOVE ZEROS TO TO-INT-DT CONV-INT.
       3310-YMD-TO-INT-EXIT.
           EXIT PROGRAM.
    
       3400-INT-TO-YMD. 
           PERFORM JDN-ACC-SELF-INIT.   
           MOVE FROM-INT-DT TO JDN-INT. 
           PERFORM JDN-ACC-DATE-OF-INT. 
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR
              IF JDN-YYYY >= 1953                                       CH-645
                  MOVE JDN-YYMMDD TO TO-YMD-DT CONV-YMD-DT  
                  MOVE 'N'   TO DATE-ERR-IND  
              ELSE  
                  MOVE 'Y'   TO DATE-ERR-IND  
                  MOVE 11    TO DATE-ERR-REASON                         CH-005  
                  MOVE ZEROS TO TO-YMD-DT CONV-YMD-DT   
           ELSE 
               MOVE 'Y'      TO DATE-ERR-IND 
               MOVE ZEROS    TO TO-YMD-DT CONV-YMD-DT. 
       3410-INT-TO-YMD-EXIT.
           EXIT PROGRAM.
    
       3500-MDY-TO-INT. 
           PERFORM JDN-ACC-SELF-INIT.   
           MOVE FROM-MDY-YY TO JDN-YY.  
           MOVE FROM-MDY-MM TO JDN-MM.  
           MOVE FROM-MDY-DD TO JDN-DD.  
           MOVE ZERO TO JDN-CC. 
           PERFORM JDN-ACC-INT-OF-DATE. 
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR
               MOVE JDN-INT TO TO-INT-DT CONV-INT   
               MOVE 'N'     TO DATE-ERR-IND 
           ELSE 
               MOVE 'Y'     TO DATE-ERR-IND 
               MOVE ZEROS   TO TO-INT-DT CONV-INT.
       3510-MDY-TO-INT-EXIT.
           EXIT PROGRAM.
    
       3600-INT-TO-MDY. 
           PERFORM JDN-ACC-SELF-INIT.   
           MOVE FROM-INT-DT TO JDN-INT. 
           PERFORM JDN-ACC-DATE-OF-INT. 
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR
              IF JDN-YYYY >= 1953                                       CH-645 
                  MOVE JDN-MM    TO TO-MDY-MM  
                  MOVE JDN-DD    TO TO-MDY-DD  
                  MOVE JDN-YY    TO TO-MDY-YY  
                  MOVE TO-MDY-DT TO CONV-MDY-DT                         CH-007  
                  MOVE 'N'       TO DATE-ERR-IND  
              ELSE  
                  MOVE 'Y'       TO DATE-ERR-IND  
                  MOVE 11        TO DATE-ERR-REASON                     CH-005  
                  MOVE ZEROS     TO TO-MDY-DT CONV-MDY-DT   
           ELSE 
               MOVE 'Y' TO DATE-ERR-IND 
               MOVE ZEROS TO TO-MDY-DT CONV-MDY-DT. 
       3610-INT-TO-MDY-EXIT.
           EXIT PROGRAM.
    
       4000-DIF-FY.                                                     CH-002  
           MOVE 'N'           TO DATE-ERR-IND.                          CH-002  
           MOVE ZEROS         TO DAYS-DIF DAYS-DIF-UNSIGNED.            CH-005  
           MOVE FROM-YMD-YY   TO WRK-CYMD-YY. 
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-002  
           MOVE WRK-CYMD-YYYY TO FROM-CYMD-YYYY.                        CH-002  
           MOVE TO-YMD-YY     TO WRK-CYMD-YY.                           CH-002  
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-002  
           MOVE WRK-CYMD-YYYY TO TO-CYMD-YYYY.                          CH-002  
           SUBTRACT FROM-CYMD-YYYY FROM TO-CYMD-YYYY GIVING DAYS-DIF.   CH-002  
           MOVE DAYS-DIF      TO DAYS-DIF-UNSIGNED.                     CH-005  
       4010-DIF-FY-EXIT.                                                CH-002  
           EXIT PROGRAM.
    
       4100-RANGE-JUL.                                                  CH-002  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-002  
           MOVE FROM-JUL-DT TO JDN-YYDDD.                               CH-002  
           MOVE ZERO TO JDN-CC.                                         CH-002  
           PERFORM JDN-ACC-INT-OF-DAY.                                  CH-002  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-002  
              MOVE JDN-INT TO FROM-INT-DT                               CH-002  
              MOVE 'N' TO DATE-ERR-IND                                  CH-002  
              PERFORM JDN-ACC-SELF-INIT                                 CH-002  
              MOVE TO-JUL-DT TO JDN-YYDDD                               CH-002  
              MOVE ZERO TO JDN-CC                                       CH-002  
              PERFORM JDN-ACC-INT-OF-DAY                                CH-002  
              MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                    CH-005  
              IF JDN-PKT-STATUS = JDN-CON-NOERR                         CH-002  
                 MOVE JDN-INT TO TO-INT-DT                              CH-002  
                 MOVE 'N' TO DATE-ERR-IND                               CH-002  
                 PERFORM JDN-ACC-SELF-INIT                              CH-002  
                 MOVE BETWEEN-JUL-DT TO JDN-YYDDD                       CH-002  
                 MOVE ZERO TO JDN-CC                                    CH-002  
                 PERFORM JDN-ACC-INT-OF-DAY                             CH-002  
                 MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                 CH-005  
                 IF JDN-PKT-STATUS = JDN-CON-NOERR                      CH-002  
                    MOVE 'N' TO DATE-ERR-IND                            CH-002  
                    IF JDN-INT > TO-INT-DT OR JDN-INT < FROM-INT-DT     CH-002  
                       MOVE 77777 TO DAYS-DIF DAYS-DIF-UNSIGNED         CH-005  
                    ELSE                                                CH-002  
                       MOVE 88888 TO DAYS-DIF DAYS-DIF-UNSIGNED         CH-005  
                 ELSE                                                   CH-002  
                    MOVE 'Y' TO DATE-ERR-IND                            CH-002  
                    MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED            CH-005  
              ELSE                                                      CH-002  
                 MOVE 'Y' TO DATE-ERR-IND                               CH-002  
                 MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED               CH-005  
           ELSE                                                         CH-002  
              MOVE 'Y' TO DATE-ERR-IND                                  CH-002  
              MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED.                 CH-005  
       4110-RANGE-JUL-EXIT.                                             CH-002  
           EXIT PROGRAM.
    
       4200-RANGE-YMD.                                                  CH-002  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-002  
           MOVE FROM-YMD-DT TO JDN-YYMMDD.                              CH-002  
           MOVE ZERO TO JDN-CC.                                         CH-002  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-002  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-002  
              MOVE JDN-INT TO FROM-INT-DT                               CH-002  
              MOVE 'N' TO DATE-ERR-IND                                  CH-002  
              PERFORM JDN-ACC-SELF-INIT                                 CH-002  
              MOVE TO-YMD-DT TO JDN-YYMMDD                              CH-002  
              MOVE ZERO TO JDN-CC                                       CH-002  
              PERFORM JDN-ACC-INT-OF-DATE                               CH-002  
              MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                    CH-005  
              IF JDN-PKT-STATUS = JDN-CON-NOERR                         CH-002  
                 MOVE JDN-INT TO TO-INT-DT                              CH-002  
                 MOVE 'N' TO DATE-ERR-IND                               CH-002  
                 PERFORM JDN-ACC-SELF-INIT                              CH-002  
                 MOVE BETWEEN-YMD-DT TO JDN-YYMMDD                      CH-002  
                 MOVE ZERO TO JDN-CC                                    CH-002  
                 PERFORM JDN-ACC-INT-OF-DATE                            CH-002  
                 MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                 CH-005  
                 IF JDN-PKT-STATUS = JDN-CON-NOERR                      CH-002  
                    MOVE 'N' TO DATE-ERR-IND                            CH-002  
                    IF JDN-INT > TO-INT-DT OR JDN-INT < FROM-INT-DT     CH-002  
                       MOVE 77777 TO DAYS-DIF DAYS-DIF-UNSIGNED         CH-005  
                    ELSE                                                CH-002  
                       MOVE 88888 TO DAYS-DIF DAYS-DIF-UNSIGNED         CH-005  
                 ELSE                                                   CH-002  
                    MOVE 'Y' TO DATE-ERR-IND                            CH-002  
                    MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED            CH-005  
              ELSE                                                      CH-002  
                 MOVE 'Y' TO DATE-ERR-IND                               CH-002  
                 MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED               CH-005  
           ELSE                                                         CH-002  
              MOVE 'Y' TO DATE-ERR-IND                                  CH-002  
              MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED.                 CH-005  
       4210-RANGE-YMD-EXIT.                                             CH-002  
           EXIT PROGRAM.
    
       4300-RANGE-MDY.                                                  CH-002  
           PERFORM JDN-ACC-SELF-INIT.                                   CH-002  
           MOVE FROM-MDY-YY TO JDN-YY.                                  CH-002  
           MOVE FROM-MDY-MM TO JDN-MM.  
           MOVE FROM-MDY-DD TO JDN-DD.  
           MOVE ZERO TO JDN-CC.                                         CH-002  
           PERFORM JDN-ACC-INT-OF-DATE.                                 CH-002  
           MOVE JDN-PKT-STATUS TO DATE-ERR-REASON.                      CH-005  
           IF JDN-PKT-STATUS = JDN-CON-NOERR                            CH-002  
              MOVE JDN-INT TO FROM-INT-DT                               CH-002  
              MOVE 'N' TO DATE-ERR-IND                                  CH-002  
              PERFORM JDN-ACC-SELF-INIT                                 CH-002  
              MOVE TO-MDY-YY TO JDN-YY                                  CH-002  
              MOVE TO-MDY-MM TO JDN-MM  
              MOVE TO-MDY-DD TO JDN-DD  
              MOVE ZERO TO JDN-CC                                       CH-002  
              PERFORM JDN-ACC-INT-OF-DATE                               CH-002  
              MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                    CH-005  
              IF JDN-PKT-STATUS = JDN-CON-NOERR                         CH-002  
                 MOVE JDN-INT TO TO-INT-DT                              CH-002  
                 MOVE 'N' TO DATE-ERR-IND                               CH-002  
                 PERFORM JDN-ACC-SELF-INIT                              CH-002  
                 MOVE BETWEEN-MDY-YY TO JDN-YY                          CH-002  
                 MOVE BETWEEN-MDY-MM TO JDN-MM  
                 MOVE BETWEEN-MDY-DD TO JDN-DD  
                 MOVE ZERO TO JDN-CC                                    CH-002  
                 PERFORM JDN-ACC-INT-OF-DATE                            CH-002  
                 MOVE JDN-PKT-STATUS TO DATE-ERR-REASON                 CH-005  
                 IF JDN-PKT-STATUS = JDN-CON-NOERR                      CH-002  
                    MOVE 'N' TO DATE-ERR-IND                            CH-002  
                    IF JDN-INT > TO-INT-DT OR JDN-INT < FROM-INT-DT     CH-002  
                       MOVE 77777 TO DAYS-DIF DAYS-DIF-UNSIGNED         CH-005  
                    ELSE                                                CH-002  
                       MOVE 88888 TO DAYS-DIF DAYS-DIF-UNSIGNED         CH-005  
                 ELSE                                                   CH-002  
                    MOVE 'Y' TO DATE-ERR-IND                            CH-002  
                    MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED            CH-005  
              ELSE                                                      CH-002  
                 MOVE 'Y' TO DATE-ERR-IND                               CH-002  
                 MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED               CH-005  
           ELSE                                                         CH-002  
              MOVE 'Y' TO DATE-ERR-IND                                  CH-002  
              MOVE ZEROS TO DAYS-DIF DAYS-DIF-UNSIGNED.                 CH-005  
       4310-RANGE-MDY-EXIT.                                             CH-002  
           EXIT PROGRAM.
    
       4400-ADD-MONTHS-TO-MDY.                                          CH-001  
           MOVE ZEROS TO MONTH-END-SWITCH.  
           MOVE FROM-MDY-YY TO WRK-CYMD-YY.                             CH-003  
           MOVE FROM-MDY-MM TO WRK-CYMD-MM. 
           MOVE FROM-MDY-DD TO WRK-CYMD-DD. 
           PERFORM 9920-CALC-YY-TO-YYYY.                                CH-003  
           PERFORM 9950-VALIDATE-YYYY THRU 9960-VALIDATE-EXIT.          CH-003  
           IF DATE-IS-VALID                                             CH-001  
               PERFORM 9910-ADD-MONTHS                                  CH-001  
               MOVE WRK-CYMD-YY TO TO-MDY-YY                            CH-003  
               MOVE WRK-CYMD-MM TO TO-MDY-MM
               MOVE WRK-CYMD-DD TO TO-MDY-DD
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-YMD-DT.                                 CH-001  
       4410-ADD-MONTHS-TO-MDY-EXIT.                                     CH-001  
           EXIT PROGRAM.
    
       4500-ADD-MONTHS-END-JUL.                                         CH-001  
           MOVE 0 TO MONTH-END-SWITCH.  
           PERFORM 2300-JUL-TO-CYMD.
           IF DATE-IS-VALID 
               MOVE TO-CYMD-DT TO WRK-CYMD-DT                           CH-003  
               PERFORM 9950-VALIDATE-YYYY   
               IF  WRK-CYMD-DD = NBRDAYS(LEAP-YEAR, WRK-CYMD-MM)        CH-003  
                    MOVE 1 TO MONTH-END-SWITCH.                         CH-003  
           IF DATE-IS-VALID 
               PERFORM 9910-ADD-MONTHS                                  CH-001  
               MOVE WRK-CYMD-DT TO FROM-CYMD-DT                         CH-003  
               PERFORM 2400-CYMD-TO-JUL 
           ELSE                                                         CH-001  
               MOVE 'Y' TO DATE-ERR-IND                                 CH-001  
               MOVE ZEROS TO TO-JUL-DT.                                 CH-001  
       4510-ADD-MONTHS-END-JUL-EXIT.                                    CH-001  
           EXIT PROGRAM.
    
       9910-ADD-MONTHS.                                                 CH-001  
      ******                                                            CH-001  
      ****** ADD MONTHS-TO-ADD TO DATE IN WRK-CYMD-DT,                  CH-001  
      ******                                                            CH-001  
           MOVE MONTHS-TO-ADD TO MONTHS-TO-ADD-UNSIGNED.                CH-001  
           DIVIDE MONTHS-TO-ADD-UNSIGNED BY 12 GIVING                   CH-001  
                YEARS-TO-ADD REMAINDER MONTHS-ONLY-TO-ADD.              CH-001  
           IF MONTHS-TO-ADD > ZERO                                      CH-001  
               ADD YEARS-TO-ADD TO WRK-CYMD-YYYY                        CH-001  
               ADD MONTHS-ONLY-TO-ADD TO WRK-CYMD-MM                    CH-001  
               IF WRK-CYMD-MM > 12                                      CH-003  
                   ADD 1 TO WRK-CYMD-YYYY                               CH-003  
                   SUBTRACT 12 FROM WRK-CYMD-MM                         CH-003  
               ELSE NEXT SENTENCE                                       CH-003  
           ELSE                                                         CH-001  
               SUBTRACT YEARS-TO-ADD FROM WRK-CYMD-YYYY                 CH-001  
               SUBTRACT MONTHS-ONLY-TO-ADD FROM WRK-CYMD-MM             CH-003  
                   GIVING DAYS-DIF                                      CH-003  
               IF DAYS-DIF < 1                                          CH-005  
                   SUBTRACT 1 FROM WRK-CYMD-YYYY                        CH-003  
                   ADD 12, DAYS-DIF GIVING WRK-CYMD-MM                  CH-003  
               ELSE                                                     CH-003  
                    MOVE DAYS-DIF TO WRK-CYMD-MM.   
           MOVE ZEROS TO DAYS-DIF.  
           PERFORM 9950-VALIDATE-YYYY.  
           IF  WRK-CYMD-DD > NBRDAYS(LEAP-YEAR, WRK-CYMD-MM) OR         CH-003  
               MONTH-END-SWITCH = 1 
               MOVE NBRDAYS(LEAP-YEAR, WRK-CYMD-MM) TO WRK-CYMD-DD.     CH-003  
       9915-ADD-MONTHS-EXIT.                                            CH-001  
           EXIT.                                                        CH-001  
    
       9920-CALC-YY-TO-YYYY.                                            CH-001  
Infer      IF  (WRK-CYMD-YY NOT NUMERIC)                                CH-001  
based      OR  (WRK-CYMD-YY > 52)                                       CH-001  
on             MOVE 19 TO WRK-CYMD-CENTURY                              CH-001  
TST's      ELSE                                                         CH-001  
b'day.         MOVE 20 TO WRK-CYMD-CENTURY.                             CH-001  
       9925-CALC-YY-TO-YYYY-EXIT.                                       CH-001  
           EXIT.                                                        CH-001  
    
       9930-CALC-JUL-30-DIF.                                            CH-004  
           SUBTRACT HLD-CJUL-JUL-DDD FROM WRK-CJUL-JUL-DDD              CH-004  
               GIVING DAYS-DIF.                                         CH-004  
           SUBTRACT HLD-CYMD-YYYY FROM WRK-CYMD-YYYY                    CH-004  
               GIVING MONTHS-TO-ADD.                                    CH-004  
           MULTIPLY MONTHS-TO-ADD BY 360 GIVING MONTHS-TO-ADD.          CH-004  
           ADD MONTHS-TO-ADD TO DAYS-DIF.                               CH-004  
           MOVE DAYS-DIF TO DAYS-DIF-UNSIGNED.                          CH-005  
       9935-CALC-JUL-30-DIF-EXIT.                                       CH-004  
           EXIT.                                                        CH-004  
    
       9940-CONV-JUL-30.                                                CH-004  
      *    PERFORM 9920-CALC-YY-TO-YYYY.                                CH-645  
           IF  WRK-CJUL-JUL-DDD LESS 31                                 CH-004  
               GO TO 9945-CONV-JUL-EXIT.                                CH-004  
           PERFORM 9950-VALIDATE-YYYY.                                  CH-004  
           IF LEAP-YEAR = 1                                             CH-004  
               IF  WRK-CJUL-JUL-DDD < 61                                CH-004  
                   SUBTRACT 1 FROM WRK-CJUL-JUL-DDD                     CH-004  
                   GO TO 9945-CONV-JUL-EXIT                             CH-004  
               ELSE NEXT SENTENCE                                       CH-004  
           ELSE                                                         CH-004  
               IF  WRK-CJUL-JUL-DDD < 60                                CH-004  
                   SUBTRACT 1 FROM WRK-CJUL-JUL-DDD                     CH-004  
                   GO TO 9945-CONV-JUL-EXIT                             CH-004  
               ELSE                                                     CH-004  
                   ADD 1 TO WRK-CJUL-JUL-DDD.                           CH-004  
           IF  WRK-CJUL-JUL-DDD LESS 91                                 CH-004  
               GO TO 9945-CONV-JUL-EXIT.                                CH-004  
           SUBTRACT 1 FROM WRK-CJUL-JUL-DDD.                            CH-004  
           IF  WRK-CJUL-JUL-DDD LESS 151                                CH-004  
               GO TO 9945-CONV-JUL-EXIT.                                CH-004  
           SUBTRACT 1 FROM WRK-CJUL-JUL-DDD.                            CH-004  
           IF  WRK-CJUL-JUL-DDD LESS 211                                CH-004  
               GO TO 9945-CONV-JUL-EXIT.                                CH-004  
           SUBTRACT 1 FROM WRK-CJUL-JUL-DDD.                            CH-004  
           IF  WRK-CJUL-JUL-DDD LESS 241                                CH-004  
               GO TO 9945-CONV-JUL-EXIT.                                CH-004  
           SUBTRACT 1 FROM WRK-CJUL-JUL-DDD.                            CH-004  
           IF  WRK-CJUL-JUL-DDD LESS 301                                CH-004  
               GO TO 9945-CONV-JUL-EXIT.                                CH-004  
           SUBTRACT 1 FROM WRK-CJUL-JUL-DDD.                            CH-004  
           IF  WRK-CJUL-JUL-DDD LESS 361                                CH-004  
               GO TO 9945-CONV-JUL-EXIT.                                CH-004  
           SUBTRACT 1 FROM WRK-CJUL-JUL-DDD.                            CH-004  
       9945-CONV-JUL-EXIT.                                              CH-004  
           EXIT.                                                        CH-004  
    
       9950-VALIDATE-YYYY.                                              CH-003  
           MOVE 'N' TO DATE-ERR-IND.                                    CH-003  
           MOVE ZEROES TO DAYS-TO-ADD DATE-ERR-REASON.                  CH-005  
           MOVE 1 TO LEAP-YEAR.                                         CH-003  
      * Note: this also validates a julian century via a redefine of    CH-645
      *       the CYMD century data field.....                          CH-645
           IF  (WRK-CYMD-YYYY NOT NUMERIC)                              CH-003  
              MOVE 'Y' TO DATE-ERR-IND                                  CH-003  
              MOVE 05  TO DATE-ERR-REASON                               CH-005  
           ELSE                                                         CH-008  
              IF  (WRK-CYMD-YYYY < 1601)
                 MOVE 'Y' TO DATE-ERR-IND   
                 MOVE 11  TO DATE-ERR-REASON.                           CH-005  
           DIVIDE WRK-CYMD-YYYY BY 4 GIVING YEARS-TO-ADD                CH-003  
              REMAINDER DAYS-TO-ADD.                                    CH-003  
           IF DAYS-TO-ADD > 0                                           CH-003  
              MOVE 2 TO LEAP-YEAR.                                      CH-003  
       9952-VALIDATE-MM.                                                CH-003  
           IF  (WRK-CYMD-MM NOT NUMERIC)                                CH-003  
              MOVE 'Y' TO DATE-ERR-IND                                  CH-003  
              MOVE 04  TO DATE-ERR-REASON                               CH-005  
              GO TO 9960-VALIDATE-EXIT.                                 CH-008  
           IF  (WRK-CYMD-MM < 1 OR > 12)
              MOVE 'Y' TO DATE-ERR-IND  
              MOVE 10  TO DATE-ERR-REASON                               CH-005  
              GO TO 9960-VALIDATE-EXIT.                                 CH-008  
       9954-VALIDATE-DD.                                                CH-003  
           IF  (WRK-CYMD-DD NOT NUMERIC)                                CH-003  
              MOVE 'Y' TO DATE-ERR-IND  
              MOVE 02  TO DATE-ERR-REASON                               CH-005  
           ELSE                                                         CH-008  
              IF (WRK-CYMD-DD < 1                                       CH-003  
                    OR > NBRDAYS(LEAP-YEAR, WRK-CYMD-MM))               CH-003  
                 MOVE 'Y' TO DATE-ERR-IND                               CH-003  
                 MOVE 07  TO DATE-ERR-REASON.                           CH-005  
           GO TO 9960-VALIDATE-EXIT.                                    CH-004  
       9956-VALIDATE-DDD.                                               CH-004  
           IF  (WRK-CJUL-JUL-DDD NOT NUMERIC)                           CH-004  
              MOVE 'Y' TO DATE-ERR-IND  
              MOVE 03  TO DATE-ERR-REASON                               CH-005  
           ELSE                                                         CH-008  
              IF (WRK-CJUL-JUL-DDD < 1                                  CH-004  
                    OR > DAYS-IN-YY(LEAP-YEAR, 13))                     CH-004  
                 MOVE 'Y' TO DATE-ERR-IND                               CH-004  
                 MOVE 08  TO DATE-ERR-REASON.                           CH-005  
       9960-VALIDATE-EXIT.                                              CH-003  
           EXIT.                                                        CH-003  
    
MIGRTN COPY JDN-RECORD-ACCESS.              
