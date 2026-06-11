      *>***************************************************************
      *> OBL-DISBURSEMENT-REC.cpy
      *>
      *> Fixed-width record layout for the obligation / disbursement
      *> activity extract produced by the legacy VA core financial
      *> system (FMS) for downstream posting into iFAMS / Momentum.
      *>
      *> STATUS: SYNTHETIC / REFERENCE LAYOUT.
      *>   This copybook is NOT a customer-supplied artifact. It is a
      *>   plausible reconstruction built to exercise the Integration &
      *>   Conversion Factory end-to-end on obligation/disbursement
      *>   activity. The real VA FMS obligation extract layout is one of
      *>   the artifacts we are asking the customer to provide (see
      *>   docs/va-fmbt-open-questions.md, Q-OBL-1 / Q-GL-1).
      *>
      *> Record length: 250 bytes, line-sequential, EBCDIC->ASCII landed.
      *> One physical record == one spending-chain event against an
      *> obligation: either the obligation itself (OBL-TXN-TYPE = 'O') or
      *> a disbursement applied to it (OBL-TXN-TYPE = 'D'). All events that
      *> share OBL-OBLIGATION-NO within a fiscal year form one obligation
      *> whose disbursements must not exceed the obligated amount.
      *>***************************************************************
       01  OBL-DISBURSEMENT-REC.
           05  OBL-FISCAL-YEAR          PIC 9(04).
      *>       Government fiscal year, e.g. 2026.
           05  OBL-ACCT-PERIOD          PIC 9(02).
      *>       Accounting period 01-12 (plus 13/14 adjustment periods).
           05  OBL-OBLIGATION-NO        PIC X(10).
      *>       Obligation / document number (PIIN-style, alphanumeric).
      *>       The natural key that ties disbursements to their obligation.
           05  OBL-LINE-NO              PIC 9(03).
      *>       Sequence of the event within the obligation document.
           05  OBL-TXN-TYPE             PIC X(01).
      *>       'O' = obligation establishment, 'D' = disbursement (outlay)
      *>       applied against the obligation. Drives which canonical
      *>       amount bucket the line lands in.
           05  OBL-VENDOR-ID            PIC X(09).
      *>       Vendor / payee id. Required for both obligations and
      *>       disbursements (no anonymous spend).
           05  OBL-TREASURY-SYMBOL      PIC X(20).
      *>       Treasury Appropriation Fund Symbol (TAFS), e.g.
      *>       '036-2026-0160-000'. Right-padded with spaces.
           05  OBL-APPROPRIATION        PIC X(06).
      *>       Internal legacy appropriation / fund code (crosswalked).
           05  OBL-OBJECT-CLASS         PIC X(04).
      *>       Object class code (OMB Circular A-11), e.g. '2520'.
           05  OBL-USSGL-ACCT           PIC 9(06).
      *>       U.S. Standard General Ledger account, e.g. 480100 for an
      *>       undelivered order, 490200 for a paid delivered order.
           05  OBL-AMOUNT               PIC 9(13)V99.
      *>       Event amount, always positive here. Implied 2 decimal
      *>       places (no decimal point in the byte stream). The sign /
      *>       bucket is carried by OBL-TXN-TYPE.
           05  OBL-POP-START-JUL        PIC 9(07).
      *>       Period-of-performance start in CCYYDDD Julian form (same
      *>       convention DATECONV ports; see source/cobol/DATECONV.cbl).
           05  OBL-POP-END-JUL          PIC 9(07).
      *>       Period-of-performance end in CCYYDDD Julian form. Must be
      *>       on or after OBL-POP-START-JUL.
           05  OBL-TXN-DATE-JUL         PIC 9(07).
      *>       Event date (obligation date or disbursement date) CCYYDDD.
           05  OBL-DESCRIPTION          PIC X(40).
      *>       Free-text line description. Right-padded with spaces.
           05  OBL-FILLER               PIC X(109).
      *>       Reserved. Present so the record length is a stable 250.
      *>***************************************************************
      *> Byte map (1-based, inclusive):
      *>   FISCAL-YEAR        001-004
      *>   ACCT-PERIOD        005-006
      *>   OBLIGATION-NO      007-016
      *>   LINE-NO            017-019
      *>   TXN-TYPE           020-020
      *>   VENDOR-ID          021-029
      *>   TREASURY-SYMBOL    030-049
      *>   APPROPRIATION      050-055
      *>   OBJECT-CLASS       056-059
      *>   USSGL-ACCT         060-065
      *>   AMOUNT             066-080   (15 digits: 13 int + 2 implied dec)
      *>   POP-START-JUL      081-087
      *>   POP-END-JUL        088-094
      *>   TXN-DATE-JUL       095-101
      *>   DESCRIPTION        102-141
      *>   FILLER             142-250
      *>   (record length is exactly 250 bytes)
      *>***************************************************************
