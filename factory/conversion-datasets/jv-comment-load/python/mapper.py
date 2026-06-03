"""Map legacy JV-comment records onto the Momentum JV-comment import contract.

This is the "map/transform/validate" stage (S2–S3). Each source row either
becomes a :class:`MomentumJvComment` (accepted) or a :class:`RejectedComment`
(with a precise, machine-readable reason code). Nothing is silently dropped —
the reconciliation engine asserts `accepted + rejected == rows_in`.

Validation is **not** re-implemented here. It delegates to the Phase-1 loader's
`determine_disposition`, which is Devin's faithful port of the eight LABD20
edits (LABD20.pco:261-307). The factory only adds two things on top of the
modernized validation:

  1. a stable, typed reject code for each legacy prose reason (so the reject
     ledger and the knowledge-fabric taxonomy are machine-comparable), and
  2. the mapping of accepted legacy fields onto Momentum's import contract,
     including the 26-byte natural key used for idempotent load + dedup
     (the same key LABD20 checks against JC_SUBMITTED_COMMENT_TBL,
     LABD20.pco:329).

The target contract (`../target/MOMENTUM-JV-COMMENT-IMPORT.md`) is a plausible
reconstruction pending the authoritative Momentum ICD (open question Q-MOM-1).
"""

from __future__ import annotations

from dataclasses import dataclass

from extract import SourceRow

# Phase-1 modernized validation (faithful port of LABD20.pco:261-307).
from python.labd20_loader import determine_disposition

# --- typed reject taxonomy --------------------------------------------------
# Maps each Phase-1 prose disposition reason (LABD20 edit) to a stable code.
# Keep in sync with factory/knowledge/reject-taxonomy.md.
REASON_CODES: dict[str, str] = {
    "blank record": "BLANK_RECORD",
    "comment date is non-numeric": "NON_NUMERIC_DATE",
    "comment date is not a valid YYYYMMDD calendar date": "BAD_DATE",
    "JV number is non-numeric or zero": "BAD_JV_NUMBER",
    "section id is non-numeric": "NON_NUMERIC_SECTION",
    "loan number is non-numeric": "NON_NUMERIC_LOAN",
    "comment text is blank": "BLANK_COMMENT",
    "requestor is blank": "BLANK_REQUESTOR",
    "approver is blank": "BLANK_APPROVER",
}


@dataclass(frozen=True)
class MomentumJvComment:
    """A canonical, contract-conformant Momentum JV-comment annotation."""

    natural_key: str  # 26-byte idempotency key (LABD20 JC_SUBMITTED, .pco:329)
    document_ref: str  # the JV document the comment annotates
    comment_date: str  # ISO YYYY-MM-DD
    jv_number: str
    section_id: str
    loan_number: str
    schedule_doc_no: str
    comment_text: str
    requestor: str
    approver: str
    control_num: str  # JV-NUMBER(6) + SECTION-ID(2), LABD20.pco:160-165
    source_system: str = "LABD20"


@dataclass(frozen=True)
class RejectedComment:
    """A row that failed the target contract, with full provenance."""

    line_index: int
    reason: str  # primary typed code
    detail: str  # all failing edits, prose, for the SME queue


def _iso_date(yyyymmdd: str) -> str:
    """Format a validated 8-digit YYYYMMDD as ISO YYYY-MM-DD.

    Only called for rows that already passed the Phase-1 date edits
    (numeric + DATECONV CHECK-CYMD-DT), so slicing is safe.
    """
    return f"{yyyymmdd[0:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:8]}"


def map_row(row: SourceRow) -> MomentumJvComment | RejectedComment:
    """Apply the target contract to a single source row."""
    rec = row.record
    is_valid, reasons = determine_disposition(rec)

    if not is_valid:
        primary = REASON_CODES.get(reasons[0], "UNMAPPED_REASON")
        return RejectedComment(
            line_index=row.line_index,
            reason=primary,
            detail="; ".join(reasons),
        )

    return MomentumJvComment(
        natural_key=rec.submitted_key,
        document_ref=f"JV-{rec.section_id}-{rec.jv_number}",
        comment_date=_iso_date(rec.comment_dt),
        jv_number=rec.jv_number,
        section_id=rec.section_id,
        loan_number=rec.loan_number,
        schedule_doc_no=rec.schedule_doc_no.rstrip(" "),
        comment_text=rec.comment_text.rstrip(" "),
        requestor=rec.requestor.rstrip(" "),
        approver=rec.approver.rstrip(" "),
        control_num=rec.control_num,
    )
