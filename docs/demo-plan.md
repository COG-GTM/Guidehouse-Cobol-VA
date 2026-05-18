# Targeted Guidehouse Demo Plan

## Proposed Agenda

1. **Repo ingestion and indexing** - Show the supplied COBOL/Pro*COBOL/copybooks/scripts/database notes indexed together.
2. **Source inventory** - Walk through `docs/source-inventory.md` and identify primary programs, wrappers, and table artifacts.
3. **Dependency graph** - Use `analysis/dependency-map.md` to show program, copybook, file, and table relationships.
4. **Business requirements extraction** - Show `business-requirements/initial-requirements.md`, then ask Devin to refine requirements with source citations.
5. **Conversion demo** - Generate either a Python loader for `LABD20` or SQL operations extracted from embedded SQL.
6. **Test generation** - Generate validation/duplicate/error-path test scenarios from the derived requirements.
7. **Open questions** - Use `docs/guidehouse-open-questions.md` as the Q&A backbone.

## Suggested Devin Tasks

- "Build a complete dependency graph for this COBOL repo, including copybooks, embedded SQL tables, external files, Perl wrappers, and missing dependencies."
- "Derive customer-ready functional requirements for LABD20 with citations to the original source lines."
- "Generate a Python implementation sketch for LABD20's fixed-width parser, validation rules, duplicate check, inserts, count update, commit, and rollback behavior."
- "Extract the SQL operations from LABD20 and CONTROL-RECORD-TABLE-IO into parameterized SQL with notes on original COBOL line references."
- "Generate test scenarios and expected outcomes from the LABD20 validation and duplicate-handling logic."

## Demo Caveats

- The supplied sample data file is effectively empty, so any runnable test demo may need synthetic non-production records.
- Missing date conversion copybooks mean exact legacy date validation must be confirmed or stubbed.
- Customer-facing security/compliance claims should be confirmed with the current Cognition/Windsurf federal positioning before final delivery.
