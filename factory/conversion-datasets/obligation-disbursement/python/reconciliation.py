"""Reconciliation engine — the part of the factory that is the actual product.

A conversion is not "done" because code ran without an exception. It is done when
the money and the row counts provably survive the trip. This module computes the
control evidence the factory gates on, reusing the GL/journal slice's structure
but enforcing the obligation domain's integrity rule instead of journal balance:

  * row accounting        lines_in == lines_loaded + lines_rejected (no drops)
  * dollar control totals Σ legacy amount (accepted) == Σ target amount
  * obligation funding    per obligation_id, Σ disbursements <= Σ obligations
  * reject ledger         every rejected line, by reason, traceable to a byte row
  * mapping coverage      % of input lines that reached the target

The same checks double as the Momentum **import simulator**: re-reading the
emitted wire file and re-asserting the obligation-funding rule is exactly what
Momentum's own import would do, so a green reconciliation is a load rehearsal.

Over-disbursing an obligation (outlays exceeding the obligated ceiling) is an
Antideficiency-Act-class finding in federal financial management, not a rounding
nit — so it trips the load gate the same way an unbalanced journal does.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from mapper import MomentumObligationLine, RejectedLine


@dataclass
class ObligationBalance:
    obligation_id: str
    obligated: Decimal
    disbursed: Decimal

    @property
    def is_funded(self) -> bool:
        """True when disbursements do not exceed the obligated amount."""
        return self.disbursed <= self.obligated

    @property
    def remaining(self) -> Decimal:
        return (self.obligated - self.disbursed).quantize(Decimal("0.01"))


@dataclass
class ReconciliationReport:
    lines_in: int = 0
    accepted: list[MomentumObligationLine] = field(default_factory=list)
    rejected: list[RejectedLine] = field(default_factory=list)
    legacy_control_total: Decimal = Decimal("0.00")
    target_control_total: Decimal = Decimal("0.00")
    obligation_balances: list[ObligationBalance] = field(default_factory=list)
    reject_reasons: dict[str, int] = field(default_factory=dict)

    # --- gates -----------------------------------------------------------
    @property
    def row_accounting_ok(self) -> bool:
        return self.lines_in == len(self.accepted) + len(self.rejected)

    @property
    def control_total_ok(self) -> bool:
        return self.legacy_control_total == self.target_control_total

    @property
    def over_disbursed_obligations(self) -> list[ObligationBalance]:
        return [b for b in self.obligation_balances if not b.is_funded]

    @property
    def all_obligations_funded(self) -> bool:
        return len(self.over_disbursed_obligations) == 0

    @property
    def mapping_coverage(self) -> float:
        if self.lines_in == 0:
            return 0.0
        return round(len(self.accepted) / self.lines_in, 4)

    @property
    def load_ready(self) -> bool:
        """The single gate the factory CI asserts before a load is allowed."""
        return (
            self.row_accounting_ok
            and self.control_total_ok
            and self.all_obligations_funded
        )


def reconcile(
    lines_in: int,
    mapped: list[MomentumObligationLine | RejectedLine],
    legacy_accepted_amounts: list[Decimal],
) -> ReconciliationReport:
    """Build a reconciliation report from a mapped batch.

    `legacy_accepted_amounts` is the list of pre-transform legacy amounts for the
    *accepted* lines, captured before scaling-independent rounding, so the dollar
    control total compares like-for-like.
    """
    report = ReconciliationReport(lines_in=lines_in)

    reason_counts: dict[str, int] = defaultdict(int)
    obligated_by_id: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    disbursed_by_id: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for item in mapped:
        if isinstance(item, RejectedLine):
            report.rejected.append(item)
            reason_counts[item.reason] += 1
            continue
        report.accepted.append(item)
        report.target_control_total += item.obligation_amount + item.disbursement_amount
        obligated_by_id[item.obligation_id] += item.obligation_amount
        disbursed_by_id[item.obligation_id] += item.disbursement_amount

    report.legacy_control_total = sum(
        legacy_accepted_amounts, start=Decimal("0.00")
    ).quantize(Decimal("0.01"))
    report.target_control_total = report.target_control_total.quantize(
        Decimal("0.01")
    )

    for oid in sorted(set(obligated_by_id) | set(disbursed_by_id)):
        report.obligation_balances.append(
            ObligationBalance(
                obligation_id=oid,
                obligated=obligated_by_id[oid].quantize(Decimal("0.01")),
                disbursed=disbursed_by_id[oid].quantize(Decimal("0.01")),
            )
        )

    report.reject_reasons = dict(sorted(reason_counts.items()))
    return report
