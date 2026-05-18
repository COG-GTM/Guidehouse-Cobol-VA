# Source Inventory

## Primary Programs

| Asset | Type | Role |
| --- | --- | --- |
| `source/cobol/LABA05.cbl` | COBOL | Fiscal-year reset job for JV control number. |
| `source/procobol/LABD20.pco` | Pro*COBOL | Daily JV comment ingestion and submitted-comment table load. |
| `source/procobol/DBIO.pco` | Pro*COBOL | Generic DB dispatcher and Oracle connection/transaction wrapper. |
| `source/procobol/CONTROL-RECORD-TABLE-IO.pco` | Pro*COBOL | Table-specific Oracle CRUD module for `CONTROL_RECORD_TABLE`. |

## Copybooks

| Asset | Notes |
| --- | --- |
| `COMCON.cpy` | Common configuration copied by `LABD20`. |
| `DBVAR.cpy` | DB linkage structure used by DBIO callers. |
| `DMCA.cpy`, `DMCAERR.cpy` | Database error fields/routine. |
| `JV-CONTROL-REC.cpy` | Legacy JV control record layout. |
| `CONTROL-RECORD-TABLE.cpy` | Oracle-backed control-record table layout. |
| `RDMS-ERR-WS.cpy`, `RDMS-ERR-RTN.cpy` | SQL/RDBMS error working storage and routine. |

## Support Files

| Asset | Type | Notes |
| --- | --- | --- |
| `source/perl/LABA05.pl` | Perl | Execution wrapper for `LABA05`. |
| `source/perl/LABD20-JV.pl` | Perl | Execution wrapper for `LABD20`. |
| `test-data/DAILY.MM-DD-CCYY.ctl` | Control | Daily process date card/control input. |
| `test-data/TST.JVCMTS.dat` | Data | Supplied sample comment data file. |

## Database Artifacts

Table descriptions are in `database/descriptions/` for:

- `CONTROL_RECORD_TABLE`
- `JC_SUBMITTED_COMMENT_TBL`
- `JC_APPLIED_COMMENT_TBL`
- `JC_REJECTED_COMMENT_TBL`
- `JC_COUNT_TBL`
