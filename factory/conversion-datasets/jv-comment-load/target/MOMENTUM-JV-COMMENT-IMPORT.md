# Target contract — Momentum JV-comment annotation import (canonical)

> **Status: SYNTHESIZED REFERENCE CONTRACT — not a customer artifact.**
> CGI's Momentum® Enterprise Suite is the FM QSMO-approved core financial
> management platform VA's iFAMS is built on
> (see <https://www.cgi.com/en/momentum>). The *real* Momentum comment/annotation
> import layout / Interface Control Document (ICD) is proprietary to CGI and the
> VA FMBT program. This file is a plausible, standards-aligned reconstruction we
> use to exercise the factory end-to-end on the **real** legacy JV-comment data.
> The authoritative layout is the first thing we ask the customer for — see
> `docs/va-fmbt-open-questions.md` (Q-MOM-1, Q-MOM-2).

## Why this contract exists

The Integration & Conversion Factory never transforms "legacy → vibes." Every
conversion targets an explicit, versioned **target contract**. The contract is
the thing the schema-match / contract tests assert against, and the thing the
reconciliation engine accounts to. If the contract is wrong, the tests fail
loudly — which is the point.

This interface carries **no dollar amounts** (JV comments are annotations on a
journal voucher, not postings). So the control evidence is **row + key
integrity**, not $ control totals.

## Canonical record — `MomentumJvComment`

The canonical form is a normalized, delimiter-free in-memory record (the factory
emits it as pipe-delimited UTF-8 for the load step, but the contract is the
field set and its rules, not the wire format).

| Target field | Type | Source (legacy) | Rule / transform |
| --- | --- | --- | --- |
| `natural_key` | str (26) | `LOAN-DT-NR` redefine `[0,26)` | Idempotency key = `JC_SUBMITTED` (LABD20.pco:329). Drives dedup + idempotent load. |
| `document_ref` | str | `SECTION-ID` + `JV-NUMBER` | `JV-{section}-{jv}`. The JV document the comment annotates. |
| `comment_date` | ISO `YYYY-MM-DD` | `COMMENT-DT` (YYYYMMDD) | Reformatted after DATECONV `CHECK-CYMD-DT` passes. |
| `jv_number` | str (6) | `JV-NUMBER` | Numeric, > 0. |
| `section_id` | str (2) | `SECTION-ID` | Numeric. |
| `loan_number` | str (10) | `LOAN-NUMBER` | Numeric. |
| `schedule_doc_no` | str | `SCHEDULE-DOC-NO` | Trim trailing spaces. |
| `comment_text` | str | `COMMENT-TEXT` `X(230)` | Trim; must be non-blank; pipe stripped for the wire. |
| `requestor` | str | `REQUESTOR` `X(020)` | Trim; must be non-blank. |
| `approver` | str | `APPROVER` `X(014)` | Trim; must be non-blank. |
| `control_num` | str (8) | `JV-NUMBER` + `SECTION-ID` | `WS-CONTROL-NUM` (LABD20.pco:160-165). |
| `source_system` | const `"LABD20"` | — | Provenance tag; constant for this interface. |

## Hard rules the contract enforces (a record is rejected if any fail)

These are the **real LABD20 edits**, reused verbatim from the Phase-1 modernized
loader (`determine_disposition`, port of LABD20.pco:261-307). The factory maps
each to a typed reject code:

1. **Record is not all-blank.** All-spaces 300-byte record → `BLANK_RECORD`.
2. **Comment date is numeric.** Non-digits in `COMMENT-DT` → `NON_NUMERIC_DATE`.
3. **Comment date is a real calendar date.** DATECONV rejects e.g. 20261345,
   20250229 → `BAD_DATE`.
4. **JV number is numeric and > 0.** Else → `BAD_JV_NUMBER`.
5. **Section id is numeric.** Else → `NON_NUMERIC_SECTION`.
6. **Loan number is numeric.** Else → `NON_NUMERIC_LOAN`.
7. **Comment text is non-blank.** Else → `BLANK_COMMENT`.
8. **Requestor is non-blank.** Else → `BLANK_REQUESTOR`.
9. **Approver is non-blank.** Else → `BLANK_APPROVER`.

## Batch-level rules the reconciliation engine enforces

- **Row accounting is closed.** `rows_in == loaded + duplicates_held + rejected`,
  with no silent drops.
- **Key integrity.** Every loaded record carries a full 26-byte `natural_key`,
  and no two *loaded* records share one (idempotent load).
- **Duplicates are held, not loaded twice.** Repeat natural keys within a batch
  are recorded in the duplicate ledger — exactly LABD20's `JC_SUBMITTED`
  duplicate skip (LABD20.pco:317-339).

## Wire format emitted for the (simulated) load

Pipe-delimited, one line per `MomentumJvComment`, header row first:

```
natural_key|document_ref|comment_date|jv_number|section_id|loan_number|schedule_doc_no|comment_text|requestor|approver|control_num|source_system
```

The Momentum **import simulator** (`python/reconciliation.py` +
`python/convert.py`) reads this back, re-asserts natural-key uniqueness as if it
were Momentum's own idempotent import, and runs post-load checks. That round-trip
is what proves the conversion is loadable — not just well-formed.
