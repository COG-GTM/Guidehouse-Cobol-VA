       01  DB-TABLE-NAME                     PIC X(30)   VALUE SPACES.
       01  DB-DMSREC-NAME REDEFINES DB-TABLE-NAME  PIC X(30).
       01  DB-FUNCTION                       PIC X(20)   VALUE SPACES.
       01  DB-FUNCTION-TYPE                  PIC X(20)   VALUE SPACES.
       01  DB-SET-NAME                       PIC X(30)   VALUE SPACES.
       01  DB-DATA                           PIC X(2100)  VALUE SPACES.
       01  DB-ROWID                          PIC X(18)   VALUE SPACES.
       01  DB-MISC                           PIC X(50)   VALUE SPACES.
       01  FILLER  REDEFINES DB-MISC.
           05  DB-AREA-NAME                  PIC X(12).
           05  FILLER                        PIC X(38).
       01  DB-RETURN-CODE.
      *** ORACLE RETURN CODE                                        ***
           05  DB-SQLCODE-NUM                PIC S9(9) BINARY VALUE +0.
             88  DB-OK                         VALUE  +0.
             88  DB-NOT-FND                    VALUES +1403 +100.
             88  DB-DUP-REC                    VALUE -0001.
             88  DB-DEADLOCK                   VALUE -0060.
             88  DB-NULL-FETCH                 VALUE -1405.
      *** TRANSLATION OF SQLCODE INTO RETURN CODE FROM DMS2200      ***
           05  DB-RTNCODE-DMS                PIC X(4).
       01  DB-MESSAGE                        PIC X(80)   VALUE SPACES.
       01  DB-SQLCODE-DISP                   PIC S9(9).

*
