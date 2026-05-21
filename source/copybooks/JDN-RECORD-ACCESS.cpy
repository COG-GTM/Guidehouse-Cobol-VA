      ***************************************************************** 
      *                        COMMENT SECTION                        * 
      ***************************************************************** 
      *                                                               * 
      * Related PROCs:  In order to use JDN-RECORD-ACCESS, you must   * 
      *                 also copy JDN-CONSTANTS-WS, JDN-PACKET-WS and * 
      *                 JDN-RECORD-WS into WORKING-STORAGE.           * 
      *                                                               * 
      *                 The WORKING-STORAGE procs cannot be combined  * 
      *                 because they are also used in JDNSUB, which   * 
      *                 must have them separate.                      * 
MIGRTN*** Note:  JDNSUB program is no longer called, since it has     *
MIGRTN*** been replaced by COBOL functions.                           *
      *                                                               * 
      ***************************************************************** 
      *                    DESCRIPTION OF THE PROC                    * 
      ***************************************************************** 
      *                                                               * 
      * The COBOL-85 standard (FIPS 21-2) was expanded in 1989 to     * 
      * include the Intrinsic Functions Module, and the result became * 
      * FIPS 21-3.  As such, the date routines it contains are a FIPS * 
      * standard that the TST can rely on to be implemented on all    * 
      * future COBOLs.  Unfortunately, they aren't yet implemented in * 
      * our present COBOLs (ACOB and UCOB), hence this proc.          * 
      *                                                               * 
      * This proc calls the subprogram JDNSUB to emulate the following* 
      * new UCOB intrinsic functions, which otherwise wouldn't be     * 
      * available until System Base Release 5R1:                      * 
      *                                                               * 
      *        DATE-OF-INTEGER                                        * 
      *        DAY-OF-INTEGER                                         * 
      *        INTEGER-OF-DATE                                        * 
      *        INTEGER-OF-DAY                                         * 
      *                                                               * 
      * Used in this context, INTEGER means "the number of days       * 
      * since December 31st, 1600 AD, Gregorian".  In other words,    * 
      * January 1st, 1601 AD, Gregorian, is day 1.  The common term   * 
      * for a sequential numbering of days is "Julian Day Number",    * 
      * or JDN.  Don't confuse this term with "Julian Date", which    * 
      * is the number of days within a year, or "Julian Calendar",    * 
      * which is the calendar introduced by Julius Caesar, in which   * 
      * every year divisible evenly by 4 is a leap year (even if      * 
      * it's a turn-of-the-century).                                  * 
      *                                                               * 
      * The US Naval Observatory's atomic clocks are the official     * 
      * time standard for the United States and astronomers world-    * 
      * wide.  This is significant to us only because the USNO uses   * 
      * a **different** JDN (also a FIPS standard!) based on 4713 BC, * 
      * Julian.  To get USNO JDN, add JDN-CON-USNO-OFFSET to JDN-INT. * 
      *                                                               * 
      * JDN-CON-USNO-OFFSET is the USNO JDN of December 31st, 1600 AD,* 
      * Gregorian, as you probably guessed.  JDN-CON-USNO-OFFSET is   * 
      * defined in JDN-CONSTANTS-WS.                                  * 
      *                                                               * 
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
    
      *** JDN-RECORD-ACCESS.cpy COPYBOOK 
      *** FROM JDNRECORDACC.txt UNISYS PROC 
      / 
       JDN-RECORD-ACCESS SECTION.   
MIGRTN*JDN-Acc-Call.
MIGRTN*    CALL 'JDNSUB' USING         JDN-Packet, JDN-Record.  
    
       JDN-Acc-CC-Inferred. 
Infer      IF  (JDN-YY NOT NUMERIC) 
based      OR  (JDN-YY > 72)                                            CHG-002
on             MOVE 19                 TO JDN-CC                         
TST's      ELSE 
b'day.         MOVE 20                 TO JDN-CC.   
    
       JDN-Acc-Date-Of-Int. 
           MOVE JDN-Con-DateOfInt      TO JDN-Pkt-Action.   
MIGRTN*    PERFORM JDN-Acc-Call.
MIGRTN     COMPUTE JDN-YYYYMMDD = 
MIGRTN             FUNCTION DATE-OF-INTEGER (JDN-Int).  
    
       JDN-Acc-Day-Of-Int.  
           MOVE JDN-Con-DayOfInt       TO JDN-Pkt-Action.   
MIGRTN*    PERFORM JDN-Acc-Call.
MIGRTN     COMPUTE JDN-YYYYDDD =
MIGRTN             FUNCTION DAY-OF-INTEGER (JDN-Int).
MIGRTN     IF JDN-DDD < 1 or > 366
MIGRTN         MOVE 8 TO JDN-PKT-STATUS
MIGRTN         MOVE 'JDN-Julian Day Number was out of range'
MIGRTN             TO JDN-PKT-STATUS-TEXT.
    
       JDN-Acc-Int-Of-Date. 
           MOVE JDN-Con-IntOfDate      TO JDN-Pkt-Action.   
    
           IF  (JDN-CC NOT NUMERIC) 
           OR  (JDN-CC = 0)                                             CH-001  
               PERFORM JDN-Acc-CC-Inferred  
MIGRTN*        PERFORM JDN-Acc-Call 
MIGRTN         COMPUTE JDN-Int =
MIGRTN                 FUNCTION INTEGER-OF-DATE (JDN-YYYYMMDD)
               MOVE 0                  TO JDN-CC
           ELSE 
MIGRTN*        PERFORM JDN-Acc-Call.
MIGRTN         COMPUTE JDN-Int =
MIGRTN                 FUNCTION INTEGER-OF-DATE (JDN-YYYYMMDD).
    
       JDN-Acc-Int-Of-Day.  
           MOVE JDN-Con-IntOfDay       TO JDN-Pkt-Action.   
    
           IF  (JDN-CC NOT NUMERIC) 
           OR  (JDN-CC = 0)                                             CH-001  
               PERFORM JDN-Acc-CC-Inferred  
MIGRTN*        PERFORM JDN-Acc-Call 
MIGRTN         COMPUTE JDN-Int =
MIGRTN                 FUNCTION INTEGER-OF-DAY (JDN-YYYYDDD)
               MOVE 0                  TO JDN-CC
MIGRTN         PERFORM CHECK-DAY-INT
           ELSE 
MIGRTN*        PERFORM JDN-Acc-Call.
MIGRTN         COMPUTE JDN-Int =
MIGRTN                 FUNCTION INTEGER-OF-DAY (JDN-YYYYDDD)
MIGRTN         PERFORM CHECK-DAY-INT.

MIGRTN CHECK-DAY-INT.
MIGRTN     IF JDN-DDD < 1 or > 366
MIGRTN         MOVE 8 TO JDN-PKT-STATUS
MIGRTN         MOVE 'JDN-Julian Day Number was out of range'
MIGRTN             TO JDN-PKT-STATUS-TEXT.

    
      *    IMPORTANT!:  PERFORM the following paragraph before using
      *    **ANY** of the previous paragraphs in a self-initializing
      *    transaction! 
    
       JDN-Acc-Self-Init.   
MIGRTN*    MOVE LOW-VALUES             TO JDN-Packet.   
MIGRTN     INITIALIZE                     JDN-Packet.
    
      *    The following are "To" versions that use the "Of" versions.  
      *    Don't use them on purpose.  (Why incur the extra overhead
      *    of an extra PERFORM?)
      * 
      *    They are provided just in case someone misreads their name   
      *    and codes the wrong name.  The official versions are the 
      *    "Of" names, of course, because their names correspond to 
      *    those of the new COBOL-85 intrinsic functions.   
    
       JDN-Acc-Date-To-Int. 
           PERFORM JDN-Acc-Int-Of-Date. 
    
       JDN-Acc-Day-To-Int.  
           PERFORM JDN-Acc-Int-Of-Day.  
    
       JDN-Acc-Int-To-Date. 
           PERFORM JDN-Acc-Date-Of-Int. 
    
       JDN-Acc-Int-To-Day.  
           PERFORM JDN-Acc-Day-Of-Int.  
    
       JDN-Acc-Exit.
           EXIT.
 END  *
