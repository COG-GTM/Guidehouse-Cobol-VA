# JV COBOL/Pro*COBOL Modernization — Migration Plan

> Customer-visible execution board for the full migration walkthrough.
> All artifacts under `migration/` are derived outputs, not modifications to customer source.
> Generated outputs are labeled **demo / prep — pending SME review**.

---

## 1. Executive summary

This effort takes the supplied legacy Journal Voucher (JV) batch programs — `LABA05.cbl` (fiscal-year reset) and `LABD20.pco` (daily JV comment ingestion) — and produces:

1. **Structured business requirements** with source citations and confidence ratings, separating what is *confirmed from source* from what is *inferred* from what is *unresolvable without missing copybooks*.
2. **Field-level data lineage** from the fixed-width `TST123-COMMENT-REC` input through working storage, validation, and Oracle table columns, including binary↔display conversion in the `JV-CONTROL-REC` control record.
3. **Dependency graph** spanning programs, copybooks, Perl wrappers, external files, Oracle tables, dynamic dispatch through `DBIO`, and the SQLCODE-to-DMS error translation layer.
4. **Embedded SQL catalog** extracted from `LABD20.pco` and `CONTROL-RECORD-TABLE-IO.pco`, including the dynamically constructed SELECT.
5. **Modernized Python** (`labd20_loader.py`, `laba05_reset.py`, `db_dispatcher.py`) with explicit fixed-width parsing, validation, parameterized Oracle SQL, configuration-driven secrets, and inline citations back to the COBOL source lines.
6. **Parameterized Oracle SQL** for both `JC_*` operations and `CONTROL_RECORD_TABLE` CRUD.
7. **Synthetic test data** covering happy-path, every validation-failure case, and the duplicate-detection case — no real customer data.
8. **Unit tests** (pytest) for the loader and the FY reset with mocked DB connections.
9. **Customer-facing artifacts** — open-questions response, demo walkthrough, conversion-efficiency view, and post-modernization documentation (answering the "can the tool document the *modernized* system?" question directly).
10. **An executive HTML report** with Cognition branding for live walkthroughs.
11. **A runnable demo entrypoint** so the modernized loader and FY reset can be exercised end-to-end against a mock in-memory database with the synthetic data — zero external setup.

> **Read these companion documents first:**
> - [`RISKS-AND-GAPS.md`](./RISKS-AND-GAPS.md) — every risk register entry with mitigation status
> - [`ASSUMPTIONS-AND-PLACEHOLDERS.md`](./ASSUMPTIONS-AND-PLACEHOLDERS.md) — every assumption made, every stub / placeholder / SME-review item, with file:line citations

---

## 2. "Before" state — what the repository already contained

| Area | Path | Notes |
| --- | --- | --- |
| Customer source — COBOL | `source/cobol/LABA05.cbl` (285 lines) | Fiscal-year JV control reset |
| Customer source — Pro*COBOL | `source/procobol/LABD20.pco` (535 lines) | Daily JV comment ingestion |
| Customer source — Pro*COBOL | `source/procobol/DBIO.pco` (407 lines) | Generic Oracle dispatcher + SQLCODE↔DMS translation |
| Customer source — Pro*COBOL | `source/procobol/CONTROL-RECORD-TABLE-IO.pco` (406 lines) | CRUD for `CONTROL_RECORD_TABLE`, dynamic SELECT |
| Copybooks | `source/copybooks/` | `COMCON`, `DBVAR`, `DMCA`, `DMCAERR`, `JV-CONTROL-REC`, `CONTROL-RECORD-TABLE`, `RDMS-ERR-WS`, `RDMS-ERR-RTN` |
| **Missing copybooks (referenced but NOT supplied)** | — | `DATECONV-WS` (referenced `LABD20.pco:182`), `DATECONV-PD` (date validation procedure) |
| Database descriptions | `database/descriptions/` | `CONTROL_RECORD_TABLE`, `JC_SUBMITTED_COMMENT_TBL`, `JC_REJECTED_COMMENT_TBL`, `JC_APPLIED_COMMENT_TBL`, `JC_COUNT_TBL` |
| Perl wrappers | `source/perl/LABA05.pl`, `source/perl/LABD20-JV.pl` | Runtime orchestration; environment variable + `rtsora` dependent |
| Existing analysis | `analysis/dependency-map.md` | High-level dependency map (baseline; superseded by `migration/analysis/dependency-map-detailed.md`) |
| Existing requirements | `business-requirements/initial-requirements.md` | Baseline requirements (BR-LABA05-001…006, BR-LABD20-001…013; superseded by `migration/business-requirements/requirements-with-citations.md`) |
| Test data | `test-data/TST.JVCMTS.dat`, `test-data/DAILY.MM-DD-CCYY.ctl` | `TST.JVCMTS.dat` is effectively empty — synthetic data required |
| Customer questions | `docs/guidehouse-open-questions.md` | 22 questions across 5 stakeholders |

---

## 3. "After" state — what this migration produces

```
migration/
├── MIGRATION-PLAN.md                       (this file)
├── RISKS-AND-GAPS.md                       (11-item risk register)
├── ASSUMPTIONS-AND-PLACEHOLDERS.md         (every assumption + stub + SME action item)
├── README.md                               (index of all artifacts)
├── executive-report.html                   (Cognition-branded full report; live walkthrough)
├── business-requirements/
│   └── requirements-with-citations.md
├── analysis/
│   ├── field-lineage.md
│   ├── dependency-map-detailed.md
│   └── sql-catalog.md
├── converted-code/
│   ├── python/
│   │   ├── labd20_loader.py
│   │   ├── laba05_reset.py
│   │   ├── db_dispatcher.py
│   │   ├── demo_app.py                     (runnable CLI + mock-DB demo entrypoint)
│   │   └── tests/
│   │       ├── test_labd20_loader.py
│   │       └── test_laba05_reset.py
│   └── sql/
│       ├── labd20_operations.sql
│       └── control_record_table_operations.sql
├── test-data/
│   ├── synthetic_comments.dat              (20+ synthetic 300-byte records)
│   └── synthetic_card.ctl                  (synthetic MM/DD/CCYY card)
├── test-results/
│   └── pytest-output.txt
└── docs/
    ├── before-after-comparison.md
    ├── guidehouse-open-questions-response.md
    ├── demo-walkthrough.md
    ├── conversion-efficiency.md
    └── post-modernization-docs.md
```

---

## 4. Phases, tasks, and status

Legend: **To Do** · **In Progress** · **Done**

### Phase 0 — Planning + risk register

| Task | Artifact | Status |
| --- | --- | --- |
| Plan board (this file) | `migration/MIGRATION-PLAN.md` | Done |
| Risk + gap register | `migration/RISKS-AND-GAPS.md` | Done |
| Assumptions + placeholders | `migration/ASSUMPTIONS-AND-PLACEHOLDERS.md` | Done |
| Open PR after Phase 0 commit | branch `demo/full-migration-execution` → `main` | Done |

### Phase 1 — Deep analysis (parallelized across 4 workstreams)

| Task | Artifact | Status |
| --- | --- | --- |
| 1A — Requirements with citations + confidence | `migration/business-requirements/requirements-with-citations.md` | To Do |
| 1B — Field-level lineage | `migration/analysis/field-lineage.md` | To Do |
| 1C — Full dependency graph (mermaid) | `migration/analysis/dependency-map-detailed.md` | To Do |
| 1D — Embedded SQL catalog | `migration/analysis/sql-catalog.md` | To Do |

### Phase 2 — Code conversion (parallelized across 4 workstreams)

| Task | Artifact | Status |
| --- | --- | --- |
| 2A — LABD20 Python loader | `migration/converted-code/python/labd20_loader.py` | To Do |
| 2B — LABA05 Python FY reset | `migration/converted-code/python/laba05_reset.py` | To Do |
| 2C — Parameterized Oracle SQL | `migration/converted-code/sql/labd20_operations.sql`, `…/control_record_table_operations.sql` | To Do |
| 2D — DBIO dispatcher in Python | `migration/converted-code/python/db_dispatcher.py` | To Do |

### Phase 3 — Test generation + validation (parallelized across 4 workstreams)

| Task | Artifact | Status |
| --- | --- | --- |
| 3A — Synthetic test data | `migration/test-data/synthetic_comments.dat`, `synthetic_card.ctl` | To Do |
| 3B — LABD20 unit tests | `migration/converted-code/python/tests/test_labd20_loader.py` | To Do |
| 3C — LABA05 unit tests | `migration/converted-code/python/tests/test_laba05_reset.py` | To Do |
| 3D — Before/after comparison | `migration/docs/before-after-comparison.md` | To Do |

### Phase 4 — Customer-facing artifacts (parallelized across 4 workstreams)

| Task | Artifact | Status |
| --- | --- | --- |
| 4A — Open-questions response | `migration/docs/guidehouse-open-questions-response.md` | To Do |
| 4B — Demo walkthrough script | `migration/docs/demo-walkthrough.md` | To Do |
| 4C — Conversion efficiency view | `migration/docs/conversion-efficiency.md` | To Do |
| 4D — Post-modernization docs | `migration/docs/post-modernization-docs.md` | To Do |

### Phase 5 — Integration, executive report, demo app, PR finalization

| Task | Artifact | Status |
| --- | --- | --- |
| 5A — Pytest run + capture | `migration/test-results/pytest-output.txt` | To Do |
| 5A — Repo index | `migration/README.md` + pointer in root `README.md` | To Do |
| 5A — Executive HTML report | `migration/executive-report.html` (Cognition-branded) | To Do |
| 5A — Runnable demo entrypoint | `migration/converted-code/python/demo_app.py` (CLI + mock DB; zero external setup) | To Do |
| 5B — Update PR description + wait for CI | branch `demo/full-migration-execution` | To Do |

---

## 5. Testing approach

- All unit tests are written for the Python conversions; they exercise the validation rules, duplicate detection, INSERT parameter shape, UPDATE conditional, COMMIT/rollback paths, and the binary↔display JV-NUMBER conversion.
- Tests **mock** the Oracle connection — no live database is required to run them.
- Synthetic 300-byte fixed-width records exercise every validation branch in `DETERMINE-COMMENT-DISPOSITION` (LABD20.pco:259-314) and the duplicate-detection branch (LABD20.pco:317-339).
- The runnable demo entrypoint (`demo_app.py`) ships with an in-process mock of the Oracle dispatcher so a stakeholder can `python demo_app.py` and see ingestion, validation, duplicate detection, and the FY reset run end-to-end with zero external dependencies.

---

## 6. Traceability principles applied across the whole effort

1. **Every requirement cites `source/...:lines`.**
2. **Every Python function has a docstring citing the originating COBOL line(s).**
3. **Every extracted SQL statement has a `-- Source:` comment with file + line range.**
4. **Every assumption is logged in `ASSUMPTIONS-AND-PLACEHOLDERS.md`** with a confidence rating and an SME-action item.
5. **Every risk is logged in `RISKS-AND-GAPS.md`** with a mitigation status.
6. **No customer source under `source/` is modified.**

---

## 7. Constraints honored throughout

- No credentials or secrets in any committed file. The legacy pattern (`/tst/.oralogin`, `/tst/.orapasswd` at `DBIO.pco:33-38`) is **replaced** in the converted Python with environment-variable / config-dict driven access.
- No real customer data — all `.dat` records are synthetic and labeled as such.
- All generated SQL uses bind parameters; the dynamically-constructed SELECT in `CONTROL-RECORD-TABLE-IO.pco` is converted to a static parameterized form.
- All generated artifacts are labeled **demo / prep — pending SME review**.
