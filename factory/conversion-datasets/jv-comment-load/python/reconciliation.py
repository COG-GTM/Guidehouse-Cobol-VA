"""Reconciliation engine for the JV-comment interface — the actual product.

A conversion is not "done" because code ran without an exception. It is done when
every legacy row is provably accounted for on the other side. This interface has
no dollar amounts, so the control evidence is **row + key integrity** rather than
$ control totals:

  * row accounting     rows_in == loaded + duplicates + rejected (no drops)
  * key integrity      every loaded record carries a 26-byte natural key, and
                       no two *loaded* records share one (idempotent load)
  * duplicate ledger   repeat natural keys are detected and held, not loaded —
                       exactly LABD20's "DUPLICATE ENTRY" skip (LABD20.pco:317-339)
  * reject ledger      every rejected row, by typed reason, traceable to a byte row
  * load coverage      % of input rows that became a loadable target record

The same checks double as the Momentum **import simulator**: re-reading the
emitted wire file and re-asserting key uniqueness is exactly what Momentum's own
idempotent import would do, so a green reconciliation is a load rehearsal.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from mapper import MomentumJvComment, RejectedComment


@dataclass
class ReconciliationReport:
    rows_in: int = 0
    loaded: list[MomentumJvComment] = field(default_factory=list)
    duplicates: list[MomentumJvComment] = field(default_factory=list)
    rejected: list[RejectedComment] = field(default_factory=list)
    reject_reasons: dict[str, int] = field(default_factory=dict)
    duplicate_keys: dict[str, int] = field(default_factory=dict)

    # --- gates -----------------------------------------------------------
    @property
    def accepted_count(self) -> int:
        """Rows that passed validation (loaded + held-duplicate)."""
        return len(self.loaded) + len(self.duplicates)

    @property
    def row_accounting_ok(self) -> bool:
        """No row is silently dropped or invented."""
        return self.rows_in == self.accepted_count + len(self.rejected)

    @property
    def key_integrity_ok(self) -> bool:
        """Every loaded record has a full-width key and all loaded keys are unique."""
        keys = [c.natural_key for c in self.loaded]
        full_width = all(len(k) == 26 and k.strip() != "" for k in keys)
        unique = len(keys) == len(set(keys))
        return full_width and unique

    @property
    def load_coverage(self) -> float:
        if self.rows_in == 0:
            return 0.0
        return round(len(self.loaded) / self.rows_in, 4)

    @property
    def load_ready(self) -> bool:
        """The single gate the factory CI asserts before a load is allowed."""
        return self.row_accounting_ok and self.key_integrity_ok


def reconcile(
    rows_in: int,
    mapped: list[MomentumJvComment | RejectedComment],
) -> ReconciliationReport:
    """Build a reconciliation report from a mapped batch.

    Duplicate detection mirrors LABD20: the first record for a natural key is
    loaded; later records with the same key are held in the duplicate ledger
    (the legacy 'DUPLICATE ENTRY' skip), never loaded twice.
    """
    report = ReconciliationReport(rows_in=rows_in)

    reason_counts: dict[str, int] = defaultdict(int)
    seen_keys: dict[str, int] = defaultdict(int)

    for item in mapped:
        if isinstance(item, RejectedComment):
            report.rejected.append(item)
            reason_counts[item.reason] += 1
            continue
        # Accepted: load the first occurrence of a key; hold the rest.
        if seen_keys[item.natural_key] == 0:
            report.loaded.append(item)
        else:
            report.duplicates.append(item)
        seen_keys[item.natural_key] += 1

    report.reject_reasons = dict(sorted(reason_counts.items()))
    report.duplicate_keys = {
        k: n for k, n in sorted(seen_keys.items()) if n > 1
    }
    return report
