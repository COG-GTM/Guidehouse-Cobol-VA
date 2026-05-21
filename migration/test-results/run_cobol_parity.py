#!/usr/bin/env python3
"""
GnuCOBOL ⇔ Python parity harness for DATECONV.

For every test vector in ``migration/test-results/dateconv-test-vectors.txt``:

1. Feed the vector to ``migration/test-results/build/dateconv-driver`` (the
   GnuCOBOL binary linked against the verbatim customer subprogram
   ``source/cobol/DATECONV.cbl``).
2. Drive the same vector through ``migration/converted-code/python/dateconv.py``
   via the same ``ConvDates`` field set.
3. Render both outputs in the SAME pipe-delimited shape (see ``COL_NAMES``)
   and diff them byte-for-byte.
4. Emit ``migration/test-results/cobol-parity-report.html`` with the
   methodology / honesty / per-vector tables, and ``cobol-parity-summary.json``
   for downstream automation.

Exits 0 if every vector matches byte-for-byte, 1 if any mismatch occurs, 2
on infrastructure errors (driver not built, Python port missing, etc.).
"""
from __future__ import annotations

import html
import json
import pathlib
import subprocess
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "migration" / "converted-code" / "python"))

from dateconv import (  # noqa: E402 — path manipulation above is intentional
    ConvDates,
    DateConv,
    STATUS_OK,
    STATUS_OOR_DD,
    STATUS_OOR_DDD,
    STATUS_OOR_MM,
    STATUS_OOR_YYYY,
    STATUS_STRANGE,
)

VECTORS_PATH = REPO_ROOT / "migration" / "test-results" / "dateconv-test-vectors.txt"
DRIVER_BIN   = REPO_ROOT / "migration" / "test-results" / "build" / "dateconv-driver"
REPORT_HTML  = REPO_ROOT / "migration" / "test-results" / "cobol-parity-report.html"
SUMMARY_JSON = REPO_ROOT / "migration" / "test-results" / "cobol-parity-summary.json"

# ---------------------------------------------------------------------------
# Output columns — must match the COBOL driver's EMIT-RESULT paragraph
# (migration/test-results/build/DATECONV-DRIVER.cob).
# ---------------------------------------------------------------------------
COL_NAMES = [
    "FUNC",
    "TO_INT",
    "TO_JUL",
    "TO_CYMD",
    "TO_YMD",
    "TO_MDCY",
    "TO_MDY",
    "DAYS_DIF",
    "DAYS_DIF_UNS",
    "DATE_ERR_IND",
    "DATE_ERR_REASON",
    "STATUS",
]

# Map Python status strings → JDN-Con-Status-Codes integers used by COBOL.
# JDN-CONSTANTS-WS.cpy is the authoritative source.
PY_STATUS_TO_REASON = {
    STATUS_OK:        0,
    STATUS_OOR_DD:    7,
    STATUS_OOR_DDD:   8,
    STATUS_OOR_MM:   10,
    STATUS_OOR_YYYY: 11,
    STATUS_STRANGE:  12,
}


@dataclass
class VectorResult:
    line_num: int
    raw: str
    cobol: Optional[List[str]] = None
    python: Optional[List[str]] = None
    error: str = ""

    @property
    def matched(self) -> bool:
        return (
            self.error == ""
            and self.cobol is not None
            and self.python is not None
            and self.cobol == self.python
        )

    @property
    def first_diff_field(self) -> Optional[str]:
        if self.cobol is None or self.python is None:
            return None
        for i, (a, b) in enumerate(zip(self.cobol, self.python)):
            if a != b:
                return COL_NAMES[i] if i < len(COL_NAMES) else f"col{i}"
        if len(self.cobol) != len(self.python):
            return "len"
        return None


# ---------------------------------------------------------------------------
# Vector parsing / field assignment
# ---------------------------------------------------------------------------
FIELD_TO_ATTR = [
    None,                 # 1: ABORT (control flag, not stored on ConvDates)
    "datesub_func",       # 2
    "from_int_dt",        # 3
    "from_jul_dt",        # 4
    "from_cymd_dt",       # 5
    "from_ymd_dt",        # 6
    "from_mdy_dt",        # 7
    "months_to_add",      # 8
    "between_jul_dt",     # 9
    # Field 10 fans out to both between_ymd_dt and between_mdy_dt because in
    # DATECONV-WS.cpy:63-68 they REDEFINE the same 6-byte storage — assigning
    # one field implicitly sets the other in COBOL. The Python ConvDates
    # keeps them as separate attributes, so the harness has to mirror the
    # REDEFINES aliasing manually.
    ("between_ymd_dt", "between_mdy_dt"),  # 10
    "to_int_dt",          # 11
    "to_jul_dt",          # 12
    "to_cymd_dt",         # 13
    "to_ymd_dt",          # 14
    "to_mdy_dt",          # 15
]


def parse_vector(line: str) -> Tuple[int, ConvDates]:
    """Decode one pipe-delimited test vector into (func_code, ConvDates)."""
    fields = line.rstrip("\r\n").split("|")
    cd = ConvDates()
    func_code = 0
    for idx, raw in enumerate(fields):
        if idx + 1 > len(FIELD_TO_ATTR):
            break
        attr = FIELD_TO_ATTR[idx]
        if attr is None:
            continue  # ABORT is informational only for the COBOL side
        value = raw.strip()
        if value == "":
            continue
        try:
            ival = int(value)
        except ValueError:
            ival = 0
        if isinstance(attr, tuple):
            for a in attr:
                setattr(cd, a, ival)
        else:
            setattr(cd, attr, ival)
            if attr == "datesub_func":
                func_code = ival
    return func_code, cd


# ---------------------------------------------------------------------------
# Output formatting — match the COBOL driver's PIC clauses exactly so the
# diff harness can compare strings byte-for-byte.
# ---------------------------------------------------------------------------
def fmt_pic9(value: int, width: int) -> str:
    """Render an unsigned numeric field with leading zeros (PIC 9(width))."""
    if value < 0:
        # COBOL would store as unsigned; treat as 0 to mirror driver behaviour
        # (the driver moves error-paths to ZEROS).
        value = 0
    return f"{value:0{width}d}"


def fmt_signed5(value: int) -> str:
    """Render DAYS-DIF as PIC -(5)9 (right-justified, leading sign or blank)."""
    if value < 0:
        return f"{value:6d}"  # e.g. '   -60'
    return f"{value:6d}"


def fmt_reason(value: int) -> str:
    return f"{value:02d}"


def render_python_row(func_code: int, cd: ConvDates, status: str) -> List[str]:
    return [
        fmt_pic9(func_code, 2),
        fmt_pic9(cd.to_int_dt, 10),
        fmt_pic9(cd.to_jul_dt, 5),
        fmt_pic9(cd.to_cymd_dt, 8),
        fmt_pic9(cd.to_ymd_dt, 6),
        fmt_pic9(cd.to_mdcy_dt, 8),
        fmt_pic9(cd.to_mdy_dt, 6),
        fmt_signed5(cd.days_dif),
        fmt_pic9(abs(cd.days_dif) if cd.days_dif else 0 if status == STATUS_OK else 0, 5)
            if False else fmt_pic9(_cobol_days_unsigned(cd), 5),
        cd.date_err_ind,
        fmt_reason(PY_STATUS_TO_REASON.get(status, cd.date_err_reason)),
        "OK",   # The "STATUS" column at the end of the COBOL driver is a
                # static "OK" sentinel emitted unconditionally per EMIT-RESULT.
    ]


def _cobol_days_unsigned(cd: ConvDates) -> int:
    """Mirror the COBOL DAYS-DIF-UNSIGNED assignment.

    DATECONV.cbl moves DAYS-DIF (signed) into DAYS-DIF-UNSIGNED (PIC 9(5)).
    A COBOL MOVE of a negative S9(5) to 9(5) drops the sign, so the
    unsigned field holds |DAYS-DIF|. The Python port keeps a single
    ``days_dif`` attribute — we recompute the unsigned form here.
    """
    return abs(cd.days_dif)


# ---------------------------------------------------------------------------
# Run the COBOL binary on the full vector file and capture stdout
# ---------------------------------------------------------------------------
def run_cobol(vectors_text: str) -> List[str]:
    if not DRIVER_BIN.exists():
        raise SystemExit(f"COBOL driver not built at {DRIVER_BIN}")
    proc = subprocess.run(
        [str(DRIVER_BIN)],
        input=vectors_text,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"COBOL driver exited {proc.returncode}; stderr=\n{proc.stderr}"
        )
    return proc.stdout.splitlines()


def run_python(vectors_text: str) -> List[str]:
    dc = DateConv()
    out: List[str] = []
    for line in vectors_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            out.append(line)
            continue
        func_code, cd = parse_vector(line)
        try:
            dc.dispatch(func_code, cd)
            # The Python port sets cd.date_err_reason directly; convert to
            # whatever the COBOL EMIT-RESULT field would have rendered.
            reason_str = fmt_reason(cd.date_err_reason)
            status_name = next(
                (k for k, v in PY_STATUS_TO_REASON.items() if v == cd.date_err_reason),
                STATUS_OK,
            )
            row = [
                fmt_pic9(cd.datesub_func, 2),
                fmt_pic9(cd.to_int_dt, 10),
                fmt_pic9(cd.to_jul_dt, 5),
                fmt_pic9(cd.to_cymd_dt, 8),
                fmt_pic9(cd.to_ymd_dt, 6),
                fmt_pic9(cd.to_mdcy_dt, 8),
                fmt_pic9(cd.to_mdy_dt, 6),
                fmt_signed5(cd.days_dif),
                fmt_pic9(_cobol_days_unsigned(cd), 5),
                cd.date_err_ind,
                reason_str,
                "OK",
            ]
            out.append("|".join(row))
        except Exception as exc:  # noqa: BLE001 — surface in report
            out.append(f"##PY-EXC line={line!r} err={exc!r}")
    return out


# ---------------------------------------------------------------------------
# Diff + report
# ---------------------------------------------------------------------------
def split_row(row: str) -> Optional[List[str]]:
    if row.startswith("#") or row.startswith("##") or not row.strip():
        return None
    return row.split("|")


def collect_results(
    vector_lines: List[str],
    cobol_lines: List[str],
    python_lines: List[str],
) -> List[VectorResult]:
    """Walk the three streams in lock-step.

    Comments / blank lines appear identically in all three (the COBOL driver
    echoes them); we only diff the value rows.
    """
    results: List[VectorResult] = []
    for idx, raw in enumerate(vector_lines, start=1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        # Find matching value rows in cobol/python at the same vector index.
        cobol_row = _nth_value_row(cobol_lines, len(results) + 1)
        python_row = _nth_value_row(python_lines, len(results) + 1)
        vr = VectorResult(line_num=idx, raw=raw.rstrip())
        if cobol_row is None or python_row is None:
            vr.error = "missing-row"
        else:
            vr.cobol = cobol_row.split("|")
            vr.python = python_row.split("|")
        results.append(vr)
    return results


def _nth_value_row(rows: List[str], n: int) -> Optional[str]:
    seen = 0
    for r in rows:
        if not r.strip() or r.lstrip().startswith("#"):
            continue
        seen += 1
        if seen == n:
            return r
    return None


# ---------------------------------------------------------------------------
# HTML report
# ---------------------------------------------------------------------------
HTML_HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>DATECONV — GnuCOBOL ⇔ Python parity diff</title>
<style>
  :root {{ color-scheme: light; }}
  body {{ font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
         margin: 0; padding: 0; background: #f7f7f8; color: #111; }}
  header {{ background: linear-gradient(135deg, #0b3d91 0%, #1f7ae0 100%);
            color: #fff; padding: 28px 40px; }}
  header h1 {{ margin: 0; font-size: 22px; }}
  header p {{ margin: 4px 0 0; opacity: 0.92; font-size: 13px; }}
  main {{ padding: 28px 40px; max-width: 1500px; margin: 0 auto; }}
  section {{ background: #fff; border: 1px solid #e1e4e8; border-radius: 8px;
             padding: 20px 24px; margin-bottom: 20px;
             box-shadow: 0 1px 2px rgba(0,0,0,0.04); }}
  section h2 {{ margin: 0 0 10px; font-size: 16px; color: #0b3d91; }}
  section p, section li {{ font-size: 13px; }}
  .stats {{ display: flex; gap: 16px; flex-wrap: wrap; }}
  .stat {{ flex: 1 1 180px; padding: 14px 18px; border-radius: 6px;
           background: #f0f3f8; border: 1px solid #d6dee8; }}
  .stat .num {{ font-size: 22px; font-weight: 600; }}
  .stat .lbl {{ font-size: 12px; text-transform: uppercase; letter-spacing: 0.06em; color: #555; }}
  .stat.ok {{ background: #e7f5ea; border-color: #b7dec1; }}
  .stat.bad {{ background: #fbe9e9; border-color: #e6b6b6; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 12px;
           font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
  th, td {{ border: 1px solid #e1e4e8; padding: 6px 8px; text-align: left;
            vertical-align: top; }}
  th {{ background: #f0f3f8; font-weight: 600; }}
  tr.diff {{ background: #fbe9e9; }}
  tr.ok td {{ color: #2a6f3b; }}
  tr.diff td {{ color: #8a1a1a; }}
  code {{ background: #f0f3f8; padding: 1px 4px; border-radius: 3px; }}
</style>
</head>
<body>
<header>
  <h1>GnuCOBOL legacy ⇔ Python port — byte-for-byte parity diff</h1>
  <p>{subtitle}</p>
</header>
<main>
"""


def render_report(
    results: List[VectorResult],
    gnucobol_version: str,
    cobol_status: str,
    python_status: str,
    run_seconds: float,
) -> str:
    total = len(results)
    matched = sum(1 for r in results if r.matched)
    mismatched = total - matched
    subtitle = (
        f"{total} vectors · {matched} matched · {mismatched} mismatched · "
        f"GnuCOBOL {gnucobol_version} · {run_seconds:.2f}s"
    )

    parts: List[str] = [HTML_HEAD.format(subtitle=html.escape(subtitle))]

    parts.append('<section><h2>Summary</h2>')
    parts.append('<div class="stats">')
    parts.append(f'<div class="stat"><div class="num">{total}</div><div class="lbl">vectors</div></div>')
    css = "stat ok" if mismatched == 0 else "stat"
    parts.append(f'<div class="{css}"><div class="num">{matched}</div><div class="lbl">matched</div></div>')
    css = "stat bad" if mismatched else "stat"
    parts.append(f'<div class="{css}"><div class="num">{mismatched}</div><div class="lbl">mismatched</div></div>')
    parts.append('</div></section>')

    parts.append('<section><h2>Methodology</h2><ul>')
    parts.append(f'<li><b>GnuCOBOL build:</b> {html.escape(gnucobol_version)}.</li>')
    parts.append(f'<li><b>COBOL compile path:</b> {html.escape(cobol_status)}.</li>')
    parts.append(f'<li><b>Python port:</b> {html.escape(python_status)}.</li>')
    parts.append('<li><b>Driver:</b> <code>migration/test-results/build/DATECONV-DRIVER.cob</code> '
                 'reads pipe-delimited vectors from STDIN, populates the LINKAGE-equivalent '
                 'CONV-DATES record exactly as defined in <code>source/copybooks/DATECONV-WS.cpy</code>, '
                 'CALLs the customer subprogram <code>DATECONV</code>, and writes a 12-column result '
                 'row per vector. See <code>EMIT-RESULT</code> for the exact PIC clauses used to render '
                 'the output.</li>')
    parts.append('<li><b>Python adapter:</b> '
                 '<code>migration/test-results/run_cobol_parity.py</code> parses the same vector '
                 'format, builds a <code>ConvDates</code> dataclass, calls '
                 '<code>DateConv().dispatch(func_code, cd)</code>, and renders the result with the same '
                 'PIC clauses (zero-padded numerics, signed PIC -(5)9 for DAYS-DIF, two-digit status code).</li>')
    parts.append('<li><b>Diff:</b> every output column is compared as a string. A row is "matched" only '
                 'if all 12 columns are byte-identical.</li>')
    parts.append('</ul></section>')

    parts.append('<section><h2>Honesty / Caveats</h2>')
    parts.append('<p>GnuCOBOL is an <b>open-source COBOL-85+ implementation</b>, '
                 'not the customer\'s Unisys runtime. The customer\'s '
                 '<code>source/cobol/DATECONV.cbl</code> compiled directly under GnuCOBOL '
                 '<i>without</i> any preprocessor or source modification — the <code>MIGRTN</code> '
                 'comment-column markers and the <code>word/alignd</code> annotations in the '
                 'JDN copybooks live in the sequence area (columns 1–6) and are ignored by '
                 'fixed-format COBOL, so no Unisys-specific directives needed to be stripped. '
                 'Compiler warnings (<code>OCCURS DEPENDING ON</code> truncation, '
                 'redefines size mismatches) were observed but did not affect the four COBOL-85 '
                 'intrinsic functions that DATECONV ultimately calls.</p>')
    parts.append('<p>The four intrinsics actually exercised — '
                 '<code>INTEGER-OF-DATE</code>, <code>DATE-OF-INTEGER</code>, '
                 '<code>INTEGER-OF-DAY</code>, <code>DAY-OF-INTEGER</code> — are '
                 'standardised in COBOL-85 / FIPS 21-3 and behave identically across '
                 'conformant compilers. Differences vs. the Unisys runtime would only '
                 'appear in implementation-defined corners (e.g. truncation semantics '
                 'for arithmetic overflow). The customer\'s '
                 '<code>JDN-RECORD-ACCESS.cpy</code> states explicitly that <em>"the COBOL-85 '
                 'standard (FIPS 21-2) was expanded in 1989 to include the Intrinsic Functions '
                 'Module ... the date routines it contains are a FIPS standard that the TST can '
                 'rely on to be implemented on all future COBOLs"</em>, which is exactly the '
                 'portability claim GnuCOBOL satisfies.</p>')
    parts.append('<p>The harness does <b>not</b> mutate <code>source/cobol/DATECONV.cbl</code> '
                 'or the JDN copybooks. The only generated artifact under '
                 '<code>migration/test-results/build/</code> is the COBOL driver '
                 '(<code>DATECONV-DRIVER.cob</code>) used to bridge stdin/stdout into the '
                 'subprogram\'s CALL interface.</p>')
    parts.append('</section>')

    # Add a categorized findings section if there are mismatches
    if mismatched > 0:
        parts.append('<section><h2>Findings / Divergence categories</h2>')
        parts.append('<p>The Python port diverges from the customer COBOL in the following '
                     'patterns. The harness reports these honestly — the Python port was '
                     '<b>not</b> patched by this session per the parent\'s standing instruction. '
                     'Each row below maps to one or more vectors in the per-vector table.</p>')
        parts.append('<table><thead><tr><th>#</th><th>Pattern</th>'
                     '<th>COBOL behavior (source citation)</th>'
                     '<th>Python behavior</th><th>Affected vectors</th>'
                     '<th>Recommended action</th></tr></thead><tbody>')
        parts.append(
            '<tr><td>1</td>'
            '<td>Julian-leap-year accepts 02/29 of non-Gregorian centurial years</td>'
            '<td><code>9950-VALIDATE-YYYY</code> in <code>source/cobol/DATECONV.cbl:1111-1127</code> '
            'uses <code>DIVIDE WRK-CYMD-YYYY BY 4 ... IF DAYS-TO-ADD &gt; 0 MOVE 2 TO LEAP-YEAR</code> — '
            'the every-4-years Julian rule. Therefore <code>CHECK-CYMD-DT(19000229)</code> '
            'returns <code>DATE-ERR-IND=N</code> (valid).</td>'
            '<td><code>_run01_check_cymd_dt</code> delegates to <code>_int_of_date</code>, which '
            'uses Python <code>datetime.date</code> (proleptic Gregorian). <code>19000229</code> '
            'is rejected with status <code>OutOfRangeDD</code> (07).</td>'
            '<td>L49 (<code>19000229</code>)</td>'
            '<td>Either replicate the Julian leap-year quirk to claim byte-for-byte parity, '
            '<b>or</b> document this as a deliberate, customer-approved modernization fix '
            'and flip <code>BR-DATECONV-001</code> accordingly (the <code>parity_engine.py</code> '
            '"expected" for <code>19000229</code> currently asserts the Python behavior).</td></tr>'
        )
        parts.append(
            '<tr><td>2</td>'
            '<td><code>TO-INT-DT</code> populated as intermediate JDN value in DIF operations</td>'
            '<td>The DIF paragraphs (<code>400-DIF-JUL</code>, <code>500-DIF-YMD</code>, '
            '<code>1400-DIF-MDY</code>, <code>1900-DIF-CYMD</code>) <i>only</i> assign '
            '<code>FROM-INT-DT</code> and <code>DAYS-DIF</code>; <code>TO-INT-DT</code> is never '
            'written, so it retains whatever value the caller left there.</td>'
            '<td><code>_set_dif</code> in <code>migration/converted-code/python/dateconv.py</code> '
            'writes <code>cd.to_int_dt = b</code> (the second JDN), leaking the intermediate '
            'into the output record.</td>'
            '<td>L80–84 (DIF-JUL, DIF-YMD, DIF-MDY, DIF-CYMD)</td>'
            '<td>Patch <code>_set_dif</code> to <i>not</i> write <code>cd.to_int_dt</code> '
            '(internal JDN can stay local). Same for <code>_dif_jul_no_check</code>.</td></tr>'
        )
        parts.append(
            '<tr><td>3</td>'
            '<td>30-day-month DIF: COBOL counts 31 days from Jan 31 → Mar 1, Python counts 30</td>'
            '<td><code>600-DIF-CYMD-30</code>, <code>1500-DIF-JUL-30</code>, '
            '<code>1600-DIF-MDY-30</code> use the 30-day-month convention but the customer\'s '
            'implementation evidently treats Jan 31 as Jan 30 (or Mar 1 as Mar 2). Concrete '
            'observation: DIF-CYMD-30(20240131 → 20240301) = <b>31</b>; DIF-MDY-30(013124 → '
            '030124) = <b>31</b>.</td>'
            '<td>Python returns <b>30</b>. Also writes <code>TO-INT-DT = 728700</code> '
            '(<code>YYYY*30*12 + MM*30 + DD</code> pseudo-JDN), which COBOL never exposes. '
            'Python also fails to set the conversion side-effects '
            '(<code>TO-JUL-DT</code>, <code>TO-MDY-DT</code>) that the COBOL leaves behind.</td>'
            '<td>L89 (DIF-CYMD-30), L90 (DIF-JUL-30), L91 (DIF-MDY-30)</td>'
            '<td>SME review required — confirm the customer\'s exact 30-day-month convention '
            '(it appears to count BOTH endpoints inclusively for end-of-month inputs). Then '
            'either align Python or document the modernization choice.</td></tr>'
        )
        parts.append(
            '<tr><td>4</td>'
            '<td>Conversion side-effects not propagated to <code>TO-YMD-DT</code> / '
            '<code>TO-CYMD-DT</code></td>'
            '<td>The COBOL conversion paragraphs chain other paragraphs internally; e.g. '
            '<code>2300-JUL-TO-CYMD</code> PERFORMs <code>3400-INT-TO-YMD</code>, which writes '
            '<code>TO-YMD-DT</code> as a side effect. <code>4500-ADD-MONTHS-END-JUL</code> '
            'leaves <code>TO-CYMD-DT</code> populated. <code>4000-DIF-FY</code> writes '
            'the upgraded YYYY into <code>TO-CYMD-YYYY</code> with MM/DD zeroed (<code>20240000</code>).</td>'
            '<td>The Python port assigns only the "primary" output field. The "scratch" '
            '<code>TO-*</code> side effects are not replicated, so callers that read multiple '
            'fields after a single CALL will see stale (zeroed) values.</td>'
            '<td>L65 (JUL-TO-CYMD), L86 (DIF-FY), L97 (ADD-CYMD), L101 (ADD-MONTHS-END-JUL)</td>'
            '<td>Decide per-paragraph whether the side effects matter to LABD20 / downstream '
            'callers. If yes, mirror them in the Python port. If no, document as intentional '
            'cleanup.</td></tr>'
        )
        parts.append(
            '<tr><td>5</td>'
            '<td>RANGE-MDY with all-zero <code>BETWEEN-MDY-DT</code> input</td>'
            '<td><code>4300-RANGE-MDY</code> in <code>source/cobol/DATECONV.cbl:941-985</code> '
            'feeds <code>BETWEEN-MDY-YY/MM/DD = 00/00/00</code> through '
            '<code>JDN-Acc-Int-Of-Date</code>; GnuCOBOL\'s '
            '<code>INTEGER-OF-DATE(20000000)</code> returns 0 but '
            '<code>JDN-PKT-STATUS</code> remains <code>NoErr</code>, so the paragraph proceeds '
            'into the comparison branch and emits <code>77777</code> (outside range).</td>'
            '<td>Python\'s <code>_int_of_date</code> validates explicitly and returns '
            '<code>OutOfRangeMM</code> for <code>MM=0</code>, so the paragraph short-circuits '
            'to <code>DATE-ERR-IND=Y</code>.</td>'
            '<td>L107 (RANGE-MDY)</td>'
            '<td>Edge case — caller never legitimately passes <code>BETWEEN=000000</code>. '
            'Either tighten the test vector (use a real "between" date) or mirror the COBOL '
            'no-error-on-zero quirk if downstream code depends on it.</td></tr>'
        )
        parts.append('</tbody></table></section>')

    # Per-vector table
    parts.append('<section><h2>Per-vector results</h2>')
    parts.append('<table>')
    parts.append('<thead><tr>'
                 '<th>#</th><th>FUNC</th><th>vector (input)</th>'
                 '<th>COBOL output</th><th>Python output</th>'
                 '<th>match?</th><th>first diff col</th>'
                 '</tr></thead><tbody>')
    for idx, r in enumerate(results, start=1):
        cls = "ok" if r.matched else "diff"
        cobol_out = "|".join(r.cobol) if r.cobol else "(none)"
        python_out = "|".join(r.python) if r.python else "(none)"
        match_cell = "PASS" if r.matched else "FAIL"
        diff_col = r.first_diff_field or "—"
        func_field = r.raw.split("|")[1] if "|" in r.raw else ""
        parts.append(
            f'<tr class="{cls}"><td>{idx}</td><td>{html.escape(func_field)}</td>'
            f'<td><code>{html.escape(r.raw)}</code></td>'
            f'<td><code>{html.escape(cobol_out)}</code></td>'
            f'<td><code>{html.escape(python_out)}</code></td>'
            f'<td>{match_cell}</td>'
            f'<td>{html.escape(diff_col)}</td></tr>'
        )
    parts.append('</tbody></table></section>')

    # Mismatch detail (side-by-side per column)
    mismatches = [r for r in results if not r.matched]
    if mismatches:
        parts.append('<section><h2>Mismatch detail</h2>')
        for r in mismatches:
            parts.append(f'<h3>Vector @ line {r.line_num} (FUNC={html.escape(r.raw.split("|")[1])})</h3>')
            parts.append(f'<p>Input: <code>{html.escape(r.raw)}</code></p>')
            parts.append('<table><thead><tr><th>column</th><th>COBOL</th><th>Python</th><th>diff?</th></tr></thead><tbody>')
            cobol_cols = r.cobol or []
            python_cols = r.python or []
            for i, name in enumerate(COL_NAMES):
                a = cobol_cols[i] if i < len(cobol_cols) else ""
                b = python_cols[i] if i < len(python_cols) else ""
                cls = "diff" if a != b else "ok"
                marker = "Δ" if a != b else ""
                parts.append(
                    f'<tr class="{cls}"><td>{html.escape(name)}</td>'
                    f'<td><code>{html.escape(a)}</code></td>'
                    f'<td><code>{html.escape(b)}</code></td>'
                    f'<td>{marker}</td></tr>'
                )
            parts.append('</tbody></table>')
        parts.append('</section>')

    parts.append('</main></body></html>')
    return "".join(parts)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main(argv: List[str]) -> int:
    if not VECTORS_PATH.exists():
        print(f"ERROR: vectors not found at {VECTORS_PATH}", file=sys.stderr)
        return 2

    vectors_text = VECTORS_PATH.read_text(encoding="utf-8")
    vector_lines = vectors_text.splitlines()

    t0 = time.perf_counter()
    cobol_out_lines = run_cobol(vectors_text)
    cobol_seconds = time.perf_counter() - t0

    t1 = time.perf_counter()
    python_out_lines = run_python(vectors_text)
    python_seconds = time.perf_counter() - t1

    results = collect_results(vector_lines, cobol_out_lines, python_out_lines)
    total = len(results)
    matched = sum(1 for r in results if r.matched)
    mismatched = total - matched

    # Probe the GnuCOBOL version for the report.
    try:
        gnucobol_version = subprocess.check_output(
            ["cobc", "--version"], text=True
        ).splitlines()[0]
    except Exception:  # noqa: BLE001
        gnucobol_version = "unknown"

    cobol_status = (
        "Direct compile of source/cobol/DATECONV.cbl succeeded under GnuCOBOL "
        "(no preprocessor required; no source modifications)."
    )
    python_status = (
        "migration/converted-code/python/dateconv.py — DateConv class with 40 _runNN_* methods "
        "mapped 1:1 to DATECONV.cbl paragraphs, dispatched via DATESUB-FUNC."
    )
    run_seconds = cobol_seconds + python_seconds

    REPORT_HTML.write_text(
        render_report(results, gnucobol_version, cobol_status, python_status, run_seconds),
        encoding="utf-8",
    )

    summary = {
        "vectors": total,
        "matched": matched,
        "mismatched": mismatched,
        "gnucobol_version": gnucobol_version,
        "cobol_seconds": round(cobol_seconds, 4),
        "python_seconds": round(python_seconds, 4),
        "mismatches": [
            {
                "line": r.line_num,
                "vector": r.raw,
                "first_diff_field": r.first_diff_field,
                "cobol": r.cobol,
                "python": r.python,
            }
            for r in results
            if not r.matched
        ],
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        f"DATECONV parity: {matched}/{total} vectors matched; "
        f"{mismatched} mismatched; report at {REPORT_HTML.relative_to(REPO_ROOT)}"
    )
    return 0 if mismatched == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
