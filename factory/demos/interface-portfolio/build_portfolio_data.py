"""Build the data sidecars for the interface-portfolio dashboard and the
executive report.

Reads the customer inventory through factory/interface-inventory/inventory.py
and the ICD through factory/icd (so neither page can disagree with the tested
model) and emits ``portfolio.data.js`` next to ``portfolio.html`` plus
``executive-report.data.js`` next to ``executive-report.html`` for file://
viewing — the same sidecar pattern the audit-trail viewer uses.

Usage:
    python build_portfolio_data.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_FACTORY = _HERE.parent.parent
sys.path.insert(0, str(_FACTORY / "interface-inventory"))
sys.path.insert(0, str(_FACTORY / "icd"))

from icd_builder import build_obligation_disbursement_icd  # noqa: E402
from inventory import assign_waves, load_inventory, summarize  # noqa: E402
from validate import validate_icd  # noqa: E402


def report_metrics() -> dict[str, int]:
    """The executive-report headline tiles, derived from the live model."""
    systems = load_inventory()
    summary = summarize(systems)
    return {
        "systems_total": summary["total_systems"],
        "factory_scope": summary["factory_scope"],
        "waves": len(assign_waves(systems)),
        "icd_violations": len(validate_icd(build_obligation_disbursement_icd())),
    }


def main() -> None:
    systems = load_inventory()
    waves = assign_waves(systems)
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "VA FMBT - FMS and iFAMS Interface Systems.xlsx (customer-provided)",
        "summary": summarize(systems),
        "systems": [
            {
                "name": s.system_name,
                "disposition": s.disposition.value,
                "managed_by_fms": s.managed_by_fms,
                "managed_by_ifams": s.managed_by_ifams,
                "in_factory_scope": s.in_factory_scope,
            }
            for s in systems
        ],
        "waves": {
            str(n): [s.system_name for s in members] for n, members in waves.items()
        },
    }
    out = _HERE / "portfolio.data.js"
    out.write_text("window.PORTFOLIO_DATA = " + json.dumps(payload, indent=2) + ";\n")
    print(f"[build_portfolio_data] wrote {out} ({len(systems)} systems, {len(waves)} waves)")

    metrics = report_metrics()
    report_out = _FACTORY / "executive-report.data.js"
    report_out.write_text("window.REPORT_DATA = " + json.dumps(metrics, indent=2) + ";\n")
    print(f"[build_portfolio_data] wrote {report_out} {metrics}")


if __name__ == "__main__":
    main()
