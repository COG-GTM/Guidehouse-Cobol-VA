"""End-to-end driver for the obligation/disbursement vertical slice.

Run order (the same five beats every factory interface follows):

    profile/parse  ->  map/transform/validate  ->  reconcile
        ->  emit loadable target  ->  simulate load + post-load checks

Usage:
    python convert.py <extract.dat> [--out target.psv] [--report report.json]

Exit code is non-zero when the batch is not load-ready, so this doubles as a CI
gate. No network, no database, no credentials — pure stdlib.
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal
from pathlib import Path

from mapper import MomentumObligationLine, RejectedLine, _scaled_amount, map_line
from obl_extract import parse_extract
from reconciliation import ReconciliationReport, reconcile

WIRE_HEADER = (
    "obligation_id|fiscal_year|accounting_period|line_number|txn_type|vendor_id|"
    "tafs|appropriation|object_class|ussgl_account|obligation_amount|"
    "disbursement_amount|pop_start_date|pop_end_date|txn_date|description|"
    "source_system"
)


def run_slice(extract_text: str) -> tuple[ReconciliationReport, list[str]]:
    """Run parse -> map -> reconcile and return (report, wire_lines)."""
    raw_lines = parse_extract(extract_text)
    mapped: list[MomentumObligationLine | RejectedLine] = []
    legacy_accepted_amounts: list[Decimal] = []

    for raw in raw_lines:
        result = map_line(raw)
        mapped.append(result)
        if isinstance(result, MomentumObligationLine):
            # Capture the pre-transform legacy amount for like-for-like $ recon.
            legacy_amt = _scaled_amount(raw.amount)
            assert legacy_amt is not None  # accepted lines always parse
            legacy_accepted_amounts.append(legacy_amt)

    report = reconcile(len(raw_lines), mapped, legacy_accepted_amounts)
    wire_lines = [_to_wire(line) for line in report.accepted]
    return report, wire_lines


def _safe(value: str) -> str:
    # Free-text legacy fields may contain a pipe; strip it so the delimiter
    # stays unambiguous and simulate_momentum_import reads the right columns.
    return value.replace("|", " ")


def _to_wire(line: MomentumObligationLine) -> str:
    return "|".join(
        [
            line.obligation_id,
            str(line.fiscal_year),
            str(line.accounting_period),
            str(line.line_number),
            line.txn_type,
            _safe(line.vendor_id),
            _safe(line.tafs),
            line.appropriation,
            _safe(line.object_class),
            line.ussgl_account,
            f"{line.obligation_amount:.2f}",
            f"{line.disbursement_amount:.2f}",
            line.pop_start_date,
            line.pop_end_date,
            line.txn_date,
            _safe(line.description),
            line.source_system,
        ]
    )


def simulate_momentum_import(wire_lines: list[str]) -> dict[str, object]:
    """Re-read the emitted wire file and re-assert the obligation-funding rule.

    This is the import-simulator / post-load transaction test: it treats the
    emitted file as an opaque inbound interface (as Momentum would) and proves
    no obligation is over-disbursed at load time, independent of the in-memory
    objects.
    """
    obligated_by_id: dict[str, Decimal] = {}
    disbursed_by_id: dict[str, Decimal] = {}
    for wire in wire_lines:
        cols = wire.split("|")
        oid = cols[0]
        obligation = Decimal(cols[10])
        disbursement = Decimal(cols[11])
        obligated_by_id[oid] = obligated_by_id.get(oid, Decimal("0.00")) + obligation
        disbursed_by_id[oid] = (
            disbursed_by_id.get(oid, Decimal("0.00")) + disbursement
        )

    over_disbursed = [
        oid
        for oid in set(obligated_by_id) | set(disbursed_by_id)
        if disbursed_by_id.get(oid, Decimal("0.00"))
        > obligated_by_id.get(oid, Decimal("0.00"))
    ]
    return {
        "obligations_loaded": len(set(obligated_by_id) | set(disbursed_by_id)),
        "lines_loaded": len(wire_lines),
        "over_disbursed_after_load": sorted(over_disbursed),
        "post_load_ok": len(over_disbursed) == 0,
    }


def report_to_dict(report: ReconciliationReport) -> dict[str, object]:
    return {
        "lines_in": report.lines_in,
        "lines_loaded": len(report.accepted),
        "lines_rejected": len(report.rejected),
        "row_accounting_ok": report.row_accounting_ok,
        "legacy_control_total": f"{report.legacy_control_total:.2f}",
        "target_control_total": f"{report.target_control_total:.2f}",
        "control_total_ok": report.control_total_ok,
        "all_obligations_funded": report.all_obligations_funded,
        "over_disbursed_obligations": [
            b.obligation_id for b in report.over_disbursed_obligations
        ],
        "mapping_coverage": report.mapping_coverage,
        "reject_reasons": report.reject_reasons,
        "rejects": [
            {"line_index": r.line_index, "reason": r.reason, "detail": r.detail}
            for r in report.rejected
        ],
        "load_ready": report.load_ready,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Obligation/disbursement extract conversion slice"
    )
    parser.add_argument("extract", type=Path, help="legacy fixed-width extract file")
    parser.add_argument("--out", type=Path, help="write the emitted target wire file")
    parser.add_argument("--report", type=Path, help="write the reconciliation JSON")
    args = parser.parse_args(argv)

    text = args.extract.read_text()
    report, wire_lines = run_slice(text)
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
