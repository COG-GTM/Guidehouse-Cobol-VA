# Guidehouse / VA FMBT — modernization + integration & conversion factory

Private working repository for the Guidehouse/VA Financial Management Business
Transformation (FMBT) demo. It now contains **two complementary deliverables**
that map onto the real program's lanes of work.

## Read this first — the two halves of this repo

VA's FMBT replaces the legacy core financial system with **iFAMS**, built on
**CGI Momentum®** (the FM QSMO-approved federal financial platform). The work
splits across three parties, and this repo embodies that split:

| Party | Lane | Where it lives in this repo |
| --- | --- | --- |
| **CGI** | The target platform — Momentum SaaS on Azure + its import contracts. | We integrate *to* it (see open questions for ICDs). |
| **CACI** | Rewriting the legacy COBOL application code. | [`migration/`](migration/) — the COBOL→Python port. **Repositioned as the "upstream given."** |
| **Guidehouse + Cognition (Devin)** | The **integration & conversion factory** — moving data + 110+ interfaces into Momentum, with reconciliation as the product. | [`factory/`](factory/) — **the net-new scope.** |

- **[`migration/`](migration/) — the upstream given (CACI's lane, as a stand-in).**
  A faithful COBOL→Python modernization of the JV comment workflow
  (`LABD20`/`LABA05`/`DATECONV`) with 151 passing tests and 79/80 COBOL-vs-Python
  parity. In the FMBT story this is **what CACI delivers**, and our proof that
  Devin can **ingest and verify someone else's modernized code** — not the new
  work, but the input the factory builds on.
- **[`factory/`](factory/) — the Integration & Conversion Factory (Guidehouse's
  net-new layer).** An agent-driven factory that converts legacy VA financial
  interfaces into Momentum-loadable artifacts **and proves each conversion is
  correct** (row + dollar control totals, per-document balance, reject ledger,
  post-load round trip). It includes a **runnable GL/journal reference slice**,
  the factory design + objective critique of the customer's AIE/A0–A8 schematic,
  the playbooks/knowledge/skill/prompts to execute it with Devin, and the
  customer open-questions list. **Start at [`factory/README.md`](factory/README.md).**

> **Engagement posture:** the factory is **designed & documented** here and run
> after the plan is approved. The executive summary of the proposal is
> [`migration/executive-report.html`](migration/executive-report.html).

---

## The upstream-given modernization (`migration/`)

> **Generated migration output:** see [`migration/`](migration/) for the full
> end-to-end deliverable — plan, risk register, business requirements with
> citations, field lineage, dependency map, SQL catalog, modernized Python +
> Oracle SQL, synthetic test data, 52 passing pytest cases, customer-facing
> docs, an executive HTML report, and a runnable demo entrypoint
> (`migration/converted-code/python/demo_app.py`).

## Demo Objective

Guidehouse requested a targeted demo using the supplied COBOL assets to show that Devin/Windsurf can:

1. Ingest and analyze COBOL, Pro*COBOL, copybooks, SQL, control files, and support scripts.
2. Derive business requirements and underlying processing logic.
3. Generate structured business requirements and traceability artifacts.
4. Demonstrate conversion patterns to Oracle SQL and/or Python.
5. Produce dependency, data-flow, test-plan, and conversion-efficiency views.

## Repository Layout

| Path | Purpose |
| --- | --- |
| `source/cobol/` | Original COBOL source programs. |
| `source/procobol/` | Pro*COBOL / embedded SQL programs and generated DB access modules. |
| `source/copybooks/` | COBOL copybooks supplied in the zip. |
| `source/perl/` | Perl wrapper / execution scripts supplied in the zip. |
| `database/sql/` | SQL files supplied in the zip. |
| `database/descriptions/` | Table description notes and sample rows. |
| `test-data/` | Control files and sample data files supplied in the zip. |
| `docs/` | Demo context, customer questions, source inventory, and execution plan. |
| `analysis/` | Derived dependency and data-flow analysis artifacts. |
| `business-requirements/` | Derived functional/business requirements. |
| `converted-code/` | Legacy placeholder — see `migration/converted-code/` for the full deliverable. |
| `migration/` | The COBOL→Python modernization — the **upstream given** (CACI's lane, stand-in). |
| `factory/` | The **Integration & Conversion Factory** — Guidehouse's **net-new** scope (design, runnable GL slice, playbooks, knowledge, prompts). |

## Source Snapshot

The supplied assets center on a VA JV comment-processing workflow:

- `LABA05` resets `JV-NUMBER` on `JV-CONTROL-REC` to `1` at fiscal-year rollover.
- `LABD20` reads comment records from a daily comment file, validates required fields, checks for duplicates, inserts accepted records into `JC_SUBMITTED_COMMENT_TBL`, and updates `JC_COUNT_TBL`.
- `DBIO` dispatches database operations to table-specific modules.
- `CONTROL-RECORD-TABLE-IO` maps legacy control-record access to Oracle `CONTROL_RECORD_TABLE` CRUD operations.

## Repository Layout — Before / After Separation

Customer-supplied artifacts (the "before" / frozen legacy state) live under `source/`, `database/`, and `test-data/`. Modernized derivatives (the "after" state) live under `migration/converted-code/`. Analytical artifacts (dependency maps, lineage, requirements, risk register, executive report) live under `analysis/`, `business-requirements/`, `docs/`, and `migration/`. The two trees are never mixed — `source/` is treated as immutable customer source.

## Closed Gaps (originally flagged as missing)

> ~~`LABD20.pco` references `COPY DATECONV-WS` and `COPY DATECONV-PD`, but those copybooks were not present in the provided zip. Any compile/run reproduction will need either the missing copybooks or a stub of their date-validation routines.~~
>
> **Resolved 2026-05-21 (customer follow-up shipment).** Guidehouse supplied the full date-conversion subsystem closure — 2 copybook wrappers (`DATECONV-WS`, `DATECONV-PD`), the subprogram itself (`source/cobol/DATECONV.cbl`, 1,159 lines, `PROGRAM-ID. DATECONV`), and 4 internal JDN helpers (`JDN-CONSTANTS-WS`, `JDN-PACKET-WS`, `JDN-RECORD-WS`, `JDN-RECORD-ACCESS`). Every `COPY` and `CALL` originating from `LABD20.pco` now resolves end-to-end. The IAI-2012 migration markers (`MIGRTN`) embedded in `DATECONV.cbl` are preserved verbatim as legacy evidence. See [`analysis/dateconv-function-inventory.md`](./analysis/dateconv-function-inventory.md) for the 42-function inventory and [`migration/executive-report.html`](./migration/executive-report.html) for the demo-cycle timeline. Risk 1 (HIGH) → CLOSED, Assumption A-1 → retired, BR-LABD20-006 → LOW → HIGH confidence.

## Security Notes

- Keep this repository private; the contents were provided for a customer-specific demo.
- Do not commit credentials or runtime files such as `.oralogin` or `.orapasswd`.
- Any generated modernization code should use parameterized database access and avoid hardcoded secrets.
- Treat all customer/sample data as sensitive unless explicitly cleared for broader sharing.

## Suggested Demo Flow

1. Open with repository indexing and source inventory.
2. Show dependency map from programs to copybooks, DB modules, tables, files, and scripts.
3. Walk through `LABD20` business rules and generated requirements.
4. Show proposed SQL/Python conversion approach for `LABD20` and `LABA05`.
5. Generate tests from extracted validation and duplicate-detection rules.
6. Close with the open-question response themes in `docs/guidehouse-open-questions.md`.
