# Assumptions and Placeholders — Single Source of Truth

> Every assumption, every stub, every placeholder, every "inferred vs. confirmed" decision lives here.
> Each entry has a confidence rating (**HIGH / MEDIUM / LOW**) and an SME-action item.
> Companion to [`MIGRATION-PLAN.md`](./MIGRATION-PLAN.md) and [`RISKS-AND-GAPS.md`](./RISKS-AND-GAPS.md).

---

## How this is enforced across artifacts

- Every generated Python file has a top-of-file docstring block listing the assumptions that apply to it, plus inline `# ASSUMPTION:`, `# PLACEHOLDER:`, and `# SME-REVIEW:` markers anywhere code had to guess or stub.
- Every generated SQL file has a header comment block listing the assumptions that apply to it.
- The executive HTML report (`migration/executive-report.html`) renders this list as a dedicated "Assumptions, placeholders & gaps" section.
- The requirements doc (`migration/business-requirements/requirements-with-citations.md`) tags every requirement as **CONFIRMED FROM SOURCE**, **INFERRED**, or **UNRESOLVABLE WITHOUT MISSING COPYBOOKS**.

---

## A. Assumptions (where a decision had to be made)

### A-1 — Calendar-date validation stub for the missing `DATECONV-WS` / `DATECONV-PD` copybooks

| Aspect | Value |
| --- | --- |
| Confidence | **LOW** (cannot verify against the real copybook) |
| Source citation | `LABD20.pco:182` (`COPY DATECONV-WS.`); `LABD20.pco:266-267` (call to `CHECK-CYMD-DT`, sets `DATE-IS-VALID`) |
| Decision | Implement `check_cymd_dt(yyyymmdd: str) -> bool` that returns `True` iff: (a) string is exactly 8 numeric digits, (b) year ≥ 1900 and ≤ 2100, (c) month in 1..12, (d) day in 1..days-in-month with Feb-29 leap-year handling. |
| Placeholder marker in code | `# PLACEHOLDER (Risk 1):` and `# SME-REVIEW:` in `labd20_loader.py` |
| Risk | [Risk 1](./RISKS-AND-GAPS.md#risk-1--missing-dateconv-ws-and-dateconv-pd-copybooks) |
| SME-action | Provide `DATECONV-WS` / `DATECONV-PD`, or sign off that the stub semantics are acceptable. |

### A-2 — Display-only representation of `JV-NUMBER` at the DB boundary

| Aspect | Value |
| --- | --- |
| Confidence | **MEDIUM** (display layout is observed in `CONTROL-RECORD-TABLE-IO.pco`, but in-memory binary callers cannot be enumerated from the provided source) |
| Source citation | `JV-CONTROL-REC.cpy:6`; `CONTROL-RECORD-TABLE-IO.pco:21-28` |
| Decision | Python `laba05_reset.py` operates on the **display** layout of `CONTROL_RECORD_DATA` (CHAR(400)). It reads the column as a string, replaces the `JV-NUMBER` 6-character zoned-decimal slice with `'000001'`, and writes back. The Python program never moves a binary form across the DB boundary. |
| Placeholder marker in code | `# ASSUMPTION (A-2):` at the top of `laba05_reset.py` |
| Risk | [Risk 2](./RISKS-AND-GAPS.md#risk-2--binarydisplay-jv-number-conversion) |
| SME-action | Confirm no other in-memory consumer relies on the binary form of `JV-CONTROL-REC` outside `CONTROL-RECORD-TABLE-IO`. |

### A-3 — Static dispatch path resolution for DBIO

| Aspect | Value |
| --- | --- |
| Confidence | **MEDIUM** for the two paths actually used by LABA05/LABD20; **LOW** for any other path |
| Source citation | `DBIO.pco:228-260` (string-built subroutine name); `DBIO.pco:267-276` (override to `CONTROL-RECORD-TABLE-IO` when record is `JV-CONTROL-REC`) |
| Decision | `db_dispatcher.py` registers two static handlers: (1) `JV-CONTROL-REC` → `ControlRecordTableIO`, (2) embedded SQL for the LABD20 paths (which do not go through the DBIO IO-module lookup). Any other dispatch raises `UnresolvedDispatchPathError`. |
| Risk | [Risk 4](./RISKS-AND-GAPS.md#risk-4--dynamic-subroutine-dispatch-in-dbio) |
| SME-action | Provide the complete list of `*-IO` Pro*COBOL modules if other dispatch targets exist in production. |

### A-4 — Canonical `TST123-COMMENT-APPROVER` width is 14 bytes (per FD)

| Aspect | Value |
| --- | --- |
| Confidence | **MEDIUM** (the *active* FD says 14; a commented predecessor at line 54 said 20; working storage at line 141 uses 20 as a redefinition window) |
| Source citation | `LABD20.pco:54` (commented `PIC X(020)`); `LABD20.pco:55` (active `PIC X(014)`); `LABD20.pco:141` (`WS-TST123-COMMENT-APPROVER PIC X(020)`) |
| Decision | Python parser uses the FD-defined 14-byte width. Total record length = 8 + 6 + 2 + 10 + 10 + 230 + 20 + 14 = **300 bytes**. The Oracle target column `JC_SUBMITTED_COMMENT_APPROVER` is `CHAR(20)`; the Python loader right-pads the parsed 14-byte field to 20 bytes for the INSERT. |
| Placeholder marker in code | `# ASSUMPTION (A-4):` in `labd20_loader.py` |
| Risk | [Risk 5](./RISKS-AND-GAPS.md#risk-5--fixed-width-record-layout-byte-precision) |
| SME-action | Confirm canonical width — is the 14-byte FD correct, or was the comment-out at line 54 a regression? |

### A-5 — Section `'MA'` is the only section updated by `POST-PROCESS`

| Aspect | Value |
| --- | --- |
| Confidence | **HIGH** (confirmed from source) |
| Source citation | `LABD20.pco:398-401` (`UPDATE JC_COUNT_TBL SET JC_SECTION_COUNT = :WS-JV-COUNTER WHERE JC_SECTION = 'MA'`) |
| Decision | Modernized loader updates only section `'MA'`. |
| Risk | n/a |

### A-6 — `JC_COUNT_TBL` primary key is `JC_SECTION` (not `JC_SUBMITTED` as the describe file claims)

| Aspect | Value |
| --- | --- |
| Confidence | **MEDIUM** (describe file says `JC_SUBMITTED` which is not a column on this table) |
| Source citation | `database/descriptions/describe JC_COUNT_TBL.txt:5` (`JC_SECTION NOT NULL CHAR(2)`); same file line 10 (claimed PK is `JC_SUBMITTED`) |
| Decision | Conversion treats `JC_SECTION` as the PK. |
| SME-action | Confirm describe file typo; correct upstream. |

### A-7 — Process date is read once from the CARDFILE in `MM/DD/CCYY` and stored as `CCYYMMDD`

| Aspect | Value |
| --- | --- |
| Confidence | **HIGH** (confirmed from source) |
| Source citation | `LABD20.pco:224-232` (read card, slice MM/DD/CC/YY, recompose into `WS-PROCESS-DATE = CCYYMMDD`) |
| Decision | Python loader reads the single-line card file, splits on `/`, recomposes as `YYYYMMDD`. Bound into the INSERT via Oracle `TO_DATE(:process_date, 'YYYYMMDD')` (`LABD20.pco:371`). |

### A-8 — Comment file is opened OUTPUT and immediately closed after the read loop to truncate it

| Aspect | Value |
| --- | --- |
| Confidence | **HIGH** (confirmed from source) |
| Source citation | `LABD20.pco:215-218` |
| Decision | Python loader matches this pattern by truncating the input file after a successful run (in CLI mode). In demo / test mode, the file is left untouched. |

### A-9 — `JC_SUBMITTED` is the 26-byte composite of `CCYYMMDD + JV-NUM(6) + SECTION(2) + LOAN(10)`

| Aspect | Value |
| --- | --- |
| Confidence | **HIGH** (confirmed from source) |
| Source citation | `LABD20.pco:44` (`TST123-LOAN-DT-NR PIC X(026)`); `LABD20.pco:46-49` (redefinition into 8+6+2+10); `LABD20.pco:329` (`WHERE JC_SUBMITTED = :WS-TST123-LOAN-DT-NR`) |
| Decision | Python uses the 26-byte composite directly as the duplicate-check key and as the inserted primary key. |

### A-10 — Modernized DB access uses parameterized SQL and the `oracledb` Python driver

| Aspect | Value |
| --- | --- |
| Confidence | **HIGH** for parameterization; **MEDIUM** for driver choice (any DB-API 2.0 driver works; `oracledb` is the supported successor to `cx_Oracle`) |
| Decision | `db_dispatcher.py` is driver-agnostic — it accepts any DB-API 2.0 connection. The default factory uses `oracledb`. In `demo_app.py`, a `sqlite3`-backed mock connection is wired in so the demo runs with zero external setup. |

### A-11 — All committed code is **demo / prep — pending SME review**

| Aspect | Value |
| --- | --- |
| Confidence | **HIGH** (this is a stated constraint) |
| Decision | Top-of-file docstrings on every generated Python file include this label. Every generated SQL file has it in the header comment. |

---

## B. Placeholders (stubs that intentionally do less than the legacy program)

### P-1 — `check_cymd_dt` calendar validation

See [A-1](#a-1--calendar-date-validation-stub-for-the-missing-dateconv-ws--dateconv-pd-copybooks). Marked `# PLACEHOLDER (Risk 1):` in the loader.

### P-2 — Error printer output

The COBOL programs route many messages to `UPON PRINTER`. Modernized Python routes the same messages to a structured logger (`logging.getLogger('jv.loader')`). The text content is reproduced verbatim where possible.

| Source | Modernized |
| --- | --- |
| `DISPLAY 'PROCESS DATE = ' WS-PARM-DATE UPON PRINTER.` (`LABD20.pco:233-234`) | `logger.info("PROCESS DATE = %s", ws_parm_date)` |
| `DISPLAY '!!! ORACLE DATABASE ERROR!!! ' SQLERRMC UPON PRINTER` (`LABD20.pco:201`) | `logger.error("!!! ORACLE DATABASE ERROR!!! %s", sqlerrmc)` |
| `DISPLAY 'DUPLICATE ENTRY ' TST123-LOAN-DT-NR UPON PRINTER` (`LABD20.pco:335-336`) | `logger.info("DUPLICATE ENTRY %s", tst123_loan_dt_nr)` |

### P-3 — Demo app mock database

`demo_app.py` ships with a SQLite-backed shim of `JC_SUBMITTED_COMMENT_TBL`, `JC_COUNT_TBL`, and `CONTROL_RECORD_TABLE`. This is **not** an Oracle equivalent — it exists to make the demo runnable. It does not exercise Oracle-specific constructs (`TO_DATE`, `ROWID`).

---

## C. Items that remain UNRESOLVABLE without input from customer

| # | Item | Blocking artifact |
| --- | --- | --- |
| U-1 | Exact behavior of `CHECK-CYMD-DT` | `DATECONV-PD` copybook |
| U-2 | Whether any in-memory caller of `JV-CONTROL-REC` reads the binary form outside `CONTROL-RECORD-TABLE-IO` | Customer codebase inventory |
| U-3 | Full set of `*-IO` modules used in production | Customer codebase inventory |
| U-4 | Production environment-variable list (`CARDFILE`, `COMMENT`, `ORACLE_*`, etc.) | Customer ops runbook |
| U-5 | Canonical width of `TST123-COMMENT-APPROVER` (14 vs. 20) | Customer SME |
| U-6 | `JC_COUNT_TBL` describe file primary-key typo | Customer DBA |

---

## D. Confidence calibration

| Rating | Meaning | Examples |
| --- | --- | --- |
| **HIGH** | Behavior is directly readable from source, with no missing dependencies or runtime ambiguity. | INSERT column list, duplicate-check SELECT key, MM/DD/CCYY → YYYYMMDD transform |
| **MEDIUM** | Behavior is readable from source but with a known dependency on something not fully evidenced (a describe-file typo, an EXTERNAL caller we can't enumerate). | A-2, A-3, A-4, A-6 |
| **LOW** | Behavior depends on a missing artifact and we are stubbing. | A-1 (`DATECONV-*` copybooks) |
