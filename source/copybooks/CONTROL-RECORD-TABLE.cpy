      *** CONTROL-RECORD-TABLE COPYBOOK FOR DMS DIRECT RECORDS
      *      
      *Control Record Name   Max Number  Data Length  Key
      *-------------------   ----------  -----------  ---
      *CPC-CONTROL-REC           1           80        1
      *CPC-REGION-REC           11           72       Region Code, PIC 9(2)
      *DT-DIRECTORY-REC          2          114        1 or 2
      *FO-NAME-KEY-REC           0            4       None
      *GLP-CONTROL-REC           1           60        1
      *JV-CONTROL-REC            1           55        1
      *LAA-CONTROL-REC           1          136        1
      *PID-RECORD             5469          400       PID (Term ID), PIC 9(4)
      *PMC-AMS-CTL-REC           1           24        1
      *PMD-ACH-CONTROL-REC       1           44        1
      *PMI-DMF-REC               0           48       None
      *SBIC-CONTROL-REC          1          200        1
      *SS-MATRIX-REC             1          400        1
      *TRANSACTION-CONTROL-REC   1           64        1
      *1175-OFFICE-REC          57           59       ofc regn code, PIC 9(4)
      *                                                   = regn cd + ofc cd

      

       01  CONTROL-RECORD-TABLE  EXTERNAL.
           05  CONTROL-RECORD-NAME           PIC X(30).
           05  CONTROL-RECORD-NUMBER         PIC 9(04).
           05  CONTROL-RECORD-DATA           PIC X(400).

MIGRTN 01  0-CURRENCY-STATUS EXTERNAL.
MIGRTN     05  0-ROWID                       PIC X(18).
