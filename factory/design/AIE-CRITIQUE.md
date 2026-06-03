# Objective critique of the AIE / A0–A8 design

The customer asked us to be objective and call out what doesn't hold up. This is
that. It is written against the AIE schematic and IFAMS modernization slicksheet
as we understand them (an A0 orchestrator coordinating A1–A8 stage agents, with
an MCP-based governance layer). **Where a critique depends on a schematic detail
we couldn't fully verify from the materials, it is flagged — confirm against the
authoritative design before treating it as settled.** This is not a teardown:
the core instinct (staged pipeline, orchestration, knowledge reuse) is right. The
issues are about where the design adds cost without adding correctness.

## What the design gets right (so we keep it)

- **A staged pipeline is the correct mental model.** Intake → model → map →
  transform → validate → load → test → learn is the right decomposition. We honor
  all of it (see the eight stages in `FACTORY-DESIGN.md` §3).
- **An orchestrator is the right top-level pattern.** Something has to own
  intake, inventory, and roll-up. We keep it.
- **Reusing knowledge across conversions is the right efficiency lever.** Our
  Knowledge Fabric is the same idea, made concrete.

## Seven things to fix

### 1. The eight-agent mesh over-engineers the vertical

Running A1…A8 as separate agents that hand off to each other maximizes the number
of context handoffs, and every handoff is where intent is lost and latency
accrues. The eight stages are a **checklist within one pass**, not eight
processes. **Fix:** one general Devin runs S0–S7 for an interface in a single
pass; parallelize *across interfaces*, where the volume actually is. (Detail in
`FACTORY-DESIGN.md` §4–§5.)

### 2. A3 "transformation code development" leaks into CACI's lane

If an agent in the conversion factory is *writing application transformation
code*, that overlaps the COBOL-rewrite scope that belongs to CACI. The factory
should transform **data** against a target **contract**, not author the
modernized application logic. Left unboundaried, this creates duplicated work and
an accountability gap at cutover. **Fix:** draw the line explicitly — factory
owns data + interface conversion to Momentum's contracts; application code
modernization stays upstream (and we *ingest and verify* it, as the `migration/`
port demonstrates). *(Confirm A3's exact charter against the schematic.)*

### 3. "MCP as the governance layer" is a category error

MCP (Model Context Protocol) is a tool/data **access** protocol — it standardizes
how an agent reaches a system. It is not a governance, control, or compliance
framework, and presenting it as one is a buzzword stretch that will not survive
an ATO/security review. **Governance for a financial conversion is concrete:**
the reconciliation gate (does the money balance?), the per-record audit/provenance
trail, role-based human review of exceptions, and immutable run logs. MCP may be
*how* an agent connects to Momentum or a file share; it is not *why* the
conversion is trustworthy. **Fix:** reframe governance around the control
evidence in `TESTING-AS-THE-PRODUCT.md`; treat MCP as plumbing.

### 4. Testing is positioned as a terminal agent, not the spine

If validation/QA is "the agent near the end," then by the time it runs, the
expensive work is already done on possibly-wrong assumptions. For financial data,
reconciliation must be **inline and continuous** — row accounting and control
totals computed as part of the same pass that maps and emits. **Fix:** make the
reconciliation engine a first-class stage every interface runs (S5/S7), gated in
CI, not a downstream reviewer. (This is the whole thesis of
`TESTING-AS-THE-PRODUCT.md`.)

### 5. The critical-path dependency — Momentum's ICDs — isn't surfaced

The design assumes the target interface specifications exist and are available.
They are the **single biggest schedule risk**: you cannot finalize a mapping or a
contract test without the real Momentum import layout / ICD, the authoritative
USSGL chart, and the fund crosswalk. A design that doesn't foreground this risk
will slip. **Fix:** make the target contract an explicit, versioned dependency
and track the artifacts as answerable customer questions
(`docs/va-fmbt-open-questions.md`).

### 6. The orchestrator has no stated idempotency / restart story

At 110+ interfaces converted in cutover windows, runs *will* be interrupted. A
single orchestrator coordinating stage-agents, without an explicit exactly-once /
resumable design, risks double-posting or dropped records on restart — the most
audit-sensitive failure mode there is. **Fix:** design idempotent re-runs and
resumable waves from the start (test angle #4 in `TESTING-AS-THE-PRODUCT.md`).

### 7. "Autonomous" framing under-specifies the human-in-the-loop

Federal financial conversion cannot be sold as fully unattended, and shouldn't
be. The strength is **expert-in-the-loop**: Devin does the volume; COBOL/finance
SMEs adjudicate exceptions and low-confidence mappings; their corrections feed the
fabric. If the design markets autonomy and hides the review loop, it will fail
the credibility test with the people who have to sign the audit. **Fix:** design
confidence scoring + exception routing in explicitly, and present the SME loop as
a feature, not a caveat (test angles #10–#11).

## Bottom line

Keep the pipeline, the orchestrator, and the knowledge-reuse instinct. Drop the
eight-agent handoff mesh in favor of single-pass + horizontal fan-out, re-anchor
"governance" on reconciliation and provenance rather than MCP, pull testing to
the spine, and foreground the ICD dependency and the human-in-the-loop. The
result is fewer moving parts, faster runs, and a story that survives a security
and audit review.
