"""Validate a generated ICD against the customer's ICD automation spec.

The rules enforced here are the ones the customer's spec
(``factory/reference/customer-artifacts/icd_schema.json``) states explicitly:
required fields, enumerations, minimum list sizes, unique file-mapping
positions, email format, and conditional requirements (closed open items need
a resolution; non-compliant code usage needs a justification).

``validate_icd`` returns a list of violation strings — empty means conformant.
The convert-style CLI in ``generate_icd.py`` exits non-zero on violations, so
ICD generation is gated the same way batch conversion is.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent
    / "reference"
    / "customer-artifacts"
    / "icd_schema.json"
)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_schema(path: Path = SCHEMA_PATH) -> dict:
    return json.loads(path.read_text())


def _enum(schema: dict, *keys: str) -> list[str]:
    node: dict = schema["sections"]
    for key in keys:
        node = node[key]
    return node["values"]


def validate_icd(icd: dict, schema: dict | None = None) -> list[str]:
    schema = schema or load_schema()
    v: list[str] = []

    def require(path: str, value) -> None:
        if value is None or (isinstance(value, str) and not value.strip()) or (
            isinstance(value, (list, dict)) and not value
        ):
            v.append(f"{path}: required value missing/empty")

    # Front matter
    tp = icd.get("title_page", {})
    require("title_page.interface_name", tp.get("interface_name"))
    if not _DATE_RE.match(tp.get("document_date", "")):
        v.append("title_page.document_date: must be YYYY-MM-DD")
    require("title_page.classification_banner", tp.get("classification_banner"))

    versions = icd.get("versions", [])
    require("versions", versions)
    status_enum = _enum(schema, "front_matter", "version_tracker", "item_fields", "status")
    seqs = [ver.get("sequence_number") for ver in versions]
    if len(seqs) != len(set(seqs)):
        v.append("versions: sequence_number values must be unique")
    for i, ver in enumerate(versions):
        if ver.get("status") not in status_enum:
            v.append(f"versions[{i}].status: {ver.get('status')!r} not in {status_enum}")
        for field in ("sequence_number", "author", "date", "change_summary"):
            require(f"versions[{i}].{field}", ver.get(field))

    for field in ("business_context", "integration_objective", "stakeholder_summary"):
        require(f"executive_summary.{field}", icd.get("executive_summary", {}).get(field))

    # Section 1
    require("purpose_statement", icd.get("purpose_statement"))
    require("in_scope_items (>=1)", icd.get("in_scope_items"))
    require("assumptions (>=1)", icd.get("assumptions"))
    require("constraints (>=1)", icd.get("constraints"))
    for i, poc in enumerate(icd.get("pocs", [])):
        for field in ("name", "email", "position", "organization"):
            require(f"pocs[{i}].{field}", poc.get(field))
        if poc.get("email") and not _EMAIL_RE.match(poc["email"]):
            v.append(f"pocs[{i}].email: invalid email format {poc['email']!r}")
    require("wave_label", icd.get("wave_label"))
    require("terms", icd.get("terms"))
    default_terms = set(
        schema["sections"]["1_introduction"]["1.9_terminology"]["defaults"]
    )
    have_terms = {t.get("term") for t in icd.get("terms", [])}
    missing_defaults = default_terms - have_terms
    if missing_defaults:
        v.append(f"terms: spec default terms missing: {sorted(missing_defaults)}")
    require("operational_agreement_text", icd.get("operational_agreement_text"))
    for i, ref in enumerate(icd.get("references", [])):
        require(f"references[{i}].title", ref.get("title"))
        require(f"references[{i}].relevance", ref.get("relevance"))
        link = ref.get("link")
        if link and not link.startswith(("http://", "https://")):
            v.append(f"references[{i}].link: must be a URL if present")

    # Section 2
    for field in ("system_name", "system_function_summary", "technical_platform_summary"):
        require(f"va_system.{field}", icd.get("va_system", {}).get(field))
    require("ifams_systems.ifams_functions_summary", icd.get("ifams_systems", {}).get("ifams_functions_summary"))
    require("ifams_systems.esb_functions", icd.get("ifams_systems", {}).get("esb_functions"))

    # Section 3
    require("legacy_process_description", icd.get("legacy_process_description"))
    require("future_process_description", icd.get("future_process_description"))
    trig_enum = _enum(schema, "3_interface_definition", "3.3_interface_overview", "3.3.1_operations", "item_fields", "trigger")
    dir_enum = _enum(schema, "3_interface_definition", "3.3_interface_overview", "3.3.1_operations", "item_fields", "direction")
    require("operations", icd.get("operations"))
    for i, op in enumerate(icd.get("operations", [])):
        if op.get("trigger") not in trig_enum:
            v.append(f"operations[{i}].trigger: {op.get('trigger')!r} not in {trig_enum}")
        if op.get("direction") not in dir_enum:
            v.append(f"operations[{i}].direction: {op.get('direction')!r} not in {dir_enum}")
    proto_enum = _enum(schema, "3_interface_definition", "3.3_interface_overview", "3.3.2_data_transfer", "item_fields", "protocol")
    pkg_enum = _enum(schema, "3_interface_definition", "3.3_interface_overview", "3.3.2_data_transfer", "item_fields", "packaging")
    require("transfer_mechanisms", icd.get("transfer_mechanisms"))
    for i, tm in enumerate(icd.get("transfer_mechanisms", [])):
        if tm.get("protocol") not in proto_enum:
            v.append(f"transfer_mechanisms[{i}].protocol: {tm.get('protocol')!r} not in {proto_enum}")
        if tm.get("packaging") not in pkg_enum:
            v.append(f"transfer_mechanisms[{i}].packaging: {tm.get('packaging')!r} not in {pkg_enum}")
    require("transaction_types", icd.get("transaction_types"))
    require("data_exchanges", icd.get("data_exchanges"))
    for i, dx in enumerate(icd.get("data_exchanges", [])):
        if dx.get("acknowledgement") not in ("yes", "no"):
            v.append(f"data_exchanges[{i}].acknowledgement: must be yes/no")
    dc = icd.get("data_compliance", {})
    require("data_compliance.compliance_strategy", dc.get("compliance_strategy"))
    if dc.get("uses_ifams_codes") is False and not dc.get("noncompliance_justification"):
        v.append("data_compliance.noncompliance_justification: required when uses_ifams_codes is false")
    require("precedence_rules", icd.get("precedence_rules"))
    require("criticality_levels", icd.get("criticality_levels"))
    require("comm_methods", icd.get("comm_methods"))
    # External connectivity exists (SFTP), so security requirements are mandatory.
    require("security_requirements (external connectivity)", icd.get("security_requirements"))
    platforms_used = {"SYSTEM", "ESB", "iFAMS"}
    logged = {row.get("platform") for row in icd.get("logging_by_platform", [])}
    if not platforms_used <= logged:
        v.append(f"logging_by_platform: missing platforms {sorted(platforms_used - logged)}")

    # Section 4
    require("volume_matrix", icd.get("volume_matrix"))
    require("peak_periods", icd.get("peak_periods"))
    require("contention_analysis", icd.get("contention_analysis"))
    require("performance_requirements", icd.get("performance_requirements"))
    require("availability_matrix", icd.get("availability_matrix"))
    require("runbook_entries", icd.get("runbook_entries"))

    # Section 5
    require("error_handling_matrix", icd.get("error_handling_matrix"))
    plat_enum = _enum(schema, "5_error_handling_and_reconciliation", "5.1_error_handling", "item_fields", "platform")
    for i, row in enumerate(icd.get("error_handling_matrix", [])):
        if row.get("platform") not in plat_enum:
            v.append(f"error_handling_matrix[{i}].platform: {row.get('platform')!r} not in {plat_enum}")
    scope_enum = _enum(schema, "5_error_handling_and_reconciliation", "5.2_reconciliation", "item_fields", "scope")
    require("recon_strategies", icd.get("recon_strategies"))
    for i, row in enumerate(icd.get("recon_strategies", [])):
        if row.get("scope") not in scope_enum:
            v.append(f"recon_strategies[{i}].scope: {row.get('scope')!r} not in {scope_enum}")

    # Section 6 — file mapping rules
    require("message_exchanges", icd.get("message_exchanges"))
    fm = icd.get("file_mapping", [])
    require("file_mapping (file-based interface)", fm)
    positions = [row.get("position") for row in fm]
    if len(positions) != len(set(positions)):
        v.append("file_mapping: positions must be unique")
    if positions and positions != sorted(positions):
        v.append("file_mapping: positions must be ordered")
    for i, row in enumerate(fm):
        for field in ("system_field_name", "ifams_field_name", "description", "format"):
            require(f"file_mapping[{i}].{field}", row.get(field))
        if not isinstance(row.get("max_length"), int) or row["max_length"] < 1:
            v.append(f"file_mapping[{i}].max_length: must be a positive int")

    # Section 7
    allowed_methods = set(schema["sections"]["7_interface_verification"]["allowed_methods"])
    methods = {m.get("method") for m in icd.get("verification_methods", [])}
    require("verification_methods", icd.get("verification_methods"))
    if not methods <= allowed_methods:
        v.append(f"verification_methods: unknown methods {sorted(methods - allowed_methods)}")
    if missing := allowed_methods - methods:
        v.append(f"verification_methods: spec methods not addressed: {sorted(missing)}")

    # Section 8
    require("controls", icd.get("controls"))
    for i, c in enumerate(icd.get("controls", [])):
        if not re.match(r"^IN-\d+\.\d+$", c.get("control_id", "")):
            v.append(f"controls[{i}].control_id: must match IN-x.y")
        for field in ("control_activity", "control_technique", "implementation_detail"):
            require(f"controls[{i}].{field}", c.get(field))

    # Section 9 + 10
    require("conversion_considerations.conversion_notes", icd.get("conversion_considerations", {}).get("conversion_notes"))
    require("transition_steps", icd.get("transition_steps"))
    require("rollback_plan", icd.get("rollback_plan"))
    require("test_scripts", icd.get("test_scripts"))

    # Section 11
    for i, oi in enumerate(icd.get("open_items", [])):
        if oi.get("status") not in ("Open", "Closed"):
            v.append(f"open_items[{i}].status: must be Open/Closed")
        if oi.get("status") == "Closed" and not oi.get("resolution"):
            v.append(f"open_items[{i}]: closed items must have a resolution")
        require(f"open_items[{i}].description", oi.get("description"))
        require(f"open_items[{i}].impact", oi.get("impact"))

    return v
