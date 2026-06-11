# Customer-provided artifacts (received 2026-06-11)

Two real customer artifacts arrived from the FMBT program and are ingested
here in machine-readable form. They replace two of the biggest "synthetic
stand-in" assumptions in the factory (see
[`../../../docs/va-fmbt-open-questions.md`](../../../docs/va-fmbt-open-questions.md)).

| File | What it is | Source document |
| --- | --- | --- |
| [`fms_ifams_interface_inventory.csv`](./fms_ifams_interface_inventory.csv) | The real **125-system FMS/iFAMS interface inventory** — every VA system/component with flags for whether its interface is managed by FMS, by iFAMS, by both, or by neither. | `VA FMBT - FMS and iFAMS Interface Systems.xlsx` |
| [`icd_schema.json`](./icd_schema.json) | A machine-readable rendering of the customer's **ICD automation spec** — every section (front matter, 1–11, appendices A–D), the inputs each section requires, required/optional flags, enumerations, and validation rules. | `FMBT_ICD-AEI-Sample.docx` |

## What consumes these

- [`../../interface-inventory/`](../../interface-inventory/) loads the CSV,
  classifies each system's migration disposition, and produces the wave-planning
  input the orchestrator (`factory/playbooks/03-interface-wave-fanout.md`) fans
  out over.
- [`../../icd/`](../../icd/) loads the JSON schema and both **generates** a
  complete ICD for a converted slice (populated from the slice's real code and
  reconciliation artifacts) and **validates** it against the customer's
  required-field/enum rules.

## Provenance and fidelity notes

- The CSV is a lossless parse of `Sheet1` of the workbook (125 named-system rows; 20 fully-blank trailing rows in the workbook were
  dropped, and the `System Category` column was empty in the source and is
  preserved as empty).
- `icd_schema.json` is a faithful restructuring of the docx's prose
  ("Inputs to collect / Validation / Source" per section) into fields. Where the
  docx states an enumeration (e.g., version `status`, operation `trigger`,
  transfer `protocol`), it is encoded as an enum; where it states a rule
  (unique file-mapping positions, email format, closed open-items need a
  resolution), it is encoded as a validation rule.
- Both documents are **inputs from the customer**, not Cognition/Guidehouse
  work product. Do not edit them to make tooling pass; fix the tooling.

## Gaps these artifacts do NOT close (still open with the customer)

1. **Volume / frequency data** — the inventory names the 125 systems but has no
   transaction volumes or schedules, which ICD §4.1 (volume matrix) and wave
   sequencing both need.
2. **Per-interface ICDs** — the docx is the ICD *template/spec*, not a filled
   ICD for any specific interface. Authoritative Momentum import contracts are
   still open questions (Q-MOM-1, Q-MOM-2).
3. **WSDL / web-service mappings** (ICD §6.3) — spec'd but no WSDL artifacts
   provided; applies to the SOAP/REST interfaces in the portfolio.
4. **Agility links** (ICD §10, Appendix A) — the spec references VA's Agility
   test-management tool for test scripts and RTM traceability; URLs/items not
   provided.
5. **SME-sourced sections** — POCs (§1.7), runbook entries (§4.6),
   troubleshooting (§5.3) require named VA/Guidehouse staff input; the
   generator emits explicit `TBD-SME` placeholders for these.
