<!-- Guidehouse × Cognition — VA FMBT Integration & Conversion Factory -->
# Guidehouse meeting — what we need from you

This is the itemized list of **materials and decisions** that move the factory
from a runnable reference (synthetic data, reconstructed contracts) to a
production conversion. It is structured for the meeting agenda: each item says
what we're asking for, why it matters, and what it unblocks. The full rationale
for every artifact request lives in
[`docs/va-fmbt-open-questions.md`](./va-fmbt-open-questions.md); the IDs below
(Q-MOM-1, etc.) point straight to it.

**How to read this:** items are grouped as **Decisions** (things only you can
decide) and **Materials** (artifacts we need a copy of). Each is tagged
**[blocker]**, **[high]**, or **[later]** by how soon we need it. You can make
real progress pre-award by clearing the **[blocker]** and **[high]** rows; the
**[later]** rows are for the production round-trip.

---

## A. Decisions to make in the meeting

| # | Decision we need | Why it matters | Ref |
| --- | --- | --- | --- |
| D1 | **Scope line: data/interface conversion only, or application code too?** Confirm the factory transforms *data* to Momentum's contracts and that application/transformation-code modernization stays with CACI. | This is the single biggest scope risk. Left ambiguous it creates duplicated work and an accountability gap at cutover. | `Q-GOV-3`, [AIE-CRITIQUE #2](../factory/design/AIE-CRITIQUE.md) |
| D2 | **Execution environment & data boundary** — where does the factory run (VA cloud / Azure tenant / Cognition-managed enclave) and does legacy financial data leave a VA boundary? | Determines the deployment model, the security review path, and whether we use synthetic vs masked-real data in each wave. | `Q-ENV-1`, `Q-ENV-3` |
| D3 | **Governance framing** — agree governance = control evidence (reconciliation gate, per-record audit trail, SME review, immutable run logs), with MCP treated as access plumbing, not the governance layer. | Presenting MCP as "the governance layer" won't survive an ATO/security review; our reconciliation + audit-trail evidence will. | [AIE-CRITIQUE #3](../factory/design/AIE-CRITIQUE.md) |
| D4 | **SME loop ownership & SLA** — who adjudicates low-confidence maps and rejects, and what's the review turnaround? | The learning loop (MVP #3) is designed around real reviewers; we need to design the queue and sign-off around your people. | `Q-GOV-1`, `Q-GOV-2` |
| D5 | **First interface(s) to target post-meeting** — pick 1–2 real interfaces from the inventory to convert first. | Lets us run the exact Scenario-2 flow on a real ICD as the first production proof. | `Q-INT-1` |

---

## B. Materials we need (artifacts)

### B1. Momentum target contracts — **critical path** [blocker]

| Ask | Unblocks | Ref |
| --- | --- | --- |
| Momentum **journal-voucher import** layout / ICD (fields, types, lengths, required/optional, delimiter or fixed-width, header/trailer/control rules). | Replaces our reconstructed contract; every mapping and contract test asserts against it. **This is the #1 blocker.** | `Q-MOM-1` |
| Momentum **import validation rules & reject behavior** (how rejects are reported, partial-load support, batch/commit boundaries). | Lets the import simulator mirror Momentum's real acceptance logic instead of our assumed checks. | `Q-MOM-2` |
| Load **transport** — file-based, API-based, or both (SFTP / Azure storage / Momentum API; FUSE ESB vs batch utilities). | Defines the emit/transport stage and its security boundary. The AIE slicksheet names FUSE ESB + Momentum Web Services — confirm which applies per interface. | `Q-MOM-3` |
| A **Momentum sandbox / test instance** for load rehearsal, and how we get access. | Moves the load step from simulated to a real non-prod round-trip. | `Q-MOM-4` |

### B2. Legacy source extracts [high]

| Ask | Unblocks | Ref |
| --- | --- | --- |
| Real legacy **GL/journal extract layout** (copybook or record spec) + a representative **de-identified** sample. | Replaces the synthetic copybook; the parser is layout-exact. | `Q-GL-1` |
| **Encoding / code page** (EBCDIC vs ASCII) and numeric formats (zoned, `COMP-3` packed, `COMP` binary). | Drives the parser's numeric decoding. | `Q-GL-2` |
| **Date convention** in the extracts (CCYYDDD Julian, CCYYMMDD, other). | Confirms date conversion correctness. | `Q-GL-3` |
| How **control totals / trailers** are represented today (record counts, hash totals, $ totals). | Lets reconciliation tie to the source's own declared totals. | `Q-GL-4` |

### B3. Reference data / crosswalks [high]

| Ask | Unblocks | Ref |
| --- | --- | --- |
| Authoritative **fiscal-year USSGL chart** as configured for VA in Momentum. | Replaces our synthetic USSGL whitelist; real account validation. | `Q-REF-1` |
| **Legacy-fund → Momentum-fund crosswalk** (+ TAFS / appropriation mapping). | Replaces our hand-built crosswalk — the most error-prone mapping in financial conversion. | `Q-REF-2` |
| **Object-class, cost-center/org, and vendor** reference data in Momentum. | Enables referential-integrity checks against target master data. | `Q-REF-3` |

### B4. Interface inventory & waves [high]

| Ask | Unblocks | Ref |
| --- | --- | --- |
| The **full interface inventory** (the "110+ interfaces"): id, direction, source system, volume, criticality. | Populates the orchestrator inventory and the child-session fan-out. | `Q-INT-1` |
| The **FMBT deployment-wave schedule** and interface-to-wave mapping. | Drives wave packing and cutover-window targets. | `Q-INT-2` |
| Expected **peak volumes** (esp. fiscal-year-end) per high-criticality interface. | Sizes the cutover-window performance proof. | `Q-INT-3` |

### B5. Environment, security & compliance [later]

| Ask | Unblocks | Ref |
| --- | --- | --- |
| Applicable **ATO / FedRAMP / NIST 800-53** controls and any boundary we inherit. | Shapes the governance/audit-trail design and the security review path. | `Q-ENV-2` |
| **Data classification & PII** in the extracts (vendor TINs, etc.) and de-identification requirements for non-prod. | Governs synthetic vs masked-real data across test waves. | `Q-ENV-3` |
| Per-wave **sign-off artifact** format (the reconciliation evidence pack your auditors accept). | Lets us tailor the evidence pack to what's actually accepted. | `Q-GOV-2` |

---

## C. What we can do *without* waiting (so the meeting ends with momentum)

These need **nothing further from you** and can start immediately:

- Generate the next 1–2 interfaces against **reconstructed** contracts for any
  interface you name (same flow as Scenario 2), then swap in the real ICD when
  `Q-MOM-1` lands.
- Stand up the **orchestrator inventory** from a partial interface list (even a
  spreadsheet of names + directions) to show the wave fan-out.
- Extend the **reject taxonomy / knowledge fabric** with any reference data you
  can share informally (even a sample fund list), exercising the learning loop.
- Produce **requirements-with-citations** documents for any additional COBOL
  programs you send.

---

## D. The one-slide version (for the agenda)

> **To go from reference to production we need, in priority order:**
> 1. **[blocker]** Momentum ICDs + import/reject rules (`Q-MOM-1/2/3`)
> 2. **[high]** Real legacy extract layouts + de-identified samples (`Q-GL-1..4`)
> 3. **[high]** USSGL chart + fund crosswalk (`Q-REF-1/2`)
> 4. **[high]** Interface inventory + wave schedule (`Q-INT-1/2`)
> 5. **Decisions:** CACI scope line (D1), execution environment (D2),
>    governance framing (D3), SME loop + SLA (D4), first target interface (D5).
>
> **And we can start today** on reconstructed contracts for any interface you
> name (Section C) — no access required.
