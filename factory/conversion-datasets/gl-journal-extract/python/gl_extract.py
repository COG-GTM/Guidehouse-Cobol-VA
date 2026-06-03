"""Fixed-width parser for the legacy GL/journal extract.

Mirrors `source/GL-JOURNAL-EXTRACT-REC.cpy`. The parser is deliberately dumb: it
slices the raw bytes into fields and trims trailing spaces, but performs NO
validation or type coercion. Validation lives in `mapper.py` so that the
"profile/parse" stage stays separable from the "map/transform/validate" stage,
exactly as the factory pipeline is described in `factory/design/FACTORY-DESIGN.md`.

Field offsets are the single source of truth here and are asserted against the
copybook byte map in the tests.
"""

from __future__ import annotations

from dataclasses import dataclass

RECORD_LENGTH = 200

# 0-based [start, end) slices. Must match GL-JOURNAL-EXTRACT-REC.cpy byte map.
FIELDS: dict[str, tuple[int, int]] = {
    "fiscal_year": (0, 4),
    "acct_period": (4, 6),
    "jv_number": (6, 12),
    "line_no": (12, 15),
    "post_date_jul": (15, 22),
    "treasury_symbol": (22, 42),
    "fund": (42, 48),
    "cost_center": (48, 56),
    "ussgl_acct": (56, 62),
    "budget_obj_class": (62, 66),
    "dr_cr_ind": (66, 67),
    "amount": (67, 82),
    "vendor_id": (82, 91),
    "description": (91, 131),
    "filler": (131, 200),
}


@dataclass(frozen=True)
class RawGlLine:
    """One parsed legacy posting line, fields as raw (right-trimmed) strings.

    `line_index` is the 1-based physical position in the extract file, used for
    reject provenance so a rejected line can always be traced back to the byte
    stream.
    """

    line_index: int
    fiscal_year: str
    acct_period: str
    jv_number: str
    line_no: str
    post_date_jul: str
    treasury_symbol: str
    fund: str
    cost_center: str
    ussgl_acct: str
    budget_obj_class: str
    dr_cr_ind: str
    amount: str
    vendor_id: str
    description: str


def parse_record(raw: str, line_index: int) -> RawGlLine:
    """Slice a single 200-char record into a :class:`RawGlLine`.

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

    return RawGlLine(
        line_index=line_index,
        fiscal_year=field("fiscal_year"),
        acct_period=field("acct_period"),
        jv_number=field("jv_number"),
        line_no=field("line_no"),
        post_date_jul=field("post_date_jul"),
        treasury_symbol=field("treasury_symbol"),
        fund=field("fund"),
        cost_center=field("cost_center"),
        ussgl_acct=field("ussgl_acct"),
        budget_obj_class=field("budget_obj_class"),
        dr_cr_ind=field("dr_cr_ind"),
        amount=field("amount"),
        vendor_id=field("vendor_id"),
        description=field("description"),
    )


def parse_extract(text: str) -> list[RawGlLine]:
    """Parse a full line-sequential extract into raw lines.

    Blank trailing lines (common when a file ends with a newline) are ignored.
    """
    lines: list[RawGlLine] = []
    for idx, raw in enumerate(text.splitlines(), start=1):
        if raw.strip() == "":
            continue
        lines.append(parse_record(raw, idx))
    return lines
