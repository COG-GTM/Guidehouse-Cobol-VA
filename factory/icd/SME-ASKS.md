# SME-ask list — open TBD markers in the generated ICD

The generated ICD
([`generated/ICD-OBL-DISBURSEMENT.md`](./generated/ICD-OBL-DISBURSEMENT.md))
deliberately emits `TBD-SME` / `TBD-CUSTOMER` markers wherever a value
requires customer or SME input rather than inventing one
(see `icd_builder.py`). This file enumerates every marker in the current
generated document — **17 markers across 9 ICD sections** — with what is
needed and who plausibly owns the answer. Closing these closes open item
OI-3 (§11).

Owner key: **VA POC** = VA OFM / interface-partner system owner,
**FMBT ID&C** = VA FMBT Interface Delivery & Conversion team,
**GH SME** = Guidehouse functional/finance SME,
**CGI** = CGI Momentum (iFAMS) SI team,
**ESB Ops** = VA ESB operations.

| # | Marker | ICD section | What's needed | Plausible owner |
| --- | --- | --- | --- | --- |
| 1 | `TBD-SME` (name/email) | §1.7 Points of Contact — Interface Partner functional POC | Named functional POC for the FMS obligation/disbursement extract, with VA email. | VA POC |
| 2 | `TBD-SME` (name/email) | §1.7 Points of Contact — ID&C technical POC | Named FMBT ID&C engineer responsible for this interface. | FMBT ID&C |
| 3 | `TBD-CUSTOMER` | §1.8 Wave | Wave assignment for this interface — blocked on per-interface volume/frequency data (see `../interface-inventory/README.md`). | FMBT ID&C + GH SME |
| 4 | `TBD-CUSTOMER` | §3.3.3 Transaction types — OBLIGATION volume_estimate | Typical daily obligation transaction count and $ value. | VA POC (FMS reports) |
| 5 | `TBD-CUSTOMER` | §3.3.3 Transaction types — DISBURSEMENT volume_estimate | Typical daily disbursement transaction count and $ value. | VA POC (FMS reports) |
| 6 | `TBD-SME` | §3.3.9 Logging & audit — SYSTEM row poc | Owner of the FMS batch-control report who can confirm extract counts/totals. | VA POC |
| 7 | `TBD-SME` | §3.3.9 Logging & audit — ESB row poc | ESB operations contact for transfer logs and missing-file alerting. | ESB Ops |
| 8 | `TBD-SME` | §3.3.9 Logging & audit — iFAMS row poc | CGI contact for Momentum import job logs and batch audit trail. | CGI |
| 9 | `TBD-CUSTOMER` | §4.1 Data volumes — transaction_volume | Daily transaction volume for the load (same gap as #4/#5; needed for load-test thresholds). | VA POC |
| 10 | `TBD-CUSTOMER` | §4.1 Data volumes — line_counts | Expected line counts per daily extract file. | VA POC |
| 11 | `TBD-CUSTOMER` | §4.5 Service availability — iFAMS maintenance_window | Momentum SaaS maintenance window applicable to the import landing zone. | CGI |
| 12 | `TBD-CUSTOMER` | §4.5 Service availability — ESB maintenance_window | ESB maintenance windows that affect SFTP delivery. | ESB Ops |
| 13 | `TBD-CUSTOMER` | §4.5 Service availability — FMS maintenance_window | FMS batch outage/maintenance calendar. | VA POC |
| 14 | `TBD-SME` | §4.6 Scheduling & operations — FCT-OBL-DAILY schedule | Exact job schedule aligned to FMS nightly batch completion time. | VA POC + FMBT ID&C |
| 15 | `TBD-SME` | §4.6 Scheduling & operations — escalation_steps | On-call rotation / escalation chain for failed daily loads. | FMBT ID&C |
| 16 | `TBD-SME` | §5.3 Troubleshooting — escalation_contact | Named escalation contact when a batch exits non-zero / not load-ready. | FMBT ID&C + GH SME |
| 17 | `TBD-CUSTOMER` | §7 Interface Verification — Load test success_criteria | Cutover-volume figure to size the load test (same source as #4/#5/#9). | VA POC |

## Notes

- Markers #3–#5, #9–#10, and #17 all collapse to **one underlying ask**: the
  per-interface volume/frequency data missing from the customer inventory
  (open item OI-1 and `docs/va-fmbt-open-questions.md`). One workbook column
  set answers six markers.
- This list is derived from the live generated document. If
  `generate_icd.py` is re-run after the builder changes, regenerate this
  enumeration (`grep -n "TBD-SME\|TBD-CUSTOMER" generated/ICD-OBL-DISBURSEMENT.md`)
  and update the table deliberately.
- §11 OI-3 references these markers in aggregate; it stays open until every
  row above has a value and the ICD is regenerated without markers.
