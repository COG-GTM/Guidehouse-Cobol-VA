# GL / journal extract — reference conversion slice

This directory is the **concrete, runnable proof** of the Integration &
Conversion Factory pattern, exercised on general-ledger / journal-voucher data —
the data domain VA's Financial Management Business Transformation (FMBT) is
actually about. It is the one place in this repo where you can run a legacy
financial extract through the entire factory and watch the money reconcile.

> **All data here is synthetic and non-production.** The legacy record layout and
> the Momentum target contract are plausible reconstructions, not customer
> artifacts. The authoritative versions are the first items in
> [`docs/va-fmbt-open-questions.md`](../../../docs/va-fmbt-open-questions.md)
> (Q-GL-1, Q-MOM-1, Q-MOM-2).

## Why GL/journal (and not just the JV comment workflow)

The existing modernization demo (`migration/`) ports the JV **comment**
ingestion programs (`LABD20`, `LABA05`, `DATECONV`). That proves Devin can ingest
and verify someone else's modernized COBOL — the "upstream given." But the thing
Guidehouse is selling is **integration & conversion**: moving financial data out
of the legacy system and into Momentum, correctly, at scale. GL/journal postings
are the highest-stakes version of that — if a journal doesn't balance or a
control total drifts by a cent, it is an audit finding, not a bug. So this slice
makes "testing is the product" literal: the deliverable is the reconciliation
evidence, and the code is what produces it.

It also reuses the repo's existing assets honestly: the posting date is carried
in the same `CCYYDDD` Julian convention the repo already ports in
`migration/converted-code/python/dateconv.py`, and `JV-NUMBER` comes from the
same generator family `LABA05` resets at fiscal-year rollover.

## The five beats (one vertical slice)

```
profile/parse  ->  map/transform/validate  ->  reconcile  ->  emit  ->  simulate load + post-load test
   gl_extract.py        mapper.py            reconciliation.py  convert.py        convert.py
```

| Stage | Module | What it proves |
| --- | --- | --- |
| Parse | `gl_extract.py` | Byte-exact fixed-width parsing against the copybook. No validation here — parsing and judgment stay separable. |
| Map / validate | `mapper.py` | Each line either conforms to the target contract or is rejected with a precise reason code. Nothing is silently dropped. |
| Reconcile | `reconciliation.py` | Row accounting, dollar control totals, per-journal debit==credit balance, reject ledger, mapping-coverage %. |
| Emit | `convert.py` | Writes the loadable pipe-delimited target file. |
| Simulate load | `convert.py` | Re-reads the emitted file as an opaque inbound interface and re-asserts journal balance — a load rehearsal, not just a format check. |

## Run it

```bash
cd factory/conversion-datasets/gl-journal-extract/python

# (re)generate the synthetic fixtures
python make_synthetic_data.py

# clean batch — every journal balances, load-ready, exit 0
python convert.py ../data/gl_extract_clean.dat

# batch with the six reject cases — accepted set still balances, exit 0
python convert.py ../data/gl_extract_with_rejects.dat --out /tmp/momentum.psv --report /tmp/recon.json

# unbalanced journal — gate trips, exit 1 (use this in CI to block a bad load)
python convert.py ../data/gl_extract_unbalanced.dat ; echo "exit=$?"

# the control evidence as tests
python -m pytest -q
```

## Files

| Path | Role |
| --- | --- |
| `source/GL-JOURNAL-EXTRACT-REC.cpy` | Frozen "before" — the legacy fixed-width extract layout (synthetic). |
| `target/MOMENTUM-JOURNAL-IMPORT.md` | The "after" target contract the conversion is tested against. |
| `python/gl_extract.py` | Fixed-width parser. |
| `python/mapper.py` | Target-contract mapping + validation + reject reasons. |
| `python/reconciliation.py` | Reconciliation engine (the product). |
| `python/convert.py` | End-to-end driver + Momentum import simulator + CI gate. |
| `python/make_synthetic_data.py` | Deterministic synthetic-fixture generator. |
| `python/tests/test_conversion_slice.py` | 18 tests covering parsing, dates, every reject reason, balance, and round-trip. |
| `data/*.dat` | Generated synthetic fixtures (clean / with-rejects / unbalanced). |

## What is intentionally NOT here

Per the engagement decision (*design & document the factory; run it after the
plan is approved*), this slice is a **reference prototype**, not the production
factory. It does not connect to a real Momentum instance, does not read the real
USSGL chart, and uses a hand-built fund crosswalk. Those externalizations, and
the horizontal fan-out across 110+ interfaces, are described in
[`factory/design/`](../../design/). This slice exists so the design is grounded
in something that actually runs and balances — not slideware.
