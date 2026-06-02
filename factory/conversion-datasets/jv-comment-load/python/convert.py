"""End-to-end driver for the JV-comment vertical slice.

Run order (the same five beats every factory interface follows):

    profile/parse  ->  map/transform/validate  ->  reconcile
        ->  emit loadable target  ->  simulate load + post-load checks

Usage:
    python convert.py <comment_file.dat> [--out target.psv] [--report report.json]

The headline run uses the *real* Phase-1 fixture:
    python convert.py ../../../../migration/test-data/synthetic_comments.dat

Exit code is non-zero when the batch is not load-ready, so this doubles as a CI
gate. No network, no database, no credentials — pure stdlib + the reused
Phase-1 parser/validator.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from extract import parse_extract
from mapper import MomentumJvComment, RejectedComment, map_row
from reconciliation import ReconciliationReport, reconcile

WIRE_HEADER = (
    "natural_key|document_ref|comment_date|jv_number|section_id|loan_number|"
    "schedule_doc_no|comment_text|requestor|approver|control_num|source_system"
)


def run_slice(comment_path: Path) -> tuple[ReconciliationReport, list[str]]:
    """Run parse -> map -> reconcile and return (report, wire_lines)."""
    rows = parse_extract(comment_path)
    mapped: list[MomentumJvComment | RejectedComment] = [map_row(r) for r in rows]
    report = reconcile(len(rows), mapped)
    wire_lines = [_to_wire(c) for c in report.loaded]
    return report, wire_lines


def _safe(value: str) -> str:
    # Free-text legacy fields may contain a pipe; strip it so the delimiter
    # stays unambiguous and the wire keeps its declared 12-column layout.
    return value.replace("|", " ")


def _to_wire(c: MomentumJvComment) -> str:
    return "|".join(
        [
            c.natural_key,
            c.document_ref,
            c.comment_date,
            c.jv_number,
            c.section_id,
            c.loan_number,
            _safe(c.schedule_doc_no),
            _safe(c.comment_text),
            _safe(c.requestor),
            _safe(c.approver),
            c.control_num,
            c.source_system,
        ]
    )


def simulate_momentum_import(wire_lines: list[str]) -> dict[str, object]:
    """Re-read the emitted wire file and re-assert the load-level rules.

    This is the import-simulator / post-load transaction test: it treats the
    emitted file as an opaque inbound interface (as Momentum would) and proves
    the load is idempotent (no duplicate natural keys), independent of the
    in-memory objects.
    """
    keys: list[str] = []
    for wire in wire_lines:
        cols = wire.split("|")
        keys.append(cols[0])

    seen: set[str] = set()
    collisions = sorted({k for k in keys if k in seen or seen.add(k)})
    return {
        "rows_loaded": len(keys),
        "unique_keys_loaded": len(set(keys)),
        "key_collisions_after_load": collisions,
        "post_load_ok": len(collisions) == 0,
    }


def report_to_dict(report: ReconciliationReport) -> dict[str, object]:
    return {
        "rows_in": report.rows_in,
        "rows_loaded": len(report.loaded),
        "rows_duplicate_held": len(report.duplicates),
        "rows_rejected": len(report.rejected),
        "row_accounting_ok": report.row_accounting_ok,
        "key_integrity_ok": report.key_integrity_ok,
        "load_coverage": report.load_coverage,
        "reject_reasons": report.reject_reasons,
        "duplicate_keys": report.duplicate_keys,
        "rejects": [
            {"line_index": r.line_index, "reason": r.reason, "detail": r.detail}
            for r in report.rejected
        ],
        "load_ready": report.load_ready,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="JV-comment interface conversion slice")
    parser.add_argument("comment_file", type=Path, help="legacy fixed-width COMMENT-FILE")
    parser.add_argument("--out", type=Path, help="write the emitted target wire file")
    parser.add_argument("--report", type=Path, help="write the reconciliation JSON")
    args = parser.parse_args(argv)

    report, wire_lines = run_slice(args.comment_file)
    post_load = simulate_momentum_import(wire_lines)

    if args.out:
        args.out.write_text(WIRE_HEADER + "\n" + "\n".join(wire_lines) + "\n")
    report_dict = report_to_dict(report)
    report_dict["momentum_import_simulation"] = post_load
    if args.report:
        args.report.write_text(json.dumps(report_dict, indent=2))

    print(json.dumps(report_dict, indent=2))
    load_ok = bool(report.load_ready and post_load["post_load_ok"])
    print(f"\nLOAD_READY={load_ok}", file=sys.stderr)
    return 0 if load_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
