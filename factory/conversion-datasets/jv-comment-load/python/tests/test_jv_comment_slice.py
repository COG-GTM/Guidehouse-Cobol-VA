"""Tests for the JV-comment conversion vertical slice.

These tests run against the **real** Phase-1 fixture
(migration/test-data/synthetic_comments.dat, 21 synthetic non-production
records) using the **real** Phase-1 parser/validator. They assert the factory's
control evidence: byte-exact reuse of the legacy layout, every reject reason,
duplicate detection (LABD20 dedup), key integrity, and the load gate.

Ground truth for this fixture: 21 rows -> 9 accepted (7 unique keys + 2 held
duplicates) -> 12 rejected.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from convert import WIRE_HEADER, _to_wire, run_slice, simulate_momentum_import
from extract import RECORD_LENGTH, parse_extract
from mapper import REASON_CODES, MomentumJvComment, RejectedComment, map_row
from reconciliation import reconcile

REPO_ROOT = Path(__file__).resolve().parents[5]
REAL_FIXTURE = REPO_ROOT / "migration" / "test-data" / "synthetic_comments.dat"


# --- the slice is built on the real repo -----------------------------------


def test_reuses_real_300_byte_layout():
    """The slice must reuse the Phase-1 record length, not redefine it."""
    assert RECORD_LENGTH == 300  # LABD20.pco:43-55


def test_real_fixture_is_present_and_parses():
    rows = parse_extract(REAL_FIXTURE)
    assert len(rows) == 21
    # provenance is 1-based and contiguous
    assert [r.line_index for r in rows] == list(range(1, 22))
    # first record's known content (from the real fixture)
    first = rows[0].record
    assert first.jv_number == "000100"
    assert first.section_id == "01"
    assert first.requestor.strip() == "ALICE.SUBMITTER"


# --- map / validate (reused Phase-1 edits) ---------------------------------


def test_accept_reject_split_matches_ground_truth():
    rows = parse_extract(REAL_FIXTURE)
    mapped = [map_row(r) for r in rows]
    accepted = [m for m in mapped if isinstance(m, MomentumJvComment)]
    rejected = [m for m in mapped if isinstance(m, RejectedComment)]
    assert len(accepted) == 9
    assert len(rejected) == 12


def test_every_reject_reason_is_typed_and_known():
    rows = parse_extract(REAL_FIXTURE)
    rejects = [m for m in (map_row(r) for r in rows) if isinstance(m, RejectedComment)]
    known_codes = set(REASON_CODES.values())
    for rj in rejects:
        assert rj.reason in known_codes, rj
        assert rj.detail  # human-readable provenance retained


def test_reject_taxonomy_coverage():
    """The real fixture should exercise the full set of legacy edits."""
    rows = parse_extract(REAL_FIXTURE)
    codes = {
        m.reason for m in (map_row(r) for r in rows) if isinstance(m, RejectedComment)
    }
    # blank record, both date edits, JV, section, loan, comment, requestor, approver
    expected = {
        "BLANK_RECORD",
        "NON_NUMERIC_DATE",
        "BAD_DATE",
        "BAD_JV_NUMBER",
        "NON_NUMERIC_SECTION",
        "NON_NUMERIC_LOAN",
        "BLANK_COMMENT",
        "BLANK_REQUESTOR",
        "BLANK_APPROVER",
    }
    assert expected.issubset(codes)


def test_accepted_record_maps_to_contract():
    rows = parse_extract(REAL_FIXTURE)
    first = map_row(rows[0])
    assert isinstance(first, MomentumJvComment)
    assert first.natural_key == "20260101000100019000000001"
    assert len(first.natural_key) == 26
    assert first.comment_date == "2026-01-01"
    assert first.document_ref == "JV-01-000100"
    assert first.control_num == "00010001"
    assert first.source_system == "LABD20"


# --- reconciliation (the product) ------------------------------------------


def test_duplicate_detection_mirrors_labd20():
    report, _ = run_slice(REAL_FIXTURE)
    # 9 accepted = 7 loaded (unique) + 2 held duplicates
    assert len(report.loaded) == 7
    assert len(report.duplicates) == 2
    assert report.accepted_count == 9
    # the two repeated keys are reported
    assert set(report.duplicate_keys) == {
        "20260101000100019000000001",
        "20251231000300119000000020",
    }


def test_row_accounting_no_silent_drops():
    report, _ = run_slice(REAL_FIXTURE)
    assert report.rows_in == 21
    assert report.row_accounting_ok
    assert report.accepted_count + len(report.rejected) == report.rows_in


def test_key_integrity_and_load_ready():
    report, _ = run_slice(REAL_FIXTURE)
    assert report.key_integrity_ok
    assert report.load_ready
    # coverage = 7 loaded / 21 in
    assert report.load_coverage == pytest.approx(round(7 / 21, 4))


# --- emit + Momentum import simulation -------------------------------------


def test_wire_emit_and_post_load_idempotent():
    report, wire = run_slice(REAL_FIXTURE)
    assert len(wire) == len(report.loaded) == 7
    sim = simulate_momentum_import(wire)
    assert sim["rows_loaded"] == 7
    assert sim["unique_keys_loaded"] == 7
    assert sim["post_load_ok"] is True
    assert sim["key_collisions_after_load"] == []


def test_gate_trips_on_duplicate_key_collision():
    """If a duplicate natural key ever reached the wire, the load gate must trip.

    This proves the post-load idempotency check is real (analogous to the GL
    slice's deliberately-unbalanced fixture).
    """
    report, wire = run_slice(REAL_FIXTURE)
    poisoned = wire + [wire[0]]  # inject a duplicate of an already-loaded key
    sim = simulate_momentum_import(poisoned)
    assert sim["post_load_ok"] is False
    assert wire[0].split("|")[0] in sim["key_collisions_after_load"]


def test_convert_cli_exit_zero_on_real_fixture():
    from convert import main

    rc = main([str(REAL_FIXTURE)])
    assert rc == 0


def test_pipe_in_text_fields_preserves_wire_column_count():
    """A pipe in any free-text field must not add columns to the wire.

    Free-text legacy fields (schedule_doc_no, comment_text, requestor, approver)
    can contain a stray '|'. The emitter strips them so the wire keeps the exact
    12 columns declared in WIRE_HEADER and downstream index-based consumers
    (including the natural-key idempotency check) stay aligned.
    """
    expected_cols = len(WIRE_HEADER.split("|"))
    assert expected_cols == 12

    comment = MomentumJvComment(
        natural_key="JV2026SEC01LN0001PORTION01",
        document_ref="JV-01-000123",
        comment_date="2026-03-01",
        jv_number="000123",
        section_id="01",
        loan_number="LN0001",
        schedule_doc_no="SCH|DOC|01",  # pipes in schedule doc no
        comment_text="PAID | INVOICE | 12",  # pipes in comment text
        requestor="SMITH|J",  # pipes in requestor
        approver="DOE|A|B",  # pipes in approver
        control_num="00012301",
    )

    wire = _to_wire(comment)
    cols = wire.split("|")
    assert len(cols) == expected_cols
    # The idempotency key (column 0) is unshifted and intact.
    assert cols[0] == "JV2026SEC01LN0001PORTION01"

    sim = simulate_momentum_import([wire])
    assert sim["post_load_ok"] is True
    assert sim["key_collisions_after_load"] == []
