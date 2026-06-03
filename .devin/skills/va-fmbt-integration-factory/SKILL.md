---
name: va-fmbt-integration-factory
description: Use when executing or extending the VA FMBT Integration & Conversion Factory — converting legacy VA financial interfaces/extracts into CGI Momentum import artifacts with reconciliation, or running the orchestrator/child-session fan-out across interfaces. Distinct from the cobol-modernization-demo skill (that one is the upstream COBOL-analysis "given"; this one is the net-new conversion factory).
---

# VA FMBT Integration & Conversion Factory

Use this skill when working in `COG-GTM/Guidehouse-Cobol-VA` on the **net-new
integration & conversion factory** (the `factory/` tree), as opposed to the
upstream COBOL modernization demo (the `migration/` tree, covered by the
`cobol-modernization-demo` skill).

## Mental model (read this first)

- **Three lanes.** CGI owns Momentum (the target). CACI owns the COBOL→app
  rewrite (the `migration/` Python port is our stand-in + proof we can ingest
  and verify it). **Guidehouse owns the factory** — moving legacy financial data
  and interfaces into Momentum, with reconciliation as the product. The factory
  is the only thing in `factory/` and it is the net-new scope.
- **Testing is the product.** A conversion is "done" only when the money
  provably survives: row accounting, $ control totals, per-document balance,
  reject ledger, and a post-load round-trip. Code is what produces that
  evidence.
- **Design & document first; run after approval.** The factory is run after the
  plan is signed off. The GL/journal slice is the one runnable reference.

## Required first reads

1. `factory/README.md` and the repo `README.md` (before/after framing).
2. `factory/design/FACTORY-DESIGN.md` — the eight stages + orchestration model.
3. `factory/design/TESTING-AS-THE-PRODUCT.md` — control layers + 11 test angles.
4. `factory/design/AIE-CRITIQUE.md` — what we changed vs the customer's A0–A8.
5. `factory/design/INTERFACE-WAVE-MODEL.md` — inventory + wave fan-out.
6. `docs/va-fmbt-open-questions.md` — what is synthetic vs awaiting real artifacts.

## The vertical slice (S0–S7) — one interface, one pass

Run profile → map/validate → reconcile → emit → load-simulate as a **single
pass** for one interface. Do NOT split the stages across separate agents. The
worked, runnable example is the GL/journal slice:

```bash
cd factory/conversion-datasets/gl-journal-extract/python
python make_synthetic_data.py            # regenerate synthetic fixtures
python -m pytest -q                       # 19 control tests
python convert.py ../data/gl_extract_clean.dat            # exit 0, load-ready
python convert.py ../data/gl_extract_unbalanced.dat       # exit 1, gate trips
```

When adding a **new interface**, copy the GL slice's structure: a frozen source
layout under `source/`, a target contract under `target/`, the four python
modules (`gl_extract` → `mapper` → `reconciliation` → `convert`), synthetic
fixtures, and a test file asserting parsing, every reject reason, balance, and
round-trip. Keep parsing dumb and concentrate judgment in the mapper.

## Scaling across interfaces (horizontal fan-out)

Parallelize **across interfaces**, never across the eight stages. The
orchestrator builds the interface inventory and launches one child session per
interface using `scripts/create_devin_session.py` (needs `DEVIN_API_KEY` in the
environment; never print it). See `factory/playbooks/03-interface-wave-fanout.md`.

## Playbooks (the repeatable procedures)

- `factory/playbooks/01-vertical-slice-conversion.md` — convert one interface.
- `factory/playbooks/02-reconciliation-test-harness.md` — build/verify the
  control evidence and CI gate.
- `factory/playbooks/03-interface-wave-fanout.md` — orchestrate a wave.

## Knowledge Fabric

Domain + pattern + reject knowledge lives in `factory/knowledge/`. Read it before
mapping, and **append to it** (especially the reject taxonomy and any SME
corrections) after every run — that feedback loop is stage S8 and is how the
factory gets faster per wave.

## Hard rules

- All sample data is **synthetic / non-production**. Never commit real VA
  financial data, vendor TINs, or credentials. Use parameterized access and
  managed secrets for any real connectivity.
- Use `Decimal` for money, never floats. Control totals compare to the cent.
- Never silently drop a record. Every input line is accepted or rejected with a
  typed reason; `lines_in == loaded + rejected` is an invariant.
- The deliberately-failing `gl_extract_unbalanced.dat` fixture must keep failing
  the gate (exit 1). If it ever passes, the gate is broken.
- Don't write application/transformation *code* that belongs in CACI's lane;
  the factory converts **data** to Momentum's **contracts** (see AIE-CRITIQUE #2).
