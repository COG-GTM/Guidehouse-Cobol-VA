      *** DATECONV-PD.cpy COPYBOOK 
      *** FROM DATECONV-PD.txt UNISYS PROC 
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
      *                                                               * 
      ***************************************************************** 
      *    Procedure division for proc DATECONV-WS  
      *    Date procedure for Julian, Julian Number (INT),              CH-001  
      *    YMD (YYMMDD format), MDY (MMDDYY format), and                CH-001  
      *    CYMD (YYYYMMDD) format conversions and computations.         CH-001  
      *                                                                 CH-001  
      *    Copy this proc to the Procedure Division, and copy           CH-001  
      *    DATECONV-WS to Working-storage.                              CH-001  
      *                                                                 CH-001  
      * FUNCTIONS AVAILABLE FROM THIS PROC:                             CH-001  
      *                                                                 CH-001  
      *   CHECK-CYMD-DT      CHECK-MDY-DT    YMD-TO-JUL    JUL-TO-YMD   CH-632  
      *   MYD-TO-JUL         JUL-TO-MDY      MDY-TO-YMD    YMD-TO-MDY   CH-001  
      *   CYMD-TO-JUL        JUL-TO-CYMD     CYMD-TO-INT   INT-TO-CYMD  CH-001  
      *   JUL-TO-INT         INT-TO-JUL      YMD-TO-INT    INT-TO-YMD   CH-001  
      *   MYD-TO-INT         INT-TO-MDY      YMD-TO-CYMD   MDY-TO-MDCY  CH-004  
      *   DIF-JUL            DIF-YMD         DIF-MDY       DIF-CYMD     CH-001  
      *   DIF-JUL-30         DIF-CYMD-30     DIF-MDY-30                 CH-645  
      *   ADD-JUL            ADD-YMD         ADD-MDY       ADD-CYMD     CH-001  
      *   ADD-MONTHS-TO-YMD                  DIF-JUL-NO-CHECK           CH-004  
      *   ADD-MONTHS-TO-CYMD                 ADD-MONTHS-TO-MDY          CH-001  
      *   ADD-MONTHS-END-JUL
      *   RANGE-JUL          RANGE-YMD       RANGE-MDY     DIF-FY       CH-002  
      *                                                                 CH-001  
      * COMPARING DATES                                                 CH-001  
      *                                                                 CH-001  
      *   The functions which compare dates (DIF-JUL, DIF-MDY, DIF-YMD, CH-001  
      *   DIF-CYMD and DIF-FY) use the sign of the output field         CH-002  
      *   DAYS-DIF to indicate if the to-date is before or after the    CH-002  
      *   from-date.                                                    CH-002  
      *                                                                 CH-001  
      *   The field DATE-ERR-IND does NOT indicate this; it indicates   CH-001  
      *   whether any of the input fields contained an invalid date.    CH-001  
      *                                                                 CH-001  
      * CHECKING OF INPUT FIELDS:                                       CH-001  
      *                                                                 CH-001  
      *   Input Julian dates and FY are always assumed to be valid      CH-002  
      *   or zero.   Input dates in other formats are, in general,      CH-001  
      *   checked for being valid dates.                                CH-001  
      *                                                                 CH-001  
      *   For most functions, if an input date is invalid or            CH-001  
      *   an input Julian date is zeros, then:                          CH-001  
      *                                                                 CH-001  
      *       If ABORT-ON-DATE-ERR is set to 'Y', 'ABORTRUN' is called. CH-001  
      *       Otherwise, DATE-ERR-IND is set to 'Y' and all output      CH-001  
      *       dates are set to zeros.                                   CH-001  
      *                                                                 CH-001  
      *   Functions CHECK-CMDY-DT and CHECK-YMD-DT never abort.         CH-001  
      *   Functions MDY-TO-YMD and YMD-TO-MDY reformat their input      CH-001  
      *   without checking it for validity.                             CH-001  
      *                                                                 CH-001  
      * OUTPUT FIELDS                                                   CH-001  
      *                                                                 CH-001  
      *   Each function moves its output value to the appropriate       CH-001  
      *   output field (DAYS-DIF, TO-JUL-DT, TO-MDY-DT, TO-YMD-DT,      CH-001  
      *   or TO-CYMD-DT).  Each function but MDY-TO-YMD and YMD-TO-MDY  CH-001  
      *   also sets DATE-ERR-IND to 'Y' or 'N'.  All other fields are   CH-001  
      *   unchanged and retain their previous values.                   CH-001  
      *                                                                 CH-001  
      ******************************************************************CH-001  
       DATECONV-PD SECTION. 
       CHECK-CYMD-DT.                                                   CH-632
           MOVE 1 TO DATESUB-FUNC.                                      CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       CHECK-MDY-DT.                                                    CH-001  
           MOVE 9 TO DATESUB-FUNC.                                      CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       YMD-TO-JUL.                                                      CH-001  
           MOVE 2 TO DATESUB-FUNC.                                      CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       JUL-TO-YMD.                                                      CH-001  
           MOVE 3 TO DATESUB-FUNC.                                      CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       MDY-TO-JUL.                                                      CH-001  
           MOVE 10 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       JUL-TO-MDY.                                                      CH-001  
           MOVE 11 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       MDY-TO-YMD.                                                      CH-001  
           MOVE 12 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       MDY-TO-MDCY.                                                     CH-004  
           MOVE 27 TO DATESUB-FUNC.                                     CH-004  
           CALL 'DATECONV' USING CONV-DATES.                            CH-004  
       YMD-TO-MDY.                                                      CH-001  
           MOVE 13 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       YMD-TO-CYMD.                                                     CH-001  
           MOVE 18 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       JUL-TO-CYMD.                                                     CH-001  
           MOVE 23 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       CYMD-TO-JUL.                                                     CH-001  
           MOVE 24 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       CYMD-TO-INT.                                                     CH-001  
           MOVE 25 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       INT-TO-CYMD.                                                     CH-001  
           MOVE 26 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       JUL-TO-INT.  
           MOVE 31 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       INT-TO-JUL.  
           MOVE 32 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       YMD-TO-INT.  
           MOVE 33 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       INT-TO-YMD.  
           MOVE 34 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       MDY-TO-INT.  
           MOVE 35 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       INT-TO-MDY.  
           MOVE 36 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       DIF-JUL.                                                         CH-001  
           MOVE 4 TO DATESUB-FUNC.                                      CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       DIF-JUL-NO-CHECK.                                                CH-004  
           MOVE 28 TO DATESUB-FUNC.                                     CH-004  
           CALL 'DATECONV' USING CONV-DATES.                            CH-004  
       DIF-YMD.                                                         CH-001  
           MOVE 5 TO DATESUB-FUNC.                                      CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       DIF-MDY.                                                         CH-001  
           MOVE 14 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       DIF-CYMD.                                                        CH-001  
           MOVE 19 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       DIF-FY.                                                          CH-002  
           MOVE 37 TO DATESUB-FUNC.                                     CH-002  
           CALL 'DATECONV' USING CONV-DATES.                            CH-002  
       DIF-JUL-30.                                                      CH-003  
           MOVE 15 TO DATESUB-FUNC.                                     CH-003  
           CALL 'DATECONV' USING CONV-DATES.                            CH-003  
       DIF-CYMD-30.                                                     CH-645  
           MOVE 6 TO DATESUB-FUNC.                                      CH-003  
           CALL 'DATECONV' USING CONV-DATES.                            CH-003  
       DIF-MDY-30.                                                      CH-003  
           MOVE 16 TO DATESUB-FUNC.                                     CH-003  
           CALL 'DATECONV' USING CONV-DATES.                            CH-003  
       ADD-JUL.                                                         CH-001  
           MOVE 7 TO DATESUB-FUNC.                                      CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       ADD-YMD.                                                         CH-001  
           MOVE 8 TO DATESUB-FUNC.                                      CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       ADD-MDY.                                                         CH-001  
           MOVE 17 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       ADD-CYMD.                                                        CH-001  
           MOVE 20 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       ADD-MONTHS-TO-YMD.                                               CH-001  
           MOVE 21 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       ADD-MONTHS-TO-CYMD.                                              CH-001  
           MOVE 22 TO DATESUB-FUNC.                                     CH-001  
           CALL 'DATECONV' USING CONV-DATES.                            CH-001  
       ADD-MONTHS-TO-MDY.   
           MOVE 41 TO DATESUB-FUNC. 
           CALL 'DATECONV' USING CONV-DATES.
       ADD-MONTHS-END-JUL.  
           MOVE 42 TO DATESUB-FUNC. 
           CALL 'DATECONV' USING CONV-DATES.
       RANGE-JUL.                                                       CH-002  
           MOVE 38 TO DATESUB-FUNC.                                     CH-002  
           CALL 'DATECONV' USING CONV-DATES.                            CH-002  
       RANGE-YMD.                                                       CH-002  
           MOVE 39 TO DATESUB-FUNC.                                     CH-002  
           CALL 'DATECONV' USING CONV-DATES.                            CH-002  
       RANGE-MDY.                                                       CH-002  
           MOVE 40 TO DATESUB-FUNC.                                     CH-002  
           CALL 'DATECONV' USING CONV-DATES.                            CH-002  
       DATECONV-PD-EXIT.                                                CH-001  
           EXIT.                                                        CH-001  
                                                                        CH-001  
 END  *
