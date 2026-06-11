"""Map raw legacy obligation/disbursement lines onto the Momentum
obligation-import target contract.

This is the "transform + validate" stage. Each raw line either becomes a
:class:`MomentumObligationLine` (accepted) or a :class:`RejectedLine` (with a
precise, machine-readable reason code). Nothing is silently dropped — the
reconciliation engine asserts `accepted + rejected == lines_in`.

The crosswalks and whitelists here are the same small synthetic stand-ins the
GL/journal slice uses (`gl-journal-extract/python/mapper.py`). In production they
are externalized to the fiscal-year Treasury USSGL chart and the VA fund/
appropriation crosswalk; the open-questions doc asks the customer for the
authoritative ones (Q-REF-1, Q-REF-2).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from obl_extract import RawOblLine

# --- synthetic reference data (production: externalized + versioned) ---------

# A minimal slice of the U.S. Standard General Ledger chart relevant to the
# obligation/disbursement spending chain. Production validates against the full
# Treasury USSGL chart for the posting fiscal year (Q-REF-1).
USSGL_WHITELIST: frozenset[str] = frozenset(
    {
        "101000",  # Fund Balance With Treasury (disbursement drawdowns)
        "211000",  # Accounts Payable
        "310000",  # Unexpended Appropriations - Cumulative
        "461000",  # Allotments - Realized Resources
        "480100",  # Undelivered Orders - Obligations, Unpaid
        "490100",  # Delivered Orders - Obligations, Unpaid
        "490200",  # Delivered Orders - Obligations, Paid
        "610000",  # Operating Expenses/Program Costs
    }
)

# Legacy appropriation/fund code -> Momentum fund. Shared with the GL slice's
# FUND_CROSSWALK so a correction in one place generalizes (S8 knowledge fabric).
# Unmapped legacy funds are rejected so a silent mis-post can never reach the
# target.
FUND_CROSSWALK: dict[str, str] = {
    "0160": "0160-OPS",
    "0162": "0162-MEDSVC",
    "4537": "4537-SCF",
    "0152": "0152-CONST",
}

# Legacy single-char event type -> canonical txn type.
TXN_TYPE_MAP: dict[str, str] = {"O": "OBLIGATION", "D": "DISBURSEMENT"}


@dataclass(frozen=True)
class MomentumObligationLine:
    """A canonical, contract-conformant Momentum obligation/disbursement line."""

    obligation_id: str
    fiscal_year: int
    accounting_period: int
    line_number: int
    txn_type: str  # "OBLIGATION" | "DISBURSEMENT"
    vendor_id: str
    tafs: str
    appropriation: str
    object_class: str
    ussgl_account: str
    obligation_amount: Decimal
    disbursement_amount: Decimal
    pop_start_date: str  # ISO YYYY-MM-DD
    pop_end_date: str  # ISO YYYY-MM-DD
    txn_date: str  # ISO YYYY-MM-DD
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
    `migration/converted-code/python/dateconv.py`, reused verbatim from the
    GL/journal slice.
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


def map_line(raw: RawOblLine) -> MomentumObligationLine | RejectedLine:
    """Apply the target contract to a single raw line.

    Check order is deliberate: structural/identity checks first, then the
    obligation-specific business rules, so each rejected line surfaces the most
    actionable single reason.
    """
    # 1. Numeric integrity of the structural fields.
    for name, value in (
        ("fiscal_year", raw.fiscal_year),
        ("acct_period", raw.acct_period),
        ("line_no", raw.line_no),
    ):
        if not value.isdigit():
            return RejectedLine(raw.line_index, "NON_NUMERIC", f"{name}={value!r}")

    # 2. Obligation number present (the key that ties the spending chain).
    if raw.obligation_no == "":
        return RejectedLine(
            raw.line_index, "MISSING_OBLIGATION_NO", "blank obligation number"
        )

    period = int(raw.acct_period)
    if period < 1 or period > 14:
        return RejectedLine(raw.line_index, "BAD_PERIOD", f"acct_period={period}")

    # 3. Transaction type (obligation vs disbursement).
    canonical_txn = TXN_TYPE_MAP.get(raw.txn_type)
    if canonical_txn is None:
        return RejectedLine(raw.line_index, "BAD_TXN_TYPE", f"type={raw.txn_type!r}")

    # 4. Vendor / payee required (no anonymous obligation or outlay).
    if raw.vendor_id == "":
        return RejectedLine(raw.line_index, "MISSING_VENDOR", "blank vendor id")

    # 5. Amount.
    amount = _scaled_amount(raw.amount)
    if amount is None:
        return RejectedLine(raw.line_index, "NON_NUMERIC", f"amount={raw.amount!r}")
    if amount == Decimal("0.00"):
        return RejectedLine(raw.line_index, "ZERO_AMOUNT", "amount=0.00")

    # 6. USSGL account.
    if raw.ussgl_acct not in USSGL_WHITELIST:
        return RejectedLine(raw.line_index, "BAD_USSGL", f"ussgl={raw.ussgl_acct!r}")

    # 7. Dates: POP window + event date must all be real ordinal dates.
    pop_start = _julian_to_iso(raw.pop_start_jul)
    if pop_start is None:
        return RejectedLine(
            raw.line_index, "BAD_DATE", f"pop_start={raw.pop_start_jul!r}"
        )
    pop_end = _julian_to_iso(raw.pop_end_jul)
    if pop_end is None:
        return RejectedLine(raw.line_index, "BAD_DATE", f"pop_end={raw.pop_end_jul!r}")
    txn_iso = _julian_to_iso(raw.txn_date_jul)
    if txn_iso is None:
        return RejectedLine(
            raw.line_index, "BAD_DATE", f"txn_date={raw.txn_date_jul!r}"
        )

    # 8. Period of performance must not be inverted.
    if pop_end < pop_start:
        return RejectedLine(
            raw.line_index, "BAD_POP", f"pop_end {pop_end} < pop_start {pop_start}"
        )

    # 9. TAFS / appropriation.
    if raw.treasury_symbol == "":
        return RejectedLine(raw.line_index, "BAD_FUND", "empty treasury symbol")
    mapped_fund = FUND_CROSSWALK.get(raw.appropriation)
    if mapped_fund is None:
        return RejectedLine(
            raw.line_index, "BAD_FUND", f"unmapped appropriation={raw.appropriation!r}"
        )

    fy = int(raw.fiscal_year)
    obligation = amount if canonical_txn == "OBLIGATION" else Decimal("0.00")
    disbursement = amount if canonical_txn == "DISBURSEMENT" else Decimal("0.00")

    return MomentumObligationLine(
        obligation_id=f"OB-{fy}-{raw.obligation_no}",
        fiscal_year=fy,
        accounting_period=period,
        line_number=int(raw.line_no),
        txn_type=canonical_txn,
        vendor_id=raw.vendor_id,
        tafs=raw.treasury_symbol,
        appropriation=mapped_fund,
        object_class=raw.object_class,
        ussgl_account=raw.ussgl_acct,
        obligation_amount=obligation,
        disbursement_amount=disbursement,
        pop_start_date=pop_start,
        pop_end_date=pop_end,
        txn_date=txn_iso,
        description=raw.description,
    )
