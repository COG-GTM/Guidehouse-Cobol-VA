"""Tests for ICD generation + spec validation.

Two angles, mirroring the conversion slices' "testing is the product" stance:
1. The generated ICD conforms to the customer's spec (the happy gate).
2. The validator actually catches spec violations (the gate is live, not
   decorative) — seeded-defect tests for each rule family.
"""

import copy
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from icd_builder import build_obligation_disbursement_icd  # noqa: E402
from validate import load_schema, validate_icd  # noqa: E402


@pytest.fixture(scope="module")
def icd():
    return build_obligation_disbursement_icd(document_date="2026-06-11")


@pytest.fixture(scope="module")
def schema():
    return load_schema()


def test_generated_icd_passes_customer_spec(icd, schema):
    assert validate_icd(icd, schema) == []


def test_file_mapping_generated_from_contract_dataclass(icd):
    import dataclasses

    from mapper import MomentumObligationLine

    contract_fields = [f.name for f in dataclasses.fields(MomentumObligationLine)]
    mapped_fields = [row["ifams_field_name"] for row in icd["file_mapping"]]
    assert mapped_fields == contract_fields
    positions = [row["position"] for row in icd["file_mapping"]]
    assert positions == list(range(1, len(contract_fields) + 1))


def test_error_codes_match_live_reject_taxonomy(icd):
    import mapper as mapper_mod

    source = Path(mapper_mod.__file__).read_text()
    system_row = next(r for r in icd["error_handling_matrix"] if r["platform"] == "SYSTEM")
    for code in system_row["common_error_codes"]:
        assert f'"{code}"' in source, f"ICD error code {code} not found in mapper.py"


def _broken(icd, mutate):
    bad = copy.deepcopy(icd)
    mutate(bad)
    return validate_icd(bad)


def test_validator_catches_missing_required_field(icd):
    violations = _broken(icd, lambda d: d["title_page"].update(interface_name=""))
    assert any("interface_name" in v for v in violations)


def test_validator_catches_bad_enum(icd):
    violations = _broken(icd, lambda d: d["operations"][0].update(trigger="whenever"))
    assert any("trigger" in v for v in violations)


def test_validator_catches_duplicate_file_positions(icd):
    def mutate(d):
        d["file_mapping"][1]["position"] = d["file_mapping"][0]["position"]

    assert any("unique" in v for v in _broken(icd, mutate))


def test_validator_catches_bad_email(icd):
    violations = _broken(icd, lambda d: d["pocs"][0].update(email="not-an-email"))
    assert any("email" in v for v in violations)


def test_validator_catches_closed_item_without_resolution(icd):
    violations = _broken(icd, lambda d: d["open_items"][0].update(status="Closed"))
    assert any("resolution" in v for v in violations)


def test_validator_catches_missing_logging_platform(icd):
    def mutate(d):
        d["logging_by_platform"] = [r for r in d["logging_by_platform"] if r["platform"] != "ESB"]

    assert any("ESB" in v for v in _broken(icd, mutate))


def test_validator_requires_noncompliance_justification(icd):
    def mutate(d):
        d["data_compliance"]["uses_ifams_codes"] = False

    assert any("noncompliance_justification" in v for v in _broken(icd, mutate))


def test_validator_requires_all_verification_methods(icd):
    def mutate(d):
        d["verification_methods"] = d["verification_methods"][:2]

    assert any("not addressed" in v for v in _broken(icd, mutate))


def test_cli_exit_codes(tmp_path):
    from generate_icd import main

    assert main(["--out-dir", str(tmp_path), "--date", "2026-06-11"]) == 0
    assert (tmp_path / "ICD-OBL-DISBURSEMENT.md").exists()
    assert (tmp_path / "ICD-OBL-DISBURSEMENT.json").exists()
    assert (tmp_path / "icd.data.js").exists()
