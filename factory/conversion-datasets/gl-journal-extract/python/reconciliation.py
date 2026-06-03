"""Reconciliation engine — the part of the factory that is the actual product.

A conversion is not "done" because code ran without an exception. It is done when
the money and the row counts provably survive the trip. This module computes the
control evidence the factory gates on:

  * row accounting        lines_in == lines_loaded + lines_rejected (no drops)
  * dollar control totals Σ legacy amount (accepted) == Σ target amount
  * journal balance       per journal_id, Σ debits == Σ credits
  * reject ledger         every rejected line, by reason, traceable to a byte row
  * mapping coverage      % of input lines that reached the target

The same checks double as the Momentum **import simulator**: re-reading the
emitted wire file and re-asserting the journal-level rules is exactly what
Momentum's own import would do, so a green reconciliation is a load rehearsal.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from decimal import Decimal

from mapper import MomentumJournalLine, RejectedLine


@dataclass
class JournalBalance:
    journal_id: str
    debits: Decimal
    credits: Decimal

    @property
    def is_balanced(self) -> bool:
        return self.debits == self.credits

    @property
    def variance(self) -> Decimal:
        return (self.debits - self.credits).quantize(Decimal("0.01"))


@dataclass
class ReconciliationReport:
    lines_in: int = 0
    accepted: list[MomentumJournalLine] = field(default_factory=list)
    rejected: list[RejectedLine] = field(default_factory=list)
    legacy_control_total: Decimal = Decimal("0.00")
    target_control_total: Decimal = Decimal("0.00")
    journal_balances: list[JournalBalance] = field(default_factory=list)
    reject_reasons: dict[str, int] = field(default_factory=dict)

    # --- gates -----------------------------------------------------------
    @property
    def row_accounting_ok(self) -> bool:
        return self.lines_in == len(self.accepted) + len(self.rejected)

    @property
    def control_total_ok(self) -> bool:
        return self.legacy_control_total == self.target_control_total

    @property
    def unbalanced_journals(self) -> list[JournalBalance]:
        return [b for b in self.journal_balances if not b.is_balanced]

    @property
    def all_journals_balanced(self) -> bool:
        return len(self.unbalanced_journals) == 0

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
            and self.all_journals_balanced
        )


def reconcile(
    lines_in: int,
    mapped: list[MomentumJournalLine | RejectedLine],
    legacy_accepted_amounts: list[Decimal],
) -> ReconciliationReport:
    """Build a reconciliation report from a mapped batch.

    `legacy_accepted_amounts` is the list of pre-transform legacy amounts for the
    *accepted* lines, captured before scaling-independent rounding, so the dollar
    control total compares like-for-like.
    """
    report = ReconciliationReport(lines_in=lines_in)

    reason_counts: dict[str, int] = defaultdict(int)
    debit_by_journal: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
    credit_by_journal: dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

    for item in mapped:
        if isinstance(item, RejectedLine):
            report.rejected.append(item)
            reason_counts[item.reason] += 1
            continue
        report.accepted.append(item)
        report.target_control_total += item.debit_amount + item.credit_amount
        debit_by_journal[item.journal_id] += item.debit_amount
        credit_by_journal[item.journal_id] += item.credit_amount

    report.legacy_control_total = sum(
        legacy_accepted_amounts, start=Decimal("0.00")
    ).quantize(Decimal("0.01"))
    report.target_control_total = report.target_control_total.quantize(
        Decimal("0.01")
    )

    for jid in sorted(set(debit_by_journal) | set(credit_by_journal)):
        report.journal_balances.append(
            JournalBalance(
                journal_id=jid,
                debits=debit_by_journal[jid].quantize(Decimal("0.01")),
                credits=credit_by_journal[jid].quantize(Decimal("0.01")),
            )
        )

    report.reject_reasons = dict(sorted(reason_counts.items()))
    return report
