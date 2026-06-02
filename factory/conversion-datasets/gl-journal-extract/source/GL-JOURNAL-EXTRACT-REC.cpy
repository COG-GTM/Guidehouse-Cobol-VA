      *>***************************************************************
      *> GL-JOURNAL-EXTRACT-REC.cpy
      *>
      *> Fixed-width record layout for the nightly general-ledger /
      *> journal-voucher (JV) extract produced by the legacy VA core
      *> financial system (FMS) for downstream posting.
      *>
      *> STATUS: SYNTHETIC / REFERENCE LAYOUT.
      *>   This copybook is NOT a customer-supplied artifact. It is a
      *>   plausible reconstruction built to exercise the Integration &
      *>   Conversion Factory end-to-end on GL/journal data. The real VA
      *>   FMS GL extract layout is one of the artifacts we are asking the
      *>   customer to provide (see docs/va-fmbt-open-questions.md, Q-GL-1).
      *>
      *> Record length: 200 bytes, line-sequential, EBCDIC->ASCII landed.
      *> One physical record == one GL posting line. A balanced journal
      *> voucher is the set of lines sharing the same JV-NUMBER within a
      *> fiscal year / accounting period.
      *>***************************************************************
       01  GL-JOURNAL-EXTRACT-REC.
           05  GLX-FISCAL-YEAR          PIC 9(04).
      *>       Government fiscal year, e.g. 2026.
           05  GLX-ACCT-PERIOD          PIC 9(02).
      *>       Accounting period 01-12 (plus 13/14 adjustment periods).
           05  GLX-JV-NUMBER            PIC 9(06).
      *>       Journal voucher number. Same generator family as LABA05
      *>       JV-NUMBER (resets to 1 at fiscal-year rollover).
           05  GLX-LINE-NO              PIC 9(03).
      *>       Sequence of the posting line within the voucher.
           05  GLX-POST-DATE-JUL        PIC 9(07).
      *>       Posting date in CCYYDDD Julian form (same convention the
      *>       DATECONV subsystem already ports; see source/cobol/DATECONV.cbl).
           05  GLX-TREASURY-SYMBOL      PIC X(20).
      *>       Treasury Appropriation Fund Symbol (TAFS), e.g.
      *>       '036-2026/2026-0160-000'. Right-padded with spaces.
           05  GLX-FUND                 PIC X(06).
      *>       Internal legacy fund code.
           05  GLX-COST-CENTER          PIC X(08).
      *>       Cost center / organization code.
           05  GLX-USSGL-ACCT           PIC 9(06).
      *>       U.S. Standard General Ledger account, e.g. 480100.
           05  GLX-BUDGET-OBJ-CLASS     PIC X(04).
      *>       Object class code (OMB Circular A-11), e.g. '2520'.
           05  GLX-DR-CR-IND            PIC X(01).
      *>       'D' debit, 'C' credit. Drives sign on the canonical side.
           05  GLX-AMOUNT               PIC 9(13)V99.
      *>       Posting amount, always positive here; sign is carried by
      *>       GLX-DR-CR-IND. Implied 2 decimal places (no decimal point
      *>       in the byte stream).
           05  GLX-VENDOR-ID            PIC X(09).
      *>       Vendor / customer id where applicable; spaces otherwise.
           05  GLX-DESCRIPTION          PIC X(40).
      *>       Free-text line description. Right-padded with spaces.
           05  GLX-FILLER               PIC X(69).
      *>       Reserved. Present so the record length is a stable 200.
      *>***************************************************************
      *> Byte map (1-based, inclusive):
      *>   FISCAL-YEAR        001-004
      *>   ACCT-PERIOD        005-006
      *>   JV-NUMBER          007-012
      *>   LINE-NO            013-015
      *>   POST-DATE-JUL      016-022
      *>   TREASURY-SYMBOL    023-042
      *>   FUND               043-048
      *>   COST-CENTER        049-056
      *>   USSGL-ACCT         057-062
      *>   BUDGET-OBJ-CLASS   063-066
      *>   DR-CR-IND          067-067
      *>   AMOUNT             068-082   (15 digits: 13 int + 2 implied dec)
      *>   VENDOR-ID          083-091
      *>   DESCRIPTION        092-131
      *>   FILLER             132-200
      *>   (record length is exactly 200 bytes)
      *>***************************************************************
