"""Interface portfolio model built from the customer-provided FMS/iFAMS
interface inventory (factory/reference/customer-artifacts/).

This is the wave-planning input for the orchestrator
(factory/playbooks/03-interface-wave-fanout.md): it loads the 125-system
inventory, classifies each system's migration disposition, and groups the
in-scope conversion workload into waves.

Disposition logic (from the four management flags in the workbook):

    managed_by_fms  managed_by_ifams  ->  disposition
    --------------  ----------------      -----------------------------
    Y               N                     MIGRATE_TO_IFAMS   (factory scope)
    Y               Y                     DUAL_MANAGED       (factory scope —
                                          cutover/decommission of the FMS leg)
    N               Y                     ALREADY_ON_IFAMS   (verify only)
    N               N                     OUT_OF_FMS_SCOPE   (no FMS interface
                                          to convert)

Pure stdlib; no network, no database.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

INVENTORY_CSV = (
    Path(__file__).resolve().parent.parent
    / "reference"
    / "customer-artifacts"
    / "fms_ifams_interface_inventory.csv"
)


class Disposition(str, Enum):
    MIGRATE_TO_IFAMS = "MIGRATE_TO_IFAMS"
    DUAL_MANAGED = "DUAL_MANAGED"
    ALREADY_ON_IFAMS = "ALREADY_ON_IFAMS"
    OUT_OF_FMS_SCOPE = "OUT_OF_FMS_SCOPE"


# Dispositions that put a system in the factory's conversion workload.
FACTORY_SCOPE = {Disposition.MIGRATE_TO_IFAMS, Disposition.DUAL_MANAGED}


@dataclass(frozen=True)
class InventorySystem:
    """One row of the customer inventory, plus its derived disposition."""

    system_name: str
    system_category: str
    managed_by_fms: bool
    managed_by_ifams: bool
    not_managed_by_fms: bool
    not_managed_by_ifams: bool

    @property
    def disposition(self) -> Disposition:
        return classify_disposition(self.managed_by_fms, self.managed_by_ifams)

    @property
    def in_factory_scope(self) -> bool:
        return self.disposition in FACTORY_SCOPE


def classify_disposition(managed_by_fms: bool, managed_by_ifams: bool) -> Disposition:
    if managed_by_fms and managed_by_ifams:
        return Disposition.DUAL_MANAGED
    if managed_by_fms:
        return Disposition.MIGRATE_TO_IFAMS
    if managed_by_ifams:
        return Disposition.ALREADY_ON_IFAMS
    return Disposition.OUT_OF_FMS_SCOPE


def load_inventory(csv_path: Path = INVENTORY_CSV) -> list[InventorySystem]:
    """Load and validate the customer inventory CSV."""
    systems: list[InventorySystem] = []
    seen: set[str] = set()
    with csv_path.open(newline="") as fh:
        for row in csv.DictReader(fh):
            name = row["system_name"].strip()
            if not name:
                continue
            if name in seen:
                raise ValueError(f"duplicate system in inventory: {name!r}")
            seen.add(name)
            systems.append(
                InventorySystem(
                    system_name=name,
                    system_category=row.get("system_category", "").strip(),
                    managed_by_fms=row["managed_by_fms"].strip() == "Y",
                    managed_by_ifams=row["managed_by_ifams"].strip() == "Y",
                    not_managed_by_fms=row["not_managed_by_fms"].strip() == "Y",
                    not_managed_by_ifams=row["not_managed_by_ifams"].strip() == "Y",
                )
            )
    if not systems:
        raise ValueError(f"empty inventory: {csv_path}")
    return systems


def summarize(systems: list[InventorySystem]) -> dict[str, int]:
    """Headline counts for the portfolio dashboard and PR evidence."""
    summary = {
        "total_systems": len(systems),
        "factory_scope": sum(1 for s in systems if s.in_factory_scope),
    }
    for disp in Disposition:
        summary[disp.value] = sum(1 for s in systems if s.disposition is disp)
    return summary


def assign_waves(systems: list[InventorySystem], wave_size: int = 10) -> dict[int, list[InventorySystem]]:
    """Group the factory-scope workload into orchestration waves.

    Without customer volume/frequency data (open gap — see
    reference/customer-artifacts/README.md) the sequencing heuristic is:
    DUAL_MANAGED first (their iFAMS leg already exists, so they are the
    cheapest validations and the fastest knowledge-fabric seed), then
    MIGRATE_TO_IFAMS alphabetically. Each wave fans out as one Devin child
    session per interface.
    """
    if wave_size < 1:
        raise ValueError("wave_size must be >= 1")
    workload = sorted(
        (s for s in systems if s.in_factory_scope),
        key=lambda s: (s.disposition is not Disposition.DUAL_MANAGED, s.system_name.lower()),
    )
    return {
        wave_no: workload[i : i + wave_size]
        for wave_no, i in enumerate(range(0, len(workload), wave_size), start=1)
    }


def _main() -> None:
    systems = load_inventory()
    summary = summarize(systems)
    width = max(len(k) for k in summary)
    print("FMS / iFAMS interface portfolio (customer inventory)")
    print("-" * (width + 8))
    for key, value in summary.items():
        print(f"  {key:<{width}}  {value:>4}")
    waves = assign_waves(systems)
    print(f"\nFactory fan-out plan: {len(waves)} waves of <=10 interfaces")
    first = waves[1]
    print(f"  Wave 1 ({len(first)} systems, dual-managed first):")
    for s in first:
        print(f"    - {s.system_name}  [{s.disposition.value}]")


if __name__ == "__main__":
    _main()
