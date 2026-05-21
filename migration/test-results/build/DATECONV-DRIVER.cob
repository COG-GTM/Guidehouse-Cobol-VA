       IDENTIFICATION DIVISION.
       PROGRAM-ID. DATECONV-DRIVER.
      *****************************************************************
      * GnuCOBOL parity-harness driver for the customer's DATECONV
      * subprogram (source/cobol/DATECONV.cbl).
      *
      * Reads pipe-delimited test vectors from STDIN, populates the
      * CONV-DATES linkage record exactly as defined in DATECONV-WS.cpy,
      * CALLs 'DATECONV', then writes a pipe-delimited result line to
      * STDOUT for every input vector.
      *
      * INPUT line  (15 fields, '|' separated, trailing fields optional):
      *   ABORT|FUNC|FROM_INT|FROM_JUL|FROM_CYMD|FROM_YMD|FROM_MDY|
      *   MONTHS|BETWEEN_JUL|BETWEEN_YMD|
      *   TO_INT|TO_JUL|TO_CYMD|TO_YMD|TO_MDY
      *
      * The trailing TO_* fields exist because DIF-* and RANGE-*
      * functions read both FROM-* and TO-* from CONV-DATES as INPUT
      * (overwriting TO-INT-DT and DAYS-DIF as output).
      *
      * OUTPUT line (12 fields):
      *   FUNC|TO_INT|TO_JUL|TO_CYMD|TO_YMD|TO_MDCY|TO_MDY|
      *   DAYS_DIF|DAYS_DIF_UNSIGNED|DATE_ERR_IND|DATE_ERR_REASON|STATUS
      *
      * Lines whose first non-blank character is '#' are echoed as
      * '#' comment lines on STDOUT (no DATECONV call), which lets the
      * Python diff harness keep section headers aligned.
      *****************************************************************
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT IN-FILE ASSIGN TO "/dev/stdin"
                  ORGANIZATION IS LINE SEQUENTIAL
                  FILE STATUS IS WS-IN-STAT.
           SELECT OUT-FILE ASSIGN TO "/dev/stdout"
                  ORGANIZATION IS LINE SEQUENTIAL
                  FILE STATUS IS WS-OUT-STAT.

       DATA DIVISION.
       FILE SECTION.
       FD  IN-FILE.
       01  IN-REC                       PIC X(400).
       FD  OUT-FILE.
       01  OUT-REC                      PIC X(400).

       WORKING-STORAGE SECTION.
       01  WS-IN-STAT                   PIC XX.
       01  WS-OUT-STAT                  PIC XX.
       01  WS-EOF-FLAG                  PIC X VALUE 'N'.
       01  WS-LINE-BUF                  PIC X(400).
       01  WS-FIELD-BUF                 PIC X(64).
       01  WS-FIELD-LEN                 PIC 9(4) COMP.
       01  WS-IDX                       PIC 9(4) COMP.
       01  WS-START                     PIC 9(4) COMP.
       01  WS-FIELD-NUM                 PIC 9(2) COMP.
       01  WS-LINE-LEN                  PIC 9(4) COMP.
       01  WS-OUT-LINE                  PIC X(400).
       01  WS-OUT-IDX                   PIC 9(4) COMP.
       01  WS-VECTOR-NUM                PIC 9(6) COMP VALUE 0.

      *  Numeric edited copies used to render output deterministically.
       01  WS-EDIT-FUNC                 PIC 9(2).
       01  WS-EDIT-INT                  PIC 9(10).
       01  WS-EDIT-JUL                  PIC 9(5).
       01  WS-EDIT-CYMD                 PIC 9(8).
       01  WS-EDIT-YMD                  PIC 9(6).
       01  WS-EDIT-MDCY                 PIC 9(8).
       01  WS-EDIT-MDY                  PIC 9(6).
       01  WS-EDIT-DAYS-DIF             PIC -(5)9.
       01  WS-EDIT-DAYS-UNS             PIC 9(5).
       01  WS-EDIT-REASON               PIC 9(2).

      *  CONV-DATES (driver-side mirror of DATECONV-WS.cpy)
       01  CONV-DATES.
           05  ABORT-ON-DATE-ERR        PIC X        VALUE 'N'.
           05  DATESUB-FUNC             PIC 9(2)     VALUE ZEROS.
           05  FROM-INT-DT              PIC 9(10) COMP VALUE ZEROS.
           05  FROM-JUL-DT              PIC 9(5)     VALUE ZEROS.
           05  FROM-CYMD-DT             PIC 9(8)     VALUE ZEROS.
           05  FROM-YMD-DT              PIC 9(6)     VALUE ZEROS.
           05  FROM-MDY-DT              PIC 9(6)     VALUE ZEROS.
           05  MONTHS-TO-ADD            PIC S9(5)    VALUE ZEROS.
           05  BETWEEN-JUL-DT           PIC 9(5)     VALUE ZEROS.
           05  BETWEEN-YMD-DT           PIC 9(6)     VALUE ZEROS.
           05  TO-INT-DT                PIC 9(10) COMP VALUE ZEROS.
           05  TO-JUL-DT                PIC 9(5)     VALUE ZEROS.
           05  TO-CYMD-DT               PIC 9(8)     VALUE ZEROS.
           05  TO-YMD-DT                PIC 9(6)     VALUE ZEROS.
           05  TO-MDCY-DT               PIC 9(8)     VALUE ZEROS.
           05  TO-MDY-DT                PIC 9(6)     VALUE ZEROS.
           05  DAYS-DIF                 PIC S9(5)    VALUE ZEROS.
           05  DAYS-DIF-UNSIGNED        PIC 9(5)     VALUE ZEROS.
           05  DATE-ERR-IND             PIC X        VALUE 'N'.
           05  DATE-ERR-REASON          PIC 9(2) COMP VALUE ZEROS.

       PROCEDURE DIVISION.

       MAIN SECTION.
       MAIN-START.
           OPEN INPUT IN-FILE
                OUTPUT OUT-FILE.
           PERFORM READ-LOOP UNTIL WS-EOF-FLAG = 'Y'.
           CLOSE IN-FILE OUT-FILE.
           STOP RUN.

       READ-LOOP.
           READ IN-FILE INTO WS-LINE-BUF
                AT END
                    MOVE 'Y' TO WS-EOF-FLAG
                NOT AT END
                    PERFORM HANDLE-LINE
           END-READ.

       HANDLE-LINE.
      *    Skip comment lines / blanks (echo as comments).
           IF WS-LINE-BUF(1:1) = '#' OR WS-LINE-BUF = SPACES
               MOVE WS-LINE-BUF TO OUT-REC
               WRITE OUT-REC
               EXIT PARAGRAPH
           END-IF.
           ADD 1 TO WS-VECTOR-NUM.
           PERFORM RESET-CONV-DATES.
           PERFORM PARSE-VECTOR.
           CALL 'DATECONV' USING CONV-DATES.
           PERFORM EMIT-RESULT.

       RESET-CONV-DATES.
           MOVE 'N'  TO ABORT-ON-DATE-ERR.
           MOVE ZERO TO DATESUB-FUNC FROM-INT-DT FROM-JUL-DT
                        FROM-CYMD-DT FROM-YMD-DT FROM-MDY-DT
                        BETWEEN-JUL-DT BETWEEN-YMD-DT
                        TO-INT-DT TO-JUL-DT TO-CYMD-DT
                        TO-YMD-DT TO-MDCY-DT TO-MDY-DT
                        DAYS-DIF-UNSIGNED DATE-ERR-REASON.
           MOVE ZERO TO MONTHS-TO-ADD DAYS-DIF.
           MOVE 'N'  TO DATE-ERR-IND.

       PARSE-VECTOR.
      *    Compute effective line length (FUNCTION TRIM in COBOL/2014
      *    returns the leading/trailing-trim slice; we want the length
      *    of the right-trimmed content).
           MOVE 0 TO WS-LINE-LEN.
           INSPECT FUNCTION REVERSE(WS-LINE-BUF) TALLYING
                   WS-LINE-LEN FOR LEADING SPACES.
           COMPUTE WS-LINE-LEN = LENGTH OF WS-LINE-BUF - WS-LINE-LEN.
           MOVE 0 TO WS-FIELD-NUM.
           MOVE 1 TO WS-START.
           MOVE 1 TO WS-IDX.
           PERFORM UNTIL WS-IDX > WS-LINE-LEN
               IF WS-LINE-BUF(WS-IDX:1) = '|'
                   PERFORM EMIT-FIELD
                   ADD 1 TO WS-IDX
                   MOVE WS-IDX TO WS-START
               ELSE
                   ADD 1 TO WS-IDX
               END-IF
           END-PERFORM.
           PERFORM EMIT-FIELD.

       EMIT-FIELD.
           COMPUTE WS-FIELD-LEN = WS-IDX - WS-START.
           MOVE SPACES TO WS-FIELD-BUF.
           IF WS-FIELD-LEN > 0
               IF WS-FIELD-LEN > LENGTH OF WS-FIELD-BUF
                   MOVE LENGTH OF WS-FIELD-BUF TO WS-FIELD-LEN
               END-IF
               MOVE WS-LINE-BUF(WS-START:WS-FIELD-LEN) TO WS-FIELD-BUF
           END-IF.
           ADD 1 TO WS-FIELD-NUM.
           PERFORM ASSIGN-FIELD.

       ASSIGN-FIELD.
      *    FUNCTION NUMVAL is tolerant of leading/trailing spaces, so
      *    we only need to skip the case where the entire field is
      *    blank.
           EVALUATE WS-FIELD-NUM
               WHEN 1
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE WS-FIELD-BUF(1:1) TO ABORT-ON-DATE-ERR
                   END-IF
               WHEN 2
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO DATESUB-FUNC
                   END-IF
               WHEN 3
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO FROM-INT-DT
                   END-IF
               WHEN 4
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO FROM-JUL-DT
                   END-IF
               WHEN 5
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO FROM-CYMD-DT
                   END-IF
               WHEN 6
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO FROM-YMD-DT
                   END-IF
               WHEN 7
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO FROM-MDY-DT
                   END-IF
               WHEN 8
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO MONTHS-TO-ADD
                   END-IF
               WHEN 9
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO BETWEEN-JUL-DT
                   END-IF
               WHEN 10
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO BETWEEN-YMD-DT
                   END-IF
               WHEN 11
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO TO-INT-DT
                   END-IF
               WHEN 12
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO TO-JUL-DT
                   END-IF
               WHEN 13
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO TO-CYMD-DT
                   END-IF
               WHEN 14
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO TO-YMD-DT
                   END-IF
               WHEN 15
                   IF WS-FIELD-BUF NOT = SPACES
                       MOVE FUNCTION NUMVAL(WS-FIELD-BUF)
                                                   TO TO-MDY-DT
                   END-IF
               WHEN OTHER
                   CONTINUE
           END-EVALUATE.

       EMIT-RESULT.
           MOVE DATESUB-FUNC      TO WS-EDIT-FUNC.
           MOVE TO-INT-DT         TO WS-EDIT-INT.
           MOVE TO-JUL-DT         TO WS-EDIT-JUL.
           MOVE TO-CYMD-DT        TO WS-EDIT-CYMD.
           MOVE TO-YMD-DT         TO WS-EDIT-YMD.
           MOVE TO-MDCY-DT        TO WS-EDIT-MDCY.
           MOVE TO-MDY-DT         TO WS-EDIT-MDY.
           MOVE DAYS-DIF          TO WS-EDIT-DAYS-DIF.
           MOVE DAYS-DIF-UNSIGNED TO WS-EDIT-DAYS-UNS.
           MOVE DATE-ERR-REASON   TO WS-EDIT-REASON.

           STRING WS-EDIT-FUNC     DELIMITED BY SIZE  '|'
                  WS-EDIT-INT      DELIMITED BY SIZE  '|'
                  WS-EDIT-JUL      DELIMITED BY SIZE  '|'
                  WS-EDIT-CYMD     DELIMITED BY SIZE  '|'
                  WS-EDIT-YMD      DELIMITED BY SIZE  '|'
                  WS-EDIT-MDCY     DELIMITED BY SIZE  '|'
                  WS-EDIT-MDY      DELIMITED BY SIZE  '|'
                  WS-EDIT-DAYS-DIF DELIMITED BY SIZE  '|'
                  WS-EDIT-DAYS-UNS DELIMITED BY SIZE  '|'
                  DATE-ERR-IND     DELIMITED BY SIZE  '|'
                  WS-EDIT-REASON   DELIMITED BY SIZE  '|'
                  'OK'             DELIMITED BY SIZE
               INTO WS-OUT-LINE
           END-STRING.
           MOVE WS-OUT-LINE TO OUT-REC.
           WRITE OUT-REC.

       END PROGRAM DATECONV-DRIVER.
