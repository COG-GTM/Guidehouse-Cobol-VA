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
| `BAD_PERIOD` | Accounting period is outside 1–14 (periods 13–14 are federal adjustment/closing). | Extract error or unconventional period coding. | Confirm VA's period range; extend if 13/14 adjustments are real. |
| `BAD_DR_CR` | DR/CR indicator is not `D` or `C`. | Layout mismatch (wrong byte offset) or source uses a different convention. | Verify copybook alignment; add alternative indicators if documented. |
| `ZERO_AMOUNT` | Dollar amount is zero after scaling. | Informational/filler record, or a real $0 posting. | Confirm whether $0 postings are valid for the interface; if so, accept them. |
| `BAD_USSGL` | USSGL account is not on the approved whitelist. | Account is valid but not yet in the factory's chart, or the account is genuinely wrong. | Expand the whitelist (Q-REF-1) or route to SME. |
| `BAD_DATE` | Julian date fails conversion (day 0, day > 365/366, or non-parseable). | Extract date corruption or unconventional encoding. | Verify date convention per Q-GL-3. |
| `BAD_FUND` | Legacy fund code is not in the crosswalk. | Crosswalk is incomplete (the most common miss in the reference slice). | Extend `FUND_CROSSWALK` with the full mapping (Q-REF-2). |

## Current reasons (from JV-comment slice — real LABD20 edits)

These codes are emitted by the real, repo-grounded JV-comment slice
(`conversion-datasets/jv-comment-load/`). Each maps 1:1 to a legacy LABD20 edit
(LABD20.pco:261-307), reused verbatim from the Phase-1 modernized loader. The
slice's `DUPLICATE` case is handled by the dedup ledger (held, not loaded twice),
mirroring LABD20's `JC_SUBMITTED` key check (LABD20.pco:317-339).

| Code | Meaning | Root cause | Resolution |
| --- | --- | --- | --- |
| `BLANK_RECORD` | The 300-byte record is all spaces. | Filler/trailer line or extract padding. | Confirm the extract's trailer convention; drop trailers upstream. |
| `NON_NUMERIC_DATE` | Comment date (PIC 9(8)) contains non-digits. | Corrupted date zone or unconventional encoding. | Verify the date convention (Q-GL-3 analog for comments). |
| `BAD_DATE` | Comment date is numeric but not a valid YYYYMMDD calendar date (e.g. 20261345, 20250229). | Bad source date; DATECONV CHECK-CYMD-DT rejects it. | Route to SME; confirm whether out-of-range dates should be corrected or dropped. |
| `BAD_JV_NUMBER` | JV number (PIC 9(6)) is non-numeric or zero. | Layout drift or a non-JV record in the stream. | Verify copybook alignment; confirm zero-JV is never valid. |
| `NON_NUMERIC_SECTION` | Section id (PIC 9(2)) contains non-digits. | Section coded with letters (e.g. `MA`) the legacy edit rejects. | Confirm whether alpha sections are real; if so, extend the edit (SME). |
| `NON_NUMERIC_LOAN` | Loan number (PIC 9(10)) contains non-digits. | Corrupted loan zone. | Verify copybook alignment; route to SME. |
| `BLANK_COMMENT` | Comment text (PIC X(230)) is blank. | Empty annotation. | Confirm whether blank comments are ever valid for Momentum. |
| `BLANK_REQUESTOR` | Requestor (PIC X(20)) is blank. | Missing provenance. | Required by the import contract; reject to SME. |
| `BLANK_APPROVER` | Approver (PIC X(14)) is blank. | Missing approval provenance. | Required by the import contract; reject to SME. |

## Current reasons (from obligation/disbursement slice)

These codes are emitted by the obligation/disbursement slice
(`conversion-datasets/obligation-disbursement/`). The slice reuses the GL codes
above (`NON_NUMERIC`, `BAD_PERIOD`, `ZERO_AMOUNT`, `BAD_USSGL`, `BAD_DATE`,
`BAD_FUND`) verbatim and adds the rules unique to the spending chain.

| Code | Meaning | Root cause | Resolution |
| --- | --- | --- | --- |
| `BAD_TXN_TYPE` | Transaction-type indicator is not `O` (obligation) or `D` (disbursement). | Layout mismatch (wrong byte offset) or source uses a different event coding. | Verify copybook alignment; extend `TXN_TYPE_MAP` if more event types are real. |
| `MISSING_VENDOR` | Vendor / payee id is blank. | Anonymous obligation or outlay; missing provenance. | Required by the import contract; reject to SME. Confirm whether intra-governmental events legitimately lack a vendor id. |
| `MISSING_OBLIGATION_NO` | Obligation / document number is blank. | A disbursement with no obligation to apply against, or a layout drift. | Cannot reconcile a disbursement without its obligation; route to SME. |
| `BAD_POP` | Period-of-performance end date precedes the start date. | Inverted or corrupted POP window in the extract. | Confirm POP date convention; correct upstream or route to SME. |
| `OVER_DISBURSED` | (Obligation-level) Σ disbursements exceed Σ obligation for an `obligation_id`. | Outlays booked beyond the obligated ceiling — an Antideficiency-Act-class control breach. | Block the load (gate trips, exit 1). Requires SME adjudication; never auto-accept. |

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

## Learned this session (S8 feedback loop)

The block below is **maintained programmatically** by the learning-agent demo
(`factory/demos/learning-agent-demo/run_learning_demo.py`). It records reject
patterns that were resolved by an SME correction during a run — the moment a
`BAD_FUND` / `BAD_USSGL` reject is reclassified as "valid, the reference data was
incomplete" and the crosswalk/whitelist is extended so the next run accepts it.
The demo rewrites everything between the markers each time it runs, so re-running
is idempotent.

<!-- BEGIN LEARNED (auto-generated by run_learning_demo.py — do not edit by hand) -->
_Last run: 2026-06-08 16:22 UTC. The S8 loop resolved 2 reject pattern(s) by extending the reference data._

| Original reject | Pattern | SME finding | Resolution |
| --- | --- | --- | --- |
| `BAD_USSGL` | `490200` | Valid USSGL account (Delivered Orders - Obligations, Paid) missing from the GL slice whitelist. | Added to whitelist; line now posts. |
| `BAD_FUND` | legacy fund `8180` | Valid VA fund missing from the crosswalk. | Mapped to Momentum fund `8180-GPF`; line now posts. |
<!-- END LEARNED -->
