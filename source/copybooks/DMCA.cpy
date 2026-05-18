      *** COPYBOOK DMCA.
      *** ALSO REPLACES COPYBOOKS DB-DMCA AND DB-DMCA-DUMMY.
       01  DMCA.             
           02  COMMAND-SEQ-NUM         PIC 9(02)     VALUE  0.
           02  QUICK-BEF-LOOKS         PIC 9(1)      VALUE  0.
           02  FILLER                  PIC 9(1)      VALUE  0.
           02  IMPART-DEPART           PIC X(1)      VALUE '0'.
               88  NO-IMPART-DEPART                  VALUE '0'.
               88  IMPART-EXECUTED                   VALUE '1'.
               88  DEPART-EXECUTED                   VALUE '2'.
           02  RESERVED-WORD-AREA.
               03  AREA-NAME           PIC X(12).
               03  AREA-KEY.
                   04  PAGE-NUM        PIC 9(02).
                   04  RECORD-NUM      PIC 9(02).
               03  RECORD-NAME         PIC X(30).
               03  FILLER              PIC X(2)      VALUE LOW-VALUES.
               03  SET-NAME            PIC X(30).
               03  FILLER              PIC X(2)      VALUE LOW-VALUES.
               03  PRIORITY     BINARY PIC 9(10)     VALUE 0000000000.
               03  DATABASE-KEY        PIC X(18).
               03  DATABASE-TABLE      PIC X(30).
               03  CURRENT-AREA-NAME   PIC X(12).
               03  CURRENT-AREA-KEY.
                   04  PAGE-NUM        PIC 9(02).
                   04  RECORD-NUM      PIC 9(02).
               03  ERROR-AREA          PIC X(12).
               03  ERROR-RECORD        PIC X(30).
               03  FILLER              PIC X(2)      VALUE LOW-VALUES.
               03  ERROR-SET           PIC X(30).
               03  FILLER              PIC X(2)      VALUE LOW-VALUES.
               03  ERROR-STATUS.
                   04  RB-ERROR-CODE   PIC X(2).
                       88  RB-DEADLOCK               VALUE '02'.
                   04 ERROR-FUNCTION   PIC X(2).
                      88  DMS-DELETE                 VALUE '02'.
                      88  DMS-FIND-FETCH             VALUE '03'.
                      88  DMS-MODIFY                 VALUE '08'.
                      88  DMS-STORE                  VALUE '12'.
MIGRTN*            04 ERROR-CODE       PIC X(2)      VALUE '21'.
MIGRTN             04 ERROR-CODE       PIC X(2)      VALUE '00'.
               03  FILLER              PIC X(2)      VALUE LOW-VALUE.
MIGRTN*        03  ERROR-NUM           PIC X(4)      VALUE '0021'.
MIGRTN         03  ERROR-NUM           PIC X(4)      VALUE '0000'.
                   88  DMS-OK                        VALUE '0000'.
                   88  DMS-AREA-NOT-OPEN             VALUE '0001'.
                   88  DMS-DUP-KEY                   VALUE '0005'.
                   88  DMS-END-OF-SET                VALUE '0007'.
                   88  DMS-NOT-FOUND                 VALUE '0013'.
                   88  DMS-NO-IMPART                 VALUE '0021'.
                   88  DMS-AREA-ALREADY-OPEN         VALUE '0028'.
                   88  DMS-INVALID-PAGE-REC-NUM   VALUES '0035' '0036'.
                   88  DMS-INSUFFICIENT-SPACE     VALUES '0084' '0096'.
           02  IO-ERROR-STATUS  BINARY PIC 9(5).
           02  QUEUE-ERR-STATUS BINARY PIC 9(5).
           02  FILLER                  PIC 9(04).
           02  FILLER                  PIC 9(04).
           02  RUN-UNIT-ID             PIC 9(04).
           02  FILLER                  PIC S9(04).
           02  FAC-REJ-ERROR-STATUS    PIC 9         OCCURS 36 TIMES.
           02  DMR-LEV-NUM             PIC X(8).
           02  DMR-MODE                PIC 9(04)     VALUE 0.
           02  CALC-PRIME-PG           PIC 9(02)     VALUE 0.
           02  CALC-BUCKET      BINARY PIC 9(05)     VALUE 0.
           02  CURRENT-DB-KEY          PIC X(18)     VALUE SPACES.
           02  CURRENT-DB-TABLE        PIC X(30)     VALUE SPACES.
           02  FILLER           BINARY PIC 9(5)      VALUE 71.
           02  FILLER           BINARY PIC 9(5)      VALUE 84.
           02  NUM-ERROR-ITEMS  BINARY PIC 9(5)      VALUE 0.
           02  ERR-ITEM-SIZE    BINARY PIC 9(5)      VALUE 8.
           02  RUN-UNIT-STATISTICS.
               03  COMMAND-STATISTICS  USAGE IS BINARY.
                   04 CLOSE-COUNT      PIC 9(5).
                   04 DELETE-COUNT     PIC 9(5).
                   04 FIND-COUNT       PIC 9(5).
                   04 FREE-COUNT       PIC 9(5).
                   04 GET-COUNT        PIC 9(5).
                   04 KEEP-COUNT       PIC 9(5).
                   04 INSERT-COUNT     PIC 9(5).
                   04 MODIFY-COUNT     PIC 9(5).
                   04 OPEN-COUNT       PIC 9(5).
                   04 FILLER           PIC 9(5)      VALUE IS ZERO.
                   04 REMOVE-COUNT     PIC 9(5).
                   04 STORE-COUNT      PIC 9(5).
                   04 DEPART-COUNT     PIC 9(5).
                   04 IF-COUNT         PIC 9(5).
                   04 IMPART-COUNT     PIC 9(5).
                   04 MOVE-COUNT       PIC 9(5).
                   04 LOG-COUNT        PIC 9(5).
                   04 FILLER           PIC 9(5)      VALUE ZERO.
                   04 ACQUIRE-COUNT    PIC 9(5).
                   04 FILLER           PIC 9(5)      VALUE ZERO.
                   04 FILLER           PIC 9(10)     VALUE ZERO.
                   04 FILLER           PIC 9(10)     VALUE ZERO.
                   04 FILLER           PIC 9(5)      VALUE ZERO.
                   04 FILLER           PIC 9(5)      VALUE ZERO.
               03  QUEUE-STATISTICS    USAGE IS BINARY.
                   04 TABLE-COUNT      PIC 9(5).
                   04 PAGE-COUNT       PIC 9(5).
                   04 AREA-COUNT       PIC 9(5).
                   04 LRI-COUNT        PIC 9(5).
                   04 TRL-COUNT        PIC 9(5).
                   04 USAGE-LOCK-COUNT PIC 9(5).
                   04 I-O-COUNT        PIC 9(5).
                   04 CORE-LOCK-COUNT  PIC 9(5).
                   04 CURRENT-LOCK-COUNT     PIC 9(5).
                   04 CORE-ALLOCATION-COUNT  PIC 9(5).
                   04 ROLLBACK-BUFFER-COUNT  PIC 9(5).
                   04 TIP-PAGE-COUNT   PIC 9(5).
                   04 OVERLAY-COUNT    PIC 9(5).
                   04 SEGMENT-COUNT    PIC 9(5).
                   04 CURRENT-LOCK-COUNT2    PIC 9(5).
                   04 USAGE-LOCK-COUNT2      PIC 9(5).
                   04 CHECKPOINT-COUNT PIC 9(5).
                   04 QUEUE-CNT-DOWN   PIC 9(5).
                   04 FILLER           PIC 9(5)      VALUE ZERO.
               03  FILLER              PIC X(30)     VALUE ZERO.
 END  *
