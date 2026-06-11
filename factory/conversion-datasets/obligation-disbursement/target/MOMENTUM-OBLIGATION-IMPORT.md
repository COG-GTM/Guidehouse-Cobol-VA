# Target contract — Momentum obligation / disbursement import (canonical)

> **Status: SYNTHESIZED REFERENCE CONTRACT — not a customer artifact.**
> CGI's Momentum® Enterprise Suite is the FM QSMO-approved core financial
> management platform VA's iFAMS is built on
> (see <https://www.cgi.com/en/momentum>). The *real* Momentum obligation /
> disbursement import layout / Interface Control Document (ICD) is proprietary to
> CGI and the VA FMBT program. This file is a plausible, standards-aligned
> reconstruction we use to exercise the factory end-to-end. The authoritative
> layout is the first thing we ask the customer for — see
> `docs/va-fmbt-open-questions.md` (Q-OBL-1, Q-MOM-1, Q-MOM-2).

## Why this contract exists

The Integration & Conversion Factory never transforms "legacy → vibes." Every
conversion targets an explicit, versioned **target contract** (an ICD). The
contract is the thing the schema-match / contract tests assert against, and the
thing the reconciliation engine balances to. If the contract is wrong, the tests
fail loudly — which is the point.

This is also the ICD that drives **interface generation**: handed this contract
plus the GL/journal and JV-comment slices as worked examples, the factory
produces the parser, mapper, reconciliation, and tests for this interface in one
pass. The contract is the input; the runnable slice is the output.

## Canonical record — `MomentumObligationLine`

The canonical form is a normalized, delimiter-free in-memory record (the factory
emits it as pipe-delimited UTF-8 for the load step, but the contract is the field
set and its rules, not the wire format). One record is one event on the spending
chain: an obligation (`txn_type = OBLIGATION`) or a disbursement applied to it
(`txn_type = DISBURSEMENT`).

| Target field | Type | Source (legacy) | Rule / transform |
| --- | --- | --- | --- |
| `obligation_id` | str | `OBL-FISCAL-YEAR` + `OBL-OBLIGATION-NO` | `OB-{fy}-{obligation_no}`. Groups all events on one obligation. |
| `fiscal_year` | int (YYYY) | `OBL-FISCAL-YEAR` | Pass-through; must be 4 digits. |
| `accounting_period` | int 1–14 | `OBL-ACCT-PERIOD` | 1–12 normal, 13/14 adjustment. Reject if 0 or >14. |
| `line_number` | int | `OBL-LINE-NO` | Pass-through, 1-based. |
| `txn_type` | enum | `OBL-TXN-TYPE` | `O`→`OBLIGATION`, `D`→`DISBURSEMENT`. Anything else rejects. |
| `vendor_id` | str | `OBL-VENDOR-ID` | Trim; **required** (no anonymous obligation or outlay). |
| `tafs` | str | `OBL-TREASURY-SYMBOL` | Trim trailing spaces; must be non-empty. |
| `appropriation` | str | `OBL-APPROPRIATION` | Trim; mapped through the fund crosswalk (shared with the GL slice). |
| `object_class` | str | `OBL-OBJECT-CLASS` | Trim. |
| `ussgl_account` | str (6) | `OBL-USSGL-ACCT` | Validated against the USSGL account whitelist. |
| `obligation_amount` | Decimal | `OBL-AMOUNT` if `O` | Scaled /100 (2 implied decimals). 0 on disbursement lines. |
| `disbursement_amount` | Decimal | `OBL-AMOUNT` if `D` | Scaled /100. 0 on obligation lines. |
| `pop_start_date` | ISO `YYYY-MM-DD` | `OBL-POP-START-JUL` (CCYYDDD) | Ordinal-date → calendar date (same `dateconv` convention). |
| `pop_end_date` | ISO `YYYY-MM-DD` | `OBL-POP-END-JUL` (CCYYDDD) | Ordinal-date → calendar date; must be ≥ `pop_start_date`. |
| `txn_date` | ISO `YYYY-MM-DD` | `OBL-TXN-DATE-JUL` (CCYYDDD) | Obligation/disbursement event date. |
| `description` | str | `OBL-DESCRIPTION` | Trim trailing spaces. |
| `source_system` | const `"FMS"` | — | Provenance tag; constant for this extract. |

## Hard rules the contract enforces (a line is rejected if any fail)

1. **Numeric fields are numeric.** `fiscal_year`, `accounting_period`, `line_no`,
   `amount`, and all three dates must be all-digits in the fixed field.
   Blank/garbage → reject with reason `NON_NUMERIC`.
2. **Obligation number present.** Blank document number → `MISSING_OBLIGATION_NO`
   (a disbursement with no obligation to apply against cannot be reconciled).
3. **Accounting period is 1–14.** Otherwise → `BAD_PERIOD`.
4. **Transaction type is `O` or `D`.** Anything else → `BAD_TXN_TYPE`.
5. **Vendor present.** Blank vendor/payee → `MISSING_VENDOR`.
6. **Amount is non-negative and non-zero.** Zero-dollar events → `ZERO_AMOUNT`.
7. **USSGL account is on the approved list.** Unknown account → `BAD_USSGL`.
8. **Dates are real ordinal dates.** Day-of-year out of range → `BAD_DATE`.
9. **Period of performance is not inverted.** `pop_end < pop_start` → `BAD_POP`.
10. **TAFS / appropriation present and mapped.** Empty treasury symbol or unmapped
    appropriation → `BAD_FUND`.

## Obligation-level rule the reconciliation engine enforces

- **No obligation is over-disbursed.** For each `obligation_id`, Σ
  `disbursement_amount` ≤ Σ `obligation_amount`. An obligation whose outlays
  exceed its obligated ceiling fails the load gate (`OVER_DISBURSED`) even if
  every individual line is valid. Over-disbursing an appropriation is an
  Antideficiency-Act-class control breach, so it blocks the load the same way an
  unbalanced journal does in the GL slice.
- **Control totals are preserved.** Σ legacy `OBL-AMOUNT` (accepted lines) ==
  Σ (`obligation_amount` + `disbursement_amount`) in the target, to the cent.
- **Row accounting is closed.** `lines_in == lines_loaded + lines_rejected`, with
  no silent drops.

## Wire format emitted for the (simulated) load

Pipe-delimited, one line per `MomentumObligationLine`, header row first:

```
obligation_id|fiscal_year|accounting_period|line_number|txn_type|vendor_id|tafs|appropriation|object_class|ussgl_account|obligation_amount|disbursement_amount|pop_start_date|pop_end_date|txn_date|description|source_system
```

The Momentum **import simulator** (`python/reconciliation.py` +
`python/convert.py`) reads this back, re-applies the obligation-funding rule as if
it were Momentum's own import validation, and runs post-load transaction checks.
That round-trip is what proves the conversion is loadable — not just well-formed.
