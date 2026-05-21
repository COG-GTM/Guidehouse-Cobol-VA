# Risks and Gaps Register

> Companion to [`MIGRATION-PLAN.md`](./MIGRATION-PLAN.md) and [`ASSUMPTIONS-AND-PLACEHOLDERS.md`](./ASSUMPTIONS-AND-PLACEHOLDERS.md).
> Every risk below has been carried into the corresponding artifact (requirements, lineage, code, tests). Generated code and SQL include inline `RISK:` / `# RISK:` markers where these items materialize.

---

## Risk register summary

| # | Risk | Severity | Status | Where it materializes |
| --- | --- | --- | --- | --- |
| 1 | ~~Missing~~ `DATECONV-WS` / `DATECONV-PD` copybooks **+ DATECONV.cbl + 4 JDN helpers** | ~~**HIGH**~~ **CLOSED** | ~~Mitigated with stub; flagged for SME~~ **Resolved 2026-05-21** — full date-conversion closure supplied by customer; stub replaced by faithful Python port; `BR-LABD20-006` LOW → HIGH | `LABD20.pco:182, 267`; `source/copybooks/DATECONV-*.cpy`; `source/cobol/DATECONV.cbl`; `source/copybooks/JDN-*.cpy` |
| 2 | Binary↔display `JV-NUMBER` conversion | **HIGH** | Modeled explicitly in Python | `CONTROL-RECORD-TABLE-IO.pco:21-28, 257-266`; `JV-CONTROL-REC.cpy:6` |
| 3 | Credential files `/tst/.oralogin`, `/tst/.orapasswd` | **HIGH** | Replaced with env-var / config | `DBIO.pco:33-38, 41-45` |
| 4 | Dynamic subroutine dispatch in DBIO | **MEDIUM** | Static paths documented; runtime-only paths flagged | `DBIO.pco:228-260` |
| 5 | Fixed-width record layout byte precision | **HIGH** | Explicit byte-offset parser with tests | `LABD20.pco:43-55` |
| 6 | SQLCODE → DMS-style return-code translation | **MEDIUM** | Translation table reproduced verbatim | `DBIO.pco:374-398` |
| 7 | Transaction rollback paths (SQL + DMS) | **MEDIUM** | Single rollback policy with both error sources logged | `LABD20.pco:331, 373, 402, 414, 424, 434, 444, 489-` and `LABA05.cbl:171, 196, 207-` |
| 8 | EXTERNAL shared data items | **MEDIUM** | Modeled as shared context object in Python | `JV-CONTROL-REC.cpy:1`, `CONTROL-RECORD-TABLE.cpy:24` |
| 9 | Empty / missing real test data | **MEDIUM** | Synthetic 20+ record fixture generated | `test-data/TST.JVCMTS.dat` (empty) |
| 10 | Perl wrapper environment dependencies | **MEDIUM** | Documented; modern orchestration equivalent proposed | `source/perl/LABA05.pl`, `source/perl/LABD20-JV.pl` |
| 11 | `PERFORM PERFORM` typo | **LOW** | Documented for SME review | `LABD20.pco:213` |

---

## Detailed risk entries

### Risk 1 — ~~Missing `DATECONV-WS` and `DATECONV-PD` copybooks~~ CLOSED 2026-05-21

**Status:** ~~HIGH~~ **CLOSED**. Customer supplied the full date-conversion subsystem closure in the 2026-05-21 follow-up shipment.

**Original framing (preserved for audit trail):**

> ~~**Severity:** HIGH. Date validation logic for `TST123-COMMENT-DT` cannot be reproduced exactly without these copybooks.~~
>
> ~~**Evidence:**~~
> ~~- `LABD20.pco:182` — `COPY DATECONV-WS.`~~
> ~~- `LABD20.pco:266-267` — `MOVE TST123-COMMENT-DT TO FROM-CYMD-DT` then `PERFORM CHECK-CYMD-DT`. `FROM-CYMD-DT`, `CHECK-CYMD-DT`, and `DATE-IS-VALID` are all defined inside the missing copybooks.~~
>
> ~~**Mitigation:**~~
> ~~- Python loader implements a stub `check_cymd_dt(yyyymmdd: str) -> bool` that validates: 8 numeric digits, year ≥ 1900, valid calendar month and day (including Feb 29 leap-year). This is **almost certainly a superset** of what the legacy copybook does, but exact behavior cannot be confirmed.~~
> ~~- Code marks the stub with `# PLACEHOLDER (Risk 1):` and `# SME-REVIEW:` comments.~~
> ~~- Logged separately in `ASSUMPTIONS-AND-PLACEHOLDERS.md` as Assumption A-1.~~
>
> ~~**Action required of customer SME:** Provide `DATECONV-WS` and `DATECONV-PD` copybooks, or confirm the standard YYYYMMDD calendar check is acceptable.~~

**Resolution 2026-05-21:** customer follow-up shipment supplied:

- `source/copybooks/DATECONV-WS.cpy` — caller-side data contract (`CONV-DATES`, `DATESUB-FUNC`, `FROM-CYMD-DT`, `DATE-IS-VALID`, …).
- `source/copybooks/DATECONV-PD.cpy` — caller-side procedure-division wrappers (42 entry paragraphs that set `DATESUB-FUNC` and `CALL 'DATECONV'`).
- `source/cobol/DATECONV.cbl` — the subprogram itself (`PROGRAM-ID. DATECONV`, 1,159 lines). Dispatches on `DATESUB-FUNC` to internal paragraphs. IAI-2012 `MIGRTN` migration markers preserved verbatim.
- `source/copybooks/JDN-CONSTANTS-WS.cpy`, `JDN-PACKET-WS.cpy`, `JDN-RECORD-WS.cpy`, `JDN-RECORD-ACCESS.cpy` — internal JDN constants, packet, record layout, and intrinsic-function-based access section.

**Effect:**
- `LABD20.pco:182` `COPY DATECONV-WS` — resolved.
- `LABD20.pco:531` `COPY DATECONV-PD` — resolved.
- `LABD20.pco:266-267` call into `CHECK-CYMD-DT` — fully traceable.
- `migration/converted-code/python/labd20_loader.py` `check_cymd_dt` stub — replaced by faithful port (`migration/converted-code/python/dateconv.py`).
- `BR-LABD20-006` parity row — confidence LOW → HIGH.
- [Assumption A-1](./ASSUMPTIONS-AND-PLACEHOLDERS.md#a-1--calendar-date-validation-stub-for-the-missing-dateconv-ws--dateconv-pd-copybooks) — retired.
- COBOL runtime parity harness (`migration/test-results/cobol-parity-report.html`) compiles `DATECONV.cbl` under GnuCOBOL 3.1.2 verbatim and diffs 52 test vectors against the Python port byte-for-byte. **52 vectors, 51 matched, 1 documented modernization improvement, 0 unresolved mismatches.**

**Verification-loop finding (2026-05-21):** the harness caught **13 Python-port defects** before merge that all 77 unit tests passed cleanly. `TO-INT-DT` leaking the intermediate JDN in DIF operations, alias `TO-*` fields not propagated through `JUL-TO-CYMD` / `ADD-CYMD` / `ADD-MONTHS-END-JUL` / `DIF-FY`, 30-day-month DIF counting Day-31 separately, and over-strict `BETWEEN` validation in `RANGE-MDY`. All 13 patched in the same commit as the harness landed. The single remaining diff is `9950-VALIDATE-YYYY` accepting 02/29/1900 (legacy Julian leap rule); the Python port correctly rejects it (Gregorian) and the harness classifies it as a documented modernization improvement, not a regression.

**See:** [`../analysis/dateconv-function-inventory.md`](../analysis/dateconv-function-inventory.md) for the 40-function dispatcher inventory, intrinsic-function mapping, and the full verification-loop findings table.

---

### Risk 2 — Binary↔display `JV-NUMBER` conversion

**Severity:** HIGH. `JV-NUMBER` is stored as `USAGE BINARY` inside the in-memory `JV-CONTROL-REC` (6 bytes claimed at PIC 9(6) BINARY, which on most COBOL runtimes occupies 4 bytes COMP/binary). The persisted column `CONTROL_RECORD_DATA` is `CHAR(400)` — a display string. The `CONTROL-RECORD-TABLE-IO` module shuttles the value between a binary view (`JV-CONTROL-REC-B`) and a display view (`JV-CONTROL-REC-D`).

**Evidence:**
- `JV-CONTROL-REC.cpy:6` — `05 JV-NUMBER PIC 9(006) USAGE BINARY.`
- `CONTROL-RECORD-TABLE-IO.pco:21-28` — Two parallel layouts: `JV-CONTROL-REC-B` (binary) and `JV-CONTROL-REC-D` (display).

**Mitigation:**
- `laba05_reset.py` reads the `CONTROL_RECORD_DATA` column as a 400-character display string, slices fields by byte offset (display layout), updates `JV-NUMBER` to display `'000001'`, and writes back. The Python code never relies on a binary representation crossing the database boundary.
- `db_dispatcher.py` documents the translation behavior of the COBOL module for traceability.
- Logged as Assumption A-2.

**Action required of customer SME:** Confirm whether any caller depends on the **in-memory binary** representation (i.e. is there anything besides `CONTROL-RECORD-TABLE-IO` that reads JV-CONTROL-REC's binary form?). If yes, the modernized client must handle that — flagged for SME review.

---

### Risk 3 — Credential files `/tst/.oralogin`, `/tst/.orapasswd`

**Severity:** HIGH (security).

**Evidence:**
- `DBIO.pco:33-38` — Two file SELECTs assigning external files `/tst/.oralogin` and `/tst/.orapasswd`.
- `DBIO.pco:41-45` — `USRID-REC PIC X(20)` and `PASSWD-REC PIC X(20)`.

**Mitigation:**
- Modernized Python (`db_dispatcher.py`) reads connection parameters from environment variables (`ORACLE_USER`, `ORACLE_PASSWORD`, `ORACLE_DSN`) or from a config-dict injected at construction time.
- No credential strings appear in any committed file.

**Action required of customer SME:** Move secrets into the customer's managed secrets store (e.g. AWS Secrets Manager / HashiCorp Vault); confirm acceptable rotation policy.

---

### Risk 4 — Dynamic subroutine dispatch in DBIO

**Severity:** MEDIUM. The DBIO module constructs the IO-module subroutine name at runtime by concatenating the record name with `-IO` or `-CYMD-IO`.

**Evidence:**
- `DBIO.pco:228-260` — Loop walks `DB-DMSREC-NAME` looking for `-REC` and `STRING`s either `-CYMD-IO` or `-IO` into `IO-SUBROUTINE`.
- `DBIO.pco:311-320` — `CALL IO-SUBROUTINE USING ...`.

**Mitigation:**
- Statically resolvable paths for the two programs in scope: `LABA05` → `JV-CONTROL-REC` → DBIO 1100 override → `CONTROL-RECORD-TABLE-IO`. `LABD20` → embedded SQL directly (not via DBIO IO module) except for the `CONNECT`.
- `db_dispatcher.py` documents these two paths as the resolved set. Any other record name encountered would be a path that requires runtime evidence — `db_dispatcher.py` raises an explicit `UnresolvedDispatchPathError` for those.
- Logged as Assumption A-3.

**Action required of customer SME:** Provide the full list of `*-IO` modules in the runtime environment so any dispatch beyond LABA05/LABD20 can be statically mapped.

---

### Risk 5 — Fixed-width record layout byte precision

**Severity:** HIGH. Off-by-one in `TST123-COMMENT-REC` parsing produces silently wrong field values.

**Evidence:**
- `LABD20.pco:43-55` — Record layout. **Note:** at line 55 the *current* definition of `TST123-COMMENT-APPROVER` is `PIC X(014)`, while the commented-out line 54 had `PIC X(020)`. The working storage version at `LABD20.pco:141` redefines it back to `PIC X(020)`. This makes the **input record exactly 8+6+2+10+10+230+20+14 = 300 bytes**, while the working-storage scratch view sees a 20-byte approver field that includes 6 trailing bytes of the next-record buffer.

**Mitigation:**
- Python parser uses `struct.Struct` with explicit offsets; lengths derived from the FD record layout (the 14-byte approver), not the working storage layout.
- Unit tests assert each byte boundary on golden records.
- Logged as Assumption A-4.

**Action required of customer SME:** Confirm the **canonical** approver field width (14 vs. 20) and whether downstream systems expect the column truncated/padded.

---

### Risk 6 — SQLCODE → DMS-style return-code translation

**Severity:** MEDIUM. Callers of DBIO check `ERROR-NUM` (DMS-style 4-character code) — not raw `SQLCODE`. The translation must be preserved.

**Evidence:**
- `DBIO.pco:374-398` — `5300-TRANSLATE-SQLCODE`:
  - `SQLCODE = 0` → `'0000'`
  - `SQLCODE = 100` → `'0013'` (or `'0007'` if `DB-SET-NAME > SPACES` and `FUNCTION-TYPE ≠ 'FETCH OWNER'`)
  - `SQLCODE = -1` → `'0005'`
  - `SQLCODE = -8103` → `'0000'` (continue, log) — Oracle "object no longer exists"
  - Any other value → `'9999'`

**Mitigation:**
- `db_dispatcher.py` ports this table verbatim in `translate_sqlcode(sqlcode, set_name, function_type) -> str`. Test cases assert each branch.

---

### Risk 7 — Transaction rollback paths (SQL and DMS)

**Severity:** MEDIUM. LABD20 has multiple error paths: every `EXEC SQL` checks `SQLCODE NOT = 0` and `GO TO 9999-ROLL-BACK`; the connect step in DBIO has its own DMS-style `IF NOT DB-OK` path.

**Evidence:**
- `LABD20.pco:331-333, 373-375, 402-404, 414-416, 424-426, 434-436, 444-446` — SQL error paths
- `LABD20.pco:489-` — `9999-ROLL-BACK` paragraph
- `LABA05.cbl:171-174, 196-205` — DMS error checks via `ERROR-NUM`

**Mitigation:**
- Modernized Python centralizes rollback in `db_dispatcher.py`. Both validation/data errors and connection errors funnel into a single context manager that rolls back and re-raises with logged context.

---

### Risk 8 — EXTERNAL shared data items

**Severity:** MEDIUM. `JV-CONTROL-REC` and `CONTROL-RECORD-TABLE` are both declared `EXTERNAL` in their copybooks — they are shared memory between the calling program and `CONTROL-RECORD-TABLE-IO`. The Python conversion must model this as a shared in-memory object, not as ad-hoc copies.

**Evidence:**
- `JV-CONTROL-REC.cpy:1` — `01 JV-CONTROL-REC EXTERNAL.`
- `CONTROL-RECORD-TABLE.cpy:24` — `01 CONTROL-RECORD-TABLE EXTERNAL.`

**Mitigation:**
- Python conversion uses dataclasses passed by reference between the loader/reset functions and `db_dispatcher.py` to mirror EXTERNAL semantics.

---

### Risk 9 — Empty / missing real test data

**Severity:** MEDIUM. `test-data/TST.JVCMTS.dat` is effectively empty in the supplied repo, so no real records exist to test against.

**Mitigation:**
- `migration/test-data/synthetic_comments.dat` ships with **20+ synthetic 300-byte records** covering happy path, every validation-failure case, and a duplicate-detection case. Synthetic only — no real customer data.
- `migration/test-data/synthetic_card.ctl` ships with a valid synthetic MM/DD/CCYY card.

---

### Risk 10 — Perl wrapper environment dependencies

**Severity:** MEDIUM. `LABA05.pl` and `LABD20-JV.pl` rely on a `rtsora` runtime plus a number of environment variables (e.g. `ORACLE_HOME`, `LD_LIBRARY_PATH`, `PATH`, file location env vars for `CARDFILE` / `COMMENT`).

**Mitigation:**
- Modernized Python entrypoints accept a config object (env-var-backed) for runtime parameters. The `demo_app.py` entrypoint ships with sane defaults and a mock DB so the modernized programs can be exercised without any external runtime.

**Action required of customer SME:** Provide the canonical list of environment variables / file locations used in production for the orchestration migration plan.

---

### Risk 11 — `PERFORM PERFORM` typo

**Severity:** LOW. Likely benign — the second `PERFORM` is interpreted by COBOL as the paragraph name, so the program still calls `CLOSE-SQL-ENVIRONMENT` as a normal `PERFORM`. But it's a code-smell that should be confirmed.

**Evidence:**
- `LABD20.pco:213` — `PERFORM PERFORM CLOSE-SQL-ENVIRONMENT.`

**Mitigation:**
- Flagged in the requirements doc with a note for SME review. The Python conversion calls `close_sql_environment()` exactly once.

---

### Bonus observation — `JC_COUNT_TBL` describe file primary key

The database describe file at `database/descriptions/describe JC_COUNT_TBL.txt:10` claims the primary key uses `JC_SUBMITTED`. That column does not exist in `JC_COUNT_TBL`. Almost certainly a copy-paste error in the describe file; the real primary key is `JC_SECTION` (the only `NOT NULL` non-timestamp column). Flagged for SME confirmation; the converted code assumes the PK is `JC_SECTION`.
