# Source Inventory

## Primary Programs

| Asset | Type | Role | Provided |
| --- | --- | --- | --- |
| `source/cobol/LABA05.cbl` | COBOL | Fiscal-year reset job for JV control number. | initial zip |
| `source/cobol/DATECONV.cbl` | COBOL | Date-conversion subprogram (`PROGRAM-ID. DATECONV`); dispatches on `DATESUB-FUNC` to 42 entry paragraphs. Called from `LABD20` via `DATECONV-PD` wrapper paragraphs. Preserves `MIGRTN` IAI-2012 markers verbatim. | **2026-05-21 customer follow-up** |
| `source/procobol/LABD20.pco` | Pro*COBOL | Daily JV comment ingestion and submitted-comment table load. | initial zip |
| `source/procobol/DBIO.pco` | Pro*COBOL | Generic DB dispatcher and Oracle connection/transaction wrapper. | initial zip |
| `source/procobol/CONTROL-RECORD-TABLE-IO.pco` | Pro*COBOL | Table-specific Oracle CRUD module for `CONTROL_RECORD_TABLE`. | initial zip |

## Copybooks

| Asset | Notes | Provided |
| --- | --- | --- |
| `COMCON.cpy` | Common configuration copied by `LABD20`. | initial zip |
| `DBVAR.cpy` | DB linkage structure used by DBIO callers. | initial zip |
| `DMCA.cpy`, `DMCAERR.cpy` | Database error fields/routine. | initial zip |
| `JV-CONTROL-REC.cpy` | Legacy JV control record layout. | initial zip |
| `CONTROL-RECORD-TABLE.cpy` | Oracle-backed control-record table layout. | initial zip |
| `RDMS-ERR-WS.cpy`, `RDMS-ERR-RTN.cpy` | SQL/RDBMS error working storage and routine. | initial zip |
| `DATECONV-WS.cpy` | Caller-side data contract for the date-conversion subsystem. Defines `CONV-DATES` (the parameter group), `DATESUB-FUNC`, `FROM-CYMD-DT` / `FROM-JUL-DT` / `FROM-YMD-DT` / `FROM-MDY-DT` / `FROM-INT-DT`, `TO-CYMD-DT` / `TO-YMD-DT` / `TO-MDCY-DT` / `TO-MDY-DT`, `DAYS-DIF`, and the 88-level conditions `DATE-IS-VALID` / `DATE-ERR`. COPYed by `LABD20.pco:182`. | **2026-05-21 follow-up** |
| `DATECONV-PD.cpy` | Caller-side procedure-division entry paragraphs (`CHECK-CYMD-DT`, `CHECK-MDY-DT`, `YMD-TO-JUL`, `JUL-TO-YMD`, `CYMD-TO-JUL`, …, `ADD-MONTHS-END-JUL`). Each paragraph sets `DATESUB-FUNC` then `CALL 'DATECONV' USING CONV-DATES`. COPYed by `LABD20.pco:531`. | **2026-05-21 follow-up** |
| `JDN-CONSTANTS-WS.cpy` | Action / status / year-type constants and the USNO Julian Day Number offset (2305813). Used internally by `DATECONV.cbl`. | **2026-05-21 follow-up** |
| `JDN-PACKET-WS.cpy` | Internal packet (`JDN-Packet`) for action codes, status flags, and overflow controls used by `DATECONV.cbl`'s internal date-access routines. | **2026-05-21 follow-up** |
| `JDN-RECORD-WS.cpy` | Internal `JDN-Record` layout with `REDEFINES` for CCYYMMDD / YYYYMMDD / CCYYDDD / YYYYDDD / YYDDD plus `JDN-Int`. Backbone data structure for the date math. | **2026-05-21 follow-up** |
| `JDN-RECORD-ACCESS.cpy` | Internal procedure-division section that implements the four core JDN operations via COBOL-85 intrinsic functions: `INTEGER-OF-DATE`, `DAY-OF-INTEGER`, `INTEGER-OF-DAY`, `DATE-OF-INTEGER`. Customer's IAI-2012 migration replaced the legacy `JDNSUB` subroutine with these intrinsics — `MIGRTN` markers preserved verbatim in `DATECONV.cbl`. | **2026-05-21 follow-up** |

See [`../analysis/dateconv-function-inventory.md`](../analysis/dateconv-function-inventory.md) for the full 42-function inventory of the date-conversion subsystem (paragraph names, `DATESUB-FUNC` codes, intrinsic-function dependencies, and `LABD20`-actually-invoked subset).

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
