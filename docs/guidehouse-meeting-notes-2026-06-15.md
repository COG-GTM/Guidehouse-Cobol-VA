<!-- Guidehouse × Cognition — VA FMBT Integration & Conversion Factory -->
# Guidehouse × Cognition meeting notes — 2026-06-15

Cleaned and structured notes from the 2026-06-15 working session between
Guidehouse and Cognition on the VA Financial Management Business Transformation
(FMBT) interface and data-conversion opportunity. The intent is to capture the
program context, the scope being pursued, and the decisions/open items so the
next working session and the companion white paper start from a shared picture.

> **Status note.** This is an internal working record, not a customer
> deliverable. Items marked **(confirm)** were stated in the meeting but still
> need an authoritative source (a VA/CGI/CACI artifact or a follow-up from the
> Guidehouse team). The artifact-level asks here are tracked formally in
> [`docs/va-fmbt-open-questions.md`](./va-fmbt-open-questions.md) and
> [`docs/guidehouse-meeting-asks.md`](./guidehouse-meeting-asks.md).

---

## 1. Competitive landscape

- VA FMBT is a long-running program to modernize the legacy **Financial
  Management System (FMS)** onto **CGI Momentum** (VA's iFAMS implementation),
  rolled out across **12 deployment waves**. *(System age: the official PWS,
  VA-26-00061414, states the FMS is **30 years old**; working notes from the
  session said "~20 years." Using the PWS figure; discrepancy flagged in
  [open questions](./va-fmbt-open-questions.md).)*
- This is a **re-compete.** Guidehouse has bid this scope before; the award
  carries a **transition-in period** *(working notes said 60 days; the PWS
  incoming-contractor-transition-support optional task specifies a **90-day**
  window — flagged)*.
- The field is small. The last competition drew only **two bidders (CGI and
  Guidehouse)**; this round is expected to draw **fewer than five** — likely
  CGI, **CACI**, and possibly Deloitte and Booz Allen. **The gating requirement
  to bid credibly is knowing Momentum**, and the PWS reinforces this by requiring
  key personnel with prior Momentum implementation experience at a Cabinet-level
  agency.
- **Why Momentum knowledge is rare:** Momentum is CGI's own enterprise SaaS
  financial-ERP product (general ledger, vendor management, acquisitions, fixed
  assets, imaging). Almost no one outside CGI knows it deeply, and **CACI
  acquired CGI's federal business**, which reshuffles who holds that knowledge.
- **Scale of the prize:** CGI's original Momentum systems-integration contract
  was **~$1B, single-vendor** (a "$2B system" all-in). The current pursuit is the
  interface-and-conversion scope around the remaining waves.
- The **current delivery approach is hand-coded**: a workforce of **135+ people**
  builds the conversions and interfaces manually, with **no AI-assisted
  tooling** in the loop today. This is the status quo we are proposing to
  displace/augment.
- Guidehouse + Cognition's differentiation is an **AI-driven approach** built on
  Devin (autonomous software engineering) that produces the interface code, the
  conversion logic, and — critically — the **test harness and audit evidence**,
  with people reviewing exceptions rather than writing every line.

## 2. Program architecture

- FMBT replaces the legacy core financial system (FMS) with **iFAMS** — the
  **Integrated Financial and Acquisition Management System**, VA's implementation
  of **CGI's Momentum Financials and Acquisitions** product (the FM QSMO-approved
  federal core financial platform). Per the PWS, iFAMS runs in the **Veterans
  Affairs Enterprise Cloud on Microsoft Azure (FISMA High)**, delivered through
  CGI's **Software-as-a-Service (SaaS)** model.
- **CGI is the systems integrator (SI).** CGI hosts Momentum, holds the licenses,
  and understands both the legacy environment and Momentum. The interface and
  conversion work is done in **close collaboration with the SI** to define
  configuration and touch points in iFAMS.
- The program is being delivered **wave by wave because the system is large**.
  **Wave 1 started in 2019; the program is currently around wave 6–7.** The
  general shape: **waves 1–6 cover VBA / loan-guaranty**, **waves 6–12 cover
  VHA / payroll.** The **remaining waves are what is being competed** as the
  contract is awarded. Sub-agencies already migrated (e.g., loan guaranty) are on
  Momentum and no longer use FMS.
- Per the PWS, the **VHA CO 2 and EHRM Office waves are priced in the base
  period**; the **remaining waves are priced as optional tasks** (Attachment A).
- The program is fundamentally an **integration and data-conversion** effort:
  the in-scope legacy financial data and the interfaces around it have to move
  from FMS into Momentum, wave by wave, without losing money or breaking
  downstream operations.
- **Interfaces connect VA to both internal and external systems:**
  - *Internal:* electronic health record (EHR), payroll, spending verification
    (confirming funds are available before payroll/spend).
  - *External:* Treasury, vendors, and medical suppliers/hospitals.
- Interfaces run in **both directions** — inbound to Momentum and outbound from
  Momentum. External interfaces export flat files plus the necessary outbound
  processing.

## 3. How Momentum loads data (important correction)

- Momentum sits on an **Oracle backend, but you do not load its tables
  directly.** Data enters through Momentum's **Form Import** and **Reference
  Table Import** batch processes (the PWS names these explicitly, alongside
  PL/SQL and the GSOffline process).
- The legacy exports are **comma-delimited flat files**, and loads run across
  **multiple/various threads**.
- Form Import **applies Momentum's own business-logic validation** as part of the
  load — so the load step is itself a validation gate, not a dumb insert.
  Momentum performs the necessary validation rather than us loading raw tables.
- **History to design around:** past efforts ran **5–6 conversion runs and then
  hit errors.** The practical consequence: our conversion output has to land in
  exactly the format Form Import expects, and our pre-load validation must
  anticipate the rules Form Import will enforce so records don't bounce on load.
  We still need the **Form Import specifications/layouts** per form (tracked as
  `Q-MOM-3`).

## 4. Who owns what (and a contradiction the PWS resolves)

The program involves four parties. Cognition/Devin sits inside Guidehouse's lane
as the AI delivery engine.

| Party | Lane |
| --- | --- |
| **VA** | Program owner. Retains overall program-management responsibility and owns the delivered software — the PWS grants the Government **Unlimited Rights** to source code under FAR 52.227-14. |
| **CGI** | The **systems integrator.** Owns the **Momentum platform**, hosts it (SaaS on Azure), and provides the **import specifications** (Form Import layouts/ICDs), configuration, and **environment access**. We integrate *to* Momentum; the contract **excludes any modifications to the CGI Momentum baseline product**. |
| **CACI / incumbent** | Performs the legacy-side exports and, today, the **hand-coded conversion/interface work** (the 135-person effort). CACI acquired CGI's federal business. *(See the contradiction note below.)* |
| **Guidehouse + Cognition (Devin)** | The **integration & conversion factory** being bid — interface application code, conversion logic, data cleanse, the two-part test harness, the audit trail, and reconciliation evidence. Guidehouse owns program management, O&M, Momentum SME depth (Rama + team), business design documents, the interface inventory, and business-rule sign-off; Cognition/Devin owns the AI-driven code generation and testing. |

> **Contradiction flagged (resolved by the PWS).** The raw session notes are
> internally inconsistent about CACI's lane — at one point "CACI owns the ETL /
> data-conversion code," at another "they're not even writing the ETL." The
> authoritative PWS (VA-26-00061414) settles the scope question for *our* bid: its
> **Scope of Work explicitly covers interface development *and* data-conversion
> development/execution *and* data cleanse.** So the work we are bidding includes
> the conversion, not interfaces alone. What remains genuinely open is the precise
> boundary between the incumbent's current lane and ours at takeover — tracked in
> [open questions](./va-fmbt-open-questions.md) (`Q-GOV-3`).

## 5. What we're bidding on (scope)

- The opportunity is the PWS titled **"Interface and Data Conversion
  Development" (VA-26-00061414, v1.0, dated April 23, 2026)** covering the
  **remaining FMBT waves** — standing up **50–100 interfaces** (inbound and
  outbound) and converting the in-scope data drawn from **~100 source tables**.
- **We are doing two things** (Peter's framing, confirmed by the PWS Scope of
  Work):
  1. **Interface development** — rewrite the inbound/outbound interfaces that
     used to pull from FMS so they now exchange transactions with Momentum/iFAMS.
     Where a **Business Design Document (BDD)** exists it should carry all the
     rules and we accelerate; where it does not, we **reverse-engineer** the
     requirements from legacy behavior.
  2. **One-time data conversion** — migrate the in-scope data from the legacy
     source systems (FMS) into Momentum, then prove it.
- The PWS also puts a **sustained, automated data-cleanse capability** in scope
  (open-transaction and reference-data cleanse; see Section 7).
- **Scope now explicitly includes the interface application code rewrite** — the
  new modules that connect to Momentum instead of FMS — **in addition to** the
  conversion/ETL/mapping and testing. The PWS deliverables include **"iFAMS
  Software Builds including Source Code."** This updates earlier framing that
  treated application/transformation code as out of scope (CACI's lane). (See
  `Q-GOV-3`.)
- **Scope excludes** any modification to the CGI Momentum baseline product, and
  the contractor is to **continue work already in progress** (the re-compete /
  transition reality).
- **Code ownership:** delivered interface/conversion code will live on Momentum
  or in VA's **Azure Government** environment; **VA owns it** (Unlimited Rights),
  and **Guidehouse owns O&M.** Because the code was built on the Government's
  behalf, the working assumption is that **we will get access** to the existing
  interface source.
- Target outcome: a **70% reduction in manual effort** versus the current
  hand-coding approach (the team set this above the 50–60% figure from earlier
  notes — aim higher).
- A **co-authored Guidehouse + Cognition white paper** is the near-term
  deliverable that frames this approach for VA leadership.

## 6. COBOL is not the story here

- The prior demo work (the COBOL→Python modernization of the JV programs) is an
  **upstream "given"**, not the subject of this contract. **COBOL is irrelevant
  to this scope** and should **not** be led with or emphasized.
- This opportunity is about **interfaces and data conversion into Momentum**, the
  test harness that proves correctness, and the audit evidence — framed in
  business and mission terms, not language-migration terms.

## 7. Data scale (and what actually converts)

- The FMS holds **millions of rows — gigabytes of data** — but **we are not
  converting history.**
- **Only open transactions and reference data convert.** "Open transactions" are
  items that have not closed out — e.g., **unpaid invoices and open payments** —
  plus the **reference data** they depend on. The PWS confirms this:
  *"Transactional data cleansing shall be limited to open transactions sourced
  from designated legacy systems."* Historical records are deliberately left
  behind.
- **12 deployment waves** across the full program.
- The next major target is the **VHA wave**, with concrete scale:
  - **50–100 interfaces**
  - **~100 source tables**
  - **4 back-to-back conversion runs**
- Individual conversions run at the scale of **100,000+ records**, where even a
  small failure rate (e.g., 5 failures in 100,000) has to be explained
  record-by-record for audit.

## 8. Two-part testing (testing is the product)

The test harness is the core of the value proposition. It has two parts:

- **Part 1 — Pre-load validation (before data enters Momentum).** Automated
  validation proves:
  - **Row-level accounting** — every record is accounted for; no silent drops.
  - **Dollar-amount integrity** — totals tie to the cent.
  - **Business-rule compliance** — and **every rejection has a documented
    reason**.
- **Part 2 — Post-load verification (after Form Import).** Transaction-level
  test scripts prove the loaded data actually **supports real operations** —
  accounts-payable transactions, purchase orders, and spending-chain integrity.
  **This is where ~75% of the testing value is realized.**
- The PWS frames these as a continuum of named activities our scripts must cover:
  **conversion dry runs (mock migrations)** and **post-conversion data
  verification** on the conversion side, and **Regression, System Integration
  (SIT), User Acceptance (UAT), Load/Performance, and Production Support testing**
  on the interface side — with **automated regression scripts** and **end-to-end
  traceability from requirements to release** (the Requirements Traceability
  Matrix).
- **99% first-pass success rate** is framed as the **goal the test harness drives
  toward across successive waves** — not a day-one promise. Early waves
  establish patterns; later waves converge on it. *(The 99% target is from the
  working notes, not the PWS.)*
- **There is no CI/CD at VA.** Failed tests do **not** flow into an automated
  pipeline — they route into the existing **change control board (CCB)** process.
  Our language should say "change control," never "CI/CD," in customer-facing
  material.

## 9. White paper requirements

- **Co-branded Guidehouse + Cognition (Devin).**
- **2–3 pages**, business-level. Audience is **GS-14/15 government officials with
  no AI experience** — medium verbosity, **no code references, no technical
  architecture internals**, no jargon.
- Government-friendly framing throughout: **audit readiness, compliance,
  traceability, cost reduction, mission outcomes, taxpayer value, risk
  reduction.**
- **No slop** — every sentence carries weight; it should "pass the weight test."
- **Rama's companion technical white paper:** Rama (Guidehouse architect) has a
  companion technical perspective. **Alignment between the two papers is an
  explicit dependency** — the user will request Rama's paper; until it's in hand,
  flag alignment as **pending (confirm)**.

## 10. RFI / proposal status

- The **RFI released in late April (2026).** During the RFI we **will most likely
  not get a demo** — you can't talk to a vendor during the RFI window — so the
  written artifacts have to carry the message.
- There are **three opportunities** in front of us:
  1. **A co-branded white paper** on this tool — **2–3 pages**, business-level,
     "passes the weight test." (This is the companion to Rama's technical paper.)
  2. **A proposal** — hours billed, an estimate, and a **count of interfaces**
     (anchor on the VHA wave: 50–100 interfaces; data conversion across ~100
     tables in 4 back-to-back runs).
  3. **Pricing** — **Justin to talk to Arijit** about pricing with the **small
     business (SBA)** considerations.
- The contract vehicle is governed by the **PWS** (VA-26-00061414); a PWS won't
  contain backend architecture, so we should also **ask for the CGI contract's
  PWS** for additional detail.

## 11. Obfuscated / synthetic data

- All demonstrations and the test harness run on **obfuscated/synthetic data**.
- **No access to production systems is required to prove the capability** —
  reconstructed contracts + synthetic fixtures now, with real artifacts swapped
  in as they arrive (the architecture treats the target contract as external
  reference data, so no rewrite is needed when real layouts land).

## 12. Key people

| Name | Org / role | Note |
| --- | --- | --- |
| **Rama** | Guidehouse architect | Authoring the **companion technical white paper**; alignment dependency for our business-level paper. Brings the Momentum SMEs in. |
| Rahul Jain | Guidehouse, Partner | **Proposed Cognition** for this pursuit; listed author/owner on the AIE iFAMS slicksheet. |
| Peter Lanik | Guidehouse, Director | Primary Guidehouse counterpart; framed the "two things" (interface dev + one-time data conversion). |
| Joe D'Auria | Guidehouse, Director | Listed author/owner on the AIE iFAMS slicksheet. |
| Justin | Guidehouse | Owns **pricing**; to talk to Arijit on the small-business (SBA) angle. |
| Arijit | Guidehouse | **Pricing / SBA** counterpart for Justin. |

> Prior demo reviewers (Jill, Sunil, Srinjoy, Charles, Margarita) are tracked in
> [`docs/guidehouse-open-questions.md`](./guidehouse-open-questions.md).

## 13. Open items / next steps

1. **Obtain CACI's flat-file export formats/layouts** for the FMS tables in scope
   (one layout per table, delimiter/encoding confirmation, field order, control
   totals). → `Q-SRC-1` / Section B in open questions.
2. **Obtain Momentum Form Import specifications/layouts** per form (which forms,
   required fields, validation behavior, reject reporting). → `Q-MOM-3`.
3. **Get Rama's technical white paper** and confirm alignment with the
   business-level paper. → tracked as an alignment dependency.
4. **Confirm the CCB process** that failed tests/exceptions route into (cadence,
   membership, sign-off artifact) — VA has no CI/CD. → `Q-GOV-4`.
5. **Lock the VHA-wave specifics** (50–100 interfaces, ~100 tables, 4 back-to-back
   runs) into the interface inventory and wave plan. → `Q-INT-4`.
6. **Confirm the expanded scope line** (interface application code rewrite + data
   conversion + testing). → `Q-GOV-3`.
7. **Reconcile the FMS system age** — PWS says 30 years; working notes said ~20.
   → `Q-GOV-5`.
8. **Confirm the transition-in window** — working notes said 60 days; PWS says a
   **90-day** incoming-contractor transition. → `Q-GOV-6`.
9. **Confirm "open transactions + reference data only"** (no historical
   conversion) and which legacy tables/record types count as "open." → `Q-SRC-2`.
10. **Request the CGI contract's PWS** and confirm **access to the existing
    interface source code** (Government-owned, Unlimited Rights). → `Q-GOV-7`.
11. **Map Business Design Document (BDD) availability per interface** — drives the
    "accelerate vs. reverse-engineer" estimate. → `Q-INT-5`.
12. **Draft and circulate the co-authored white paper** for Guidehouse review.
