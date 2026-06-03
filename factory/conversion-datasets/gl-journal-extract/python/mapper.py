"""Map raw legacy GL lines onto the Momentum journal-import target contract.

This is the "transform + validate" stage. Each raw line either becomes a
:class:`MomentumJournalLine` (accepted) or a :class:`RejectedLine` (with a
precise, machine-readable reason code). Nothing is silently dropped — the
reconciliation engine asserts `accepted + rejected == lines_in`.

The crosswalks and whitelists here are small synthetic stand-ins. In production
they are externalized to the fiscal-year Treasury USSGL chart and the VA fund
crosswalk; the open-questions doc asks the customer for the authoritative ones.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from gl_extract import RawGlLine

# --- synthetic reference data (production: externalized + versioned) ---------

# A minimal slice of the U.S. Standard General Ledger chart relevant to journal
# postings in this demo. Production validates against the full Treasury USSGL
# chart for the posting fiscal year.
USSGL_WHITELIST: frozenset[str] = frozenset(
    {
        "101000",  # Fund Balance With Treasury
        "131000",  # Accounts Receivable
        "211000",  # Accounts Payable
        "310000",  # Unexpended Appropriations - Cumulative
        "480100",  # Undelivered Orders - Obligations, Unpaid
        "490100",  # Delivered Orders - Obligations, Unpaid
        "610000",  # Operating Expenses/Program Costs
    }
)

# Legacy fund code -> Momentum fund. Unmapped legacy funds are rejected so a
# silent mis-post can never reach the target.
FUND_CROSSWALK: dict[str, str] = {
    "0160": "0160-OPS",
    "0162": "0162-MEDSVC",
    "4537": "4537-SCF",
    "0152": "0152-CONST",
}

VALID_DR_CR = frozenset({"D", "C"})


@dataclass(frozen=True)
class MomentumJournalLine:
    """A canonical, contract-conformant Momentum journal line."""

    journal_id: str
    fiscal_year: int
    accounting_period: int
    line_number: int
    posting_date: str  # ISO YYYY-MM-DD
    tafs: str
    fund: str
    cost_center: str
    ussgl_account: str
    budget_object_class: str
    debit_amount: Decimal
    credit_amount: Decimal
    vendor_id: str | None
    description: str
    source_system: str = "FMS"


@dataclass(frozen=True)
class RejectedLine:
    """A line that failed the target contract, with provenance."""

    line_index: int
    reason: str
    detail: str


def _julian_to_iso(ccyyddd: str) -> str | None:
    """Convert a CCYYDDD ordinal date to ISO `YYYY-MM-DD`, or None if invalid.

    CCYYDDD = 4-digit year + 3-digit day-of-year (001..365/366). This is the
    same ordinal-date convention the repo already ports in
    `migration/converted-code/python/dateconv.py`.
    """
    if len(ccyyddd) != 7 or not ccyyddd.isdigit():
        return None
    year = int(ccyyddd[:4])
    doy = int(ccyyddd[4:])
    if year < 1900 or year > 9999 or doy < 1:
        return None
    is_leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    max_doy = 366 if is_leap else 365
    if doy > max_doy:
        return None
    d = date(year, 1, 1) + timedelta(days=doy - 1)
    return d.isoformat()


def _scaled_amount(raw_amount: str) -> Decimal | None:
    """Interpret a 9(13)V99 zoned-numeric string as a Decimal dollar amount."""
    if not raw_amount.isdigit():
        return None
    # Implied 2 decimal places.
    try:
        return (Decimal(raw_amount) / Decimal(100)).quantize(Decimal("0.01"))
    except InvalidOperation:  # pragma: no cover - defensive
        return None


def map_line(raw: RawGlLine) -> MomentumJournalLine | RejectedLine:
    """Apply the target contract to a single raw line."""
    # 1. Numeric integrity.
    for name, value in (
        ("fiscal_year", raw.fiscal_year),
        ("acct_period", raw.acct_period),
        ("jv_number", raw.jv_number),
        ("line_no", raw.line_no),
    ):
        if not value.isdigit():
            return RejectedLine(raw.line_index, "NON_NUMERIC", f"{name}={value!r}")

    period = int(raw.acct_period)
    if period < 1 or period > 14:
        return RejectedLine(raw.line_index, "BAD_PERIOD", f"acct_period={period}")

    # 2. DR/CR indicator.
    if raw.dr_cr_ind not in VALID_DR_CR:
        return RejectedLine(raw.line_index, "BAD_DR_CR", f"ind={raw.dr_cr_ind!r}")

    # 3. Amount.
    amount = _scaled_amount(raw.amount)
    if amount is None:
        return RejectedLine(raw.line_index, "NON_NUMERIC", f"amount={raw.amount!r}")
    if amount == Decimal("0.00"):
        return RejectedLine(raw.line_index, "ZERO_AMOUNT", "amount=0.00")

    # 4. USSGL account.
    if raw.ussgl_acct not in USSGL_WHITELIST:
        return RejectedLine(raw.line_index, "BAD_USSGL", f"ussgl={raw.ussgl_acct!r}")

    # 5. Posting date.
    iso = _julian_to_iso(raw.post_date_jul)
    if iso is None:
        return RejectedLine(raw.line_index, "BAD_DATE", f"jul={raw.post_date_jul!r}")

    # 6. TAFS / fund.
    if raw.treasury_symbol == "":
        return RejectedLine(raw.line_index, "BAD_FUND", "empty treasury symbol")
    mapped_fund = FUND_CROSSWALK.get(raw.fund)
    if mapped_fund is None:
        return RejectedLine(raw.line_index, "BAD_FUND", f"unmapped fund={raw.fund!r}")

    fy = int(raw.fiscal_year)
    debit = amount if raw.dr_cr_ind == "D" else Decimal("0.00")
    credit = amount if raw.dr_cr_ind == "C" else Decimal("0.00")

    return MomentumJournalLine(
        journal_id=f"JV-{fy}-{int(raw.jv_number):06d}",
        fiscal_year=fy,
        accounting_period=period,
        line_number=int(raw.line_no),
        posting_date=iso,
        tafs=raw.treasury_symbol,
        fund=mapped_fund,
        cost_center=raw.cost_center,
        ussgl_account=raw.ussgl_acct,
        budget_object_class=raw.budget_obj_class,
        debit_amount=debit,
        credit_amount=credit,
        vendor_id=raw.vendor_id or None,
        description=raw.description,
    )
