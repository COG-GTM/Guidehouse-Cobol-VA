"""Doc-drift gate for factory/knowledge/reject-taxonomy.md.

The taxonomy hand-lists the typed reject codes per conversion slice. This test
derives both sides from the live artifacts and asserts bidirectional set
equality:

  * doc side  — backticked codes in each slice's table rows of the markdown
  * code side — ``RejectedLine(...)`` reason literals in each slice's mapper
                (and the JV slice's ``REASON_CODES`` taxonomy dict)

If a slice gains/loses a reject code, or the doc drifts, this fails with the
exact difference. ``OVER_DISBURSED`` is documented as an obligation-level
(reconciliation-gate) code, not a per-line ``RejectedLine`` reason, so it is
asserted against the funding gate in reconciliation.py instead.

Pure stdlib + file reads; no imports from the slices (their flat modules need
per-slice sys.path setup that this test deliberately avoids).
"""

import re
from pathlib import Path

FACTORY = Path(__file__).resolve().parent.parent.parent
TAXONOMY_MD = FACTORY / "knowledge" / "reject-taxonomy.md"
SLICES = FACTORY / "conversion-datasets"

GL_MAPPER = SLICES / "gl-journal-extract" / "python" / "mapper.py"
JV_MAPPER = SLICES / "jv-comment-load" / "python" / "mapper.py"
OBL_MAPPER = SLICES / "obligation-disbursement" / "python" / "mapper.py"
OBL_RECON = SLICES / "obligation-disbursement" / "python" / "reconciliation.py"

GL_HEADING = "## Current reasons (from GL/journal slice)"
JV_HEADING = "## Current reasons (from JV-comment slice"
OBL_HEADING = "## Current reasons (from obligation/disbursement slice)"
ANTICIPATED_HEADING = "## Anticipated reasons"


def _section(md: str, heading: str) -> str:
    start = md.index(heading)
    next_heading = md.find("\n## ", start + len(heading))
    return md[start : next_heading if next_heading != -1 else len(md)]


def _table_codes(section: str) -> set[str]:
    """Backticked codes in the first column of the section's table rows."""
    return {
        m.group(1)
        for line in section.splitlines()
        if line.startswith("| `")
        for m in [re.match(r"\| `([A-Z_]+)` \|", line)]
        if m
    }


def _prose_codes(section: str) -> set[str]:
    """Backticked all-caps codes mentioned outside table rows (reuse lists)."""
    prose = "\n".join(
        line for line in section.splitlines() if not line.startswith("|")
    )
    return set(re.findall(r"`([A-Z][A-Z_]+)`", prose))


def _rejected_line_codes(mapper_path: Path) -> set[str]:
    src = mapper_path.read_text()
    return set(re.findall(r'RejectedLine\(\s*[^,]+,\s*"([A-Z_]+)"', src, re.S))


def _jv_reason_codes(mapper_path: Path) -> set[str]:
    src = mapper_path.read_text()
    block = re.search(r"REASON_CODES[^=]*=\s*\{(.*?)\}", src, re.S).group(1)
    return set(re.findall(r':\s*"([A-Z_]+)"', block))


def test_gl_slice_codes_match_doc():
    md = TAXONOMY_MD.read_text()
    doc = _table_codes(_section(md, GL_HEADING))
    code = _rejected_line_codes(GL_MAPPER)
    assert doc == code, f"doc-only: {doc - code}; code-only: {code - doc}"


def test_jv_slice_codes_match_doc():
    md = TAXONOMY_MD.read_text()
    doc = _table_codes(_section(md, JV_HEADING))
    code = _jv_reason_codes(JV_MAPPER)
    assert doc == code, f"doc-only: {doc - code}; code-only: {code - doc}"


def test_obl_slice_codes_match_doc():
    """Obl/disb doc = its table (new codes) + the GL codes its prose says it
    reuses, minus the gate-level OVER_DISBURSED (not a per-line reject)."""
    md = TAXONOMY_MD.read_text()
    section = _section(md, OBL_HEADING)
    doc = (_table_codes(section) | _prose_codes(section)) - {"OVER_DISBURSED"}
    code = _rejected_line_codes(OBL_MAPPER)
    assert doc == code, f"doc-only: {doc - code}; code-only: {code - doc}"


def test_obl_reused_prose_codes_are_real_gl_codes():
    md = TAXONOMY_MD.read_text()
    reused = _prose_codes(_section(md, OBL_HEADING))
    gl = _rejected_line_codes(GL_MAPPER)
    assert reused <= gl, f"prose claims reuse of non-GL codes: {reused - gl}"


def test_over_disbursed_gate_is_live():
    """OVER_DISBURSED is documented as the funding-gate breach; the gate
    (disbursed <= obligated per obligation) must exist in reconciliation.py."""
    md = TAXONOMY_MD.read_text()
    assert "OVER_DISBURSED" in _table_codes(_section(md, OBL_HEADING))
    recon = OBL_RECON.read_text()
    assert "disbursed <= self.obligated" in recon


def test_anticipated_codes_not_yet_in_code():
    """'Anticipated (not yet triggered)' codes must NOT exist as live
    RejectedLine reasons — if one goes live, move it to its slice's table."""
    md = TAXONOMY_MD.read_text()
    anticipated = _table_codes(_section(md, ANTICIPATED_HEADING))
    live = (
        _rejected_line_codes(GL_MAPPER)
        | _rejected_line_codes(OBL_MAPPER)
        | _jv_reason_codes(JV_MAPPER)
    )
    assert not (anticipated & live), f"anticipated codes now live: {anticipated & live}"


def test_control_totals():
    """Deliberate-change guard: current expected code sets per slice."""
    assert _rejected_line_codes(GL_MAPPER) == {
        "NON_NUMERIC", "BAD_PERIOD", "BAD_DR_CR", "ZERO_AMOUNT",
        "BAD_USSGL", "BAD_DATE", "BAD_FUND",
    }
    assert _jv_reason_codes(JV_MAPPER) == {
        "BLANK_RECORD", "NON_NUMERIC_DATE", "BAD_DATE", "BAD_JV_NUMBER",
        "NON_NUMERIC_SECTION", "NON_NUMERIC_LOAN", "BLANK_COMMENT",
        "BLANK_REQUESTOR", "BLANK_APPROVER",
    }
    assert _rejected_line_codes(OBL_MAPPER) == {
        "NON_NUMERIC", "BAD_PERIOD", "BAD_TXN_TYPE", "MISSING_VENDOR",
        "ZERO_AMOUNT", "BAD_USSGL", "BAD_DATE", "BAD_FUND",
        "MISSING_OBLIGATION_NO", "BAD_POP",
    }
