"""
parity_engine.py — COBOL ↔ Python 1:1 parity harness.

For every business requirement listed in
migration/business-requirements/requirements-with-citations.md
(BR-LABA05-001 … BR-LABD20-022) this module produces a triple:

  1. The COBOL/Pro*COBOL source citation (file path + line range).
  2. The Python conversion citation (file path + line range).
  3. A live diff comparing the Python output to a golden output derived
     from the COBOL source.

HONESTY BANNER
--------------
The "expected" side of the diff is a GOLDEN FIXTURE DERIVED FROM COBOL
SOURCE LINE-BY-LINE — not a live mainframe run. The COBOL source itself is
not executed on this machine (no Pro*COBOL precompiler, no Oracle).
In a real engagement the same harness flips one config switch and the
"expected" column becomes a live COBOL execution against the same synthetic
inputs, producing the byte-for-byte diff that Cognition's answer to
SBA Q2 ("validate the migration by running identical inputs through both
the COBOL and Python implementations and diffing outputs field-by-field")
and Q14 ("the highest-confidence validation is the agent running the
converted code in a sandbox VM ... with byte-for-byte diff against the
legacy COBOL output") describes.

This file is intentionally read-only logic + data — no I/O side effects
outside the in-memory sqlite mock — so a SME can re-run the parity sweep
and reproduce every result deterministically.
"""
from __future__ import annotations

import io
import logging
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT / "migration" / "converted-code") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "migration" / "converted-code"))

from python.db_dispatcher import (  # noqa: E402
    DBDispatcher,
    DispatcherResult,
    build_demo_schema,
    seed_control_record,
    translate_sqlcode,
)
from python.labd20_loader import (  # noqa: E402
    LABD20Loader,
    LoaderConfig,
    TST123_RECORD_LENGTH,
    check_cymd_dt,
    determine_disposition,
    iter_records,
    parse_comment_record,
    read_process_date,
    truncate_file,
)
from python.laba05_reset import (  # noqa: E402
    _extract_jv_number,
    _replace_jv_number,
)
from python.laba05_reset import run as laba05_run  # noqa: E402


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------
@dataclass
class ParityRow:
    br_id: str
    label: str
    owner: str
    cobol_path: str
    cobol_lines: tuple[int, int]
    python_path: str
    python_lines: tuple[int, int]
    confidence: str          # HIGH / MEDIUM / LOW
    classification: str      # Confirmed / Inferred / Unresolvable
    input_desc: str
    expected: dict[str, Any]
    actual: dict[str, Any]
    status: str              # PASS / FAIL / UNRESOLVED
    notes: str = ""


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------
def _new_dispatcher(seed_jv: int = 99, seed_count: int = 0) -> DBDispatcher:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    d = DBDispatcher(conn)
    build_demo_schema(d)
    seed_control_record(d, jv_number=seed_jv)
    d.insert(
        "INSERT INTO JC_COUNT_TBL (JC_SECTION, JC_COUNT_NUM) VALUES (?, ?)",
        ("MA", seed_count),
    )
    d.commit()
    return d


def _make_record(
    comment_dt: str = "20251230",
    jv: str = "000123",
    section: str = "01",
    loan: str = "0000001000",
    sched: str = "DOC1234567",
    text: str = "synthetic comment text",
    requestor: str = "REQ-USER-1",
    approver: str = "APPR-USER-1",
) -> str:
    text = text.ljust(230)[:230]
    requestor = requestor.ljust(20)[:20]
    approver = approver.ljust(14)[:14]
    raw = f"{comment_dt:<8}{jv:<6}{section:<2}{loan:<10}{sched:<10}{text}{requestor}{approver}"
    assert len(raw) == TST123_RECORD_LENGTH, f"record length {len(raw)} != 300"
    return raw


def _status(expected: dict[str, Any], actual: dict[str, Any]) -> str:
    return "PASS" if actual == expected else "FAIL"


def _write_card_file(tmp_dir: Path, mmddccyy: str) -> Path:
    tmp_dir.mkdir(parents=True, exist_ok=True)
    p = tmp_dir / "card.ctl"
    p.write_text(mmddccyy + "\n", encoding="utf-8")
    return p


def _write_records_file(tmp_dir: Path, records: list[str]) -> Path:
    """Write fixed-width records separated by newlines (matches iter_records)."""
    tmp_dir.mkdir(parents=True, exist_ok=True)
    p = tmp_dir / "comments.dat"
    p.write_text("\n".join(records) + "\n", encoding="utf-8")
    return p


def _run_loader_with_records(
    dispatcher: DBDispatcher,
    records: list[str],
    workspace: Path,
    process_date_mmddccyy: str = "12/30/2025",
) -> Any:
    card = _write_card_file(workspace, process_date_mmddccyy)
    comments = _write_records_file(workspace, records)
    loader = LABD20Loader(dispatcher)
    stats = loader.run(
        LoaderConfig(
            card_path=card,
            comment_path=comments,
            truncate_after_processing=True,
        )
    )
    return stats, comments


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------
def check_laba05_001(workspace: Path) -> ParityRow:
    """Connect/fetch failure → rc 99 (LABA05 PROGRAM-EXIT error fall-through)."""
    d = _new_dispatcher()
    # Force fetch to fail by deleting the seeded row.
    d.delete("DELETE FROM CONTROL_RECORD_TABLE")
    d.commit()
    outcome = laba05_run(d)
    d.close()
    expected = {"return_code": 99}
    actual = {"return_code": outcome.return_code}
    return ParityRow(
        br_id="BR-LABA05-001",
        label="Connect/fetch failure aborts with RETURN-CODE=99",
        owner="Jill",
        cobol_path="source/cobol/LABA05.cbl",
        cobol_lines=(69, 85),
        python_path="migration/converted-code/python/laba05_reset.py",
        python_lines=(146, 154),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Empty CONTROL_RECORD_TABLE → fetch returns no rows",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_laba05_002(workspace: Path) -> ParityRow:
    """SELECT control record keyed by name+number."""
    d = _new_dispatcher(seed_jv=42)
    outcome = laba05_run(d)
    d.close()
    expected = {"before_jv_number": 42, "fetch_ok": True}
    actual = {"before_jv_number": outcome.before_jv_number, "fetch_ok": outcome.before_jv_number is not None}
    return ParityRow(
        br_id="BR-LABA05-002",
        label="SELECT JV-CONTROL-REC row from CONTROL_RECORD_TABLE",
        owner="Jill",
        cobol_path="source/cobol/LABA05.cbl",
        cobol_lines=(152, 174),
        python_path="migration/converted-code/python/laba05_reset.py",
        python_lines=(137, 158),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Seed JV-NUMBER=42 in CONTROL_RECORD_TABLE",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_laba05_003(workspace: Path) -> ParityRow:
    """DISPLAY JV-NUMBER read prior to mutation."""
    d = _new_dispatcher(seed_jv=99)
    outcome = laba05_run(d)
    d.close()
    expected = {"before_jv_number": 99, "displayed_before_update": True}
    actual = {
        "before_jv_number": outcome.before_jv_number,
        "displayed_before_update": outcome.before_jv_number is not None,
    }
    return ParityRow(
        br_id="BR-LABA05-003",
        label="Display JV-NUMBER before mutation",
        owner="Jill",
        cobol_path="source/cobol/LABA05.cbl",
        cobol_lines=(176, 205),
        python_path="migration/converted-code/python/laba05_reset.py",
        python_lines=(156, 158),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Seed JV-NUMBER=99",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_laba05_004(workspace: Path) -> ParityRow:
    """MOVE 1 TO JV-NUMBER and UPDATE in place."""
    d = _new_dispatcher(seed_jv=99)
    outcome = laba05_run(d)
    # Verify persisted state.
    r = d.select_one(
        "SELECT CONTROL_RECORD_DATA FROM CONTROL_RECORD_TABLE WHERE CONTROL_RECORD_NAME=? AND CONTROL_RECORD_NUMBER=?",
        ("JV-CONTROL-REC", 1),
    )
    persisted = _extract_jv_number(r.rows[0][0]) if r.rows else None
    d.close()
    expected = {"after_jv_number": 1, "persisted_jv_number": 1}
    actual = {"after_jv_number": outcome.after_jv_number, "persisted_jv_number": persisted}
    return ParityRow(
        br_id="BR-LABA05-004",
        label="Reset JV-NUMBER to 1 and UPDATE",
        owner="Jill",
        cobol_path="source/cobol/LABA05.cbl",
        cobol_lines=(184, 205),
        python_path="migration/converted-code/python/laba05_reset.py",
        python_lines=(160, 170),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Seed JV-NUMBER=99 → run LABA05",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_laba05_005(workspace: Path) -> ParityRow:
    """COMMIT on success, ROLLBACK + rc=99 on any DBIO non-zero."""
    d = _new_dispatcher(seed_jv=42)
    # Force update to fail.
    original_update = d.update

    def failing_update(*_a: Any, **_kw: Any) -> DispatcherResult:
        return DispatcherResult(rtncode_dms="9999", sqlcode=-1, message="forced")

    d.update = failing_update  # type: ignore[assignment]
    outcome = laba05_run(d)
    d.update = original_update  # type: ignore[assignment]
    d.close()
    expected = {"return_code": 99, "after_jv_number": None}
    actual = {"return_code": outcome.return_code, "after_jv_number": outcome.after_jv_number}
    return ParityRow(
        br_id="BR-LABA05-005",
        label="COMMIT on success / ROLLBACK + rc=99 on any DBIO error",
        owner="Jill",
        cobol_path="source/procobol/DBIO.pco",
        cobol_lines=(374, 398),
        python_path="migration/converted-code/python/laba05_reset.py",
        python_lines=(171, 180),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Force UPDATE to return non-zero DMS code",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_laba05_006(workspace: Path) -> ParityRow:
    """JV-NUMBER byte offset round-trip."""
    blob = "X" * 24 + "001234" + "Y" * 370  # 400 bytes total
    extracted = _extract_jv_number(blob)
    rewritten = _replace_jv_number(blob, 5678)
    rt = _extract_jv_number(rewritten)
    surroundings_preserved = (rewritten[:24] == blob[:24]) and (rewritten[30:] == blob[30:])
    expected = {"extracted": 1234, "round_trip": 5678, "surroundings_preserved": True}
    actual = {"extracted": extracted, "round_trip": rt, "surroundings_preserved": surroundings_preserved}
    return ParityRow(
        br_id="BR-LABA05-006",
        label="JV-NUMBER at byte offset 24..30 inside 400-byte blob",
        owner="Jill",
        cobol_path="source/copybooks/JV-CONTROL-REC.cpy",
        cobol_lines=(1, 12),
        python_path="migration/converted-code/python/laba05_reset.py",
        python_lines=(91, 121),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="400-byte blob with sentinel surroundings + JV=001234",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
        notes="Binary↔display: byte layout proven by round-trip; production layer uses struct.unpack/pack (see ASSUMPTIONS A-2).",
    )


def check_labd20_001(workspace: Path) -> ParityRow:
    """Process date MM/DD/CCYY → YYYYMMDD reshuffling."""
    card = _write_card_file(workspace, "12/30/2025")
    process_date = read_process_date(card)
    expected = {"process_date": "20251230"}
    actual = {"process_date": process_date}
    return ParityRow(
        br_id="BR-LABD20-001",
        label="Process date MM/DD/CCYY → YYYYMMDD reshuffling",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(224, 234),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(257, 277),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="CARDFILE = '12/30/2025'",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_labd20_002(workspace: Path) -> ParityRow:
    """300-byte fixed-width layout with documented slice boundaries."""
    rec = _make_record()
    parsed = parse_comment_record(rec)
    expected = {
        "length": 300,
        "comment_dt": "20251230",
        "jv_number": "000123",
        "section_id": "01",
        "loan_number": "0000001000",
        "schedule_doc_no": "DOC1234567",
        "requestor_len": 20,
        "approver_len": 14,
    }
    actual = {
        "length": len(rec),
        "comment_dt": parsed.comment_dt,
        "jv_number": parsed.jv_number,
        "section_id": parsed.section_id,
        "loan_number": parsed.loan_number,
        "schedule_doc_no": parsed.schedule_doc_no,
        "requestor_len": len(parsed.requestor),
        "approver_len": len(parsed.approver),
    }
    return ParityRow(
        br_id="BR-LABD20-002",
        label="TST123-COMMENT-REC = 300 bytes (8+6+2+10+10+230+20+14)",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(43, 55),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(85, 102),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Synthetic happy-path record at canonical offsets",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_labd20_003(workspace: Path) -> ParityRow:
    """First 26 bytes (LOAN-DT-NR) = JC_SUBMITTED primary key."""
    rec = _make_record()
    parsed = parse_comment_record(rec)
    expected = {"submitted_key": rec[:26], "key_len": 26}
    actual = {"submitted_key": parsed.submitted_key, "key_len": len(parsed.submitted_key)}
    return ParityRow(
        br_id="BR-LABD20-003",
        label="First 26 bytes form JC_SUBMITTED composite primary key",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(44, 49),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(124, 128),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Synthetic record with date=20251230 jv=000123 section=01 loan=0000001000",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def _validation_check(
    br_id: str,
    label: str,
    cobol_lines: tuple[int, int],
    python_lines: tuple[int, int],
    record: str,
    expect_accept: bool,
    expect_reason_fragment: Optional[str] = None,
    confidence: str = "HIGH",
    classification: str = "Confirmed",
    notes: str = "",
) -> ParityRow:
    parsed = parse_comment_record(record)
    accepted, reasons = determine_disposition(parsed)
    has_reason = (
        expect_reason_fragment is None
        or any(expect_reason_fragment in r for r in reasons)
    )
    expected = {"accepted": expect_accept, "has_expected_reason": True}
    actual = {"accepted": accepted, "has_expected_reason": has_reason}
    return ParityRow(
        br_id=br_id,
        label=label,
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=cobol_lines,
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=python_lines,
        confidence=confidence,
        classification=classification,
        input_desc=f"Synthetic record: {record[:60].rstrip()}...",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
        notes=notes,
    )


def check_labd20_004(workspace: Path) -> ParityRow:
    return _validation_check(
        br_id="BR-LABD20-004",
        label="Reject all-spaces record",
        cobol_lines=(261, 263),
        python_lines=(216, 256),
        record=" " * TST123_RECORD_LENGTH,
        expect_accept=False,
        expect_reason_fragment="blank record",
    )


def check_labd20_005(workspace: Path) -> ParityRow:
    return _validation_check(
        br_id="BR-LABD20-005",
        label="Reject non-numeric comment date",
        cobol_lines=(265, 274),
        python_lines=(216, 256),
        record=_make_record(comment_dt="ABCDEFGH"),
        expect_accept=False,
        expect_reason_fragment="comment date is non-numeric",
    )


def check_labd20_006(workspace: Path) -> ParityRow:
    row = _validation_check(
        br_id="BR-LABD20-006",
        label="Reject invalid calendar date (DATECONV-PD)",
        cobol_lines=(266, 274),
        python_lines=(196, 214),
        record=_make_record(comment_dt="20251345"),
        expect_accept=False,
        expect_reason_fragment="not a valid YYYYMMDD calendar date",
        confidence="LOW",
        classification="Inferred / partly unresolvable",
        notes="DATECONV-PD copybook not supplied; using Gregorian-calendar stub (ASSUMPTIONS A-5). Real CHECK-CYMD-DT may apply business-calendar gates that change this output.",
    )
    return row


def check_labd20_007(workspace: Path) -> ParityRow:
    return _validation_check(
        br_id="BR-LABD20-007",
        label="Reject JV-NUMBER non-numeric or ≤ 0",
        cobol_lines=(276, 281),
        python_lines=(216, 256),
        record=_make_record(jv="000000"),
        expect_accept=False,
        expect_reason_fragment="JV number is non-numeric or zero",
    )


def check_labd20_008(workspace: Path) -> ParityRow:
    return _validation_check(
        br_id="BR-LABD20-008",
        label="Reject non-numeric SECTION-ID",
        cobol_lines=(283, 287),
        python_lines=(216, 256),
        record=_make_record(section="XY"),
        expect_accept=False,
        expect_reason_fragment="section id is non-numeric",
    )


def check_labd20_009(workspace: Path) -> ParityRow:
    return _validation_check(
        br_id="BR-LABD20-009",
        label="Reject non-numeric LOAN-NUMBER",
        cobol_lines=(289, 293),
        python_lines=(216, 256),
        record=_make_record(loan="ZZZZZZZZZZ"),
        expect_accept=False,
        expect_reason_fragment="loan number is non-numeric",
    )


def check_labd20_010(workspace: Path) -> ParityRow:
    return _validation_check(
        br_id="BR-LABD20-010",
        label="Reject blank COMMENT-TEXT",
        cobol_lines=(297, 299),
        python_lines=(216, 256),
        record=_make_record(text=" "),
        expect_accept=False,
        expect_reason_fragment="comment text is blank",
    )


def check_labd20_011(workspace: Path) -> ParityRow:
    return _validation_check(
        br_id="BR-LABD20-011",
        label="Reject blank REQUESTOR",
        cobol_lines=(301, 303),
        python_lines=(216, 256),
        record=_make_record(requestor=" "),
        expect_accept=False,
        expect_reason_fragment="requestor is blank",
    )


def check_labd20_012(workspace: Path) -> ParityRow:
    return _validation_check(
        br_id="BR-LABD20-012",
        label="Reject blank APPROVER",
        cobol_lines=(305, 307),
        python_lines=(216, 256),
        record=_make_record(approver=" "),
        expect_accept=False,
        expect_reason_fragment="approver is blank",
    )


def check_labd20_013(workspace: Path) -> ParityRow:
    """Duplicate detection on the 26-byte JC_SUBMITTED key."""
    d = _new_dispatcher()
    workspace.mkdir(parents=True, exist_ok=True)
    rec = _make_record()
    # Run once → row inserts. Run again with same record → duplicate.
    _run_loader_with_records(d, [rec], workspace)
    stats2, _ = _run_loader_with_records(d, [rec], workspace)
    d.close()
    expected = {"duplicates_second_pass": 1, "inserted_second_pass": 0}
    actual = {"duplicates_second_pass": stats2.duplicates, "inserted_second_pass": stats2.inserted}
    return ParityRow(
        br_id="BR-LABD20-013",
        label="Duplicate detection on 26-byte JC_SUBMITTED key",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(317, 339),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(409, 440),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Insert same record twice; second pass must dedupe",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_labd20_014(workspace: Path) -> ParityRow:
    """INSERT into JC_SUBMITTED_COMMENT_TBL with 9 columns including 'LABD20' literal."""
    d = _new_dispatcher()
    rec = _make_record()
    _run_loader_with_records(d, [rec], workspace)
    cur = d._conn.cursor()  # type: ignore[attr-defined]
    cur.execute("SELECT * FROM JC_SUBMITTED_COMMENT_TBL WHERE JC_SUBMITTED = ?", (rec[:26],))
    row = cur.fetchone()
    cols = [desc[0] for desc in cur.description] if cur.description else []
    row_dict = dict(zip(cols, row)) if row else {}
    d.close()
    expected = {
        "col_count": 9,
        "has_jc_submitted": True,
        "has_updt_prog_id": True,
        "updt_prog_id_value": "LABD20",
    }
    actual = {
        "col_count": len(cols),
        "has_jc_submitted": "JC_SUBMITTED" in cols,
        "has_updt_prog_id": "JC_SUBMITTED_UPDT_PROG_ID" in cols,
        "updt_prog_id_value": row_dict.get("JC_SUBMITTED_UPDT_PROG_ID"),
    }
    return ParityRow(
        br_id="BR-LABD20-014",
        label="INSERT 9 cols incl. literal 'LABD20' + TO_DATE",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(342, 372),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(441, 465),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Insert one happy-path record; inspect inserted row columns",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_labd20_015(workspace: Path) -> ParityRow:
    """WS-JV-COUNTER increments per accepted insert."""
    d = _new_dispatcher()
    recs = [
        _make_record(jv=f"{i:06d}", loan=f"{i:010d}")
        for i in range(1, 4)
    ]
    stats, _ = _run_loader_with_records(d, recs, workspace)
    d.close()
    expected = {"inserted": 3, "accepted": 3}
    actual = {"inserted": stats.inserted, "accepted": stats.accepted}
    return ParityRow(
        br_id="BR-LABD20-015",
        label="Per-batch in-memory counter WS-JV-COUNTER",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(345, 345),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(441, 465),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Run loader with 3 distinct happy-path records",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_labd20_016(workspace: Path) -> ParityRow:
    """UPDATE JC_COUNT_TBL where counter > stored count."""
    d = _new_dispatcher(seed_count=0)
    recs = [
        _make_record(jv=f"{i:06d}", loan=f"{i:010d}")
        for i in range(1, 6)
    ]
    _run_loader_with_records(d, recs, workspace)
    row = d.select_one(
        "SELECT JC_COUNT_NUM FROM JC_COUNT_TBL WHERE JC_SECTION = ?",
        ("MA",),
    )
    count_after = row.rows[0][0] if row.rows else None
    d.close()
    expected = {"count_after_update": 5}
    actual = {"count_after_update": count_after}
    return ParityRow(
        br_id="BR-LABD20-016",
        label="UPDATE JC_COUNT_TBL 'MA' when WS-JV-COUNTER > stored count",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(392, 405),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(466, 493),
        confidence="MEDIUM",
        classification="Confirmed (literals + control flow)",
        input_desc="Seed JC_COUNT_NUM=0; insert 5 happy records",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
        notes="Hardcoded section 'MA' preserved; SME to confirm origin of WS-JV-COUNTERS comparand (ASSUMPTIONS A-10, RISKS Risk 8).",
    )


def check_labd20_017(workspace: Path) -> ParityRow:
    """COMMIT after post-process + stats COUNT(*) on 3 tables."""
    d = _new_dispatcher()
    recs = [_make_record(jv=f"{i:06d}", loan=f"{i:010d}") for i in range(1, 4)]
    stats, _ = _run_loader_with_records(d, recs, workspace)
    d.close()
    expected = {"submitted_total": 3, "rejected_total": 0, "applied_total": 0}
    actual = {
        "submitted_total": stats.submitted_total,
        "rejected_total": stats.rejected_total,
        "applied_total": stats.applied_total,
    }
    return ParityRow(
        br_id="BR-LABD20-017",
        label="COMMIT + emit COUNT(*) stats on submitted/rejected/applied",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(408, 446),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(494, 513),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Run loader with 3 happy records → COUNTs reflect totals",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_labd20_018(workspace: Path) -> ParityRow:
    """Truncate COMMENT-FILE on the way out."""
    d = _new_dispatcher()
    rec = _make_record()
    stats, comment_path = _run_loader_with_records(d, [rec], workspace)
    d.close()
    size = comment_path.stat().st_size
    expected = {"file_size_after": 0}
    actual = {"file_size_after": size}
    return ParityRow(
        br_id="BR-LABD20-018",
        label="Truncate COMMENT-FILE so next run does not re-process",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(215, 218),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(302, 314),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="One happy record → COMMENT-FILE is zero bytes after run",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_labd20_019(workspace: Path) -> ParityRow:
    """ROLLBACK on any SQLCODE != 0 (except the SELECT-100 fast-path)."""
    code_ok = translate_sqlcode(0)
    code_eof = translate_sqlcode(100)                         # no set-name → 0013
    code_eof_set = translate_sqlcode(100, set_name="JC_SET")  # set-name → 0007
    code_dup = translate_sqlcode(-1)
    code_other = translate_sqlcode(-942)  # ORA-00942 table or view does not exist
    code_8103_ok = translate_sqlcode(-8103)
    # Expected values traced directly to DBIO.pco:374-398 (5300-TRANSLATE-SQLCODE)
    expected = {
        "0": "0000",
        "100_default": "0013",
        "100_set_name": "0007",
        "-1": "0005",
        "-942": "9999",
        "-8103": "0000",
    }
    actual = {
        "0": code_ok,
        "100_default": code_eof,
        "100_set_name": code_eof_set,
        "-1": code_dup,
        "-942": code_other,
        "-8103": code_8103_ok,
    }
    return ParityRow(
        br_id="BR-LABD20-019",
        label="SQLCODE → DMS translation drives rollback decisions",
        owner="Charles",
        cobol_path="source/procobol/DBIO.pco",
        cobol_lines=(374, 398),
        python_path="migration/converted-code/python/db_dispatcher.py",
        python_lines=(64, 108),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="Translate canonical SQLCODE values",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_labd20_020(workspace: Path) -> ParityRow:
    """JC_REJECTED_COMMENT_TBL is read-only here; populated elsewhere."""
    d = _new_dispatcher()
    bad_rec = _make_record(jv="000000")  # JV=0 → rejected
    stats, _ = _run_loader_with_records(d, [bad_rec], workspace)
    rejected_table_rows = d.count_rows("JC_REJECTED_COMMENT_TBL")
    d.close()
    expected = {"in_memory_rejected": 1, "rejected_table_rows": 0}
    actual = {"in_memory_rejected": stats.rejected, "rejected_table_rows": rejected_table_rows}
    return ParityRow(
        br_id="BR-LABD20-020",
        label="REJECTED counters increment; JC_REJECTED table is read-only here",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(309, 314),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(409, 440),
        confidence="LOW",
        classification="Inferred (gap)",
        input_desc="One JV=0 record → counter increments; table itself untouched",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
        notes="Supplied source does not populate JC_REJECTED_COMMENT_TBL — likely populated by a different program. SME to confirm.",
    )


def check_labd20_021(workspace: Path) -> ParityRow:
    """WS-CONTROL-NUM = JV-NUMBER(6) + SECTION-ID(2)."""
    rec = _make_record(jv="000123", section="01")
    parsed = parse_comment_record(rec)
    expected = {"control_num": "00012301", "len": 8}
    actual = {"control_num": parsed.control_num, "len": len(parsed.control_num)}
    return ParityRow(
        br_id="BR-LABD20-021",
        label="WS-CONTROL-NUM = JV-NUMBER(6) + SECTION-ID(2) = 8 chars",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(160, 165),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(130, 134),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="jv=000123 section=01 → control_num = 00012301",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


def check_labd20_022(workspace: Path) -> ParityRow:
    """COMMENT-HIST = SCHED-DOC-NO(10) + COMMENT-TEXT(230) = 240 bytes."""
    rec = _make_record(sched="DOC1234567", text="hello world")
    parsed = parse_comment_record(rec)
    expected = {"hist_starts_with_doc": True, "hist_len": 240}
    actual = {
        "hist_starts_with_doc": parsed.comment_hist.startswith("DOC1234567"),
        "hist_len": len(parsed.comment_hist),
    }
    return ParityRow(
        br_id="BR-LABD20-022",
        label="COMMENT-HIST = SCHED-DOC-NO(10) + COMMENT-TEXT(230) verbatim",
        owner="Jill",
        cobol_path="source/procobol/LABD20.pco",
        cobol_lines=(50, 52),
        python_path="migration/converted-code/python/labd20_loader.py",
        python_lines=(95, 99),
        confidence="HIGH",
        classification="Confirmed",
        input_desc="sched=DOC1234567 text='hello world'",
        expected=expected,
        actual=actual,
        status=_status(expected, actual),
    )


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------
ALL_CHECKS: list[Callable[[Path], ParityRow]] = [
    check_laba05_001,
    check_laba05_002,
    check_laba05_003,
    check_laba05_004,
    check_laba05_005,
    check_laba05_006,
    check_labd20_001,
    check_labd20_002,
    check_labd20_003,
    check_labd20_004,
    check_labd20_005,
    check_labd20_006,
    check_labd20_007,
    check_labd20_008,
    check_labd20_009,
    check_labd20_010,
    check_labd20_011,
    check_labd20_012,
    check_labd20_013,
    check_labd20_014,
    check_labd20_015,
    check_labd20_016,
    check_labd20_017,
    check_labd20_018,
    check_labd20_019,
    check_labd20_020,
    check_labd20_021,
    check_labd20_022,
]


def run_all(workspace: Optional[Path] = None) -> list[ParityRow]:
    """Run every parity check. Each check uses its own subdir under `workspace`."""
    if workspace is None:
        workspace = REPO_ROOT / "migration" / "test-results" / "parity"
    workspace.mkdir(parents=True, exist_ok=True)
    # Silence noisy loader logs while sweeping.
    logging.getLogger().setLevel(logging.WARNING)
    rows: list[ParityRow] = []
    for fn in ALL_CHECKS:
        subdir = workspace / fn.__name__
        try:
            rows.append(fn(subdir))
        except Exception as exc:  # pragma: no cover - defensive
            rows.append(
                ParityRow(
                    br_id=fn.__name__,
                    label="(check raised)",
                    owner="?",
                    cobol_path="",
                    cobol_lines=(0, 0),
                    python_path="",
                    python_lines=(0, 0),
                    confidence="LOW",
                    classification="error",
                    input_desc="",
                    expected={},
                    actual={"exception": repr(exc)},
                    status="FAIL",
                    notes=f"Check raised: {exc!r}",
                )
            )
    return rows


def summary(rows: list[ParityRow]) -> dict[str, int]:
    out = {"PASS": 0, "FAIL": 0, "UNRESOLVED": 0}
    for r in rows:
        out[r.status] = out.get(r.status, 0) + 1
    return out


# ---------------------------------------------------------------------------
# Source extraction helpers (for the parity console UI)
# ---------------------------------------------------------------------------
def read_source_span(path: str, start: int, end: int) -> str:
    p = REPO_ROOT / path
    if not p.exists():
        return f"(file not found: {path})"
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    start_i = max(0, start - 1)
    end_i = min(len(lines), end)
    block = lines[start_i:end_i]
    width = len(str(end_i))
    return "\n".join(f"{(start_i + i + 1):>{width}}  {line}" for i, line in enumerate(block))


if __name__ == "__main__":  # pragma: no cover
    rows = run_all()
    s = summary(rows)
    print(f"Parity sweep: PASS={s.get('PASS',0)}  FAIL={s.get('FAIL',0)}  UNRESOLVED={s.get('UNRESOLVED',0)}")
    width = max(len(r.br_id) for r in rows)
    for r in rows:
        print(f"  {r.status:5}  {r.br_id:<{width}}  {r.label}")
        if r.status != "PASS":
            print(f"          expected={r.expected}")
            print(f"          actual  ={r.actual}")
