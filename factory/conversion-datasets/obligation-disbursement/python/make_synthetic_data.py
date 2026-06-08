"""Generate synthetic, non-production obligation/disbursement extract fixtures.

Writes three fixed-width (250-byte) line-sequential files into ../data:

  obl_disbursement_clean.dat          all lines valid, every obligation funded
  obl_disbursement_with_rejects.dat   valid obligations + a spread of reject cases
  obl_disbursement_unbalanced.dat     one obligation over-disbursed (gate trips)

Run from this directory:
    python make_synthetic_data.py

The records are built field-by-field against OBL-DISBURSEMENT-REC.cpy so the
byte alignment is exact. All amounts/vendors/obligation numbers/descriptions are
invented — no real VA data.
"""

from __future__ import annotations

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def rec(
    *,
    fy: str = "2026",
    period: str = "07",
    obl_no: str = "VA26OBL001",
    line: str = "001",
    txn: str = "O",
    vendor: str = "V00012345",
    tafs: str = "036-2026-0160-000",
    approp: str = "0160",
    boc: str = "2520",
    ussgl: str = "480100",
    amount_cents: str = "000000010000000",  # $100,000.00
    pop_start: str = "2026001",  # 2026-01-01
    pop_end: str = "2026365",  # 2026-12-31
    txn_date: str = "2026032",  # 2026-02-01
    desc: str = "OBLIGATION - MEDICAL SUPPLIES",
) -> str:
    """Build one exact 250-char record. Each arg is already the field's content."""
    fields = [
        (fy, 4),
        (period, 2),
        (obl_no, 10),
        (line, 3),
        (txn, 1),
        (vendor, 9),
        (tafs, 20),
        (approp, 6),
        (boc, 4),
        (ussgl, 6),
        (amount_cents, 15),
        (pop_start, 7),
        (pop_end, 7),
        (txn_date, 7),
        (desc, 40),
        ("", 109),
    ]
    out = []
    for value, width in fields:
        if len(value) > width:
            raise ValueError(f"field {value!r} exceeds width {width}")
        # Numeric-looking fixed fields are right-justified zero/space filled by the
        # caller; text fields are left-justified, space-padded to width.
        out.append(value.ljust(width))
    record = "".join(out)
    assert len(record) == 250, len(record)
    return record


def cents(dollars: int) -> str:
    """Whole dollars -> 15-char zero-padded implied-2-decimal field.

    Money is integer cents end-to-end; never float (factory hard rule:
    use Decimal/int for money, never floats).
    """
    return str(dollars * 100).zfill(15)


def clean_lines() -> list[str]:
    # OBL VA26OBL001: $100k obligation, fully disbursed in two outlays
    #                 ($60k + $40k == $100k, funded exactly).
    # OBL VA26OBL002: $250k obligation, partially disbursed ($120k <= $250k).
    return [
        rec(obl_no="VA26OBL001", line="001", txn="O", ussgl="480100",
            amount_cents=cents(100000), desc="OBLIGATION - MEDICAL SUPPLIES"),
        rec(obl_no="VA26OBL001", line="002", txn="D", ussgl="490200",
            vendor="V00012345", amount_cents=cents(60000), txn_date="2026060",
            desc="DISBURSEMENT - PARTIAL A"),
        rec(obl_no="VA26OBL001", line="003", txn="D", ussgl="490200",
            vendor="V00012345", amount_cents=cents(40000), txn_date="2026120",
            desc="DISBURSEMENT - PARTIAL B"),
        rec(obl_no="VA26OBL002", line="001", txn="O", ussgl="480100", approp="0162",
            tafs="036-2026-0162-000", vendor="V00099001",
            amount_cents=cents(250000), desc="OBLIGATION - PROSTHETICS CONTRACT"),
        rec(obl_no="VA26OBL002", line="002", txn="D", ussgl="490200", approp="0162",
            tafs="036-2026-0162-000", vendor="V00099001",
            amount_cents=cents(120000), txn_date="2026200",
            desc="DISBURSEMENT - MILESTONE 1"),
    ]


def reject_lines() -> list[str]:
    # Reject cases — each isolated so a single reason fires, none belonging to a
    # funded accepted obligation (so accepted obligations stay funded).
    return [
        # BAD_USSGL: account not on whitelist.
        rec(obl_no="VA26REJ200", txn="O", ussgl="999999", amount_cents=cents(500),
            desc="BAD USSGL ACCOUNT"),
        # ZERO_AMOUNT: filler line.
        rec(obl_no="VA26REJ201", txn="O", ussgl="480100", amount_cents=cents(0),
            desc="ZERO DOLLAR FILLER"),
        # BAD_TXN_TYPE: indicator 'X'.
        rec(obl_no="VA26REJ202", txn="X", ussgl="480100", amount_cents=cents(10),
            desc="BAD TXN TYPE"),
        # BAD_DATE: txn date day-of-year 400.
        rec(obl_no="VA26REJ203", txn="O", ussgl="480100", txn_date="2026400",
            amount_cents=cents(10), desc="BAD JULIAN DATE"),
        # BAD_FUND: appropriation not in crosswalk.
        rec(obl_no="VA26REJ204", txn="O", ussgl="480100", approp="9999",
            amount_cents=cents(10), desc="UNMAPPED APPROPRIATION"),
        # NON_NUMERIC amount.
        rec(obl_no="VA26REJ205", txn="O", ussgl="480100",
            amount_cents="ABC000000000000", desc="NON NUMERIC AMOUNT"),
        # MISSING_VENDOR: blank vendor id.
        rec(obl_no="VA26REJ206", txn="O", ussgl="480100", vendor="",
            amount_cents=cents(10), desc="MISSING VENDOR"),
        # BAD_POP: period-of-performance end before start.
        rec(obl_no="VA26REJ207", txn="O", ussgl="480100", pop_start="2026300",
            pop_end="2026100", amount_cents=cents(10), desc="INVERTED POP WINDOW"),
        # MISSING_OBLIGATION_NO: blank obligation number.
        rec(obl_no="", txn="O", ussgl="480100", amount_cents=cents(10),
            desc="MISSING OBLIGATION NO"),
        # BAD_PERIOD: accounting period 00.
        rec(obl_no="VA26REJ209", period="00", txn="O", ussgl="480100",
            amount_cents=cents(10), desc="BAD PERIOD"),
    ]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    clean = clean_lines()
    (DATA_DIR / "obl_disbursement_clean.dat").write_text("\n".join(clean) + "\n")

    with_rejects = clean + reject_lines()
    (DATA_DIR / "obl_disbursement_with_rejects.dat").write_text(
        "\n".join(with_rejects) + "\n"
    )

    # Unbalanced: OBL VA26OBL900 is obligated for $100k but disbursed $110k
    # ($60k + $50k), over-disbursing by $10k — an Antideficiency-class breach.
    unbalanced = [
        rec(obl_no="VA26OBL900", line="001", txn="O", ussgl="480100",
            amount_cents=cents(100000), desc="OBLIGATION - OVER DISBURSED EXAMPLE"),
        rec(obl_no="VA26OBL900", line="002", txn="D", ussgl="490200",
            amount_cents=cents(60000), txn_date="2026060",
            desc="DISBURSEMENT - PARTIAL A"),
        rec(obl_no="VA26OBL900", line="003", txn="D", ussgl="490200",
            amount_cents=cents(50000), txn_date="2026120",
            desc="DISBURSEMENT - OVER BY 10K"),
    ]
    (DATA_DIR / "obl_disbursement_unbalanced.dat").write_text(
        "\n".join(unbalanced) + "\n"
    )

    print(f"wrote fixtures to {DATA_DIR}")


if __name__ == "__main__":
    main()
