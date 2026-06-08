"""Fixed-width parser for the legacy obligation/disbursement extract.

Mirrors `source/OBL-DISBURSEMENT-REC.cpy`. The parser is deliberately dumb: it
slices the raw bytes into fields and trims trailing spaces, but performs NO
validation or type coercion. Validation lives in `mapper.py` so that the
"profile/parse" stage stays separable from the "map/transform/validate" stage,
exactly as the factory pipeline is described in `factory/design/FACTORY-DESIGN.md`
and reused from the GL/journal slice's `gl_extract.py`.

Field offsets are the single source of truth here and are asserted against the
copybook byte map in the tests.
"""

from __future__ import annotations

from dataclasses import dataclass

RECORD_LENGTH = 250

# 0-based [start, end) slices. Must match OBL-DISBURSEMENT-REC.cpy byte map.
FIELDS: dict[str, tuple[int, int]] = {
    "fiscal_year": (0, 4),
    "acct_period": (4, 6),
    "obligation_no": (6, 16),
    "line_no": (16, 19),
    "txn_type": (19, 20),
    "vendor_id": (20, 29),
    "treasury_symbol": (29, 49),
    "appropriation": (49, 55),
    "object_class": (55, 59),
    "ussgl_acct": (59, 65),
    "amount": (65, 80),
    "pop_start_jul": (80, 87),
    "pop_end_jul": (87, 94),
    "txn_date_jul": (94, 101),
    "description": (101, 141),
    "filler": (141, 250),
}


@dataclass(frozen=True)
class RawOblLine:
    """One parsed legacy obligation/disbursement event, fields as raw
    (right-trimmed) strings.

    `line_index` is the 1-based physical position in the extract file, used for
    reject provenance so a rejected line can always be traced back to the byte
    stream.
    """

    line_index: int
    fiscal_year: str
    acct_period: str
    obligation_no: str
    line_no: str
    txn_type: str
    vendor_id: str
    treasury_symbol: str
    appropriation: str
    object_class: str
    ussgl_acct: str
    amount: str
    pop_start_jul: str
    pop_end_jul: str
    txn_date_jul: str
    description: str


def parse_record(raw: str, line_index: int) -> RawOblLine:
    """Slice a single 250-char record into a :class:`RawOblLine`.

    Trailing spaces are stripped from every field (legacy is space-padded).
    Leading spaces/zeros are preserved so the mapper can decide what is valid.
    """
    if len(raw) < RECORD_LENGTH:
        # Pad short lines so slicing is well-defined; the mapper will reject the
        # resulting blank numeric fields with a precise reason.
        raw = raw.ljust(RECORD_LENGTH)

    def field(name: str) -> str:
        start, end = FIELDS[name]
        return raw[start:end].rstrip(" ")

    return RawOblLine(
        line_index=line_index,
        fiscal_year=field("fiscal_year"),
        acct_period=field("acct_period"),
        obligation_no=field("obligation_no"),
        line_no=field("line_no"),
        txn_type=field("txn_type"),
        vendor_id=field("vendor_id"),
        treasury_symbol=field("treasury_symbol"),
        appropriation=field("appropriation"),
        object_class=field("object_class"),
        ussgl_acct=field("ussgl_acct"),
        amount=field("amount"),
        pop_start_jul=field("pop_start_jul"),
        pop_end_jul=field("pop_end_jul"),
        txn_date_jul=field("txn_date_jul"),
        description=field("description"),
    )


def parse_extract(text: str) -> list[RawOblLine]:
    """Parse a full line-sequential extract into raw lines.

    Blank trailing lines (common when a file ends with a newline) are ignored.
    """
    lines: list[RawOblLine] = []
    for idx, raw in enumerate(text.splitlines(), start=1):
        if raw.strip() == "":
            continue
        lines.append(parse_record(raw, idx))
    return lines
