"""GL/journal extract → Momentum journal-import reference conversion slice.

This package is the *concrete, runnable* vertical slice of the VA FMBT
Integration & Conversion Factory, exercised on general-ledger / journal-voucher
data. It is reference/prototype code that proves the factory pattern end to end:

    parse (fixed-width legacy) -> map to target contract -> validate
        -> reconcile (row + $ control totals, balance per journal)
        -> emit loadable target -> simulate Momentum import + post-load checks

All inputs are synthetic, non-production data. The legacy layout and the
Momentum target contract are plausible reconstructions, not customer artifacts;
the authoritative versions are listed as open questions in
`docs/va-fmbt-open-questions.md`.
"""
