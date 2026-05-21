# LABD20 Field Lineage — Comment File → Oracle

> Demo / prep output — supplements `analysis/dependency-map.md` with **field-level**
> lineage from the `TST123-COMMENT-REC` fixed-width input record into
> `JC_SUBMITTED_COMMENT_TBL` columns (and related tables).
> Source files were not modified.

## 1. Scope & Confidence Convention

This document traces every field of the supplied LABD20 input file
(`TST123-COMMENT-REC`, defined in `source/procobol/LABD20.pco:43–55`) through:

1. Working-storage host variables (the bind variables used by the embedded SQL).
2. The duplicate-check `SELECT` and `INSERT` against `JC_SUBMITTED_COMMENT_TBL`.
3. The `JC_COUNT_TBL` section-count update.
4. The EOJ stats `SELECT COUNT(*)` queries against `JC_SUBMITTED_COMMENT_TBL`,
   `JC_REJECTED_COMMENT_TBL`, and `JC_APPLIED_COMMENT_TBL`.

Each row carries an explicit **confidence level**:

- **High** — derived directly from the supplied source and table descriptions.
- **Medium** — derived from supplied source but with a noted ambiguity
  (typically resolved by SME confirmation).
- **Low / Unknown** — ~~depends on missing artifacts (e.g. `DATECONV-WS`, `DATECONV-PD`)~~ depends on contradictory documentation or unresolved SME questions; flagged for confirmation. **Update 2026-05-21:** the `DATECONV` closure has been supplied (DATECONV-WS, DATECONV-PD, DATECONV.cbl + 4 JDN helpers), so date-validation lineage previously rated **Low** is upgraded to **High**. See [`dateconv-function-inventory.md`](./dateconv-function-inventory.md).

## 2. File & Table Dependencies (LABD20 Scope)

| Asset | Kind | Role | Source |
| --- | --- | --- | --- |
| `CARDFILE` (external `LINE SEQUENTIAL`) | Input file | Process-date control card | `source/procobol/LABD20.pco:35–36, 57–60`; `test-data/DAILY.MM-DD-CCYY.ctl` |
| `COMMENT` (external `LINE SEQUENTIAL`) | Input file | JV comment records (`TST123-COMMENT-REC`, 330 bytes/record) | `source/procobol/LABD20.pco:32–33, 40–55` |
| `JC_SUBMITTED_COMMENT_TBL` | Oracle table | Target of accepted-record `INSERT`; source of duplicate-check `SELECT` and EOJ count | `source/procobol/LABD20.pco:325–372, 421–423`; `database/descriptions/describe JC_SUBMITTED_COMMENT_TBL.txt` |
| `JC_COUNT_TBL` | Oracle table | Per-section running count; updated when this run advances the section counter | `source/procobol/LABD20.pco:398–401`; `database/descriptions/describe JC_COUNT_TBL.txt` |
| `JC_REJECTED_COMMENT_TBL` | Oracle table | **Read-only** in LABD20 (EOJ count only); inserts performed elsewhere | `source/procobol/LABD20.pco:431–433`; `database/descriptions/describe JC_REJECTED_COMMENT_TBL.txt` |
| `JC_APPLIED_COMMENT_TBL` | Oracle table | **Read-only** in LABD20 (EOJ count only); LABD21 populates it | `source/procobol/LABD20.pco:14–17, 441–443`; `database/descriptions/describe JC_APPLIED_COMMENT_TBL.txt` |
| ~~`DATECONV-WS.cpy`~~ `DATECONV-WS.cpy` | Copybook | ~~Defines `FROM-CYMD-DT`, `DATE-IS-VALID`, etc. **Missing.**~~ Defines `CONV-DATES` (parameter group), `DATESUB-FUNC`, `FROM-CYMD-DT`, `DATE-IS-VALID`. **Supplied 2026-05-21.** | `source/procobol/LABD20.pco:182`; `source/copybooks/DATECONV-WS.cpy` |
| ~~`DATECONV-PD.cpy`~~ `DATECONV-PD.cpy` | Copybook | ~~Defines `CHECK-CYMD-DT` paragraph. **Missing.**~~ Defines 42 entry paragraphs (`CHECK-CYMD-DT`, `CHECK-MDY-DT`, `YMD-TO-JUL`, …). Each sets `DATESUB-FUNC` and `CALL 'DATECONV'`. **Supplied 2026-05-21.** | `source/procobol/LABD20.pco:531`; `source/copybooks/DATECONV-PD.cpy` |
| `DATECONV.cbl` | COBOL subprogram | `PROGRAM-ID. DATECONV`. Dispatches on `DATESUB-FUNC` to internal paragraphs that delegate to JDN helpers using COBOL-85 intrinsic functions (`INTEGER-OF-DATE`, `DAY-OF-INTEGER`, `INTEGER-OF-DAY`, `DATE-OF-INTEGER`). Customer's IAI-2012 migration markers (`MIGRTN`) preserved verbatim. **Supplied 2026-05-21.** | `source/cobol/DATECONV.cbl` |
| `JDN-CONSTANTS-WS.cpy` / `JDN-PACKET-WS.cpy` / `JDN-RECORD-WS.cpy` / `JDN-RECORD-ACCESS.cpy` | Copybooks | DATECONV-internal JDN data structures and intrinsic-function access section. **Supplied 2026-05-21.** | `source/copybooks/JDN-*.cpy` |

## 3. `TST123-COMMENT-REC` → `JC_SUBMITTED_COMMENT_TBL` Field Lineage

The submitted-table insert is at `source/procobol/LABD20.pco:352–372`.
Column types are from
`database/descriptions/describe JC_SUBMITTED_COMMENT_TBL.txt`.

| Source field (file) | Source bytes | COBOL PIC | Host variable / value | Target column | Target type | Transform | Confidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `TST123-LOAN-DT-NR` | 1–26 | `PIC X(026)` | `WS-TST123-LOAN-DT-NR` (set at `source/procobol/LABD20.pco:319`) | `JC_SUBMITTED` | `CHAR(26) NOT NULL` (PK) | Identity copy of the 26-byte submitted key. | High |
| Computed (per-row counter) | n/a | `PIC 9(012)` | `WS-JV-COUNTER` (`source/procobol/LABD20.pco:149`) incremented at `source/procobol/LABD20.pco:343–345` | `JC_SUBMITTED_NUMBER` | `NUMBER NOT NULL` | New value = previous max in-memory counter + 1 for each accepted insert in this run. | High |
| `TST123-SCHEDULE-DOC-NO` | 27–36 | `PIC X(010)` | `WS-TST123-SCHEDULE-DOC-NO` (set at `source/procobol/LABD20.pco:320`) | `JC_SUBMITTED_SCHED_DOC_NO` | `CHAR(10)` | Identity copy. Not validated by LABD20 (see `source/procobol/LABD20.pco:294–296`). | High |
| `TST123-COMMENT-HIST` (= `TST123-SCHEDULE-DOC-NO` + `TST123-COMMENT-TEXT`) | 27–266 | `PIC X(240)` group | `WS-TST123-COMMENT-HIST` (240 bytes; populated via `MOVE TST123-COMMENT-REC TO WS-TST123-COMMENT-REC`) | `JC_SUBMITTED_COMMENT_HIST` | `CHAR(240)` | Identity copy of the 240-byte comment-history group (which includes the schedule doc number prefix). | High |
| `TST123-COMMENT-REQUESTOR` | 267–286 | `PIC X(020)` | `WS-TST123-COMMENT-REQUESTOR` | `JC_SUBMITTED_COMMENT_REQUESTOR` | `CHAR(20)` | Identity copy. Reject if blank (`source/procobol/LABD20.pco:301–303`). | High |
| `TST123-COMMENT-APPROVER` | 287–300 (14 bytes in active layout) | `PIC X(014)` (active); `PIC X(020)` (original, commented out) | `WS-TST123-COMMENT-APPROVER` (`PIC X(020)`) — space-padded on the right when MOVE'd from a shorter source | `JC_SUBMITTED_COMMENT_APPROVER` | `CHAR(20)` | 14-byte input padded to 20 bytes via COBOL MOVE semantics. Reject if blank. | Medium — width discrepancy in legacy source (see `source/procobol/LABD20.pco:54–55, 141`). |
| Derived from `TST123-JV-NUMBER` + `TST123-SECTION-ID` | 9–14 + 15–16 (8 bytes) | `PIC 9(006)` + `PIC 9(002)` | `WS-CONTROL-NUM` (8-byte `PIC X(8)`) — built by populating `WS-TST123-JV-NUMBER` and `WS-TST123-SECTION-ID` redefines (`source/procobol/LABD20.pco:162–165, 343–344`) | `JC_SUBMITTED_CONTROL_NUM` | `CHAR(8)` | 6-digit JV number concatenated with 2-digit section id. | High |
| Program literal | n/a | `PIC X(006)` | `'LABD20'` literal in the INSERT VALUES clause | `JC_SUBMITTED_UPDT_PROG_ID` | `CHAR(6)` | Hard-coded source identifier; modernized loader should emit its own logical name. | High |
| `CARDFILE` process date (`WS-PROCESS-DATE`) | 1–10 (in `CARDFILE`) | `PIC 9(008)` (`CCYYMMDD` form) | `WS-PROCESS-DATE` after re-ordering from `MM/DD/CCYY` in `LABD20-HOUSE-KEEPING` (`source/procobol/LABD20.pco:223–234`) | `JC_SUBMITTED_UPDT_PROG_DT` | `DATE` | Converted via `TO_DATE(:WS-PROCESS-DATE,'YYYYMMDD')` at insert time (`source/procobol/LABD20.pco:371`). | High |
| Oracle default (`SYSDATE`) | n/a | n/a | DB default | `CREATE_TIMESTAMP`, `LAST_UPDATE_TIMESTAMP` | `TIMESTAMP(6)` | LABD20 does not set these explicitly; they default to row insert / update time in the database. | Medium — defaults are not in the supplied DDL; confirm with DBA. |

### 3.1 Duplicate-Check Lineage

| Source field | Host variable | SQL position | Confidence |
| --- | --- | --- | --- |
| `TST123-LOAN-DT-NR` | `WS-TST123-LOAN-DT-NR` | `WHERE JC_SUBMITTED = :WS-TST123-LOAN-DT-NR` (`source/procobol/LABD20.pco:329`) | High |
| `JC_SUBMITTED_NUMBER` (Oracle column) | `WS-CHECK-NUMBER` (`PIC 9(012)`) | `SELECT JC_SUBMITTED_NUMBER INTO :WS-CHECK-NUMBER` (`source/procobol/LABD20.pco:326–327`) | High |

The duplicate-check is **not** a strict primary-key lookup expressed in the
DDL — it depends on `JC_SUBMITTED_COMMENT_TBL.JC_SUBMITTED` being unique (which
the description confirms: "primary key uses JC_SUBMITTED").

## 4. `JC_COUNT_TBL` Lineage

The section-count update lives at `source/procobol/LABD20.pco:398–401`:

```text
UPDATE JC_COUNT_TBL
   SET JC_SECTION_COUNT = :WS-JV-COUNTER
 WHERE JC_SECTION = 'MA'
```

| Source | Target column | Type | Notes / Confidence |
| --- | --- | --- | --- |
| Program literal `'MA'` | `JC_SECTION` | `CHAR(2) NOT NULL` (PK per description, but description is ambiguous) | High that filter is `'MA'`; **Medium** that `JC_SECTION` is the PK — see risk note below. |
| `WS-JV-COUNTER` after all inserts | `JC_SECTION_COUNT` | `NUMBER` | High |
| Guard condition (not a column) | (n/a) | (n/a) | Update fires only when `WS-JV-COUNTER > WS-JV-COUNTERS` (`source/procobol/LABD20.pco:393`); confidence High. |

**Risk:** `database/descriptions/describe JC_COUNT_TBL.txt` says
"`primary key uses JC_SUBMITTED`" even though `JC_SUBMITTED` is not a column
in that table. This is almost certainly a copy/paste artifact from
`JC_SUBMITTED_COMMENT_TBL`. Confirm the actual primary key (likely
`JC_SECTION`) before generating the modernized DDL.

## 5. EOJ Stats Lineage

The end-of-job stats queries write into `WS-COUNTERS` so they can be printed.
All four counts are emitted to the program's PRINTER device
(`source/procobol/LABD20.pco:448–486`).

| SQL | Target counter | Source ref |
| --- | --- | --- |
| `SELECT COUNT(*) FROM JC_SUBMITTED_COMMENT_TBL` | `WS-TOTAL-SUBMIT-END-CNT` | `source/procobol/LABD20.pco:421–423` |
| `SELECT COUNT(*) FROM JC_REJECTED_COMMENT_TBL` | `WS-TOTAL-REJECT-END-CNT` | `source/procobol/LABD20.pco:431–433` |
| `SELECT COUNT(*) FROM JC_APPLIED_COMMENT_TBL` | `WS-TOTAL-APPLIED-END-CNT` | `source/procobol/LABD20.pco:441–443` |

The **prior** counts (`WS-TOTAL-*-BEG-CNT`) appear in the EOJ report
(`source/procobol/LABD20.pco:469–478`) but are never populated by an EOJ
SELECT — confirm with the SME whether equivalent BOJ queries exist in a
predecessor program or were intended but never implemented. Marked
**Medium confidence**.

## 6. Validation-Rule Lineage (LABD20 Reject Reasons)

Every rule that can flip `WS-TST123-RECORD-FLAG → TST123-RECORD-IN-ERROR`
contributes to the per-record reject decision but does **not** write to any
table in LABD20 itself; only the counters
(`WS-TST123-RECS-ERR-CNT`, `WS-ERRORS-CNT`) are incremented
(`source/procobol/LABD20.pco:309–311`).

| Rule | Source | Confidence |
| --- | --- | --- |
| Whole record blank → reject | `source/procobol/LABD20.pco:261–263` | High |
| `TST123-COMMENT-DT` non-numeric → reject | `source/procobol/LABD20.pco:265, 272–274` | High |
| `TST123-COMMENT-DT` numeric but not a valid calendar date (`CHECK-CYMD-DT` returns not `DATE-IS-VALID`) → reject | `source/procobol/LABD20.pco:266–271` | **Low** — depends on missing `DATECONV-WS` / `DATECONV-PD` (`source/procobol/LABD20.pco:182, 531`). |
| `TST123-JV-NUMBER` non-numeric or ≤ 0 → reject | `source/procobol/LABD20.pco:276–281` | High |
| `TST123-SECTION-ID` non-numeric → reject | `source/procobol/LABD20.pco:283–287` | High |
| `TST123-LOAN-NUMBER` non-numeric → reject | `source/procobol/LABD20.pco:289–293` | High |
| `TST123-COMMENT-TEXT` blank → reject | `source/procobol/LABD20.pco:297–299` | High |
| `TST123-COMMENT-REQUESTOR` blank → reject | `source/procobol/LABD20.pco:301–303` | High |
| `TST123-COMMENT-APPROVER` blank → reject | `source/procobol/LABD20.pco:305–307` | High |
| `TST123-SCHEDULE-DOC-NO` — **no validation** | `source/procobol/LABD20.pco:294–296` | High |

## 7. Modernization Notes For Each Field Family

- **26-byte submitted key (`JC_SUBMITTED`)** — keep as a strict
  primary key with deterministic encoding (CCYYMMDD + 6-digit JV + 2-digit
  section + 10-digit loan), and enforce a unique index in the modernized
  schema so a deduplicate-by-`SELECT`-then-`INSERT` race cannot insert two
  identical rows. Prefer `ON CONFLICT DO NOTHING` or `MERGE` semantics over
  the legacy two-statement pattern.
- **JV control number (`WS-CONTROL-NUM` → `JC_SUBMITTED_CONTROL_NUM`)** — built
  from two file fields; the modernized loader should derive it from the
  parsed sub-fields rather than from a re-read of bytes 9–16.
- **Numeric fields (`PIC 9(*)`)** — model as fixed-width strings up to the
  parser layer, then convert to `int` / `Decimal` only after passing the
  numeric-and-positive checks. Do not load into floating-point types.
- **`USAGE BINARY` fields (`JV-NUMBER` in `JV-CONTROL-REC`)** — treat as
  big-endian unsigned 32-bit when reading the on-disk record format; the
  modernized control table column is `NUMBER` so the on-the-wire binary
  representation can be dropped after parsing (`source/copybooks/JV-CONTROL-REC.cpy:6`).
- **Process date (`WS-PROCESS-DATE`)** — Oracle insert uses
  `TO_DATE(:WS-PROCESS-DATE,'YYYYMMDD')`; the modernized loader should pass a
  native `date` object and rely on the driver's type conversion rather than
  string-formatted dates.
- **Logical program id (`'LABD20'`)** — replace with a per-deployment loader
  identifier so the audit column tracks the modernized service name.

## 8. Confidence Summary

| Lineage area | Overall confidence | Driver |
| --- | --- | --- |
| Submitted-table insert columns | **High** | Direct INSERT statement + table description match. |
| Duplicate-check semantics | **High** | Direct SELECT statement + unique-key invariant. |
| `JC_COUNT_TBL` filter / counter | **High** for value, **Medium** for PK | Description text contradicts column list. |
| EOJ stats (end counts) | **High** | Direct SELECT COUNT(*) statements. |
| EOJ stats (begin counts) | **Medium** | No code populates `WS-TOTAL-*-BEG-CNT`; report prints zeros unless populated by an upstream job. |
| Calendar-date validation | **Low** | `DATECONV-WS.cpy` / `DATECONV-PD.cpy` missing. |
| `TST123-COMMENT-APPROVER` width | **Medium** | Source has commented-out 20-byte variant alongside active 14-byte field. |
