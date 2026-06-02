# VA FMBT Integration & Conversion Factory — open questions for the customer

This is the list of things we need from VA / Guidehouse / CGI to move the factory
from a runnable **reference** (synthetic data, reconstructed contracts) to a
**production** conversion. We OSINT'd what is publicly knowable; everything that
is program-proprietary or instance-specific is asked for directly here. Each
question says *why* we need it and *what it unblocks*, so it can be triaged fast.

> Companion list: `docs/guidehouse-open-questions.md` holds the COBOL-analysis
> demo questions (the "upstream given"). This file is specifically the net-new
> **integration & conversion factory** scope.

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
| Q-MOM-3 | Are loads **file-based, API-based, or both**, and what is the transport (SFTP drop, Azure storage, Momentum API)? | Determines the emit/transport stage and the security boundary for the load step. |
| Q-MOM-4 | What **environments** are available for load rehearsal (a Momentum sandbox/test instance), and how do we get access? | Moves the load step from simulated to a real round-trip against a non-prod Momentum. |

## B. Legacy source extracts

| ID | Question | Why we need it / what it unblocks |
| --- | --- | --- |
| Q-GL-1 | Provide the **real legacy GL/journal extract layout** (copybook or record spec) and a representative **de-identified** sample file. | Replaces the synthetic `GL-JOURNAL-EXTRACT-REC.cpy`. The parser stage is layout-exact, so the real layout is required for production. |
| Q-GL-2 | What **character encoding / code page** do the extracts use (EBCDIC vs ASCII), and are numeric fields zoned, packed (`COMP-3`), or binary (`COMP`)? | Drives the parser's numeric decoding. Our slice assumes landed ASCII zoned; packed/binary needs explicit handling. |
| Q-GL-3 | What is the **date convention** in the extracts (CCYYDDD Julian, CCYYMMDD, other)? | We assumed CCYYDDD (reusing the repo's DATECONV work). Confirm so date conversion is correct. |
| Q-GL-4 | How are **control totals / trailers** represented in the legacy files today (record counts, hash totals, $ totals)? | Lets reconciliation tie to the source's own declared totals, not just our recomputation. |

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
| Q-GOV-3 | Is the factory **transforming data only**, or is application/transformation code in scope here? (Confirms the CACI boundary.) | Resolves the scope overlap flagged in `factory/design/AIE-CRITIQUE.md` #2. |
