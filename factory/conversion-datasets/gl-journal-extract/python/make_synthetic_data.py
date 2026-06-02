"""Generate synthetic, non-production GL/journal extract fixtures.

Writes three fixed-width (200-byte) line-sequential files into ../data:

  gl_extract_clean.dat          all lines valid, every journal balances
  gl_extract_with_rejects.dat   valid journals + a spread of reject cases
  gl_extract_unbalanced.dat     one journal whose debits != credits (gate trips)

Run from this directory:
    python make_synthetic_data.py

The records are built field-by-field against GL-JOURNAL-EXTRACT-REC.cpy so the
byte alignment is exact. All amounts/vendors/descriptions are invented.
"""

from __future__ import annotations

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def rec(
    *,
    fy: str = "2026",
    period: str = "07",
    jv: str = "000123",
    line: str = "001",
    jul: str = "2026032",  # 2026-02-01
    tafs: str = "036-2026-0160-000",
    fund: str = "0160",
    cc: str = "VHA00001",
    ussgl: str = "480100",
    boc: str = "2520",
    drcr: str = "D",
    amount_cents: str = "000000010000000",  # $100,000.00
    vendor: str = "         ",
    desc: str = "OBLIGATION - MEDICAL SUPPLIES",
) -> str:
    """Build one exact 200-char record. Each arg is already the field's content."""
    fields = [
        (fy, 4),
        (period, 2),
        (jv, 6),
        (line, 3),
        (jul, 7),
        (tafs, 20),
        (fund, 6),
        (cc, 8),
        (ussgl, 6),
        (boc, 4),
        (drcr, 1),
        (amount_cents, 15),
        (vendor, 9),
        (desc, 40),
        ("", 69),
    ]
    out = []
    for value, width in fields:
        if len(value) > width:
            raise ValueError(f"field {value!r} exceeds width {width}")
        # Numeric-looking fixed fields are right-justified zero/space filled by the
        # caller; text fields are left-justified, space-padded to width.
        out.append(value.ljust(width))
    record = "".join(out)
    assert len(record) == 200, len(record)
    return record


def cents(dollars: float) -> str:
    """Dollars -> 15-char zero-padded implied-2-decimal field."""
    return str(int(round(dollars * 100))).zfill(15)


def clean_lines() -> list[str]:
    # JV 123: two-line balanced obligation ($100k debit / $100k credit).
    # JV 124: four-line balanced disbursement ($60k + $40k debits / $100k credit
    #         split across two credit lines $70k + $30k).
    return [
        rec(jv="000123", line="001", drcr="D", ussgl="480100", amount_cents=cents(100000),
            desc="UDO - MEDICAL SUPPLIES"),
        rec(jv="000123", line="002", drcr="C", ussgl="211000", amount_cents=cents(100000),
            desc="ACCOUNTS PAYABLE - MED SUPPLIES"),
        rec(jv="000124", line="001", drcr="D", ussgl="610000", fund="0162",
            tafs="036-2026-0162-000", amount_cents=cents(60000),
            desc="PROGRAM COST - PROSTHETICS"),
        rec(jv="000124", line="002", drcr="D", ussgl="610000", fund="0162",
            tafs="036-2026-0162-000", amount_cents=cents(40000),
            desc="PROGRAM COST - PHARMACY"),
        rec(jv="000124", line="003", drcr="C", ussgl="101000", fund="0162",
            tafs="036-2026-0162-000", amount_cents=cents(70000),
            desc="FBWT DRAWDOWN A"),
        rec(jv="000124", line="004", drcr="C", ussgl="101000", fund="0162",
            tafs="036-2026-0162-000", amount_cents=cents(30000),
            desc="FBWT DRAWDOWN B"),
    ]


def reject_lines() -> list[str]:
    # Reject cases — each isolated so a single reason fires, none belonging to a
    # balanced accepted journal (so accepted journals still balance).
    return [
        # BAD_USSGL: account not on whitelist.
        rec(jv="000200", line="001", drcr="D", ussgl="999999", amount_cents=cents(500),
            desc="BAD USSGL ACCOUNT"),
        # ZERO_AMOUNT: filler line.
        rec(jv="000201", line="001", drcr="D", ussgl="480100", amount_cents=cents(0),
            desc="ZERO DOLLAR FILLER"),
        # BAD_DR_CR: indicator 'X'.
        rec(jv="000202", line="001", drcr="X", ussgl="480100", amount_cents=cents(10),
            desc="BAD DR CR INDICATOR"),
        # BAD_DATE: day-of-year 400.
        rec(jv="000203", line="001", drcr="D", ussgl="480100", jul="2026400",
            amount_cents=cents(10), desc="BAD JULIAN DATE"),
        # BAD_FUND: fund not in crosswalk.
        rec(jv="000204", line="001", drcr="D", ussgl="480100", fund="9999",
            amount_cents=cents(10), desc="UNMAPPED FUND"),
        # NON_NUMERIC amount.
        rec(jv="000205", line="001", drcr="D", ussgl="480100",
            amount_cents="ABC000000000000", desc="NON NUMERIC AMOUNT"),
    ]


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    clean = clean_lines()
    (DATA_DIR / "gl_extract_clean.dat").write_text("\n".join(clean) + "\n")

    with_rejects = clean + reject_lines()
    (DATA_DIR / "gl_extract_with_rejects.dat").write_text(
        "\n".join(with_rejects) + "\n"
    )

    # Unbalanced: JV 300 has a $100k debit but only a $90k credit.
    unbalanced = [
        rec(jv="000300", line="001", drcr="D", ussgl="480100", amount_cents=cents(100000),
            desc="UDO - UNBALANCED EXAMPLE"),
        rec(jv="000300", line="002", drcr="C", ussgl="211000", amount_cents=cents(90000),
            desc="AP - SHORT BY 10K"),
    ]
    (DATA_DIR / "gl_extract_unbalanced.dat").write_text("\n".join(unbalanced) + "\n")

    print(f"wrote fixtures to {DATA_DIR}")


if __name__ == "__main__":
    main()
