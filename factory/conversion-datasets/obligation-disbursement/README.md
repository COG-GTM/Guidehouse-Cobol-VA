# Obligation / disbursement — ICD-driven conversion slice

This directory is the **third runnable conversion slice** in the factory, and the
one built to demonstrate **ICD-driven interface generation**: given the Momentum
target contract (an ICD) plus the two existing slices (GL/journal and JV-comment)
as worked examples, the factory produces a complete vertical slice — parser,
mapper, reconciliation, tests, and synthetic fixtures — for a brand-new interface
in one pass.

It is exercised on the **obligation → disbursement spending chain**: the
highest-stakes integrity rule in federal financial management, because
disbursing more than was obligated is an Antideficiency-Act-class finding, not a
rounding nit.

> **All data here is synthetic and non-production.** The legacy record layout and
> the Momentum target contract are plausible reconstructions, not customer
> artifacts. The authoritative versions are open questions in
> [`docs/va-fmbt-open-questions.md`](../../../docs/va-fmbt-open-questions.md)
> (Q-OBL-1, Q-MOM-1, Q-MOM-2, Q-REF-1, Q-REF-2).

## Why obligation/disbursement (and why it proves "generation from an ICD")

The first two slices proved the factory can convert (GL/journal) and can reuse
real modernized COBOL edits (JV-comment, grounded in `LABD20`). This slice proves
the **acceleration claim**: the factory does not hand-build each of the 110+ VA
interfaces from scratch. Given a target contract and prior slices as patterns, it
generates the next one — reusing the USSGL whitelist, the fund crosswalk, and the
`CCYYDDD` date convention verbatim from the GL slice, and adding only the rules
unique to this domain. That reuse is the [S8 knowledge fabric](../../knowledge/)
working: every slice makes the next one cheaper. (This is exactly the
"Contextual Generation from proven patterns" capability in the customer's own AIE
framing — see `docs/reference/`.)

## What is reused vs. net-new

| Reused verbatim from the GL slice | Net-new for this domain |
| --- | --- |
| `USSGL_WHITELIST`, `FUND_CROSSWALK` | Obligation/disbursement `TXN_TYPE_MAP` |
| `_julian_to_iso` (CCYYDDD), `_scaled_amount` (`Decimal`) | Period-of-performance window validation (`BAD_POP`) |
| Reject taxonomy + "never silently drop" invariant | `MISSING_VENDOR`, `MISSING_OBLIGATION_NO`, `BAD_TXN_TYPE` |
| Row accounting + `$` control-total gates | **Per-obligation funding gate** (Σ disbursements ≤ Σ obligation) |
| Pipe-safe wire emit + import-simulator round trip | Obligation-funding re-assertion at load time |

## The five beats (one vertical slice)

```
profile/parse  ->  map/transform/validate  ->  reconcile  ->  emit  ->  simulate load + post-load test
 obl_extract.py        mapper.py            reconciliation.py  convert.py        convert.py
```

| Stage | Module | What it proves |
| --- | --- | --- |
| Parse | `obl_extract.py` | Byte-exact fixed-width parsing against the 250-byte copybook. No validation here — parsing and judgment stay separable. |
| Map / validate | `mapper.py` | Each line either conforms to the target contract or is rejected with a precise reason code. Obligation-specific rules (vendor required, POP window, txn type) live here. Nothing is silently dropped. |
| Reconcile | `reconciliation.py` | Row accounting, dollar control totals, **per-obligation funding** (disbursed ≤ obligated), reject ledger, mapping-coverage %. |
| Emit | `convert.py` | Writes the loadable pipe-delimited target file. |
| Simulate load | `convert.py` | Re-reads the emitted file as an opaque inbound interface and re-asserts the funding rule — a load rehearsal, not just a format check. |

## Run it

```bash
cd factory/conversion-datasets/obligation-disbursement/python

# (re)generate the synthetic fixtures
python make_synthetic_data.py

# clean batch — every obligation funded, load-ready, exit 0
python convert.py ../data/obl_disbursement_clean.dat

# batch with the ten reject cases — accepted set still funded, exit 0
python convert.py ../data/obl_disbursement_with_rejects.dat --out /tmp/momentum_obl.psv --report /tmp/recon_obl.json

# over-disbursed obligation — gate trips, exit 1 (use this in CI to block a bad load)
python convert.py ../data/obl_disbursement_unbalanced.dat ; echo "exit=$?"

# the control evidence as tests
python -m pytest -q
```

## Files

| Path | Role |
| --- | --- |
| `source/OBL-DISBURSEMENT-REC.cpy` | Frozen "before" — the legacy fixed-width extract layout (synthetic). |
| `target/MOMENTUM-OBLIGATION-IMPORT.md` | The "after" target contract (ICD) the conversion is tested against. |
| `python/obl_extract.py` | Fixed-width parser. |
| `python/mapper.py` | Target-contract mapping + validation + reject reasons. |
| `python/reconciliation.py` | Reconciliation engine (the product) with the per-obligation funding gate. |
| `python/convert.py` | End-to-end driver + Momentum import simulator + CI gate. |
| `python/make_synthetic_data.py` | Deterministic synthetic-fixture generator. |
| `python/tests/test_conversion_slice.py` | 20 tests covering parsing, dates, every reject reason, funding, round-trip, and pipe-delimiter safety. |
| `data/*.dat` | Generated synthetic fixtures (clean / with-rejects / unbalanced). |

## What is intentionally NOT here

Per the engagement decision (*design & document the factory; run it after the
plan is approved*), this slice is a **reference prototype**, not the production
factory. It does not connect to a real Momentum instance, does not read the real
USSGL chart, and uses a hand-built fund crosswalk. Those externalizations, and
the horizontal fan-out across 110+ interfaces, are described in
[`factory/design/`](../../design/). This slice exists so the design is grounded
in something that actually runs and reconciles — not slideware.
