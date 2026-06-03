"""Fixed-width extractor for the legacy JV-comment interface (TST123-COMMENT-REC).

This is the "profile/parse" stage (S0–S1) of the factory pipeline, but unlike the
GL slice it does **not** re-implement the parser. It reuses the Phase-1
modernized loader verbatim:

    migration/converted-code/python/labd20_loader.py

That module is Devin's faithful Python port of `source/procobol/LABD20.pco`
(record layout cited to LABD20.pco:43-55). Reusing it is the whole point of this
slice: the conversion factory is built *on top of* the real, already-verified
Guidehouse modernization — same bytes, same offsets, same DATECONV date check —
so there is exactly one definition of the legacy record in the repo.

The factory only adds provenance: each parsed record is paired with its 1-based
physical line index so a reject can always be traced back to the source byte
stream.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# Put the Phase-1 modernization package on the path and import the *real*
# parser/record. REPO_ROOT = .../factory/conversion-datasets/jv-comment-load/python
# -> parents[4] is the repo root.
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "migration" / "converted-code"))

from python.labd20_loader import (  # noqa: E402
    TST123_RECORD_LENGTH,
    CommentRecord,
    iter_records,
    parse_comment_record,
)

RECORD_LENGTH = TST123_RECORD_LENGTH  # 300, from LABD20.pco:43-55


@dataclass(frozen=True)
class SourceRow:
    """One parsed legacy comment record plus its byte-stream provenance.

    `line_index` is the 1-based physical position in the extract file, used for
    reject provenance so a rejected row can always be traced back to the source.
    """

    line_index: int
    record: CommentRecord


def parse_extract(path: Path) -> list[SourceRow]:
    """Parse a full line-sequential COMMENT-FILE into provenance-tagged rows.

    Streaming + fixed-width normalization (pad/truncate to 300 bytes) are
    handled by the reused `iter_records` (LABD20.pco:239-253 semantics). Blank
    trailing lines are skipped by `iter_records`.
    """
    rows: list[SourceRow] = []
    for idx, raw in enumerate(iter_records(path), start=1):
        rows.append(SourceRow(line_index=idx, record=parse_comment_record(raw)))
    return rows
