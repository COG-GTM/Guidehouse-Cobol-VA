<!-- Guidehouse × Cognition — VA FMBT Integration & Conversion Factory -->
# `docs/` index

Navigation guide for the documentation in this workspace. The repo holds two
complementary efforts (see the [root README](../README.md)):

1. **The upstream "given"** — the COBOL→Python modernization of the JV programs
   (`migration/`). Most of the demo/analysis docs below describe this.
2. **The net-new integration & conversion factory** — moving VA financial data and
   interfaces into CGI Momentum (`factory/`). The FMBT meeting notes, open
   questions, and white paper below describe this.

> **Start here for the current FMBT pursuit:**
> [`guidehouse-meeting-notes-2026-06-15.md`](./guidehouse-meeting-notes-2026-06-15.md)
> → [`va-fmbt-open-questions.md`](./va-fmbt-open-questions.md)
> → [`cognition-devin-whitepaper-va-fmbt.md`](./cognition-devin-whitepaper-va-fmbt.md).

---

## FMBT integration & conversion factory (net-new scope)

| Document | What it is |
| --- | --- |
| [`guidehouse-meeting-notes-2026-06-15.md`](./guidehouse-meeting-notes-2026-06-15.md) | Cleaned, structured notes from the 2026-06-15 Guidehouse × Cognition working session, reconciled against the official PWS (VA-26-00061414) — program context, the re-compete, the 12-wave roadmap, scope (interfaces + one-time data conversion + cleanse), Momentum Form Import, two-part testing, data scale, key people, and open items. |
| [`cognition-devin-whitepaper-va-fmbt.md`](./cognition-devin-whitepaper-va-fmbt.md) | The co-branded Guidehouse + Cognition business-level white paper (2–3 pages) — the challenge, the two work streams, the test harness, the audit trail, the roadmap, and the responsibility matrix. Written for VA program leadership. |
| [`va-fmbt-open-questions.md`](./va-fmbt-open-questions.md) | The artifacts/decisions needed to move the factory from reference to production — Momentum contracts, legacy extracts, interface inventory/waves, environment, governance, and alignment. Updated 2026-06-15 against PWS VA-26-00061414. |
| [`guidehouse-meeting-asks.md`](./guidehouse-meeting-asks.md) | The meeting-agenda framing of the asks above — decisions and materials tagged by priority, for working the open questions in a live session. |

## Reference material (customer-provided)

| Document | What it is |
| --- | --- |
| [`reference/AIE-iFAMS-Modernization-Slicksheet.md`](./reference/AIE-iFAMS-Modernization-Slicksheet.md) | Guidehouse's own AIE iFAMS modernization slicksheet, transcribed verbatim from the source PDF, plus a crosswalk to this repo's factory artifacts. Use it to speak the customer's language. |
| [`reference/AIE-iFAMS-Modernization-Slicksheet-2026-02-12.pdf`](./reference/AIE-iFAMS-Modernization-Slicksheet-2026-02-12.pdf) | The original slicksheet PDF (2026-02-12). |
| [`../factory/reference/customer-artifacts/fms_ifams_interface_inventory.csv`](../factory/reference/customer-artifacts/fms_ifams_interface_inventory.csv) | Customer-provided FMS↔iFAMS interface inventory (managed-by flags per system). Drives the orchestrator inventory and wave fan-out. |
| [`../factory/reference/customer-artifacts/icd_schema.json`](../factory/reference/customer-artifacts/icd_schema.json) | Machine-readable rendering of the customer ICD sample (`FMBT_ICD-AEI-Sample.docx`). |

> The official PWS **VA-26-00061414** ("Interface and Data Conversion
> Development," v1.0, April 23, 2026) is the authoritative scope document. Its
> facts are folded into the meeting notes, open questions, and white paper above;
> the source `.docx` itself is held with the customer-supplied inputs and is not
> committed to the repo.

## COBOL modernization demo (the upstream given)

| Document | What it is |
| --- | --- |
| [`guidehouse-open-questions.md`](./guidehouse-open-questions.md) | The authoritative COBOL-analysis question list for the original demo, organized by owner. |
| [`demo-plan.md`](./demo-plan.md) | High-level agenda for the targeted Guidehouse COBOL demo. |
| [`customer-demo-script.md`](./customer-demo-script.md) | ~45–60 minute walkthrough script for the JV comment-processing programs (`LABA05`, `LABD20`). |
| [`proposal-demo-script.md`](./proposal-demo-script.md) | Two-scenario proposal demo script — legacy code conversion with parity, and interface generation from an ICD — mapped to the AIE slicksheet. |
| [`demo-walkthrough-guide.md`](./demo-walkthrough-guide.md) | End-to-end walkthrough guide — what to open, in what order, with an honest live-vs-static assessment. |
| [`source-inventory.md`](./source-inventory.md) | Inventory of the supplied COBOL/Pro*COBOL/copybook/script/database assets. |
| [`devin-workflow.md`](./devin-workflow.md) | Repo/indexing state and the Devin workflow notes for this engagement. |
| [`email-context.md`](./email-context.md) | Demo follow-up email context. |
