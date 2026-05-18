# Initial Derived Business Requirements

## LABA05 - Fiscal-Year JV Control Reset

| ID | Requirement |
| --- | --- |
| BR-LABA05-001 | The system shall connect to the JV database before attempting control-record maintenance. |
| BR-LABA05-002 | The system shall fetch the `JV-CONTROL-REC` control record from `CONTROL_RECORD_TABLE`. |
| BR-LABA05-003 | If the control record cannot be fetched, the job shall stop with a non-zero return code. |
| BR-LABA05-004 | The system shall set the `JV-NUMBER` field to `1` during the fiscal-year reset job. |
| BR-LABA05-005 | The system shall update the persisted control record after changing `JV-NUMBER`. |
| BR-LABA05-006 | On update failure, the system shall stop with a non-zero return code and avoid reporting success. |

## LABD20 - Daily JV Comment Submission Load

| ID | Requirement |
| --- | --- |
| BR-LABD20-001 | The system shall read a daily process date from `CARDFILE` in `MM/DD/CCYY` form and transform it to `YYYYMMDD`. |
| BR-LABD20-002 | The system shall read each external comment-file record using the fixed-width layout in `TST123-COMMENT-REC`. |
| BR-LABD20-003 | The system shall reject blank comment records. |
| BR-LABD20-004 | The system shall validate that comment date is numeric and a valid calendar date. |
| BR-LABD20-005 | The system shall validate that JV number is numeric and greater than zero. |
| BR-LABD20-006 | The system shall validate that section id and loan number are numeric. |
| BR-LABD20-007 | The system shall reject records with blank comment text, blank requestor, or blank approver. |
| BR-LABD20-008 | The system shall check `JC_SUBMITTED_COMMENT_TBL` for an existing submitted key before insert. |
| BR-LABD20-009 | Duplicate submitted keys shall be reported and not inserted again. |
| BR-LABD20-010 | Accepted comments shall be inserted into `JC_SUBMITTED_COMMENT_TBL` with schedule document number, comment history, requestor, approver, control number, update program id `LABD20`, and process date. |
| BR-LABD20-011 | The system shall update `JC_COUNT_TBL` for section `MA` when the current run's JV counter exceeds the stored count. |
| BR-LABD20-012 | The system shall commit successful SQL work and report end-of-job table counts. |
| BR-LABD20-013 | On SQL or DMS error, the system shall print context and roll back database work. |
