# Target contract — Momentum journal-voucher import (canonical)

> **Status: SYNTHESIZED REFERENCE CONTRACT — not a customer artifact.**
> CGI's Momentum® Enterprise Suite is the FM QSMO-approved core financial
> management platform VA's iFAMS is built on
> (see <https://www.cgi.com/en/momentum>). The *real* Momentum journal import
> layout / Interface Control Document (ICD) is proprietary to CGI and the VA
> FMBT program. This file is a plausible, standards-aligned reconstruction we
> use to exercise the factory end-to-end. The authoritative layout is the first
> thing we ask the customer for — see `docs/va-fmbt-open-questions.md`
> (Q-MOM-1, Q-MOM-2, Q-GL-1).

## Why this contract exists

The Integration & Conversion Factory never transforms "legacy → vibes." Every
conversion targets an explicit, versioned **target contract**. The contract is
the thing the schema-match / contract tests assert against, and the thing the
reconciliation engine balances to. If the contract is wrong, the tests fail
loudly — which is the point.

## Canonical record — `MomentumJournalLine`

The canonical form is a normalized, delimiter-free in-memory record (the factory
emits it as pipe-delimited UTF-8 for the load step, but the contract is the
field set and its rules, not the wire format).

| Target field | Type | Source (legacy) | Rule / transform |
| --- | --- | --- | --- |
| `fiscal_year` | int (YYYY) | `GLX-FISCAL-YEAR` | Pass-through; must be 4 digits. |
| `accounting_period` | int 1–14 | `GLX-ACCT-PERIOD` | 1–12 normal, 13/14 adjustment. Reject if 0 or >14. |
| `journal_id` | str | `GLX-FISCAL-YEAR` + `GLX-JV-NUMBER` | `JV-{fy}-{jv:06d}`. Groups balanced lines. |
| `line_number` | int | `GLX-LINE-NO` | Pass-through, 1-based. |
| `posting_date` | ISO `YYYY-MM-DD` | `GLX-POST-DATE-JUL` (CCYYDDD) | Ordinal-date → calendar date. Same Julian convention the repo already ports in `migration/converted-code/python/dateconv.py`. |
| `tafs` | str | `GLX-TREASURY-SYMBOL` | Trim trailing spaces; must be non-empty. |
| `fund` | str | `GLX-FUND` | Trim; mapped through the fund crosswalk (see below). |
| `cost_center` | str | `GLX-COST-CENTER` | Trim. |
| `ussgl_account` | str (6) | `GLX-USSGL-ACCT` | Validated against the USSGL account whitelist. |
| `budget_object_class` | str | `GLX-BUDGET-OBJ-CLASS` | Trim. |
| `debit_amount` | Decimal | `GLX-AMOUNT` if `D` | Scaled /100 (2 implied decimals). 0 if credit line. |
| `credit_amount` | Decimal | `GLX-AMOUNT` if `C` | Scaled /100. 0 if debit line. |
| `vendor_id` | str or null | `GLX-VENDOR-ID` | Trim; null if all spaces. |
| `description` | str | `GLX-DESCRIPTION` | Trim trailing spaces. |
| `source_system` | const `"FMS"` | — | Provenance tag; constant for this extract. |

## Hard rules the contract enforces (a line is rejected if any fail)

1. **Numeric fields are numeric.** `fiscal_year`, `accounting_period`,
   `jv_number`, `line_no`, `post_date`, `amount` must be all-digits in the fixed
   field. Blank/garbage → reject with reason `NON_NUMERIC`.
2. **DR/CR indicator is `D` or `C`.** Anything else → `BAD_DR_CR`.
3. **Amount is non-negative and non-zero.** Zero-dollar postings → `ZERO_AMOUNT`
   (legacy sometimes emits filler lines; they must not enter Momentum).
4. **USSGL account is on the approved list.** Unknown account → `BAD_USSGL`.
   (The whitelist here is a small synthetic set; production uses the Treasury
   USSGL chart for the fiscal year.)
5. **Posting date is a real ordinal date.** Day-of-year out of range for the
   year → `BAD_DATE`.
6. **TAFS / fund present.** Empty treasury symbol or unmapped fund → `BAD_FUND`.

## Journal-level rules the reconciliation engine enforces

- **Every journal balances.** For each `journal_id`, Σ debits == Σ credits.
  An unbalanced voucher fails the load gate (`UNBALANCED_JOURNAL`) even if every
  individual line is valid.
- **Control totals are preserved.** Σ legacy `GLX-AMOUNT` (accepted lines) ==
  Σ (`debit_amount` + `credit_amount`) in the target, to the cent.
- **Row accounting is closed.** `lines_in == lines_loaded + lines_rejected`,
  with no silent drops.

## Wire format emitted for the (simulated) load

Pipe-delimited, one line per `MomentumJournalLine`, header row first:

```
journal_id|fiscal_year|accounting_period|line_number|posting_date|tafs|fund|cost_center|ussgl_account|budget_object_class|debit_amount|credit_amount|vendor_id|description|source_system
```

The Momentum **import simulator** (`python/reconciliation.py` +
`python/convert.py`) reads this back, re-applies the journal-level rules as if it
were Momentum's own import validation, and runs post-load transaction checks.
That round-trip is what proves the conversion is loadable — not just well-formed.
