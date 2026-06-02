# JV-comment load — real, repo-grounded conversion slice

This directory is the **most tangible proof** in the repo that the Integration &
Conversion Factory is built on Guidehouse's actual code, not a reconstruction. It
runs the real legacy JV-comment interface through the entire factory using the
**real Phase-1 modernized parser/validator** and the **real fixture** already in
this repository.

> **All data here is synthetic / non-production** (the fixture is
> `migration/test-data/synthetic_comments.dat`, 21 records). The Momentum target
> contract is a plausible reconstruction pending the authoritative ICD — see
> [`docs/va-fmbt-open-questions.md`](../../../docs/va-fmbt-open-questions.md)
> (Q-MOM-1, Q-MOM-2).

## How this slice is different from the GL slice

| | GL / journal slice | **JV-comment slice (this one)** |
| --- | --- | --- |
| Legacy layout | Reconstructed copybook (`.cpy`) | **Real** `TST123-COMMENT-REC` (LABD20.pco:43-55) |
| Parser | New `gl_extract.py` | **Reuses** `migration/converted-code/python/labd20_loader.py` |
| Validation | New rules in `mapper.py` | **Reuses** the 8 real LABD20 edits (`determine_disposition`) |
| Date check | New `_julian_to_iso` | **Reuses** the Phase-1 `dateconv.py` port of `DATECONV.cbl` |
| Fixture | Generated synthetic | **Real** `synthetic_comments.dat` (the Phase-1 parity fixture) |
| Control evidence | Row + **$ control totals** + balance | Row + **key integrity** + dedup (no $; comments aren't postings) |

The GL slice proves the pattern generalizes to high-stakes financial postings.
This slice proves the factory sits **directly on top of** the work Devin already
did in Phase 1 — same bytes, same edits, same date subprogram.

## The five beats (one vertical slice)

```
profile/parse  ->  map/transform/validate  ->  reconcile  ->  emit  ->  simulate load + post-load test
  extract.py            mapper.py            reconciliation.py  convert.py        convert.py
 (reuses LABD20)     (reuses LABD20 edits)
```

| Stage | Module | What it proves |
| --- | --- | --- |
| Parse | `extract.py` | Reuses the Phase-1 300-byte parser verbatim; adds byte-stream provenance (line index). |
| Map / validate | `mapper.py` | Reuses the 8 real LABD20 edits; each record conforms to the Momentum contract or is rejected with a typed code. Nothing silently dropped. |
| Reconcile | `reconciliation.py` | Row accounting, key integrity, duplicate ledger (LABD20 dedup), reject ledger, load-coverage %. |
| Emit | `convert.py` | Writes the loadable pipe-delimited Momentum file. |
| Simulate load | `convert.py` | Re-reads the emitted file as an opaque inbound interface and re-asserts natural-key uniqueness — an idempotent-load rehearsal. |

## Run it

```bash
cd factory/conversion-datasets/jv-comment-load/python

# convert the REAL fixture: 21 rows -> 7 loaded, 2 duplicates held, 12 rejected
python convert.py ../../../../migration/test-data/synthetic_comments.dat \
    --out /tmp/momentum_jv_comments.psv --report /tmp/jv_recon.json
echo "exit=$?"   # 0 = load-ready

# the control evidence as tests (runs on the real fixture)
python -m pytest -q
```

Expected reconciliation on the real fixture:

| Metric | Value |
| --- | --- |
| rows_in | 21 |
| loaded (unique keys) | 7 |
| duplicates held | 2 |
| rejected | 12 |
| reject reasons covered | all 9 LABD20 edits |
| row_accounting_ok | true |
| key_integrity_ok | true |
| load_ready | **true** |

## Files

| Path | Role |
| --- | --- |
| `source/RECORD-LAYOUT.md` | Citations to the **real** copybook/loader (not a copy) + the byte map. |
| `target/MOMENTUM-JV-COMMENT-IMPORT.md` | The "after" target contract the conversion is tested against. |
| `python/extract.py` | Parser that **reuses** the Phase-1 `labd20_loader`. |
| `python/mapper.py` | Target-contract mapping + **reused** LABD20 validation + typed reject codes. |
| `python/reconciliation.py` | Reconciliation engine (the product). |
| `python/convert.py` | End-to-end driver + Momentum import simulator + CI gate. |
| `python/tests/test_jv_comment_slice.py` | 12 tests over the real fixture: layout reuse, every reject reason, dedup, key integrity, round-trip. |

## What is intentionally NOT here

Per the engagement decision (*design & document the factory; run it after the
plan is approved*), this slice is a **reference prototype**, not the production
factory. It does not connect to a real Momentum instance and uses a synthesized
target contract. Those externalizations, and the horizontal fan-out across 110+
interfaces, are described in [`factory/design/`](../../design/). This slice exists
so the design is grounded in something that actually runs on the real legacy
artifacts — not slideware.
