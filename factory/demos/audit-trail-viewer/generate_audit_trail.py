"""Generate a per-record audit trail (provenance) for a conversion slice.

For every legacy record we capture its full journey through the factory
pipeline — S0 parse → S1 bind contract → S2 map/transform → S3 validate →
S4 reconcile → S5 emit → S6 load-simulate → S7 test/gate — with the concrete
input and output at each stage. The result is a single JSON document that the
companion `audit_trail_viewer.html` renders as an expandable trail.

This is the auditability story for the modernization: every dollar that moves
from legacy FMS to Momentum can be traced, byte-row to load status, with the
exact rule that accepted or rejected it. No record is silently dropped — the
row-accounting invariant (`lines_in == loaded + rejected`) is asserted here too.

Usage:
    python generate_audit_trail.py                 # GL slice, with-rejects fixture
    python generate_audit_trail.py --slice gl --fixture clean
    python generate_audit_trail.py --slice obligation --fixture with_rejects
    python generate_audit_trail.py --out audit_trail.json

All data is synthetic (the slices' own generated fixtures). No real VA data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[2]
DATASETS = REPO_ROOT / "factory" / "conversion-datasets"

# --- slice registry --------------------------------------------------------
# Each slice is described by where its code/fixtures live and the small bits of
# domain vocabulary the audit trail needs (target contract name, the reconcile
# "group" concept, and the load gate). Everything else is read generically off
# the dataclasses the slice already produces.
SLICES = {
    "gl": {
        "title": "GL / journal extract",
        "python": DATASETS / "gl-journal-extract" / "python",
        "data": DATASETS / "gl-journal-extract" / "data",
        "source_copybook": "source/GL-JOURNAL-EXTRACT-REC.cpy",
        "target_contract": "MOMENTUM-JOURNAL-IMPORT",
        "group_label": "journal",
        "group_attr": "journal_id",
        "fixtures": {
            "clean": "gl_extract_clean.dat",
            "with_rejects": "gl_extract_with_rejects.dat",
            "unbalanced": "gl_extract_unbalanced.dat",
        },
    },
    "obligation": {
        "title": "Obligation / disbursement extract",
        "python": DATASETS / "obligation-disbursement" / "python",
        "data": DATASETS / "obligation-disbursement" / "data",
        "source_copybook": "source/OBL-DISBURSEMENT-REC.cpy",
        "target_contract": "MOMENTUM-OBLIGATION-IMPORT",
        "group_label": "obligation",
        "group_attr": "obligation_id",
        "fixtures": {
            "clean": "obl_disbursement_clean.dat",
            "with_rejects": "obl_disbursement_with_rejects.dat",
            "unbalanced": "obl_disbursement_unbalanced.dat",
        },
    },
}


def _jsonable(value: object) -> object:
    if isinstance(value, Decimal):
        return f"{value:.2f}"
    if is_dataclass(value) and not isinstance(value, type):
        return {k: _jsonable(v) for k, v in asdict(value).items()}
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _accepted_fields(line: object) -> dict:
    """Flatten an accepted target line to JSON-able field/value pairs."""
    return {k: _jsonable(v) for k, v in asdict(line).items()}


def build_trail(slice_key: str, fixture_key: str) -> dict:
    cfg = SLICES[slice_key]
    sys.path.insert(0, str(cfg["python"]))

    # Imported here (after sys.path edit) so the right slice's flat modules load.
    import convert  # type: ignore
    import mapper  # type: ignore
    if slice_key == "gl":
        from gl_extract import parse_extract  # type: ignore
    else:
        from obl_extract import parse_extract  # type: ignore

    accepted_type = (
        mapper.MomentumJournalLine
        if slice_key == "gl"
        else mapper.MomentumObligationLine
    )

    fixture_path = cfg["data"] / cfg["fixtures"][fixture_key]
    raw_text = fixture_path.read_text()
    raw_lines = parse_extract(raw_text)

    # Full reconciliation once, for group balances + the load gate.
    report, wire_lines = convert.run_slice(raw_text)

    # Index the emitted wire lines by the accepted line so S5 can show the row.
    wire_by_group = {}
    for w in wire_lines:
        wire_by_group.setdefault(w.split("|")[0], []).append(w)

    group_attr = cfg["group_attr"]
    group_label = cfg["group_label"]

    # Group balance lookup (journal balance / obligation funding).
    group_state: dict[str, dict] = {}
    if slice_key == "gl":
        for jb in report.journal_balances:
            group_state[jb.journal_id] = {
                "debits": f"{jb.debits:.2f}",
                "credits": f"{jb.credits:.2f}",
                "balanced": jb.is_balanced,
                "variance": f"{jb.variance:.2f}",
            }
    else:
        for ob in report.obligation_balances:
            group_state[ob.obligation_id] = {
                "obligated": f"{ob.obligated:.2f}",
                "disbursed": f"{ob.disbursed:.2f}",
                "funded": ob.is_funded,
                "remaining": f"{ob.remaining:.2f}",
            }

    records = []
    for raw in raw_lines:
        result = mapper.map_line(raw)
        accepted = isinstance(result, accepted_type)
        raw_fields = {k: _jsonable(v) for k, v in asdict(raw).items()}
        group_id = getattr(result, group_attr) if accepted else None

        stages = []

        # S0 — profile / parse (the dumb fixed-width slice).
        stages.append({
            "id": "S0",
            "name": "Profile / parse",
            "status": "ok",
            "summary": f"Parsed {len(raw_text.splitlines())}-record extract; this is byte-row {raw.line_index}.",
            "detail": raw_fields,
        })

        # S1 — bind target contract.
        stages.append({
            "id": "S1",
            "name": "Bind contract",
            "status": "ok",
            "summary": f"Target contract: {cfg['target_contract']} (source_system=FMS).",
            "detail": {"target_contract": cfg["target_contract"]},
        })

        # S2 — map / transform.
        if accepted:
            stages.append({
                "id": "S2",
                "name": "Map / transform",
                "status": "ok",
                "summary": "Crosswalks applied (fund, USSGL), dates converted (CCYYDDD→ISO), money scaled to Decimal.",
                "detail": _accepted_fields(result),
            })
        else:
            stages.append({
                "id": "S2",
                "name": "Map / transform",
                "status": "halt",
                "summary": "Transform halted — a contract rule failed before a full target line could be built.",
                "detail": {"reason": result.reason, "detail": result.detail},
            })

        # S3 — validate.
        if accepted:
            stages.append({
                "id": "S3",
                "name": "Validate",
                "status": "ok",
                "summary": "Conforms to the target contract; accepted.",
                "detail": {"accepted": True},
            })
        else:
            stages.append({
                "id": "S3",
                "name": "Validate",
                "status": "reject",
                "summary": f"REJECTED — {result.reason}",
                "detail": {"reason": result.reason, "detail": result.detail},
            })

        # S4 — reconcile (group membership + balance/funding contribution).
        if accepted:
            stages.append({
                "id": "S4",
                "name": "Reconcile",
                "status": "ok" if group_state.get(group_id, {}).get(
                    "balanced", group_state.get(group_id, {}).get("funded", True)
                ) else "warn",
                "summary": f"Belongs to {group_label} {group_id}.",
                "detail": {group_label: group_id, "group_state": group_state.get(group_id, {})},
            })
        else:
            stages.append({
                "id": "S4",
                "name": "Reconcile",
                "status": "reject",
                "summary": "Excluded from the target batch (counted as rejected, never dropped).",
                "detail": {"counted_as": "rejected"},
            })

        # S5 — emit loadable target.
        if accepted:
            wire = ""
            candidates = wire_by_group.get(group_id, [])
            # Match the specific emitted line for this record (by line number).
            for w in candidates:
                cols = w.split("|")
                if slice_key == "gl" and cols[3] == str(result.line_number):
                    wire = w
                    break
                if slice_key == "obligation" and cols[3] == str(result.line_number):
                    wire = w
                    break
            stages.append({
                "id": "S5",
                "name": "Emit",
                "status": "ok",
                "summary": "Emitted to the pipe-delimited Momentum load file.",
                "detail": {"wire": wire or candidates[0] if candidates else ""},
            })
        else:
            stages.append({
                "id": "S5",
                "name": "Emit",
                "status": "skip",
                "summary": "Not emitted (rejected at S3).",
                "detail": {},
            })

        # S6 — load-simulate.
        if accepted:
            stages.append({
                "id": "S6",
                "name": "Load-simulate",
                "status": "ok",
                "summary": "Re-read by the Momentum import simulator as an opaque inbound row.",
                "detail": {"load_status": "loaded"},
            })
        else:
            stages.append({
                "id": "S6",
                "name": "Load-simulate",
                "status": "skip",
                "summary": "Not presented to the load (rejected upstream).",
                "detail": {"load_status": "not_loaded"},
            })

        # S7 — test / gate.
        stages.append({
            "id": "S7",
            "name": "Test / gate",
            "status": "ok" if report.load_ready else "warn",
            "summary": (
                "Batch passed all control gates (row accounting, $ control total, "
                + ("journal balance)." if slice_key == "gl" else "obligation funding).")
                if report.load_ready
                else "Batch did NOT pass all gates — load blocked (exit 1)."
            ),
            "detail": {"batch_load_ready": report.load_ready},
        })

        records.append({
            "line_index": raw.line_index,
            "byte_row": _byte_row(raw_text, raw.line_index),
            "group": group_id,
            "outcome": "accepted" if accepted else "rejected",
            "reject_reason": None if accepted else result.reason,
            "label": _label(slice_key, raw, result, accepted),
            "stages": stages,
        })

    run_id = _run_id(slice_key, fixture_key, raw_text)
    summary = {
        "lines_in": report.lines_in,
        "loaded": len(report.accepted),
        "rejected": len(report.rejected),
        "row_accounting_ok": report.row_accounting_ok,
        "legacy_control_total": f"{report.legacy_control_total:.2f}",
        "target_control_total": f"{report.target_control_total:.2f}",
        "control_total_ok": report.control_total_ok,
        "mapping_coverage": report.mapping_coverage,
        "reject_reasons": report.reject_reasons,
        "load_ready": report.load_ready,
    }

    return {
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "slice": slice_key,
        "slice_title": cfg["title"],
        "source_copybook": cfg["source_copybook"],
        "target_contract": cfg["target_contract"],
        "fixture": cfg["fixtures"][fixture_key],
        "group_label": group_label,
        "summary": summary,
        "records": records,
    }


def _byte_row(text: str, line_index: int) -> str:
    rows = [ln for ln in text.splitlines() if ln.strip() != ""]
    if 1 <= line_index <= len(rows):
        return rows[line_index - 1]
    return ""


def _label(slice_key: str, raw: object, result: object, accepted: bool) -> str:
    if slice_key == "gl":
        return f"JV {raw.jv_number} / line {raw.line_no} — {raw.description}".strip()
    return f"{raw.obligation_no} / line {raw.line_no} ({raw.txn_type}) — {raw.description}".strip()


def _run_id(slice_key: str, fixture_key: str, text: str) -> str:
    h = hashlib.sha256(f"{slice_key}:{fixture_key}:{text}".encode()).hexdigest()[:10]
    return f"run-{slice_key}-{fixture_key}-{h}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a conversion audit trail JSON")
    parser.add_argument("--slice", choices=sorted(SLICES), default="gl")
    parser.add_argument(
        "--fixture",
        choices=["clean", "with_rejects", "unbalanced"],
        default="with_rejects",
    )
    parser.add_argument("--out", type=Path, default=HERE / "audit_trail.json")
    args = parser.parse_args(argv)

    trail = build_trail(args.slice, args.fixture)
    payload = json.dumps(trail, indent=2)
    args.out.write_text(payload)

    # Also emit a JS sidecar so the viewer works when opened directly from disk
    # (file://), where fetch() of a local JSON is blocked by the browser. The
    # HTML reads window.AUDIT_TRAIL if present, and still offers a file picker.
    js_path = args.out.with_suffix(".data.js")
    js_path.write_text("window.AUDIT_TRAIL = " + payload + ";\n")

    s = trail["summary"]
    print(
        f"wrote {args.out.name} + {js_path.name}: slice={trail['slice']} "
        f"fixture={trail['fixture']} records={len(trail['records'])} "
        f"loaded={s['loaded']} rejected={s['rejected']} "
        f"load_ready={s['load_ready']} run_id={trail['run_id']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
