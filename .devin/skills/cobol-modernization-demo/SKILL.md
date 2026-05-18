---
name: cobol-modernization-demo
description: Use for Guidehouse/VA COBOL modernization demo tasks involving COBOL/Pro*COBOL analysis, requirements extraction, lineage, SQL/Python conversion, and customer demo artifacts.
---

# COBOL Modernization Demo Skill

Use this skill when working in `COG-GTM/Guidehouse-Cobol`.

## Goal

Create traceable, customer-demo-ready artifacts from the supplied COBOL/Pro*COBOL assets.

## Required First Steps

1. Read `README.md`.
2. Read `AGENTS.md`.
3. Read `docs/email-context.md`.
4. Read `docs/guidehouse-open-questions.md`.
5. Read `docs/source-inventory.md`.
6. Read `analysis/dependency-map.md`.
7. Inspect relevant source:
   - `source/procobol/LABD20.pco`
   - `source/cobol/LABA05.cbl`
   - `source/procobol/DBIO.pco`
   - `source/procobol/CONTROL-RECORD-TABLE-IO.pco`
   - relevant copybooks under `source/copybooks/`
   - relevant table descriptions under `database/descriptions/`

## Source Anchors

### LABA05

Use `source/cobol/LABA05.cbl` for fiscal-year JV control reset behavior.

Key behaviors:
- Connect to DB through `DBIO`.
- Fetch `JV-CONTROL-REC`.
- Set `JV-NUMBER` to `1`.
- Update persisted control record.
- Stop with non-zero return code on key failures.

### LABD20

Use `source/procobol/LABD20.pco` for JV comment ingestion behavior.

Key behaviors:
- Read `CARDFILE` for process date.
- Read external `COMMENT` file line sequentially.
- Parse `TST123-COMMENT-REC`.
- Validate required numeric/date/text fields.
- Check duplicates in `JC_SUBMITTED_COMMENT_TBL`.
- Insert accepted comments into `JC_SUBMITTED_COMMENT_TBL`.
- Update `JC_COUNT_TBL` for section `MA`.
- Commit successful work.
- Query end-of-job table counts.
- Roll back and report context on SQL/DMS errors.

## Known Gaps

Always mention:
- `DATECONV-WS` is referenced but missing.
- `DATECONV-PD` is referenced but missing.
- Exact legacy date validation cannot be fully proven without those copybooks.
- `TST.JVCMTS.dat` is effectively empty, so runnable tests may require synthetic non-production data.

## Output Types

### Requirements

Place in `business-requirements/`.

Requirements must:
- be structured,
- include source citations,
- include confidence/risk notes,
- separate source facts from inferred behavior.

### Dependency/Lineage

Place in `analysis/`.

Lineage must:
- trace input fields to table columns,
- include file/table/copybook dependencies,
- identify missing artifacts and dynamic dispatch.

### SQL Conversion

Place in `converted-code/sql/`.

SQL output must:
- use parameterized Oracle SQL examples,
- include citations in comments,
- avoid credentials,
- document transaction semantics.

### Python Conversion

Place in `converted-code/python/`.

Python output must:
- model fixed-width parsing,
- implement validation rules,
- use parameterized DB access placeholders,
- avoid hardcoded secrets,
- include synthetic tests.

### Customer Demo

Place in `docs/`.

Customer-facing drafts must:
- be concise,
- avoid unverified compliance claims,
- call out assumptions,
- map to Guidehouse open questions.

## Quality Bar

Before completing:
- Do not modify original customer source files.
- Verify generated markdown links/paths.
- Include source citations for every material claim.
- Clearly label generated outputs as demo/prep artifacts.
- Include validation/test notes.
