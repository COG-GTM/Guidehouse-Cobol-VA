# Playbook 01 — convert one interface (vertical slice)

**Goal.** Take a single legacy VA financial interface from raw extract to a
Momentum-loadable artifact plus reconciliation evidence, in one pass.

**When to use.** A child session owns exactly one `interface_id` from the
inventory and runs this playbook end-to-end. Do not split across agents.

**Inputs.** `interface_id`; the legacy source layout (copybook/DDL); a sample
extract; the Momentum target contract/ICD; relevant crosswalks.

**Reference implementation.** `factory/conversion-datasets/gl-journal-extract/` —
copy its shape for any new interface.

## Steps

1. **Profile / parse (S0–S1).** Read the source layout and build a byte-exact
   parser (see `gl_extract.py`). Parser does *no* validation — it only lands raw
   fields into a source-tagged record. Assert the field map tiles the record
   length with no gaps/overlaps (there is a test for this).
2. **Bind the target contract (S2).** Confirm you have the real Momentum import
   layout. If not, use the reconstructed contract and flag the gap against
   `docs/va-fmbt-open-questions.md` (Q-MOM-1/2). Never map to "vibes" — always to
   a versioned contract.
3. **Map & transform (S3).** Field mapping, crosswalks (fund/USSGL), unit
   scaling (use `Decimal`), date conversion, derived debit/credit. Concentrate
   *all* judgment here.
4. **Validate (S4).** Apply contract rules; every failure becomes a typed reject
   reason (`NON_NUMERIC`, `BAD_DR_CR`, `ZERO_AMOUNT`, `BAD_USSGL`, `BAD_DATE`,
   `BAD_FUND`, …). Never silently drop.
5. **Reconcile (S5).** Row accounting, $ control totals, per-document balance,
   mapping coverage. (`reconciliation.py`.)
6. **Emit (S6).** Write the loadable target artifact in the contract's wire
   format. Emit must be deterministic (idempotent — golden-file safe).
7. **Load-simulate & post-load test (S7).** Re-read the emitted artifact as an
   opaque inbound file and re-assert journal balance. (`simulate_momentum_import`.)
8. **Test.** Add/extend a pytest file covering parsing offsets, every reject
   reason, balance, control totals, and the round trip. All green before done.
9. **Update knowledge (S8).** Append new reject patterns and any SME corrections
   to `factory/knowledge/`. Record final `coverage` and `status` on the inventory
   row.

## Done criteria

- `python convert.py <clean fixture>` exits 0 and is load-ready.
- A deliberately-broken fixture (e.g. unbalanced) exits 1.
- `pytest -q` green.
- Inventory row updated; knowledge appended.
