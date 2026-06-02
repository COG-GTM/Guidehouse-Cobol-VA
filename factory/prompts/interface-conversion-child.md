# Prompt — interface conversion (child session)

> Paste into a Cloud Devin session (or launch via the orchestrator). This session
> converts **exactly one** interface end-to-end.

---

You are converting interface `{{interface_id}}` for the VA FMBT Integration &
Conversion Factory in `COG-GTM/Guidehouse-Cobol-VA`. Invoke the
`va-fmbt-integration-factory` skill and follow
`factory/playbooks/01-vertical-slice-conversion.md`.

Run the full vertical slice **in one pass** (do not split stages across agents):

1. **Read knowledge first** — `factory/knowledge/` (domain, conversion patterns,
   reject taxonomy, Momentum contracts).
2. **Profile/parse** the legacy source layout for this interface into raw,
   source-tagged records (parser does no validation). Use
   `factory/conversion-datasets/gl-journal-extract/python/gl_extract.py` as the
   reference shape.
3. **Bind the target contract** (Momentum ICD). If unavailable, use the
   reconstructed contract and flag against `docs/va-fmbt-open-questions.md`.
4. **Map & validate** — crosswalks, scaling (`Decimal`), date conversion, derived
   debit/credit; every failure becomes a typed reject reason.
5. **Reconcile** — row accounting, $ control totals, per-document balance,
   coverage. Use `reconciliation.py` as the reference.
6. **Emit** the loadable target artifact (deterministic/idempotent).
7. **Load-simulate** — re-read the emitted artifact and re-assert balance.
8. **Test** — pytest covering parsing offsets, every reject reason, balance, and
   round-trip. All green.
9. **Update knowledge** — append new reject patterns / SME corrections.

Done criteria: clean fixture converts load-ready (exit 0); a deliberately broken
fixture trips the gate (exit non-zero); `pytest -q` green; reconciliation result
reported back (load-ready?, coverage, reject histogram, balance).

Rules: never commit real VA data or secrets; money uses `Decimal`; no silent
drops (`lines_in == loaded + rejected`); the factory converts **data** to
Momentum's **contract** — do not author application/transformation code that
belongs to the upstream COBOL rewrite.
