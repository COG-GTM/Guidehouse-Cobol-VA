# Reject-reason taxonomy

Every record the factory cannot map to the target contract is **rejected with a
typed reason** — never silently dropped. This file is the growing taxonomy. Each
reason has a code, meaning, likely root cause, and recommended resolution.

> As more interfaces are converted, new reasons will be added here. SME
> corrections also go here — "reason X actually means Y and should map to Z."

## Current reasons (from GL/journal slice)

| Code | Meaning | Root cause | Resolution |
| --- | --- | --- | --- |
| `NON_NUMERIC` | A field declared as numeric contains non-digit characters. | Corrupted extract, trailing spaces in a numeric zone, COMP field read as text. | Fix the parser (COMP handling) or reject the source record to the SME queue. |
| `BAD_PERIOD` | Accounting period is outside 1–16 (periods 13–16 are federal adjustment/closing). | Extract error or unconventional period coding. | Confirm VA's period range; extend if 13/14 adjustments are real. |
| `BAD_DR_CR` | DR/CR indicator is not `D` or `C`. | Layout mismatch (wrong byte offset) or source uses a different convention. | Verify copybook alignment; add alternative indicators if documented. |
| `ZERO_AMOUNT` | Dollar amount is zero after scaling. | Informational/filler record, or a real $0 posting. | Confirm whether $0 postings are valid for the interface; if so, accept them. |
| `BAD_USSGL` | USSGL account is not on the approved whitelist. | Account is valid but not yet in the factory's chart, or the account is genuinely wrong. | Expand the whitelist (Q-REF-1) or route to SME. |
| `BAD_DATE` | Julian date fails conversion (day 0, day > 365/366, or non-parseable). | Extract date corruption or unconventional encoding. | Verify date convention per Q-GL-3. |
| `BAD_FUND` | Legacy fund code is not in the crosswalk. | Crosswalk is incomplete (the most common miss in the reference slice). | Extend `FUND_CROSSWALK` with the full mapping (Q-REF-2). |

## Anticipated reasons (not yet triggered)

| Code | Meaning | Notes |
| --- | --- | --- |
| `DUPLICATE` | Record appeared in a previous extract/batch. | Test angle #9; needs a dedup store. |
| `REF_INTEGRITY` | Fund/TAFS/vendor exists in the extract but not in Momentum master data. | Test angle #8; needs real reference data. |
| `LOW_CONFIDENCE` | Mapping exists but was inferred, not from a deterministic crosswalk. | Test angle #10; routes to SME review. |
| `OVERFLOW` | Amount exceeds the target field width. | Edge case for very large appropriations. |

## How this grows

After every conversion run:
1. Check the `reject_reasons` histogram in the reconciliation report.
2. Any new code that appears here gets a row in this file.
3. Any SME correction ("this BAD_USSGL was actually correct; the chart needed updating") gets recorded as a note under the original reason.
