"""Tests for the customer interface-inventory model.

Counts asserted here are facts of the customer-provided workbook
(VA FMBT - FMS and iFAMS Interface Systems.xlsx, 2026-06-11). If the customer
ships a revised inventory, regenerate the CSV and update these expectations
deliberately — they are control totals, not incidental numbers.
"""

import sys
import warnings
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from inventory import (  # noqa: E402
    Disposition,
    assign_waves,
    classify_disposition,
    load_inventory,
    summarize,
)


@pytest.fixture(scope="module")
def systems():
    return load_inventory()


def test_classify_disposition_matrix():
    assert classify_disposition(True, False) is Disposition.MIGRATE_TO_IFAMS
    assert classify_disposition(True, True) is Disposition.DUAL_MANAGED
    assert classify_disposition(False, True) is Disposition.ALREADY_ON_IFAMS
    assert classify_disposition(False, False) is Disposition.OUT_OF_FMS_SCOPE


def test_inventory_control_totals(systems):
    s = summarize(systems)
    assert s["total_systems"] == 125
    assert s["MIGRATE_TO_IFAMS"] == 55
    assert s["DUAL_MANAGED"] == 7
    assert s["ALREADY_ON_IFAMS"] == 13
    assert s["OUT_OF_FMS_SCOPE"] == 50
    assert s["factory_scope"] == 62
    # Row accounting: every system has exactly one disposition.
    assert (
        s["MIGRATE_TO_IFAMS"] + s["DUAL_MANAGED"] + s["ALREADY_ON_IFAMS"] + s["OUT_OF_FMS_SCOPE"]
        == s["total_systems"]
    )


def test_no_duplicate_system_names(systems):
    names = [s.system_name for s in systems]
    assert len(names) == len(set(names))


def test_factory_scope_equals_fms_managed(systems):
    # Everything FMS manages must be converted or cut over — nothing dropped.
    fms_managed = [s for s in systems if s.managed_by_fms]
    in_scope = [s for s in systems if s.in_factory_scope]
    assert sorted(s.system_name for s in fms_managed) == sorted(s.system_name for s in in_scope)


def test_assign_waves_covers_full_workload_once(systems):
    waves = assign_waves(systems, wave_size=10)
    flattened = [s.system_name for wave in waves.values() for s in wave]
    in_scope = sorted(s.system_name for s in systems if s.in_factory_scope)
    assert sorted(flattened) == in_scope
    assert all(len(w) <= 10 for w in waves.values())


def test_wave_one_prioritizes_dual_managed(systems):
    waves = assign_waves(systems, wave_size=10)
    dual_count = summarize(systems)["DUAL_MANAGED"]
    first_dispositions = [s.disposition for s in waves[1][:dual_count]]
    assert all(d is Disposition.DUAL_MANAGED for d in first_dispositions)


def test_assign_waves_rejects_bad_size(systems):
    with pytest.raises(ValueError):
        assign_waves(systems, wave_size=0)


def test_contradictory_flags_emit_warnings():
    """load_inventory() warns when positive and negative flags contradict."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        load_inventory()
    contradictory = [w for w in caught if "Contradictory flags" in str(w.message)]
    # The customer CSV has 6 rows with contradictory flags.
    assert len(contradictory) == 6
    # Spot-check one known system.
    messages = [str(w.message) for w in contradictory]
    assert any("Budget Tracking Tool" in m for m in messages)
