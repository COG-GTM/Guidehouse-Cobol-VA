"""
demo_app.py — Runnable demo entrypoint for the modernized JV comment loader
and FY-reset utilities.

STATUS: Demo output pending SME review. Generated as part of the Guidehouse
JV COBOL/Pro*COBOL modernization walkthrough.

USAGE
-----
Zero-setup demo (uses bundled synthetic data + an in-memory sqlite mock of
Oracle):

    python -m migration.converted-code.python.demo_app run

Or the alias:

    python migration/converted-code/python/demo_app.py run

Sub-commands:
  run        Seed mock DB, then execute LABA05 (FY reset) and LABD20 (comment
             loader) against migration/test-data/. Prints a structured report.
  serve      Same as `run`, but exposes a tiny HTML dashboard at
             http://127.0.0.1:8765 showing the inputs, the run log, the
             database state before/after, and the rejection reasons. Useful
             for the live demo.

ASSUMPTIONS
-----------
- The mock DB is sqlite3 in-memory. Production wiring uses oracledb via
  DBDispatcher.from_env() (see ASSUMPTIONS-AND-PLACEHOLDERS.md A-1).
- Synthetic data is used (see migration/test-data/README.md) — no real
  customer information.
"""

from __future__ import annotations

import argparse
import io
import json
import logging
import sqlite3
import sys
from contextlib import redirect_stdout
from html import escape
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "migration" / "converted-code"))

from python.db_dispatcher import (  # noqa: E402
    DBDispatcher,
    build_demo_schema,
    seed_control_record,
)
from python.labd20_loader import (  # noqa: E402
    LABD20Loader,
    LoaderConfig,
    LoaderStats,
)
from python.laba05_reset import ResetOutcome  # noqa: E402
from python.laba05_reset import run as laba05_run  # noqa: E402
from python.parity_engine import (  # noqa: E402
    ParityRow,
    read_source_span,
    run_all as run_parity,
    summary as parity_summary,
)


SYNTHETIC_DATA = REPO_ROOT / "migration" / "test-data" / "synthetic_comments.dat"
SYNTHETIC_CARD = REPO_ROOT / "migration" / "test-data" / "synthetic_card.ctl"


def _build_dispatcher_with_seed(seed_jv: int = 99) -> DBDispatcher:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    dispatcher = DBDispatcher(conn)
    build_demo_schema(dispatcher)
    seed_control_record(dispatcher, jv_number=seed_jv)
    # Seed JC_COUNT_TBL row for section 'MA' so the post-process update path
    # has a baseline (per ASSUMPTIONS A-10).
    dispatcher.insert(
        "INSERT INTO JC_COUNT_TBL (JC_SECTION, JC_COUNT_NUM) VALUES (?, ?)",
        ("MA", 0),
    )
    dispatcher.commit()
    return dispatcher


# Tables surfaced in the demo's post-run summary. The strings are hard-coded
# module-level literals — there is no path by which untrusted input reaches
# the f-string below, so the SELECT * FROM {table} interpolation is safe.
# Keeping the list explicit here (rather than reusing db_dispatcher's broader
# _ALLOWED_TABLES) documents exactly what the demo summary surfaces.
_DISPLAY_TABLES: tuple[str, ...] = (
    "CONTROL_RECORD_TABLE",
    "JC_SUBMITTED_COMMENT_TBL",
    "JC_COUNT_TBL",
)


def _table_state(dispatcher: DBDispatcher) -> dict[str, list[dict[str, Any]]]:
    cur = dispatcher._conn.cursor()  # type: ignore[attr-defined]
    state: dict[str, list[dict[str, Any]]] = {}
    for table in _DISPLAY_TABLES:
        cur.execute(f"SELECT * FROM {table}")  # noqa: S608 - static literal table names
        rows = [dict(r) for r in cur.fetchall()]
        if table == "CONTROL_RECORD_TABLE":
            for r in rows:
                # Trim the 400-byte blob for display.
                r["CONTROL_RECORD_DATA"] = r["CONTROL_RECORD_DATA"][:30] + "..."
        state[table] = rows
    return state


def _run_full_demo(prepare_comments_path: Path) -> dict[str, Any]:
    """Build a fresh mock DB, run LABA05 + LABD20, return a structured report."""
    log_buffer = io.StringIO()
    handler = logging.StreamHandler(log_buffer)
    handler.setLevel(logging.INFO)
    root = logging.getLogger()
    prior_level = root.level
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    dispatcher = _build_dispatcher_with_seed(seed_jv=99)
    try:
        before_state = _table_state(dispatcher)

        # Phase 1: FY reset
        reset_outcome: ResetOutcome = laba05_run(dispatcher)

        # Phase 2: comment load
        loader = LABD20Loader(dispatcher)
        stats: LoaderStats = loader.run(
            LoaderConfig(
                card_path=SYNTHETIC_CARD,
                comment_path=prepare_comments_path,
                truncate_after_processing=True,
            )
        )

        after_state = _table_state(dispatcher)

        report = {
            "process_date": stats.process_date,
            "laba05": {
                "return_code": reset_outcome.return_code,
                "before_jv_number": reset_outcome.before_jv_number,
                "after_jv_number": reset_outcome.after_jv_number,
                "message": reset_outcome.message,
            },
            "labd20": {
                "total_read": stats.total_read,
                "accepted": stats.accepted,
                "inserted": stats.inserted,
                "duplicates": stats.duplicates,
                "rejected": stats.rejected,
                "submitted_total": stats.submitted_total,
                "rejected_reasons": stats.rejected_reasons,
                "report": stats.format_report(),
            },
            "before_state": before_state,
            "after_state": after_state,
            "log": log_buffer.getvalue(),
        }
        return report
    finally:
        root.removeHandler(handler)
        root.setLevel(prior_level)
        dispatcher.close()


def _copy_comments(tmp_dir: Path) -> Path:
    """Copy the synthetic file so the truncate doesn't clobber the fixture."""
    tmp_dir.mkdir(parents=True, exist_ok=True)
    target = tmp_dir / "comments.dat"
    target.write_bytes(SYNTHETIC_DATA.read_bytes())
    return target


# ---------------------------------------------------------------------------
# CLI: run
# ---------------------------------------------------------------------------
def cmd_run(args: argparse.Namespace) -> int:
    work_dir = Path(args.work_dir) if args.work_dir else REPO_ROOT / "migration" / "test-results" / "demo-run"
    comments_path = _copy_comments(work_dir)

    report = _run_full_demo(comments_path)

    if args.json:
        sys.stdout.write(json.dumps(report, indent=2, default=str))
        sys.stdout.write("\n")
        return 0

    print("=" * 72)
    print("Cognition × Guidehouse — JV COBOL modernization demo")
    print("=" * 72)
    print(f"Process date           : {report['process_date']}")
    print()
    print("LABA05 fiscal-year reset")
    print(f"  return code          : {report['laba05']['return_code']}")
    print(f"  JV-NUMBER before     : {report['laba05']['before_jv_number']}")
    print(f"  JV-NUMBER after      : {report['laba05']['after_jv_number']}")
    print(f"  message              : {report['laba05']['message']}")
    print()
    print("LABD20 comment loader")
    print(f"  records read         : {report['labd20']['total_read']}")
    print(f"  inserted             : {report['labd20']['inserted']}")
    print(f"  duplicates           : {report['labd20']['duplicates']}")
    print(f"  rejected             : {report['labd20']['rejected']}")
    print(f"  submitted total      : {report['labd20']['submitted_total']}")
    print()
    print("Rejection reasons (first 12):")
    for reason in report["labd20"]["rejected_reasons"][:12]:
        print(f"  - {reason}")
    print()
    print("Mock-DB final state (truncated for readability):")
    for table, rows in report["after_state"].items():
        print(f"  [{table}]: {len(rows)} row(s)")
    print()
    print(report["labd20"]["report"])
    return 0


# ---------------------------------------------------------------------------
# CLI: serve  (tiny HTML dashboard)
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Cognition — JV modernization demo</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Inter Tight', 'Inter', system-ui, -apple-system, sans-serif;
    margin: 0; padding: 0; background: #fafafa; color: #111;
  }}
  header {{
    background: #000; color: #fff; padding: 18px 28px;
    display: flex; align-items: center; justify-content: space-between;
  }}
  .wordmark {{ font-weight: 600; letter-spacing: 0.3px; font-size: 18px; }}
  .wordmark .mono {{ opacity: 0.8; }}
  .container {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
  h1 {{ font-size: 24px; margin: 0 0 4px; font-weight: 600; }}
  h2 {{ font-size: 16px; margin: 24px 0 8px; font-weight: 600; }}
  .subtitle {{ color: #555; margin-bottom: 24px; font-size: 14px; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .card {{
    background: #fff; border: 1px solid #e2e2e2; border-radius: 10px;
    padding: 16px 20px;
  }}
  .card .label {{ color: #666; font-size: 12px; text-transform: uppercase;
                  letter-spacing: 0.6px; }}
  .card .value {{ font-size: 28px; font-weight: 600; margin-top: 4px; }}
  .stat-row {{ display: flex; gap: 12px; flex-wrap: wrap; }}
  .stat-row .card {{ flex: 1; min-width: 180px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th, td {{ padding: 8px 10px; text-align: left;
            border-bottom: 1px solid #eee; }}
  th {{ background: #f4f4f4; font-weight: 600; }}
  pre {{
    background: #0d0d0d; color: #f4f4f4; padding: 16px;
    border-radius: 8px; overflow-x: auto; font-size: 12px; line-height: 1.45;
  }}
  .pill {{ display: inline-block; padding: 2px 10px; border-radius: 999px;
            font-size: 12px; }}
  .pill.ok {{ background: #d6f5dd; color: #14532d; }}
  .pill.warn {{ background: #fde7c5; color: #7a4a00; }}
  footer {{ color: #666; font-size: 12px; padding: 24px; text-align: center; }}
</style>
</head>
<body>
<header>
  <span class="wordmark">▰ Cognition <span class="mono">/ JV demo</span></span>
  <span style="font-size:12px; opacity:0.8;">
    <a href="/" style="color:#fff; opacity:0.9;">dashboard</a> ·
    <a href="/parity" style="color:#fff; opacity:0.9;">parity console</a> ·
    Demo output — pending SME review
  </span>
</header>
<div class="container">
  <h1>JV COBOL modernization — live demo</h1>
  <div class="subtitle">
    Mock Oracle (sqlite in-memory) · Synthetic data only · Process date
    <strong>{process_date}</strong>
  </div>

  <h2>LABA05 — fiscal-year JV-NUMBER reset</h2>
  <div class="stat-row">
    <div class="card"><div class="label">return code</div><div class="value">{laba05_rc} <span class="pill {laba05_pill}">{laba05_status}</span></div></div>
    <div class="card"><div class="label">JV-number before</div><div class="value">{laba05_before}</div></div>
    <div class="card"><div class="label">JV-number after</div><div class="value">{laba05_after}</div></div>
  </div>

  <h2>LABD20 — daily comment loader</h2>
  <div class="stat-row">
    <div class="card"><div class="label">read</div><div class="value">{read}</div></div>
    <div class="card"><div class="label">inserted</div><div class="value">{inserted}</div></div>
    <div class="card"><div class="label">duplicates</div><div class="value">{duplicates}</div></div>
    <div class="card"><div class="label">rejected</div><div class="value">{rejected}</div></div>
    <div class="card"><div class="label">submitted total</div><div class="value">{submitted}</div></div>
  </div>

  <h2>Rejection reasons (sampled)</h2>
  <div class="card">
    <ul style="margin:0; padding-left: 18px;">{rejection_items}</ul>
  </div>

  <h2>JC_SUBMITTED_COMMENT_TBL — final rows</h2>
  <div class="card" style="overflow-x:auto;">
    <table>
      <thead><tr>{submitted_headers}</tr></thead>
      <tbody>{submitted_rows}</tbody>
    </table>
  </div>

  <h2>Run log</h2>
  <pre>{log}</pre>
</div>
<footer>
  Cognition — federal modernization preview. All data synthetic; no real
  customer information used.
</footer>
</body>
</html>
"""


def _render_html(report: dict[str, Any]) -> str:
    submitted_rows = report["after_state"].get("JC_SUBMITTED_COMMENT_TBL", [])
    if submitted_rows:
        headers = list(submitted_rows[0].keys())
        submitted_headers = "".join(f"<th>{escape(h)}</th>" for h in headers)
        submitted_rows_html = "".join(
            "<tr>" + "".join(f"<td>{escape(str(r.get(h,'')))}</td>" for h in headers) + "</tr>"
            for r in submitted_rows
        )
    else:
        submitted_headers = "<th>(no rows)</th>"
        submitted_rows_html = ""

    rejection_items = "".join(
        f"<li>{escape(r)}</li>"
        for r in report["labd20"]["rejected_reasons"][:20]
    ) or "<li>(no rejections)</li>"

    laba05_rc = report["laba05"]["return_code"]
    return HTML_TEMPLATE.format(
        process_date=escape(report["process_date"]),
        laba05_rc=laba05_rc,
        laba05_pill="ok" if laba05_rc == 0 else "warn",
        laba05_status="success" if laba05_rc == 0 else "needs review",
        laba05_before=report["laba05"]["before_jv_number"],
        laba05_after=report["laba05"]["after_jv_number"],
        read=report["labd20"]["total_read"],
        inserted=report["labd20"]["inserted"],
        duplicates=report["labd20"]["duplicates"],
        rejected=report["labd20"]["rejected"],
        submitted=report["labd20"]["submitted_total"],
        rejection_items=rejection_items,
        submitted_headers=submitted_headers,
        submitted_rows=submitted_rows_html,
        log=escape(report["log"]),
    )


# ---------------------------------------------------------------------------
# Parity console rendering
# ---------------------------------------------------------------------------
PARITY_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Cognition — COBOL↔Python parity console</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: 'Inter Tight','Inter',system-ui,sans-serif;
    margin:0; padding:0; background:#fafafa; color:#111;
  }}
  header {{ background:#000; color:#fff; padding:18px 28px;
            display:flex; align-items:center; justify-content:space-between; }}
  .wordmark {{ font-weight:600; font-size:18px; letter-spacing:0.3px; }}
  header a {{ color:#fff; opacity:0.85; text-decoration:none; margin-left:8px; }}
  header a:hover {{ opacity:1; }}
  .container {{ max-width:1280px; margin:0 auto; padding:24px; }}
  h1 {{ font-size:24px; margin:0 0 4px; font-weight:600; }}
  .subtitle {{ color:#555; font-size:14px; margin-bottom:18px; }}
  .banner {{
    background:#fff7e6; border:1px solid #f0c674; color:#5a3e00;
    padding:14px 18px; border-radius:10px; margin:18px 0 22px;
    font-size:13px; line-height:1.55;
  }}
  .banner strong {{ color:#7a4a00; }}
  .stat-row {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:16px; }}
  .card {{ background:#fff; border:1px solid #e2e2e2; border-radius:10px;
           padding:14px 18px; flex:1; min-width:180px; }}
  .card .label {{ color:#666; font-size:11px; text-transform:uppercase;
                  letter-spacing:0.6px; }}
  .card .value {{ font-size:26px; font-weight:600; margin-top:2px; }}
  .pill {{ display:inline-block; padding:2px 10px; border-radius:999px;
           font-size:11px; font-weight:600; letter-spacing:0.2px; }}
  .pill.pass {{ background:#d6f5dd; color:#14532d; }}
  .pill.fail {{ background:#fadbd8; color:#7c1d12; }}
  .pill.unresolved {{ background:#fde7c5; color:#7a4a00; }}
  .pill.conf-high {{ background:#dbeafe; color:#1e3a8a; }}
  .pill.conf-medium {{ background:#fde7c5; color:#7a4a00; }}
  .pill.conf-low {{ background:#fadbd8; color:#7c1d12; }}
  details {{ background:#fff; border:1px solid #e2e2e2; border-radius:10px;
             padding:0; margin-bottom:10px; }}
  details[open] {{ box-shadow:0 4px 14px rgba(0,0,0,0.04); }}
  summary {{ cursor:pointer; padding:14px 18px; display:flex;
              align-items:center; gap:10px; font-size:14px;
              list-style:none; outline:none; }}
  summary::-webkit-details-marker {{ display:none; }}
  summary .br-id {{ font-family:'JetBrains Mono', ui-monospace,
                     SFMono-Regular, monospace; font-weight:600;
                     color:#111; min-width:140px; }}
  summary .label {{ flex:1; color:#222; }}
  summary .pills {{ display:flex; gap:6px; }}
  .body {{ padding:0 18px 16px; }}
  .meta {{ font-size:12px; color:#555; margin-bottom:8px; }}
  .grid3 {{ display:grid; grid-template-columns: 1fr 1fr; gap:14px;
            margin-top:8px; }}
  .col {{ background:#fafafa; border:1px solid #ececec; border-radius:8px;
          overflow:hidden; }}
  .col h3 {{ margin:0; font-size:12px; padding:8px 12px;
             background:#f4f4f4; color:#333; font-weight:600;
             text-transform:uppercase; letter-spacing:0.6px; }}
  pre.src {{ margin:0; padding:12px; font-size:11.5px;
              font-family:'JetBrains Mono', ui-monospace, monospace;
              background:#0d0d0d; color:#e8e8e8; overflow-x:auto;
              line-height:1.5; }}
  .diff {{ display:grid; grid-template-columns: 1fr 1fr; gap:10px;
            font-family:'JetBrains Mono', ui-monospace, monospace;
            font-size:12px; }}
  .diff > div {{ background:#fafafa; border:1px solid #ececec;
                 border-radius:6px; padding:10px; }}
  .diff h4 {{ margin:0 0 6px; font-size:11px; color:#666;
              text-transform:uppercase; letter-spacing:0.5px;
              font-family:'Inter Tight',sans-serif; }}
  .diff .kv {{ display:grid; grid-template-columns: max-content 1fr;
               gap:6px 14px; }}
  .diff .kv .key {{ color:#555; }}
  .diff .kv .val.equal {{ color:#14532d; }}
  .diff .kv .val.mismatch {{ color:#7c1d12; font-weight:600; }}
  .notes {{ background:#fff7e6; border-left:3px solid #f0c674;
             color:#5a3e00; padding:8px 12px; margin-top:10px;
             font-size:12px; border-radius:0 6px 6px 0; }}
  footer {{ color:#666; font-size:12px; padding:24px; text-align:center; }}
</style>
</head>
<body>
<header>
  <span class="wordmark">▰ Cognition <span style="opacity:0.8;">/ parity console</span></span>
  <span style="font-size:12px;">
    <a href="/">dashboard</a> · <a href="/parity">parity console</a>
  </span>
</header>
<div class="container">
  <h1>COBOL↔Python parity per business requirement</h1>
  <div class="subtitle">
    {n_total} checks · derived golden output vs. live Python execution against
    the in-memory mock Oracle. Click any row for source + diff.
  </div>

  <div class="banner">
    <strong>How to read this.</strong>
    The <em>expected</em> column is a <strong>golden output derived line-by-line
    from the COBOL/Pro*COBOL source</strong> — it is not produced by running
    the legacy program. There is no Pro*COBOL precompiler or Oracle on this
    box, so re-executing the COBOL itself is out of scope here.
    The <em>actual</em> column is produced live by the modernized Python
    against an in-memory mock Oracle. In a real engagement, flip one config
    switch and the expected column becomes a live mainframe execution against
    the same synthetic input, producing the byte-for-byte diff that SBA
    question 2 / 14 describes.
  </div>

  <div class="stat-row">
    <div class="card"><div class="label">PASS</div><div class="value" style="color:#14532d;">{n_pass}</div></div>
    <div class="card"><div class="label">FAIL</div><div class="value" style="color:#7c1d12;">{n_fail}</div></div>
    <div class="card"><div class="label">UNRESOLVED</div><div class="value" style="color:#7a4a00;">{n_unresolved}</div></div>
    <div class="card"><div class="label">confidence</div><div class="value" style="font-size:16px;">
      <span class="pill conf-high">HIGH {n_high}</span>
      <span class="pill conf-medium">MED {n_med}</span>
      <span class="pill conf-low">LOW {n_low}</span>
    </div></div>
  </div>

  {rows_html}
</div>
<footer>
  Cognition — federal modernization preview. Synthetic data only.
</footer>
</body>
</html>
"""


def _diff_kv(expected: dict[str, Any], actual: dict[str, Any]) -> str:
    """Render side-by-side expected vs. actual key/value lists."""
    keys = list(dict.fromkeys(list(expected.keys()) + list(actual.keys())))
    exp_rows = []
    act_rows = []
    for k in keys:
        e = expected.get(k, "(missing)")
        a = actual.get(k, "(missing)")
        cls = "equal" if e == a else "mismatch"
        exp_rows.append(
            f'<div class="key">{escape(str(k))}</div>'
            f'<div class="val {cls}">{escape(repr(e))}</div>'
        )
        act_rows.append(
            f'<div class="key">{escape(str(k))}</div>'
            f'<div class="val {cls}">{escape(repr(a))}</div>'
        )
    return (
        '<div class="diff">'
        '<div><h4>expected — derived from COBOL source</h4>'
        f'<div class="kv">{"".join(exp_rows)}</div></div>'
        '<div><h4>actual — live Python output</h4>'
        f'<div class="kv">{"".join(act_rows)}</div></div>'
        '</div>'
    )


def _render_parity_row(r: ParityRow) -> str:
    status_cls = r.status.lower()
    conf_cls = f"conf-{r.confidence.lower()}"
    cobol_src = read_source_span(r.cobol_path, r.cobol_lines[0], r.cobol_lines[1])
    py_src = read_source_span(r.python_path, r.python_lines[0], r.python_lines[1])
    notes_block = (
        f'<div class="notes"><strong>Note.</strong> {escape(r.notes)}</div>'
        if r.notes
        else ""
    )
    return f"""
<details>
  <summary>
    <span class="br-id">{escape(r.br_id)}</span>
    <span class="label">{escape(r.label)}</span>
    <span class="pills">
      <span class="pill {status_cls}">{escape(r.status)}</span>
      <span class="pill {conf_cls}">{escape(r.confidence)}</span>
    </span>
  </summary>
  <div class="body">
    <div class="meta">
      <strong>Asked by:</strong> {escape(r.owner)} ·
      <strong>Classification:</strong> {escape(r.classification)} ·
      <strong>Input:</strong> {escape(r.input_desc)}
    </div>
    <div class="grid3">
      <div class="col">
        <h3>COBOL source — {escape(r.cobol_path)}:{r.cobol_lines[0]}–{r.cobol_lines[1]}</h3>
        <pre class="src">{escape(cobol_src)}</pre>
      </div>
      <div class="col">
        <h3>Python conversion — {escape(r.python_path)}:{r.python_lines[0]}–{r.python_lines[1]}</h3>
        <pre class="src">{escape(py_src)}</pre>
      </div>
    </div>
    <div style="margin-top:12px;">{_diff_kv(r.expected, r.actual)}</div>
    {notes_block}
  </div>
</details>
"""


def _render_parity_html(rows: list[ParityRow]) -> str:
    summary = parity_summary(rows)
    n_high = sum(1 for r in rows if r.confidence == "HIGH")
    n_med = sum(1 for r in rows if r.confidence == "MEDIUM")
    n_low = sum(1 for r in rows if r.confidence == "LOW")
    rows_html = "".join(_render_parity_row(r) for r in rows)
    return PARITY_PAGE.format(
        n_total=len(rows),
        n_pass=summary.get("PASS", 0),
        n_fail=summary.get("FAIL", 0),
        n_unresolved=summary.get("UNRESOLVED", 0),
        n_high=n_high,
        n_med=n_med,
        n_low=n_low,
        rows_html=rows_html,
    )


def cmd_parity(args: argparse.Namespace) -> int:
    """CLI: run the parity sweep and print a tabular summary."""
    rows = run_parity()
    summary = parity_summary(rows)
    width = max(len(r.br_id) for r in rows)
    print(
        f"Parity sweep: PASS={summary.get('PASS',0)} "
        f"FAIL={summary.get('FAIL',0)} "
        f"UNRESOLVED={summary.get('UNRESOLVED',0)} "
        f"(of {len(rows)} business requirements)"
    )
    print("-" * 72)
    for r in rows:
        print(f"  {r.status:5}  {r.br_id:<{width}}  {r.label}")
        if r.status != "PASS":
            print(f"          expected = {r.expected}")
            print(f"          actual   = {r.actual}")
    if args.out:
        out = Path(args.out)
        out.write_text(_render_parity_html(rows), encoding="utf-8")
        print(f"Wrote parity console HTML to {out}")
    return 0 if summary.get("FAIL", 0) == 0 else 1


def cmd_serve(args: argparse.Namespace) -> int:
    import http.server
    import socketserver

    work_dir = Path(args.work_dir) if args.work_dir else REPO_ROOT / "migration" / "test-results" / "demo-serve"
    comments_path = _copy_comments(work_dir)
    report = _run_full_demo(comments_path)
    html = _render_html(report)

    parity_rows = run_parity()
    parity_html = _render_parity_html(parity_rows)

    out_path = work_dir / "index.html"
    out_path.write_text(html, encoding="utf-8")
    parity_path = work_dir / "parity.html"
    parity_path.write_text(parity_html, encoding="utf-8")
    print(f"Wrote dashboard to {out_path}")
    print(f"Wrote parity console to {parity_path}")

    if args.no_serve:
        return 0

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            if self.path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            elif self.path in ("/parity", "/parity.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(parity_html.encode("utf-8"))
            elif self.path == "/report.json":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(report, indent=2, default=str).encode())
            elif self.path == "/parity.json":
                payload = [
                    {
                        "br_id": r.br_id, "label": r.label, "owner": r.owner,
                        "status": r.status, "confidence": r.confidence,
                        "classification": r.classification,
                        "cobol": f"{r.cobol_path}:{r.cobol_lines[0]}-{r.cobol_lines[1]}",
                        "python": f"{r.python_path}:{r.python_lines[0]}-{r.python_lines[1]}",
                        "expected": r.expected, "actual": r.actual,
                        "notes": r.notes,
                    }
                    for r in parity_rows
                ]
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(payload, indent=2, default=str).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *fmt_args):  # noqa: A002, N802
            pass

    address = ("127.0.0.1", args.port)
    print(f"Serving demo dashboard at http://127.0.0.1:{args.port}/ — Ctrl-C to stop.")
    print(f"Parity console:           http://127.0.0.1:{args.port}/parity")
    with socketserver.TCPServer(address, Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down.")
    return 0


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="demo_app", description="Cognition × Guidehouse JV modernization demo")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run LABA05 + LABD20 against the in-memory mock DB.")
    p_run.add_argument("--work-dir", help="Where to copy synthetic input (truncate-safe).")
    p_run.add_argument("--json", action="store_true", help="Emit machine-readable JSON only.")
    p_run.set_defaults(func=cmd_run)

    p_serve = sub.add_parser("serve", help="Run + open a tiny HTML dashboard.")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--no-serve", action="store_true", help="Generate the HTML and exit.")
    p_serve.add_argument("--work-dir", help="Where to copy synthetic input (truncate-safe).")
    p_serve.set_defaults(func=cmd_serve)

    p_parity = sub.add_parser("parity", help="Run the 28-BR COBOL↔Python parity sweep.")
    p_parity.add_argument("--out", help="Optional path to write the parity console HTML.")
    p_parity.set_defaults(func=cmd_parity)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))
