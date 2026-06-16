# Interface inventory & wave planning

[`inventory.py`](./inventory.py) loads the customer-provided 125-system
FMS/iFAMS interface inventory
([`../reference/customer-artifacts/fms_ifams_interface_inventory.csv`](../reference/customer-artifacts/fms_ifams_interface_inventory.csv)),
classifies each system's migration disposition from the workbook's management
flags, and groups the in-scope conversion workload into waves for the
orchestrator fan-out (`factory/playbooks/03-interface-wave-fanout.md`).

Run it directly for the portfolio summary and the Wave-1 plan:

```bash
python factory/interface-inventory/inventory.py
python -m pytest factory/interface-inventory/tests/ -q
```

## Data-quality note

Six rows of the customer CSV carry contradictory management flags (both
`managed_by_*=Y` and `not_managed_by_*=Y`). `load_inventory()` emits a
`UserWarning` per contradictory row; classification deterministically uses the
positive flags only. The exact rows, the resolution rule, and the portfolio
impact if the negative flags turn out to be correct are documented in
[`../reference/customer-artifacts/DATA-QUALITY-MEMO.md`](../reference/customer-artifacts/DATA-QUALITY-MEMO.md)
— a ready-to-send correction request to the workbook owners.

## Wave-plan caveat — this is a heuristic, not a sequencing plan

The 7-wave plan produced by `assign_waves()` is **not** a real migration
sequence. The customer inventory contains *only* system names and four
management flags — no interface volumes, frequencies, criticality, or
dependency data. With nothing else to sort on, the heuristic is:

1. **DUAL_MANAGED systems first** — their iFAMS leg already exists, so they
   are the cheapest validations and the fastest way to seed the knowledge
   fabric; then
2. **MIGRATE_TO_IFAMS systems alphabetically** — alphabetical order carries
   no business meaning; it is used only because it is deterministic and
   reviewable.

Treat wave numbers as orchestration batches (≤10 child sessions per wave),
not as a cutover calendar.

### Data needed to turn this into a real sequencing plan

To replace the heuristic with defensible sequencing, the program needs to
supply, per interface:

| Data | Why it changes the ordering |
| --- | --- |
| Transaction volume (rows/day, $/day) | High-volume money movers need the longest shadow-run period and the earliest start. |
| Frequency & batch windows (daily/weekly/monthly, cutoff times) | Monthly interfaces have far fewer rehearsal opportunities before cutover; they must enter the pipeline earlier. |
| Business criticality (payment-blocking? ADA exposure? audit-relevant?) | Spending-chain interfaces outrank informational extracts regardless of size. |
| Upstream/downstream dependencies between the 125 systems | A consumer cannot cut over before its producer; dependencies create hard ordering constraints the flags cannot express. |
| Interface complexity (record layouts, # of transaction types, reference-data needs) | Drives conversion effort estimates and how many interfaces fit in one wave. |
| Decommission/contract deadlines per system | External dates can force a system into an early wave irrespective of the above. |
| Fiscal-calendar constraints (year-end close, period 13/14 adjustments) | Cutovers should avoid close windows; sequencing must route around them. |

This gap is also recorded as open item OI-1 in the generated ICD
(`factory/icd/generated/ICD-OBL-DISBURSEMENT.md` §11) and in
`docs/va-fmbt-open-questions.md`. When the customer supplies volume/frequency
data, `assign_waves()` should be rewritten to sort on it and this caveat
updated.
