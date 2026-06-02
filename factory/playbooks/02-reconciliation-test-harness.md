# Playbook 02 — reconciliation & test harness

**Goal.** Build and verify the control evidence that *is* the deliverable, and
wire it into a CI gate so correctness is a build status.

**When to use.** Whenever you add or change a conversion, or stand up CI for an
interface. This is the "testing is the product" playbook.

## The control evidence every interface must produce

1. **Row accounting** — `lines_in == lines_loaded + lines_rejected`. No drops.
2. **Dollar control totals** — Σ legacy (accepted) == Σ target, to the cent,
   using `Decimal`.
3. **Per-document balance** — Σ debits == Σ credits per journal/document.
4. **Reject ledger** — every reject typed with a reason code and traceable to a
   source byte-row.
5. **Mapping coverage %** — accepted ÷ in; a release gate that may only rise.
6. **Post-load round trip** — re-read the emitted artifact and re-assert balance.

`factory/conversion-datasets/gl-journal-extract/python/reconciliation.py` and
`convert.py` are the reference implementation.

## Steps

1. **Write the contract test.** Assert the emitted record matches the target
   contract field-for-field; a contract change must break this test loudly.
2. **Exercise every reject reason.** One synthetic line per reason; assert the
   exact `reject_reasons` histogram (see `test_conversion_slice.py`).
3. **Keep a deliberately-failing fixture.** An unbalanced/short batch that must
   exit non-zero. If it ever passes, the gate is broken.
4. **Golden file.** Commit a golden emitted output for a fixed input; diff on
   each run.
5. **Wire the CI gate.** `convert.py` exits non-zero when not load-ready; CI runs
   it on the clean fixture (expect 0) and the broken fixture (expect non-zero),
   plus `pytest -q`.
6. **Cover the 11 angles over time.** Work through
   `factory/design/TESTING-AS-THE-PRODUCT.md` — round-trip reverse recon,
   cutover-window perf, schema-drift, idempotent restart, referential integrity,
   duplicate/replay, confidence scoring, provenance trail.

## Verify

```bash
cd factory/conversion-datasets/gl-journal-extract/python
python -m pytest -q
python convert.py ../data/gl_extract_clean.dat      ; echo exit=$?   # 0
python convert.py ../data/gl_extract_unbalanced.dat ; echo exit=$?   # 1
```
