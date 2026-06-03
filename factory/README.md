# VA FMBT Integration & Conversion Factory

This tree is the **net-new layer Guidehouse delivers**: an agent-driven factory
that converts legacy VA financial data and interfaces into CGI's Momentum
platform, with **reconciliation and validation as the product**. It is the
"Guidehouse scope" half of this repo. The other half — the COBOL→Python
modernization under [`../migration/`](../migration/) — is repositioned as the
**upstream given** (CACI's lane) and is *not* part of the factory.

> **Engagement posture: design & document first; run after approval.** This
> directory is a designed, documented factory with **one runnable reference
> slice** (GL/journal). The full factory is executed after the plan is signed
> off. Everything that runs uses **synthetic, non-production data**.

---

## 1. Why this exists — the problem in one breath

VA's Financial Management Business Transformation (FMBT) is moving core
financials onto **iFAMS**, built on **CGI Momentum®** (the FM QSMO-approved
federal financial platform, <https://www.cgi.com/en/momentum>). Getting there
means moving **110+ interfaces** and years of financial data out of the legacy
system and into Momentum — *correctly*. In a financial system, "correctly" is not
a vibe: if a journal doesn't balance, or a control total drifts by a penny, that
is an audit finding. The factory exists to do that movement at scale and to
**prove** each movement is correct.

## 2. The three lanes (so nobody steps on each other)

| Party | Owns | In this repo |
| --- | --- | --- |
| **CGI** | Momentum (the target platform + its import contracts). | We integrate *to* it; we need its ICDs. |
| **CACI** | The COBOL → modern application rewrite. | The `../migration/` Python port is our stand-in **and** proof we can ingest + verify it. |
| **Guidehouse + Cognition (Devin)** | The **integration & conversion factory**. | **This `factory/` tree.** Net-new. |

The reframe is deliberate: nothing already built is thrown away. The COBOL
analysis work becomes the "upstream given," and the factory is the new value.

## 3. How the factory works — the five beats

Every interface flows through the same pipeline, run as **one pass**:

```
profile/parse  ->  map/transform/validate  ->  reconcile  ->  emit  ->  simulate load + post-load test
```

- **Profile/parse** — read the legacy layout (copybook/DDL) and land raw,
  source-tagged records. No judgment here; parsing stays dumb and separable.
- **Map/transform/validate** — all the judgment: field mapping, fund/USSGL
  crosswalks, `Decimal` scaling, date conversion, derived debit/credit. Every
  failure becomes a **typed reject reason**, never a silent drop.
- **Reconcile** — row accounting (`in == loaded + rejected`), dollar control
  totals (to the cent), per-document debit==credit balance, mapping coverage %.
- **Emit** — write the Momentum-loadable artifact in an explicit, versioned
  target contract's wire format.
- **Simulate load + post-load test** — re-read the emitted file as Momentum
  would and re-assert balance. A green result is a load rehearsal, not just a
  format check.

The eight logical stages (S0–S8) and how they map to the customer's A0–A8
schematic are in [`design/FACTORY-DESIGN.md`](./design/FACTORY-DESIGN.md).

## 4. How it scales — fan out across interfaces, not across steps

The parallelism that matters is **horizontal**: one Devin child session per
interface, each running the whole pipeline end-to-end, orchestrated in **waves**
aligned to FMBT deployment groups. We explicitly do **not** build an
eight-agent mesh that hands a record from stage-agent to stage-agent — that
maximizes context loss and latency without improving correctness (see
[`design/AIE-CRITIQUE.md`](./design/AIE-CRITIQUE.md)). Orchestration model and
wave mechanics: [`design/INTERFACE-WAVE-MODEL.md`](./design/INTERFACE-WAVE-MODEL.md).

## 5. Why testing is the product

The deliverable is the **reconciliation evidence**, and the code is what produces
it. The reconciliation engine, schema/contract tests, Momentum import simulator,
golden-file regression, CI gate, and **eleven test angles the customer's design
didn't call out** (round-trip reverse recon, cutover-window perf, schema-drift,
idempotent restart, referential integrity, duplicate/replay, confidence scoring,
provenance trail, …) are in
[`design/TESTING-AS-THE-PRODUCT.md`](./design/TESTING-AS-THE-PRODUCT.md).

## 6. See it run (the GL/journal reference slice)

```bash
cd conversion-datasets/gl-journal-extract/python
python make_synthetic_data.py                          # synthetic fixtures
python -m pytest -q                                     # 19 control tests
python convert.py ../data/gl_extract_clean.dat          # exit 0, load-ready
python convert.py ../data/gl_extract_unbalanced.dat     # exit 1, gate trips
```

That slice ([`conversion-datasets/gl-journal-extract/`](./conversion-datasets/gl-journal-extract/))
is the concrete instantiation of everything above — the design is grounded in
something that actually runs and balances, not slideware.

### 6a. One-liner: executive report with embedded live terminal

For demos, the static [`factory/executive-report.html`](./executive-report.html)
embeds a real shell (via [`ttyd`](https://github.com/tsl0922/ttyd)) so the
commands above can be typed live, in the page, against this repo:

```bash
brew install ttyd          # one-time prereq
factory/scripts/serve-live-demo.sh
```

The launcher starts a static HTTP server on `:8787`, a writable `ttyd` on
`:7681` (bound to `127.0.0.1`), bootstraps `.venv-demo/` with `pytest` on
first run, and opens the report in your browser. The page's "Run it
yourself" section iframes the terminal; if `ttyd` isn't running, the
section auto-detects and shows the one-liner above as a fallback.
Stop with `Ctrl-C`.

## 7. Directory map

| Path | What it is |
| --- | --- |
| `design/FACTORY-DESIGN.md` | Architecture: the eight stages, the orchestration model, the three-lane split. |
| `design/TESTING-AS-THE-PRODUCT.md` | Control layers + 11 test angles. |
| `design/AIE-CRITIQUE.md` | Objective critique of the customer's A0–A8 / AIE design. |
| `design/INTERFACE-WAVE-MODEL.md` | Interface inventory schema + wave fan-out. |
| `conversion-datasets/gl-journal-extract/` | The runnable reference slice (code, synthetic data, 19 tests, contract). |
| `playbooks/` | The 3 repeatable procedures (convert one interface / build the test harness / orchestrate a wave). |
| `knowledge/` | The Knowledge Fabric (USSGL/TAFS/funds, COBOL patterns, reject taxonomy, Momentum contracts). |
| `prompts/` | Cloud-Devin prompts for the orchestrator and per-interface child sessions. |

## 8. What we need to go from reference to production

Real Momentum ICDs, the authoritative USSGL chart and fund crosswalk, the legacy
extract layouts, and the interface inventory — all enumerated as answerable
questions in [`../docs/va-fmbt-open-questions.md`](../docs/va-fmbt-open-questions.md).
