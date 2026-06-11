"""Obligation/disbursement extract → Momentum obligation-import reference slice.

This package is a *concrete, runnable* vertical slice of the VA FMBT Integration
& Conversion Factory, exercised on obligation/disbursement (spending-chain) data.
It is reference/prototype code that proves the factory pattern end to end:

    parse (fixed-width legacy) -> map to target contract -> validate
        -> reconcile (row + $ control totals, per-obligation funding)
        -> emit loadable target -> simulate Momentum import + post-load checks

It follows the GL/journal slice (`gl-journal-extract/`) exactly, reusing the
USSGL whitelist, fund crosswalk, and CCYYDDD date convention, and adds the
obligation-domain integrity rule: disbursements must never exceed the obligated
amount for an obligation (an Antideficiency-Act-class control).

All inputs are synthetic, non-production data. The legacy layout and the
Momentum target contract are plausible reconstructions, not customer artifacts;
the authoritative versions are listed as open questions in
`docs/va-fmbt-open-questions.md`.
"""
