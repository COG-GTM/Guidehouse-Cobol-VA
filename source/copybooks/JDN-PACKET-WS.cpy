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
      * This proc defines a packet used to emulate the following      * 
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
    
      *** JDN-PACKET-WS.cpy COPYBOOK 
      *** FROM JDNPACKETWS.txt UNISYS PROC 
    
       01  JDN-Packet.  
    
MIGRTN*    05  JDN-Pkt-Action          PIC 1(09).   
MIGRTN     05  JDN-Pkt-Action          PIC 9(1).   
           05  JDN-Pkt-Flags.   
MIGRTN*        10  JDN-Pkt-AllowOvDD   PIC 1(01).   
MIGRTN         10  JDN-Pkt-AllowOvDD   PIC 9(1).   
MIGRTN*        10  JDN-Pkt-AllowOvDDD  PIC 1(01).   
MIGRTN         10  JDN-Pkt-AllowOvDDD  PIC 9(1).   
MIGRTN*        10  JDN-Pkt-AllowOvInt  PIC 1(01).   
MIGRTN         10  JDN-Pkt-AllowOvInt  PIC 9(1).   
MIGRTN*        10  JDN-Pkt-AllowOvMM   PIC 1(01).   
MIGRTN         10  JDN-Pkt-AllowOvMM   PIC 9(1).   
MIGRTN*        10  JDN-Pkt-AllowOvYYYY PIC 1(01).   
MIGRTN         10  JDN-Pkt-AllowOvYYYY PIC 9(1).   
MIGRTN*        10  FILLER              PIC 1(04).   
MIGRTN*    05  FILLER                  PIC X(02).   
MIGRTN*    05  JDN-Pkt-LY              PIC 1(09).   
MIGRTN     05  JDN-Pkt-LY              PIC 9(1).   
MIGRTN*    05  JDN-Pkt-Status          PIC 1(09).   
MIGRTN     05  JDN-Pkt-Status          PIC 9(1).   
           05  JDN-Pkt-Status-Text     PIC X(78).   
           05  JDN-Pkt-Reserved        PIC X(80).   
 END  *
