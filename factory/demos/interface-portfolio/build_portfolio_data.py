"""Build the data sidecar for the interface-portfolio dashboard.

Reads the customer inventory through factory/interface-inventory/inventory.py
(so the dashboard can never disagree with the tested model) and emits
``portfolio.data.js`` next to ``portfolio.html`` for file:// viewing — the same
sidecar pattern the audit-trail viewer uses.

Usage:
    python build_portfolio_data.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent.parent / "interface-inventory"))

from inventory import assign_waves, load_inventory, summarize  # noqa: E402


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


if __name__ == "__main__":
    main()
