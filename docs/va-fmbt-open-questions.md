# VA FMBT Integration & Conversion Factory — open questions for the customer

This is the list of things we need from VA / Guidehouse / CGI to move the factory
from a runnable **reference** (synthetic data, reconstructed contracts) to a
**production** conversion. We OSINT'd what is publicly knowable; everything that
is program-proprietary or instance-specific is asked for directly here. Each
question says *why* we need it and *what it unblocks*, so it can be triaged fast.

> Companion list: `docs/guidehouse-open-questions.md` holds the COBOL-analysis
> demo questions (the "upstream given"). This file is specifically the net-new
> **integration & conversion factory** scope.
>
> **Updated 2026-06-15** from the Guidehouse × Cognition working session and the
> official PWS **VA-26-00061414** ("Interface and Data Conversion Development,"
> v1.0, April 23, 2026) — see
> [`docs/guidehouse-meeting-notes-2026-06-15.md`](./guidehouse-meeting-notes-2026-06-15.md).
> Material changes this round: `Q-MOM-3` (Momentum loads via **Form Import**,
> not a direct table load), `Q-GOV-3` (scope now includes the interface
> application code rewrite), new `Q-SRC-1` (CACI flat-file export layouts),
> `Q-SRC-2` (open-transactions-only confirmation), `Q-INT-4` (VHA-wave scale),
> `Q-INT-5` (BDD availability per interface), `Q-GOV-4` (change-control board /
> no CI-CD), `Q-GOV-5` (FMS age 30 vs 20), `Q-GOV-6` (transition 90 vs 60 days),
> `Q-GOV-7` (CGI PWS + source-code access), and `Q-ALIGN-1` (Rama white-paper
> alignment).
>
> Where the working notes and the PWS disagree, the **PWS is treated as
> authoritative** and the discrepancy is flagged rather than silently absorbed.

## What we already established from open sources

- **Momentum is the target.** CGI's Momentum® Enterprise Suite is the
  FM QSMO-approved federal core financial management platform iFAMS is built on
  (<https://www.cgi.com/en/momentum>). So the factory integrates *to* Momentum's
  import contracts; it does not build the platform.
- **The data domain is core financials** — general ledger / journal vouchers,
  obligations, disbursements, USSGL posting, TAFS/appropriation structures,
  object-class coding. The GL/journal reference slice is built on these public
  standards.
- **What is NOT public** — the actual Momentum import layouts / ICDs for this
  VA instance, the VA fund crosswalk, the fiscal-year USSGL chart as configured,
  and the interface inventory. These are the questions below.

## A. Momentum target contracts (highest priority — critical path)

| ID | Question | Why we need it / what it unblocks |
| --- | --- | --- |
| Q-MOM-1 | Can you provide the Momentum **journal-voucher import** layout / ICD (field names, types, lengths, required vs optional, delimiter or fixed-width, header/trailer/control-record rules)? | This is the target contract every mapping and contract test asserts against. Today we use a reconstructed contract (`factory/.../target/MOMENTUM-JOURNAL-IMPORT.md`). Real ICD → real conversion. |
| Q-MOM-2 | What are Momentum's **import validation rules and reject behavior** (how it reports rejects, whether partial loads are possible, batch/commit boundaries)? | Lets the import simulator mirror Momentum's actual acceptance logic instead of our assumed journal-balance check. |
| Q-MOM-3 | **Form Import specifications/layouts.** *(Updated 2026-06-15: loads are **not** a direct table load — they go through Momentum's **Form Import** and **Reference Table Import** batch processes, which apply Momentum's own business-logic validation on load; legacy exports arrive as **comma-delimited flat files**.)* Which Momentum **forms** are in scope, and what is each form's import layout — field names/order, required vs optional, the validation rules Form Import enforces, and how it reports rejects? | Form Import is the real target contract and the real reject gate. The conversion must emit exactly what Form Import expects, and our pre-load validation must anticipate the rules Form Import enforces so records don't bounce on load. |
| Q-MOM-4 | What **environments** are available for load rehearsal (a Momentum sandbox/test instance), and how do we get access? | Moves the load step from simulated to a real round-trip against a non-prod Momentum. |

## B. Legacy source extracts

| ID | Question | Why we need it / what it unblocks |
| --- | --- | --- |
| Q-GL-1 | Provide the **real legacy GL/journal extract layout** (copybook or record spec) and a representative **de-identified** sample file. | Replaces the synthetic `GL-JOURNAL-EXTRACT-REC.cpy`. The parser stage is layout-exact, so the real layout is required for production. |
| Q-GL-2 | What **character encoding / code page** do the extracts use (EBCDIC vs ASCII), and are numeric fields zoned, packed (`COMP-3`), or binary (`COMP`)? | Drives the parser's numeric decoding. Our slice assumes landed ASCII zoned; packed/binary needs explicit handling. |
| Q-GL-3 | What is the **date convention** in the extracts (CCYYDDD Julian, CCYYMMDD, other)? | We assumed CCYYDDD (reusing the repo's DATECONV work). Confirm so date conversion is correct. |
| Q-GL-4 | How are **control totals / trailers** represented in the legacy files today (record counts, hash totals, $ totals)? | Lets reconciliation tie to the source's own declared totals, not just our recomputation. |
| Q-SRC-1 | Obtain **CACI's flat-file export formats/layouts** for the FMS tables in scope (one layout per table: field order, delimiter — confirmed comma-delimited — encoding, and any per-file control totals). *(CACI owns the legacy exports; this is their lane.)* | CACI's exports are the actual factory inputs. Real layouts replace the synthetic copybooks and make the parser layout-exact per table across the ~100-table VHA wave. |
| Q-SRC-2 | **Confirm "open transactions + reference data only"** — no historical conversion — and define which legacy tables/record types count as "open" (e.g., unpaid invoices, open/unclosed payments). *(PWS: "Transactional data cleansing shall be limited to open transactions sourced from designated legacy systems.")* | Sizes the actual conversion volume (the FMS holds gigabytes, but only the open + reference slice converts) and scopes the data-cleanse effort. Corrects an earlier "historical / 100+ tables" framing in the white-paper draft. |

## C. Reference data / crosswalks

| ID | Question | Why we need it / what it unblocks |
| --- | --- | --- |
| Q-REF-1 | The authoritative **fiscal-year USSGL chart** as configured for VA in Momentum. | Replaces our synthetic USSGL whitelist; enables real account validation. |
| Q-REF-2 | The **legacy-fund → Momentum-fund crosswalk** (and TAFS/appropriation mapping). | Replaces our hand-built crosswalk; the single most error-prone mapping in financial conversion. |
| Q-REF-3 | **Object-class, cost-center/org, and vendor** reference data in Momentum. | Enables referential-integrity checks against target master data (test angle #8). |

## D. Interface inventory & waves

| ID | Question | Why we need it / what it unblocks |
| --- | --- | --- |
| Q-INT-1 | The **full interface inventory** (the "110+ interfaces"): id, direction, source system, volume, criticality. | Populates the orchestrator's inventory and the child-session fan-out. |
| Q-INT-2 | The **FMBT deployment-wave schedule** and which interfaces belong to which wave. | Drives wave packing and the cutover-window performance targets. |
| Q-INT-3 | Expected **peak volumes** (esp. fiscal-year-end) per high-criticality interface. | Sizes the cutover-window performance proof (test angle #2). |
| Q-INT-4 | Confirm the **VHA-wave specifics** captured 2026-06-15 — **50–100 interfaces, ~100 tables, 4 back-to-back conversion runs** — and bind them to the interface inventory and wave plan. | Sizes the first major wave's child-session fan-out, the number of conversion runs to orchestrate back-to-back, and the per-run reconciliation roll-up. |
| Q-INT-5 | For the in-scope interfaces, **which have a current Business Design Document (BDD)** and which do not? | Drives the "accelerate vs. reverse-engineer" split that anchors the proposal's hours/estimate. Where a BDD carries the rules we accelerate; where it is missing we reconstruct requirements from legacy behavior. |

## E. Environment, security & compliance

| ID | Question | Why we need it / what it unblocks |
| --- | --- | --- |
| Q-ENV-1 | Where does the factory **execute** (VA cloud, Azure tenant, Cognition-managed enclave), and what is the data-handling boundary for legacy financial data? | Determines deployment model and whether data leaves a VA boundary. |
| Q-ENV-2 | What **ATO / FedRAMP / NIST 800-53** controls apply, and is there an existing boundary we inherit? | Shapes the governance/audit-trail design and the security review path. |
| Q-ENV-3 | **Data classification & PII** in the financial extracts (vendor TINs, etc.) and de-identification requirements for non-prod. | Governs how synthetic vs masked-real data is used in test waves. |

## F. Governance & SME loop

| ID | Question | Why we need it / what it unblocks |
| --- | --- | --- |
| Q-GOV-1 | Who are the **finance/COBOL SMEs** who adjudicate exceptions, and what is the review SLA? | The factory routes low-confidence maps + rejects to SMEs; we need to design the loop around real reviewers. |
| Q-GOV-2 | What **sign-off artifact** does the customer need per wave (the reconciliation evidence pack format)? | Lets us tailor the per-wave evidence pack to what their auditors actually accept. |
| Q-GOV-3 | **Confirm the expanded scope line.** *(Updated 2026-06-15: scope now explicitly includes the **interface application code rewrite** — the new modules that connect to Momentum instead of FMS — **in addition to** data conversion/ETL and testing.)* Confirm in writing that interface application code is in our lane and that CACI's lane is the legacy flat-file **exports**. | Locks the single biggest scope risk. Earlier framing (`factory/design/AIE-CRITIQUE.md` #2) drew the line at data-only; this updates it, removing the duplicated-work / accountability-gap risk at cutover. |
| Q-GOV-4 | **Change-control board (CCB) process.** *(Noted 2026-06-15: VA has **no CI/CD** — failed tests/exceptions route into a **change control board**, not an automated pipeline.)* What is the CCB cadence, membership, and expected sign-off artifact, and how do failed-test exceptions enter it? | Our reconciliation/exception evidence must be packaged for the CCB, not a build pipeline. Shapes the per-wave evidence pack and the SME exception flow. Customer-facing language must say "change control," never "CI/CD." |
| Q-GOV-5 | **Reconcile the FMS system age.** The PWS BACKGROUND states the FMS is **30 years old**; the working-session notes said **~20 years**. Which is correct for proposal/white-paper use? | A contradictory customer-facing number undermines credibility. We default to the PWS figure (30 years) in customer-facing material until confirmed. |
| Q-GOV-6 | **Confirm the transition-in window.** Working notes said a **60-day** transition-in; the PWS incoming-contractor-transition-support optional task specifies a **90-day calendar period**. Which governs, and are we incumbent or challenger for that transition? | Drives the transition staffing/ramp plan and the optional-task pricing. |
| Q-GOV-7 | **Request the CGI contract's PWS** and **confirm access to the existing interface/conversion source code** (Government-owned; PWS grants Unlimited Rights under FAR 52.227-14). Also request the FMBT reference documents the PWS cites (ICD Processes & Procedures v3.0, Data Cleanse BRD v1.6, Data Cleansing Data Quality Baseline v1.0, VHA Data Cleansing Plan v1.1). | The PWS won't carry backend architecture; the CGI PWS and the cited reference docs fill the gap. Confirmed source-code access turns "reverse-engineer from behavior" into "accelerate from existing code" for many interfaces. |

## G. Program alignment & positioning

| ID | Question | Why we need it / what it unblocks |
| --- | --- | --- |
| Q-ALIGN-1 | Obtain **Rama's (Guidehouse architect) companion technical white paper** and confirm the co-authored business-level paper aligns with it. | The Guidehouse + Cognition white paper is the business-level companion to Rama's technical perspective; the two must not contradict each other. Alignment is an explicit dependency before the paper goes to VA leadership. |
