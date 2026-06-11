# Data-quality memo — contradictory management flags in the FMS/iFAMS interface inventory

**To:** VA FMBT program / Guidehouse workbook owners (`VA FMBT - FMS and iFAMS Interface Systems.xlsx`)
**From:** Integration & Conversion Factory
**Re:** 6 of 125 rows carry logically contradictory management flags; please correct the workbook
**Status:** Open — awaiting corrected workbook

## What we found

The customer inventory ([`fms_ifams_interface_inventory.csv`](./fms_ifams_interface_inventory.csv),
a lossless parse of Sheet1 of the workbook) has four flag columns per system:
`managed_by_fms`, `managed_by_ifams`, `not_managed_by_fms`, `not_managed_by_ifams`.
Six rows assert **both** the positive and the negative flag for the same
platform, which cannot both be true:

| # | System | Contradiction | Disposition as loaded today |
| --- | --- | --- | --- |
| 1 | Budget Tracking Tool | `managed_by_ifams=Y` **and** `not_managed_by_ifams=Y` | DUAL_MANAGED |
| 2 | Corporate Data Warehouse | `managed_by_fms=Y` **and** `not_managed_by_fms=Y` | MIGRATE_TO_IFAMS |
| 3 | Electronic Contract Management System/Acquisition Enterprise Systems | `managed_by_ifams=Y` **and** `not_managed_by_ifams=Y` (also flagged `not_managed_by_fms=Y`, consistent with `managed_by_fms` blank) | ALREADY_ON_IFAMS |
| 4 | Financial Content Management | `managed_by_fms=Y` **and** `not_managed_by_fms=Y` | MIGRATE_TO_IFAMS |
| 5 | Frontier Fiserv Reconciliation | `managed_by_ifams=Y` **and** `not_managed_by_ifams=Y` | ALREADY_ON_IFAMS |
| 6 | Human Resources - Payroll Application Services | `managed_by_ifams=Y` **and** `not_managed_by_ifams=Y` (also flagged `not_managed_by_fms=Y`, consistent with `managed_by_fms` blank) | ALREADY_ON_IFAMS |

These six rows are exactly the rows for which
`load_inventory()` in [`factory/interface-inventory/inventory.py`](../../interface-inventory/inventory.py)
emits a `UserWarning` at load time (`_warn_contradictory_flags`), and the
test suite asserts that exactly six such warnings fire — the contradiction is
surfaced on every run, never silently absorbed.

## How the factory resolves the contradiction today

The disposition logic uses **only the positive flags** (`managed_by_fms`,
`managed_by_ifams`); the negative flags are loaded and checked for
consistency but do not drive classification. In other words: when a row says
both "managed" and "not managed," **the positive flag wins**. This is a
deterministic, documented choice — not a judgment that the positive flag is
more likely correct.

## Impact if the *negative* flags are actually the correct ones

If for these six rows the `not_managed_by_*=Y` flags are right and the
positive flags are data-entry errors, the portfolio shifts as follows
(computed by re-running `classify_disposition` with the positive flag
suppressed wherever it is contradicted):

| System | Disposition today (positive wins) | Disposition if negative wins |
| --- | --- | --- |
| Budget Tracking Tool | DUAL_MANAGED | MIGRATE_TO_IFAMS |
| Corporate Data Warehouse | MIGRATE_TO_IFAMS | OUT_OF_FMS_SCOPE |
| Electronic Contract Management System/Acquisition Enterprise Systems | ALREADY_ON_IFAMS | OUT_OF_FMS_SCOPE |
| Financial Content Management | MIGRATE_TO_IFAMS | OUT_OF_FMS_SCOPE |
| Frontier Fiserv Reconciliation | ALREADY_ON_IFAMS | OUT_OF_FMS_SCOPE |
| Human Resources - Payroll Application Services | ALREADY_ON_IFAMS | OUT_OF_FMS_SCOPE |

Portfolio control totals would change:

| Metric | Today | If negative flags correct | Delta |
| --- | --- | --- | --- |
| DUAL_MANAGED | 7 | 6 | −1 (Budget Tracking Tool) |
| MIGRATE_TO_IFAMS | 55 | 54 | +1 (BTT) −2 (CDW, FCM) |
| ALREADY_ON_IFAMS | 13 | 10 | −3 |
| OUT_OF_FMS_SCOPE | 50 | 55 | +5 |
| **Factory conversion scope** | **62** | **60** | **−2 systems** |

**Wave-plan impact.** Under the current heuristic (`assign_waves()`:
dual-managed first, then alphabetical), Wave 1's *membership* happens to stay
the same 10 systems, but its *composition* changes: Budget Tracking Tool drops
out of the "cheapest validation" dual-managed bucket (6 dual-managed + 4
migrations instead of 7 + 3), and Corporate Data Warehouse and Financial
Content Management leave the conversion workload entirely (Waves 2–7 reflow).
Two systems' worth of conversion effort (and their child-session fan-out) would
be planned against work that does not exist.

## Ask

Please have the workbook owner confirm, for each of the six systems above,
which flag is correct, and ship a corrected
`VA FMBT - FMS and iFAMS Interface Systems.xlsx`. On receipt we will
regenerate the CSV losslessly, the loader warnings will drop to zero, and the
control-total tests will be updated deliberately to the corrected counts.
Until then the factory continues with the documented positive-flags-win rule
and flags every load with the six warnings above.
