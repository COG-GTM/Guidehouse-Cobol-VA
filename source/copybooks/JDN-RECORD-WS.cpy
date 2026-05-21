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
      * This proc defines a data record used to emulate the following * 
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
      * CH-000 030194               931115 Initial implementation     * 
      ***************************************************************** 
    
      *** JDN-RECORD-WS.cpy COPYBOOK 
      *** FROM JDNRECORDWS.txt UNISYS PROC 
      / 
       01  JDN-Record.  
    
      *    Part 1 of JDN-Record (display formats).  
      * 
      *    Easy-to-remember convention:  Fields containing CC, YY, MM,  
      *    DD and DDD in their name are numeric.  Date and Day are not. 
      *    Also, since COBOL's DATE and DAY do not include century, use 
      *    one of the following:
      * 
      *        MOVE   0                TO   JDN-CC. 
      *        ACCEPT JDN-YYMMDD       FROM DATE.   
      *    or   
      *        MOVE   0                TO   JDN-CC. 
      *        ACCEPT JDN-YYDDD        FROM DAY.
      * 
      *    If you do that, JDN-Acc-Int-Of-Date and JDN-Acc-Int-Of-Day   
      *    will infer century based on YY and the birthdate of the TST. 
      *    Moreover, unless you yourself stuff 19 or 20 into JDN-CC, or 
      *    if you call JDN-Acc-Date-Of-Int or JDN-Acc-Day-Of-Int (which 
      *    return a value in JDN-CC), Int-Of-Date and Int-Of-Day will   
      *    continue to keep 0 in JDN-CC and continue to infer century.  
    
word
alignd     05  JDN-Date.
               10  JDN-CC              PIC 9(02).   
               10  JDN-YYMMDD          PIC 9(06).   
               10  JDN-Filler1         REDEFINES JDN-YYMMDD.
                   15  JDN-YY          PIC 9(02).   
                   15  JDN-MM          PIC 9(02).   
                   15  JDN-DD          PIC 9(02).   
           05  JDN-CCYYMMDD            REDEFINES JDN-Date PIC 9(08).
           05  JDN-YYYYMMDD            REDEFINES JDN-Date PIC 9(08).
word
alignd     05  JDN-Filler2             REDEFINES JDN-Date.  
               10  JDN-Day. 
                   15  JDN-CCYY        PIC 9(04).   
                   15  JDN-YYYY        REDEFINES JDN-CCYY PIC 9(04).
                   15  JDN-DDD         PIC 9(03).   
               10  JDN-CCYYDDD         REDEFINES JDN-Day  PIC 9(07).
               10  JDN-YYYYDDD         REDEFINES JDN-Day  PIC 9(07).
               10  JDN-Filler3         REDEFINES JDN-Day.   
                   15  FILLER          PIC X(02).   
                   15  JDN-YYDDD       PIC 9(05).   
               10  FILLER              PIC X(01).   
    
      *    Part 2 of JDN-Record (number of days since 12/31/1600 AD):   
word
MIGRTN*    05  JDN-Int                 PIC 1(36).   
MIGRTN*** NOTE:  JDN-Int must be PIC 9(7) to handle USNO offset value.
MIGRTN     05  JDN-Int                 PIC 9(07).
    
 END  *
