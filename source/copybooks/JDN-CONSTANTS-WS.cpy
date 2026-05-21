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
      * This proc defines constants used to emulate the following     * 
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
      * defined here in JDN-CONSTANTS-WS.                             * 
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
    
      *** JDN-CONSTANTS-WS.cpy COPYBOOK 
      *** FROM JDNCONSTANTS.txt UNISYS PROC 
      / 
       01  JDN-Constants.   
word
alignd  02  JDN-Con-Action-Codes.   
MIGRTN*    05  JDN-Con-DateOfInt       PIC 1(09) VALUE 1.   
MIGRTN     05  JDN-Con-DateOfInt       PIC 9(1) VALUE 1.   
MIGRTN*    05  JDN-Con-DayOfInt        PIC 1(09) VALUE 2.   
MIGRTN     05  JDN-Con-DayOfInt        PIC 9(1) VALUE 2.   
MIGRTN*    05  JDN-Con-IntOfDate       PIC 1(09) VALUE 3.   
MIGRTN     05  JDN-Con-IntOfDate       PIC 9(1) VALUE 3.   
MIGRTN*    05  JDN-Con-IntOfDay        PIC 1(09) VALUE 4.   
MIGRTN     05  JDN-Con-IntOfDay        PIC 9(1) VALUE 4.   
word
alignd  02  JDN-Con-Status-Codes.   
MIGRTN*    05  JDN-Con-NoErr           PIC 1(09) VALUE 0.   
MIGRTN     05  JDN-Con-NoErr           PIC 9(1) VALUE 0.   
MIGRTN*    05  JDN-Con-BadAction       PIC 1(09) VALUE 1.   
MIGRTN     05  JDN-Con-BadAction       PIC 9(1) VALUE 1.   
MIGRTN*    05  JDN-Con-NonNumericDD    PIC 1(09) VALUE 2.   
MIGRTN     05  JDN-Con-NonNumericDD    PIC 9(1) VALUE 2.   
MIGRTN*    05  JDN-Con-NonNumericDDD   PIC 1(09) VALUE 3.   
MIGRTN     05  JDN-Con-NonNumericDDD   PIC 9(1) VALUE 3.   
MIGRTN*    05  JDN-Con-NonNumericMM    PIC 1(09) VALUE 4.   
MIGRTN     05  JDN-Con-NonNumericMM    PIC 9(1) VALUE 4.   
MIGRTN*    05  JDN-Con-NonNumericYYYY  PIC 1(09) VALUE 5.   
MIGRTN     05  JDN-Con-NonNumericYYYY  PIC 9(1) VALUE 5.   
MIGRTN*    05  JDN-Con-NotImplemented  PIC 1(09) VALUE 6.   
MIGRTN     05  JDN-Con-NotImplemented  PIC 9(1) VALUE 6.   
MIGRTN*    05  JDN-Con-OutOfRangeDD    PIC 1(09) VALUE 7.   
MIGRTN     05  JDN-Con-OutOfRangeDD    PIC 9(1) VALUE 7.   
MIGRTN*    05  JDN-Con-OutOfRangeDDD   PIC 1(09) VALUE 8.   
MIGRTN     05  JDN-Con-OutOfRangeDDD   PIC 9(1) VALUE 8.   
MIGRTN*    05  JDN-Con-OutOfRangeInt   PIC 1(09) VALUE 9.   
MIGRTN     05  JDN-Con-OutOfRangeInt   PIC 9(1) VALUE 9.   
MIGRTN*    05  JDN-Con-OutOfRangeMM    PIC 1(09) VALUE 10.  
MIGRTN     05  JDN-Con-OutOfRangeMM    PIC 9(2) VALUE 10.  
MIGRTN*    05  JDN-Con-OutOfRangeYYYY  PIC 1(09) VALUE 11.  
MIGRTN     05  JDN-Con-OutOfRangeYYYY  PIC 9(2) VALUE 11.  
MIGRTN*    05  JDN-Con-Strange         PIC 1(09) VALUE 12.  
MIGRTN     05  JDN-Con-Strange         PIC 9(2) VALUE 12.  
MIGRTN*    05  FILLER                  PIC 1(27) VALUE 0.   
MIGRTN*    05  FILLER                  PIC 9(03) VALUE 0.   
word
alignd  02  JDN-Con-Year-Type-Codes.
MIGRTN*    05  JDN-Con-YearTypeUnknown PIC 1(09) VALUE 0.   
MIGRTN     05  JDN-Con-YearTypeUnknown PIC 9(1) VALUE 0.   
MIGRTN*    05  JDN-Con-Leap            PIC 1(09) VALUE 1.   
MIGRTN     05  JDN-Con-Leap            PIC 9(1) VALUE 1.   
MIGRTN*    05  JDN-Con-NotLeap         PIC 1(09) VALUE 2.   
MIGRTN     05  JDN-Con-NotLeap         PIC 9(1) VALUE 2.   
MIGRTN*    05  FILLER                  PIC 1(09).   
MIGRTN*    05  FILLER                  PIC 9(1).   
word
alignd  02  JDN-Con-Misc.   
MIGRTN*    05  JDN-Con-USNO-Offset     PIC 1(36) VALUE 2305813. 
MIGRTN     05  JDN-Con-USNO-Offset     PIC 9(07) VALUE 2305813. 
 END  *
