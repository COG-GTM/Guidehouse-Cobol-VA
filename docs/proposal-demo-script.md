<!-- Guidehouse × Cognition — VA FMBT Integration & Conversion Factory -->
# Proposal demo script — two scenarios

**Audience:** Guidehouse (Peter + team), VA FMBT stakeholders.
**Goal:** show, on real Guidehouse-supplied COBOL, that an agentic factory can
(1) convert legacy code and (2) generate a new interface from an ICD — with the
control evidence that makes it trustworthy for a financial system.

**Framing (say this up front):** *"Everything you'll see runs on the COBOL you
sent us. Where we don't yet have a VA artifact — a Momentum ICD, the real fund
crosswalk — we reconstructed a stand-in and wrote down exactly what we need from
you to make it production. Nothing here is a mock-up; it's runnable code with the
money reconciled. All data is synthetic."*

This maps directly to the AIE iFAMS slicksheet: AIE's **Knowledge Fabric** and
**Agentic Automation Layer** are exactly what these demos make concrete — and
where the slicksheet leans on MCP "governance," we show governance as *control
evidence* (reconciliation, per-record audit trail, SME loop). See
[`factory/design/AIE-CRITIQUE.md`](../factory/design/AIE-CRITIQUE.md).

---

## The four MVP capabilities, mapped to what you'll watch run

| # | MVP capability (DC's list) | What proves it | Artifact |
| --- | --- | --- | --- |
| 1 | **Legacy code conversion** with extracted rules + parity | Scenario 1 | [`migration/converted-code/python/labd20_loader.py`](../migration/converted-code/python/labd20_loader.py), [`migration/business-requirements/requirements-with-citations.md`](../migration/business-requirements/requirements-with-citations.md) |
| 2 | **Interface generation from an ICD** | Scenario 2 | [`factory/conversion-datasets/obligation-disbursement/`](../factory/conversion-datasets/obligation-disbursement/) |
| 3 | **Learning agent** (knowledge fabric improves over runs) | Scenario 2, beat 5 | [`factory/demos/learning-agent-demo/`](../factory/demos/learning-agent-demo/) |
| 4 | **Audit-trail / lineage visualization** | both scenarios, closing | [`factory/demos/audit-trail-viewer/`](../factory/demos/audit-trail-viewer/) |

Keep all four in your back pocket; they come up naturally in the two scenarios
below.

---

## Scenario 1 — Data conversion (legacy COBOL → modern, with parity)

**One-line:** *"You give us a COBOL program; we give you back readable, tested
code plus a requirements document that cites the original line numbers — and we
prove the new code behaves like the old code."*

### Beat 1 — Start from the real source (before)
- Open [`source/procobol/LABD20.pco`](../source/procobol/LABD20.pco).
- Say: *"This is your daily JV-comment ingestion program. Fixed-width parse,
  date validation, duplicate check against `JC_SUBMITTED_COMMENT_TBL`, insert,
  count update, rollback on error. ~600 lines of Pro*COBOL, embedded SQL, and it
  `COPY`s a date subsystem."*
- Point out the realism: it `CALL`s `DATECONV` and copies `DATECONV-WS` /
  `DATECONV-PD` — a dependency that was **missing** in the first shipment and
  that Guidehouse later supplied. We resolved it end-to-end (see AGENTS.md note).

### Beat 2 — Requirements with citations (the "documentation after modernization" question)
- Open [`migration/business-requirements/requirements-with-citations.md`](../migration/business-requirements/requirements-with-citations.md).
- Say: *"Before we touch conversion, the agent derives the business rules and
  cites the source line ranges for each one. This is the artifact your auditors
  and SMEs review — and it answers your question 'can documentation be generated
  after modernization?' directly: yes, with traceability."*
- Call out a confidence note (e.g. a rule that was LOW confidence while
  `DATECONV` was missing, now HIGH after the closure). *"We don't overstate — we
  mark confidence and what's unverified."*

### Beat 3 — The converted code (after)
- Open [`migration/converted-code/python/labd20_loader.py`](../migration/converted-code/python/labd20_loader.py)
  and [`migration/converted-code/python/dateconv.py`](../migration/converted-code/python/dateconv.py).
- Say: *"Same behavior, modern form: explicit fixed-width parsing, parameterized
  SQL (no string-built queries, no hard-coded credentials like the legacy
  `/tst/.oralogin`), validation, duplicate detection, commit/rollback."*
- Tie to their COBOL questions: *"`COMP`/`COMP-3`/binary fields, line- vs
  record-sequential — these are handled explicitly at the parse layer, not
  guessed."*

### Beat 4 — Parity (the proof)
- Open [`migration/test-results/`](../migration/test-results/) and run the parity
  engine ([`migration/converted-code/python/parity_engine.py`](../migration/converted-code/python/parity_engine.py)).
- Say: *"We generate test scenarios from the derived rules and check the modern
  code against expected legacy behavior. Conversion isn't 'done' because it
  compiles — it's done when it behaves the same and we can show it."*

**Scenario 1 lands:** code conversion (MVP #1), generated documentation,
SME-reviewable citations, parity testing — all on your real program.

---

## Scenario 2 — Interface development from an ICD (the third slice, generated)

**One-line:** *"You give us a target interface contract — a Momentum ICD — plus a
couple of examples of interfaces we've already done. The factory generates the
next interface: parser, mapper, reconciliation, tests, and a load simulation,
with the money tied out."*

This is **Peter's Ask #2**. The repo already has two slices (GL/journal and
JV-comment). For the meeting we generated a **third** — obligation/disbursement —
to show the pattern generalizes, not that we hand-built three one-offs.

### Beat 1 — The target contract (the ICD)
- Open [`factory/conversion-datasets/obligation-disbursement/target/MOMENTUM-OBLIGATION-IMPORT.md`](../factory/conversion-datasets/obligation-disbursement/target/MOMENTUM-OBLIGATION-IMPORT.md).
- Say: *"This is the contract the factory converts toward — obligation number,
  vendor, appropriation, object class, obligation vs disbursement amounts, period
  of performance, TAFS. In production this is your real Momentum ICD; here it's a
  reconstruction, and it's the #1 thing on our ask list."*

### Beat 2 — The pattern it learned from
- Show the GL slice ([`factory/conversion-datasets/gl-journal-extract/`](../factory/conversion-datasets/gl-journal-extract/))
  side by side.
- Say: *"The factory reused these patterns verbatim — `Decimal` money,
  USSGL validation, the fund crosswalk, the reject taxonomy, the
  reconciliation engine — and added only what's new to obligations."*

### Beat 3 — What's net-new for this interface
- Open [`factory/conversion-datasets/obligation-disbursement/python/mapper.py`](../factory/conversion-datasets/obligation-disbursement/python/mapper.py).
- Say: *"The obligation-specific rule that matters: total disbursements can't
  exceed the obligation. That's an Antideficiency-class control. Watch what
  happens when it's violated."*

### Beat 4 — Run it; the control totals are the product
- Run the clean batch:
  ```bash
  cd factory/conversion-datasets/obligation-disbursement/python
  python convert.py ../data/obl_disbursement_clean.dat ; echo "exit=$?"
  ```
  *"Five lines in, five accepted, control total ties, `LOAD_READY=True`, exit 0."*
- Run the deliberately broken batch:
  ```bash
  python convert.py ../data/obl_disbursement_unbalanced.dat ; echo "exit=$?"
  ```
  *"Same code, an obligation over-disbursed. The gate trips, `LOAD_READY=False`,
  exit 1. The factory refuses to load money that doesn't reconcile — and it tells
  you exactly which obligation and by how much."*
- Show the tests pass:
  ```bash
  python -m pytest -q
  ```

### Beat 5 — The learning agent (MVP #3)
- Say: *"Interfaces fail the first time because reference data is incomplete —
  an unmapped fund, a USSGL account not in the chart. Here's the loop that fixes
  that permanently."*
- Run it:
  ```bash
  cd factory/demos/learning-agent-demo
  python run_learning_demo.py
  ```
- Walk the before/after table: *"Pass 1 — three rejects, 50% coverage, not
  load-ready. An SME confirms the rejects are valid; the knowledge fabric grows
  by two entries. Pass 2, same input — zero rejects, 100% coverage, load-ready.
  And notice one of the learned accounts, 490200, is one the obligation slice
  already knew — knowledge learned on one interface transfers to the next."*
- Point to the Git diff on
  [`factory/knowledge/reject-taxonomy.md`](../factory/knowledge/reject-taxonomy.md):
  *"Every correction is a reviewable commit, not a black box."*
- This is the slicksheet's **Knowledge Fabric "continuous learning"** made
  concrete and runnable.

### Beat 6 — The audit trail (MVP #4)
- Generate and open the viewer:
  ```bash
  cd factory/demos/audit-trail-viewer
  python generate_audit_trail.py --slice obligation --fixture with_rejects
  # open audit_trail_viewer.html
  ```
- Say: *"Every record's journey, byte-row to load status, S0 through S7, with the
  exact rule that accepted or rejected it. This is the 'audit-ready evidence'
  the slicksheet promises — here you can click into any rejected dollar and see
  why. Nothing is silently dropped: lines in equals loaded plus rejected."*

**Scenario 2 lands:** interface generation from an ICD (MVP #2), the learning
loop (MVP #3), and the audit trail (MVP #4) — all built on the two prior slices.

---

## Addressing Peter's key points (have these ready)

### 1. Access requirements — *"do you need our whole environment?"*
**No. Sample files suffice to start.** Scenario 1 ran on the COBOL programs you
emailed. To generate an interface (Scenario 2) we need a **target contract and a
representative de-identified sample** — not production access, not a Momentum
login. Production access (a Momentum sandbox for a real load round-trip) is a
*later* milestone, tracked as `Q-MOM-4` / `Q-ENV-1`. → see
[`guidehouse-meeting-asks.md`](./guidehouse-meeting-asks.md).

### 2. Pre-award strategy — *"how do we make progress before we have everything?"*
**Synthetic data + reconstructed contracts now; swap in real artifacts later.**
Every slice you'll see runs on synthetic fixtures against a *reconstructed*
Momentum ICD. The architecture is built so the real ICD, USSGL chart, and fund
crosswalk drop in as **versioned reference data** with no code rewrite — that's
the whole point of treating the contract as an external dependency. So work
starts pre-award and converges as the customer artifacts arrive.

### 3. Human review model — *"where does the SME fit; how do we trust it?"*
Three concrete mechanisms, all visible in the demo:
- **Confidence scoring & reject taxonomy** — low-confidence maps and typed
  rejects are surfaced, not buried (`factory/knowledge/reject-taxonomy.md`).
- **SME exception queue** — the learning demo *is* the loop: SME adjudicates,
  the fabric updates, the next run improves. Reviewers are designed in
  (`Q-GOV-1`, `Q-GOV-2`).
- **Git-based inspection** — requirements, mappings, and learned corrections are
  all diffable commits; the audit-trail viewer makes per-record provenance
  clickable. Trust comes from **control evidence** (does the money balance?),
  not from trusting the model.

---

## If you only have 10 minutes

1. Scenario 2, Beat 4 — run clean (exit 0) then unbalanced (exit 1). *The gate is
   the story.*
2. Scenario 2, Beat 5 — the learning loop before/after table.
3. Scenario 2, Beat 6 — click one rejected record in the audit-trail viewer.

That sequence shows generation, control, learning, and auditability in three
commands.

---

## Closing line

*"What you saw is a runnable reference on your own code. To turn it into a
production conversion we need a short list of artifacts from you — the Momentum
ICDs, the fund crosswalk, the USSGL chart, the interface inventory. That list is
the meeting-asks doc. Give us those and the same machinery you just watched runs
against the real thing."*
