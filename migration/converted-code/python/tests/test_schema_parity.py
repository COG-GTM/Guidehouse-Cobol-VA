"""
test_schema_parity.py — Schema-parity validation for the modernized loader.

STATUS: Demo output pending SME review. Generated as part of the Guidehouse JV
COBOL/Pro*COBOL modernization walkthrough.

PURPOSE
-------
Catch drift between what the converted Python code writes (DDL + INSERT shape)
and what the customer-supplied Oracle table descriptions
(`database/descriptions/describe *.txt`) say production should look like. The
goal of this module is to give reviewers a single, automated checkpoint that:

1. Parses the five Oracle describe files into structured tables.
2. Compares them column-by-column against `DEMO_SCHEMA_DDL` in
   `migration/converted-code/python/db_dispatcher.py`, classifying every column
   as matched, intentionally-omitted, known-issue, or unexpected-drift.
3. Exercises the real loader (`labd20_loader.LABD20Loader`) against an
   in-memory sqlite3 database to verify the INSERT parameter shape and per-
   column width constraints (`CHAR(n)`).
4. Verifies the 400-byte `CONTROL_RECORD_DATA` blob layout seeded by
   `seed_control_record()` matches `migration/analysis/field-lineage.md` lines
   89-102 (specifically: the 6-digit `JV-NUMBER` at bytes 25-30 / slice
   `[24:30]`).
5. Verifies the 300-byte byte-offset slices in `labd20_loader.py` lines 91-105
   add up to the Oracle CHAR widths in the describe files. The known
   `APPROVER` 14-vs-20 mismatch (`U-5`) is intentionally tolerated with an
   annotation — it does not fail the test.
6. Writes a structured JSON parity report to
   `migration/test-results/schema-parity-report.json` for downstream review.

KNOWN ISSUES (intentionally surfaced as annotations, not failures — sourced
from `migration/ASSUMPTIONS-AND-PLACEHOLDERS.md`):
- `APPROVER` width 14 (FD) vs 20 (Oracle CHAR(20)) — `U-5`.
- `JC_COUNT_TBL` describe-file PK typo: file says `JC_SUBMITTED`, but that
  column does not exist on the table — `A-6` / `U-6`.
- `JC_COUNT_TBL` column-name drift: COBOL uses `JC_SECTION_COUNT`, demo DDL
  uses `JC_COUNT_NUM`.
- `CREATE_TIMESTAMP` / `LAST_UPDATE_TIMESTAMP` are intentionally omitted from
  the demo DDL on every table; they are surfaced as
  `intentionally-omitted` rows in the report, not failures.

RUNNING
-------
    python3 -m pytest migration/converted-code/python/tests/test_schema_parity.py -v

Zero external dependencies (stdlib only; sqlite3 in-memory).
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Path / import setup — matches the convention used by
# test_labd20_loader.py and test_laba05_reset.py.
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "migration" / "converted-code"))

from python import db_dispatcher  # noqa: E402
from python.db_dispatcher import (  # noqa: E402
    DBDispatcher,
    DEMO_SCHEMA_DDL,
    build_demo_schema,
    seed_control_record,
)
from python.labd20_loader import (  # noqa: E402
    APPROVER_SLICE,
    COMMENT_DT_SLICE,
    COMMENT_HIST_SLICE,
    JV_NUMBER_SLICE,
    LABD20Loader,
    LOAN_DT_NR_SLICE,
    LOAN_NUMBER_SLICE,
    LoaderConfig,
    REQUESTOR_SLICE,
    SCHEDULE_DOC_NO_SLICE,
    SECTION_ID_SLICE,
    TST123_RECORD_LENGTH,
)


DESCRIBE_DIR = REPO_ROOT / "database" / "descriptions"
REPORT_PATH = REPO_ROOT / "migration" / "test-results" / "schema-parity-report.json"

# Describe-file → expected sqlite-side demo table.
DESCRIBE_FILES: dict[str, str] = {
    "JC_SUBMITTED_COMMENT_TBL": "describe JC_SUBMITTED_COMMENT_TBL.txt",
    "JC_COUNT_TBL": "describe JC_COUNT_TBL.txt",
    "JC_REJECTED_COMMENT_TBL": "describe JC_REJECTED_COMMENT_TBL.txt",
    "JC_APPLIED_COMMENT_TBL": "describe JC_APPLIED_COMMENT_TBL.txt",
    "CONTROL_RECORD_TABLE": "describe CONTROL_RECORD_TABLE.txt",
}

# Columns the demo intentionally skips on every table (sqlite has no Oracle
# `TIMESTAMP(6) WITH TIME ZONE` and the demo runtime never reads them).
INTENTIONALLY_OMITTED: frozenset[str] = frozenset(
    {"CREATE_TIMESTAMP", "LAST_UPDATE_TIMESTAMP"}
)

# Tables that exist in the demo only as stubs. LABD20 never INSERTs into
# JC_REJECTED_COMMENT_TBL or JC_APPLIED_COMMENT_TBL — they are referenced
# only by the post-run stats SELECTs (`count_rows`). The demo therefore only
# materializes the PK column on each, and oracle-side columns beyond that PK
# are tagged as intentionally-omitted with the reason below.
INTENTIONALLY_UNUSED_TABLES: dict[str, str] = {
    "JC_REJECTED_COMMENT_TBL": (
        "demo placeholder: LABD20 never INSERTs into this table; only "
        "`count_rows` reads it via SELECT COUNT(*) (LABD20.pco:432-435). The "
        "Oracle column is documented but unused on the demo path."
    ),
    "JC_APPLIED_COMMENT_TBL": (
        "demo placeholder: LABD20 never INSERTs into this table; only "
        "`count_rows` reads it via SELECT COUNT(*) (LABD20.pco:441-444). The "
        "Oracle column is documented but unused on the demo path."
    ),
}

# Known schema-drift issues per migration/ASSUMPTIONS-AND-PLACEHOLDERS.md.
# Surfaced as annotated rows in the report; never fail the test.
KNOWN_ISSUES: dict[tuple[str, str], str] = {
    # (table, column-or-token) -> human-readable annotation
    ("JC_COUNT_TBL", "JC_SECTION_COUNT"): (
        "A-6 / column-name drift: COBOL LABD20.pco:399 uses JC_SECTION_COUNT, "
        "demo DDL uses JC_COUNT_NUM"
    ),
    ("JC_COUNT_TBL", "__PK_TYPO__"): (
        "A-6 / U-6: describe file claims PK=JC_SUBMITTED, but that column "
        "does not exist on this table; PK is treated as JC_SECTION"
    ),
    ("JC_SUBMITTED_COMMENT_TBL", "JC_SUBMITTED_COMMENT_APPROVER"): (
        "U-5: APPROVER input slice is 14 bytes (LABD20.pco line 55) but "
        "Oracle column is CHAR(20); the modernized loader stores the 14-byte "
        "slice as-is. Oracle CHAR(20) would right-pad on the database side."
    ),
}


# ---------------------------------------------------------------------------
# Describe-file parser
# ---------------------------------------------------------------------------
_NOT_NULL = "NOT NULL"
_CHAR_RE = re.compile(r"CHAR\((\d+)\)", re.IGNORECASE)
_PK_RE = re.compile(r"primary key uses\s+(?P<cols>.+)", re.IGNORECASE)


@dataclass
class OracleColumn:
    """One row from a `describe <table>` text file."""

    name: str
    nullable: bool
    raw_type: str
    oracle_type: str  # "CHAR" | "NUMBER" | "DATE" | "TIMESTAMP"
    width: int | None  # set only for CHAR(n)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OracleTable:
    """Structured view of one describe file."""

    name: str
    columns: list[OracleColumn]
    pk: list[str]
    pk_raw: str
    source_path: Path

    @property
    def column_names(self) -> list[str]:
        return [c.name for c in self.columns]

    def column(self, name: str) -> OracleColumn | None:
        for c in self.columns:
            if c.name == name:
                return c
        return None


def _classify_type(raw_type: str) -> tuple[str, int | None]:
    """Map an Oracle type string to (canonical_kind, width-or-None)."""
    raw = raw_type.strip()
    m = _CHAR_RE.search(raw)
    if m:
        return "CHAR", int(m.group(1))
    upper = raw.upper()
    if upper.startswith("NUMBER"):
        return "NUMBER", None
    if upper.startswith("TIMESTAMP"):
        return "TIMESTAMP", None
    if upper == "DATE":
        return "DATE", None
    return "UNKNOWN", None


def _column_spans_from_dashes(dash_line: str) -> list[tuple[int, int]]:
    """Find positions of contiguous-dash runs; each run = one column."""
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(dash_line)
    while i < n:
        if dash_line[i] == "-":
            j = i
            while j < n and dash_line[j] == "-":
                j += 1
            spans.append((i, j))
            i = j
        else:
            i += 1
    return spans


def _parse_data_row(
    line: str, spans: list[tuple[int, int]]
) -> tuple[str, bool, str] | None:
    """Parse one data row of a describe file using the dash-line column
    boundaries.

    The describe layout is fixed-width with column positions defined by the
    dashes line. Some data rows (e.g. CONTROL_RECORD_NUMBER NOT NULL NUMBER)
    have only single-space padding between the Name and Null? columns, which
    means a naive re.split-on-2+-spaces parse fails. Slicing by the dash
    positions handles every row uniformly.
    """
    if not line.strip():
        return None
    if len(spans) < 3:
        return None
    name_start = spans[0][0]
    null_start = spans[1][0]
    type_start = spans[2][0]
    # Cap the Type slice at the next column's start (Sample Data), if any.
    type_end = spans[3][0] if len(spans) >= 4 else len(line)
    # Pad the line so all slice indices are in range.
    padded = line.ljust(type_end + 1)
    name = padded[name_start:null_start].strip()
    null_flag = padded[null_start:type_start].strip()
    raw_type = padded[type_start:type_end].strip()
    if not name or not raw_type:
        return None
    nullable = null_flag.upper() != _NOT_NULL
    return name, nullable, raw_type


def parse_describe_file(path: Path) -> OracleTable:
    """Parse one `database/descriptions/describe *.txt` file.

    The format is:
        describe <TABLE>;
        <blank>
        Name<spaces>Null?<spaces>Type[<spaces>Sample Data]
        ---<spaces>---<spaces>---[<spaces>---]
        <data rows...>
        <blank>
        primary key uses <col>[, <col>...]
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Table name from the `describe <TABLE>;` header. Falls back to filename.
    table_name = path.stem.replace("describe ", "").strip()
    for line in lines:
        if line.strip().lower().startswith("describe "):
            token = line.strip().split(None, 1)[1]
            table_name = token.rstrip(";").strip()
            break

    # Locate the header / dashes / data rows.
    header_idx = next(
        (
            i
            for i, line in enumerate(lines)
            if "Name" in line and "Null?" in line and "Type" in line
        ),
        None,
    )
    if header_idx is None:
        raise ValueError(f"{path}: missing Name/Null?/Type header line")

    dash_idx = header_idx + 1
    if dash_idx >= len(lines) or "---" not in lines[dash_idx]:
        raise ValueError(f"{path}: missing dash line after header")
    spans = _column_spans_from_dashes(lines[dash_idx])
    if len(spans) < 3:
        raise ValueError(
            f"{path}: expected at least 3 dash-column spans, got {len(spans)}"
        )

    columns: list[OracleColumn] = []
    i = dash_idx + 1
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            break
        if stripped.lower().startswith("primary key"):
            break
        if stripped.lower().startswith("sample data"):
            break
        parsed = _parse_data_row(line, spans)
        if parsed is None:
            i += 1
            continue
        name, nullable, raw_type = parsed
        kind, width = _classify_type(raw_type)
        columns.append(
            OracleColumn(
                name=name,
                nullable=nullable,
                raw_type=raw_type,
                oracle_type=kind,
                width=width,
            )
        )
        i += 1

    # Primary key line. CONTROL_RECORD_TABLE has a multi-column PK; the
    # JC_COUNT_TBL file has a typo (PK column = JC_SUBMITTED, which is not on
    # the table).
    pk: list[str] = []
    pk_raw = ""
    for line in lines[i:]:
        m = _PK_RE.search(line)
        if m:
            pk_raw = m.group("cols").strip().rstrip(";").rstrip(".")
            pk = [c.strip() for c in pk_raw.split(",") if c.strip()]
            break

    return OracleTable(
        name=table_name,
        columns=columns,
        pk=pk,
        pk_raw=pk_raw,
        source_path=path,
    )


def load_oracle_tables() -> dict[str, OracleTable]:
    """Parse every describe file the demo cares about."""
    result: dict[str, OracleTable] = {}
    for canonical, filename in DESCRIBE_FILES.items():
        path = DESCRIBE_DIR / filename
        assert path.exists(), f"Missing describe file: {path}"
        table = parse_describe_file(path)
        # Sanity: filename and parsed table name must agree.
        assert table.name == canonical, (
            f"{filename}: parsed table name {table.name!r} != {canonical!r}"
        )
        result[canonical] = table
    return result


# ---------------------------------------------------------------------------
# Sqlite-side inspection helpers
# ---------------------------------------------------------------------------
def _table_info(conn: sqlite3.Connection, table: str) -> list[dict]:
    """Return PRAGMA table_info(<table>) as a list of dicts."""
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    rows = cur.fetchall()
    return [
        {
            "cid": r[0],
            "name": r[1],
            "type": r[2],
            "notnull": bool(r[3]),
            "dflt_value": r[4],
            "pk": int(r[5]),  # 0 = not part of PK, 1+ = PK column ordinal
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Synthetic 300-byte record used by the INSERT-shape test
# ---------------------------------------------------------------------------
def _make_synthetic_record(
    *,
    date: str = "20260115",
    jv: str = "000100",
    section: str = "01",
    loan: str = "9000000001",
    sched: str = "SCH0000001",
    text: str = "schema-parity synthetic comment",
    requestor: str = "ALICE.SUBMITTER",
    approver: str = "BOB.APPROVER",
) -> str:
    """Build a TST123-COMMENT-REC that should pass every validation rule."""
    record = (
        f"{date:8}{jv:6}{section:2}{loan:10}"
        f"{sched:<10}{text:<230}"
        f"{requestor:<20}{approver:<14}"
    )
    assert len(record) == TST123_RECORD_LENGTH, (
        f"synthetic record length {len(record)} != {TST123_RECORD_LENGTH}"
    )
    return record


# ---------------------------------------------------------------------------
# Parity report — accumulated by the tests below and written once at session
# teardown via the `parity_report` fixture.
# ---------------------------------------------------------------------------
@dataclass
class ColumnFinding:
    """One row in the per-table parity table of the JSON report."""

    table: str
    column: str
    status: str  # matched | intentionally-omitted | known-issue | drift
    detail: str = ""
    oracle_type: str | None = None
    oracle_width: int | None = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class TableFindings:
    table: str
    oracle_columns: int = 0
    demo_columns: int = 0
    matched: int = 0
    intentionally_omitted: int = 0
    known_issues: int = 0
    drift: int = 0
    findings: list[ColumnFinding] = field(default_factory=list)

    def add(self, finding: ColumnFinding) -> None:
        self.findings.append(finding)
        if finding.status == "matched":
            self.matched += 1
        elif finding.status == "intentionally-omitted":
            self.intentionally_omitted += 1
        elif finding.status == "known-issue":
            self.known_issues += 1
        elif finding.status == "drift":
            self.drift += 1

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "oracle_columns": self.oracle_columns,
            "demo_columns": self.demo_columns,
            "matched": self.matched,
            "intentionally_omitted": self.intentionally_omitted,
            "known_issues": self.known_issues,
            "drift": self.drift,
            "findings": [f.to_dict() for f in self.findings],
        }


@dataclass
class ParityReport:
    """In-memory accumulator; written to disk in `parity_report` teardown."""

    tables: dict[str, TableFindings] = field(default_factory=dict)
    known_issue_notes: list[dict] = field(default_factory=list)
    insert_shape: dict = field(default_factory=dict)
    control_record_layout: dict = field(default_factory=dict)
    byte_width_parity: dict = field(default_factory=dict)

    def table(self, name: str) -> TableFindings:
        return self.tables.setdefault(name, TableFindings(table=name))

    def to_dict(self) -> dict:
        totals = {
            "oracle_columns": sum(t.oracle_columns for t in self.tables.values()),
            "demo_columns": sum(t.demo_columns for t in self.tables.values()),
            "matched": sum(t.matched for t in self.tables.values()),
            "intentionally_omitted": sum(
                t.intentionally_omitted for t in self.tables.values()
            ),
            "known_issues": sum(t.known_issues for t in self.tables.values()),
            "drift": sum(t.drift for t in self.tables.values()),
        }
        return {
            "totals": totals,
            "tables": {k: v.to_dict() for k, v in sorted(self.tables.items())},
            "known_issue_notes": self.known_issue_notes,
            "insert_shape": self.insert_shape,
            "control_record_layout": self.control_record_layout,
            "byte_width_parity": self.byte_width_parity,
        }


# ---------------------------------------------------------------------------
# pytest fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def oracle_tables() -> dict[str, OracleTable]:
    return load_oracle_tables()


@pytest.fixture(scope="session")
def parity_report() -> ParityReport:
    """Session-scoped accumulator. The teardown writes the JSON report once
    after every test has contributed."""
    report = ParityReport()
    yield report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(report.to_dict(), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


@pytest.fixture
def fresh_db() -> DBDispatcher:
    """In-memory sqlite + demo schema + seeded JV-CONTROL-REC row."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    dispatcher = DBDispatcher(conn)
    build_demo_schema(dispatcher)
    dispatcher.insert(
        "INSERT INTO JC_COUNT_TBL (JC_SECTION, JC_COUNT_NUM) VALUES (?, ?)",
        ("MA", 0),
    )
    dispatcher.commit()
    seed_control_record(dispatcher)
    return dispatcher


# ---------------------------------------------------------------------------
# (a) Describe-file parser tests
# ---------------------------------------------------------------------------
class TestDescribeParser:
    def test_all_five_files_parse(self, oracle_tables: dict[str, OracleTable]):
        assert set(oracle_tables) == set(DESCRIBE_FILES)

    def test_jc_submitted_comment_tbl_columns_and_types(
        self, oracle_tables: dict[str, OracleTable]
    ):
        tbl = oracle_tables["JC_SUBMITTED_COMMENT_TBL"]
        assert tbl.column_names == [
            "JC_SUBMITTED",
            "JC_SUBMITTED_NUMBER",
            "JC_SUBMITTED_SCHED_DOC_NO",
            "JC_SUBMITTED_COMMENT_HIST",
            "JC_SUBMITTED_COMMENT_REQUESTOR",
            "JC_SUBMITTED_COMMENT_APPROVER",
            "JC_SUBMITTED_CONTROL_NUM",
            "JC_SUBMITTED_UPDT_PROG_ID",
            "JC_SUBMITTED_UPDT_PROG_DT",
            "CREATE_TIMESTAMP",
            "LAST_UPDATE_TIMESTAMP",
        ]
        assert tbl.column("JC_SUBMITTED").width == 26
        assert tbl.column("JC_SUBMITTED").nullable is False
        assert tbl.column("JC_SUBMITTED_SCHED_DOC_NO").width == 10
        assert tbl.column("JC_SUBMITTED_COMMENT_HIST").width == 240
        assert tbl.column("JC_SUBMITTED_COMMENT_APPROVER").width == 20
        assert tbl.column("JC_SUBMITTED_NUMBER").oracle_type == "NUMBER"
        assert tbl.column("JC_SUBMITTED_UPDT_PROG_DT").oracle_type == "DATE"
        assert tbl.column("CREATE_TIMESTAMP").oracle_type == "TIMESTAMP"
        assert tbl.pk == ["JC_SUBMITTED"]

    def test_jc_count_tbl_pk_typo_is_visible(
        self, oracle_tables: dict[str, OracleTable]
    ):
        # The describe file says the PK is JC_SUBMITTED but that column does
        # not appear on JC_COUNT_TBL. We surface this so it's traceable from
        # the parity report — see A-6 / U-6.
        tbl = oracle_tables["JC_COUNT_TBL"]
        assert "JC_SUBMITTED" not in tbl.column_names
        assert tbl.pk == ["JC_SUBMITTED"], (
            "JC_COUNT_TBL describe file PK should be reported verbatim "
            "(it is a known typo)"
        )

    def test_control_record_table_composite_pk(
        self, oracle_tables: dict[str, OracleTable]
    ):
        tbl = oracle_tables["CONTROL_RECORD_TABLE"]
        assert tbl.pk == ["CONTROL_RECORD_NAME", "CONTROL_RECORD_NUMBER"]
        assert tbl.column("CONTROL_RECORD_DATA").width == 400
        assert tbl.column("CONTROL_RECORD_NAME").width == 30


# ---------------------------------------------------------------------------
# (b) DDL column-set parity
# ---------------------------------------------------------------------------
class TestDemoDDLMatchesOracleColumns:
    """For each table, every Oracle column either (a) appears in the demo
    DDL, (b) is in INTENTIONALLY_OMITTED, or (c) is a known-issue. No new
    invented columns are silently introduced on the demo side.

    Findings are recorded into the session parity report.
    """

    def _collect_demo_columns(self) -> dict[str, list[dict]]:
        """Build sqlite by running DEMO_SCHEMA_DDL, then PRAGMA each table."""
        conn = sqlite3.connect(":memory:")
        dispatcher = DBDispatcher(conn)
        build_demo_schema(dispatcher)
        result: dict[str, list[dict]] = {}
        for table_name in DESCRIBE_FILES:
            result[table_name] = _table_info(conn, table_name)
        conn.close()
        return result

    def test_oracle_to_demo_column_parity(
        self,
        oracle_tables: dict[str, OracleTable],
        parity_report: ParityReport,
    ):
        demo_tables = self._collect_demo_columns()
        unexpected_missing: list[tuple[str, str]] = []

        for table_name, oracle in oracle_tables.items():
            demo_cols = demo_tables[table_name]
            demo_col_names = {c["name"] for c in demo_cols}
            tf = parity_report.table(table_name)
            tf.oracle_columns = len(oracle.columns)
            tf.demo_columns = len(demo_cols)

            stub_reason = INTENTIONALLY_UNUSED_TABLES.get(table_name)
            for oc in oracle.columns:
                if oc.name in demo_col_names:
                    tf.add(
                        ColumnFinding(
                            table=table_name,
                            column=oc.name,
                            status="matched",
                            detail="column present in demo DDL",
                            oracle_type=oc.oracle_type,
                            oracle_width=oc.width,
                        )
                    )
                elif oc.name in INTENTIONALLY_OMITTED:
                    tf.add(
                        ColumnFinding(
                            table=table_name,
                            column=oc.name,
                            status="intentionally-omitted",
                            detail=(
                                "demo DDL skips Oracle timestamp columns; "
                                "sqlite has no equivalent and the demo "
                                "runtime never reads them"
                            ),
                            oracle_type=oc.oracle_type,
                            oracle_width=oc.width,
                        )
                    )
                elif (table_name, oc.name) in KNOWN_ISSUES:
                    tf.add(
                        ColumnFinding(
                            table=table_name,
                            column=oc.name,
                            status="known-issue",
                            detail=KNOWN_ISSUES[(table_name, oc.name)],
                            oracle_type=oc.oracle_type,
                            oracle_width=oc.width,
                        )
                    )
                elif stub_reason is not None:
                    tf.add(
                        ColumnFinding(
                            table=table_name,
                            column=oc.name,
                            status="intentionally-omitted",
                            detail=stub_reason,
                            oracle_type=oc.oracle_type,
                            oracle_width=oc.width,
                        )
                    )
                else:
                    tf.add(
                        ColumnFinding(
                            table=table_name,
                            column=oc.name,
                            status="drift",
                            detail="Oracle column missing from demo DDL",
                            oracle_type=oc.oracle_type,
                            oracle_width=oc.width,
                        )
                    )
                    unexpected_missing.append((table_name, oc.name))

            # Reverse direction: any column on the demo side that has no
            # corresponding Oracle column? (catches invented columns)
            oracle_col_names = {c.name for c in oracle.columns}
            for demo_col in demo_cols:
                if demo_col["name"] in oracle_col_names:
                    continue
                if (table_name, demo_col["name"]) in KNOWN_ISSUES:
                    detail = KNOWN_ISSUES[(table_name, demo_col["name"])]
                    status = "known-issue"
                elif demo_col["name"] == "JC_COUNT_NUM" and table_name == "JC_COUNT_TBL":
                    # Column-name drift documented in A-6 (`JC_SECTION_COUNT`
                    # is the COBOL name; the describe file already lists
                    # JC_SECTION_COUNT, demo DDL uses JC_COUNT_NUM).
                    status = "known-issue"
                    detail = (
                        "A-6 column-name drift: demo DDL uses JC_COUNT_NUM "
                        "while Oracle and COBOL both call this JC_SECTION_COUNT"
                    )
                elif demo_col["name"] == "JC_REJECTED_REASON" and table_name == "JC_REJECTED_COMMENT_TBL":
                    # The demo's rejected table is intentionally a
                    # placeholder; the production Oracle table is fully
                    # described in the describe file but not exercised by
                    # LABD20 (rejected rows are reported via stats SELECTs,
                    # not INSERTed by the loader).
                    status = "known-issue"
                    detail = (
                        "demo placeholder: JC_REJECTED_REASON is a demo-only "
                        "column; LABD20 never INSERTs into "
                        "JC_REJECTED_COMMENT_TBL — see RISKS-AND-GAPS Risk 4"
                    )
                else:
                    status = "drift"
                    detail = "demo DDL column has no Oracle counterpart"
                tf.add(
                    ColumnFinding(
                        table=table_name,
                        column=demo_col["name"],
                        status=status,
                        detail=detail,
                        oracle_type=None,
                        oracle_width=None,
                    )
                )
                if status == "drift":
                    unexpected_missing.append((table_name, demo_col["name"]))

        # Record the known-issue summary into the report (idempotent).
        parity_report.known_issue_notes = [
            {"key": list(k), "note": v} for k, v in KNOWN_ISSUES.items()
        ]

        assert not unexpected_missing, (
            "Unexpected column drift (not on the known-issue list):\n  "
            + "\n  ".join(f"{t}.{c}" for t, c in unexpected_missing)
        )

    def test_demo_ddl_does_not_invent_jc_submitted_pk_on_jc_count(
        self,
        oracle_tables: dict[str, OracleTable],
    ):
        """A-6 / U-6: the describe file's PK typo must NOT be propagated into
        the demo DDL. The demo's JC_COUNT_TBL must use JC_SECTION as the PK,
        not the bogus JC_SUBMITTED."""
        conn = sqlite3.connect(":memory:")
        dispatcher = DBDispatcher(conn)
        build_demo_schema(dispatcher)
        info = _table_info(conn, "JC_COUNT_TBL")
        conn.close()
        pk_cols = [c["name"] for c in info if c["pk"] >= 1]
        assert pk_cols == ["JC_SECTION"], (
            f"JC_COUNT_TBL demo PK should be JC_SECTION (working around the "
            f"describe-file typo); got {pk_cols!r}"
        )


# ---------------------------------------------------------------------------
# (c) INSERT-parameter-shape validation
# ---------------------------------------------------------------------------
class TestInsertParameterShape:
    """Execute the real loader, then verify the row layout via PRAGMA and the
    actual stored values."""

    def _run_loader_with_one_record(
        self,
        tmp_path: Path,
        fresh_db: DBDispatcher,
    ) -> dict:
        record = _make_synthetic_record()
        comments = tmp_path / "single.dat"
        comments.write_text(record + "\n", encoding="utf-8")
        card = tmp_path / "card.ctl"
        card.write_text("01/15/2026\n", encoding="utf-8")

        loader = LABD20Loader(fresh_db)
        loader.run(
            LoaderConfig(
                card_path=card,
                comment_path=comments,
                truncate_after_processing=False,
            )
        )

        cur = fresh_db._conn.cursor()  # type: ignore[attr-defined]
        cur.execute("SELECT * FROM JC_SUBMITTED_COMMENT_TBL")
        rows = cur.fetchall()
        assert len(rows) == 1, f"expected exactly one inserted row, got {len(rows)}"
        return dict(rows[0])

    def test_inserted_column_count_matches_oracle_minus_timestamps(
        self,
        tmp_path: Path,
        fresh_db: DBDispatcher,
        oracle_tables: dict[str, OracleTable],
        parity_report: ParityReport,
    ):
        row = self._run_loader_with_one_record(tmp_path, fresh_db)
        oracle = oracle_tables["JC_SUBMITTED_COMMENT_TBL"]
        expected_count = sum(
            1 for c in oracle.columns if c.name not in INTENTIONALLY_OMITTED
        )
        # The INSERT supplies 9 columns; the Oracle describe file has 11
        # columns (incl. CREATE_TIMESTAMP, LAST_UPDATE_TIMESTAMP). 11-2 = 9.
        parity_report.insert_shape["expected_populated_columns"] = expected_count
        parity_report.insert_shape["actual_populated_columns"] = len(row)
        assert len(row) == expected_count, (
            f"INSERT populates {len(row)} columns; Oracle describe file has "
            f"{expected_count} columns once timestamps are excluded"
        )

    def test_inserted_values_respect_oracle_widths(
        self,
        tmp_path: Path,
        fresh_db: DBDispatcher,
        oracle_tables: dict[str, OracleTable],
        parity_report: ParityReport,
    ):
        row = self._run_loader_with_one_record(tmp_path, fresh_db)
        oracle = oracle_tables["JC_SUBMITTED_COMMENT_TBL"]
        width_findings: list[dict] = []
        for col_name, value in row.items():
            oc = oracle.column(col_name)
            if oc is None or oc.oracle_type != "CHAR" or oc.width is None:
                continue
            if value is None:
                continue
            text = value if isinstance(value, str) else str(value)
            within = len(text) <= oc.width
            width_findings.append(
                {
                    "column": col_name,
                    "oracle_width": oc.width,
                    "actual_length": len(text),
                    "within_oracle_width": within,
                }
            )
            assert within, (
                f"{col_name} value length {len(text)} exceeds Oracle CHAR"
                f"({oc.width})"
            )
        parity_report.insert_shape["per_column_widths"] = width_findings

    def test_not_null_columns_are_populated(
        self,
        tmp_path: Path,
        fresh_db: DBDispatcher,
        oracle_tables: dict[str, OracleTable],
    ):
        row = self._run_loader_with_one_record(tmp_path, fresh_db)
        oracle = oracle_tables["JC_SUBMITTED_COMMENT_TBL"]
        violations: list[str] = []
        for oc in oracle.columns:
            if oc.nullable:
                continue
            if oc.name in INTENTIONALLY_OMITTED:
                continue
            if row.get(oc.name) is None:
                violations.append(oc.name)
        assert not violations, (
            "NOT NULL Oracle columns came back NULL after INSERT: "
            + ", ".join(violations)
        )


# ---------------------------------------------------------------------------
# (d) CONTROL_RECORD_DATA blob layout
# ---------------------------------------------------------------------------
class TestControlRecordLayout:
    def test_blob_is_400_bytes_with_valid_jv_number(
        self,
        fresh_db: DBDispatcher,
        parity_report: ParityReport,
    ):
        cur = fresh_db._conn.cursor()  # type: ignore[attr-defined]
        cur.execute(
            "SELECT CONTROL_RECORD_DATA FROM CONTROL_RECORD_TABLE "
            "WHERE CONTROL_RECORD_NAME = ? AND CONTROL_RECORD_NUMBER = ?",
            ("JV-CONTROL-REC", 1),
        )
        row = cur.fetchone()
        assert row is not None, "seed_control_record() did not insert the row"
        data = row[0]

        # Total length: 400 bytes per the Oracle describe file
        # (CONTROL_RECORD_DATA NOT NULL CHAR(400)).
        assert len(data) == 400, f"expected 400 bytes, got {len(data)}"

        # JV-NUMBER at bytes 25-30 (1-based) = slice [24:30] (0-based).
        # Field lineage: migration/analysis/field-lineage.md lines 89-102.
        jv_slice = data[24:30]
        assert len(jv_slice) == 6
        assert jv_slice.isdigit(), (
            f"JV-NUMBER slice must be a 6-digit numeric string; got {jv_slice!r}"
        )
        # JV-CONTROL-1..4 occupy bytes 1-24 (slices [0:6], [6:12], [12:18],
        # [18:24]). Each 6 bytes per field-lineage.md.
        assert data[0:6] == "000001"
        assert data[6:12] == "000002"
        assert data[12:18] == "000003"
        assert data[18:24] == "000004"
        # JV-CONTROL-5 at bytes 40-45 ([39:45]).
        assert data[39:45] == "000005"

        parity_report.control_record_layout = {
            "total_length": len(data),
            "jv_number_slice_offsets": [24, 30],
            "jv_number_value": jv_slice,
            "jv_number_is_numeric": jv_slice.isdigit(),
            "matches_field_lineage_md_lines_89_102": True,
        }


# ---------------------------------------------------------------------------
# (e) Byte-width parity between the loader's slices and Oracle CHAR widths
# ---------------------------------------------------------------------------
class TestByteWidthParity:
    """Confirm the Python parser's byte-offset slices in
    `labd20_loader.py` lines 91-105 add up to the Oracle CHAR(n) widths.

    The APPROVER 14-vs-20 mismatch (U-5) is tolerated and surfaced as a
    known-issue annotation, NOT a failure.
    """

    def test_composite_jc_submitted_is_26_bytes(
        self,
        oracle_tables: dict[str, OracleTable],
        parity_report: ParityReport,
    ):
        oracle_width = oracle_tables["JC_SUBMITTED_COMMENT_TBL"].column("JC_SUBMITTED").width
        # Composite = COMMENT_DT (8) + JV_NUMBER (6) + SECTION_ID (2) + LOAN_NUMBER (10) = 26
        composite = (
            (COMMENT_DT_SLICE.stop - COMMENT_DT_SLICE.start)
            + (JV_NUMBER_SLICE.stop - JV_NUMBER_SLICE.start)
            + (SECTION_ID_SLICE.stop - SECTION_ID_SLICE.start)
            + (LOAN_NUMBER_SLICE.stop - LOAN_NUMBER_SLICE.start)
        )
        parity_report.byte_width_parity["JC_SUBMITTED_composite"] = {
            "python_composite_width": composite,
            "oracle_width": oracle_width,
            "matches": composite == oracle_width,
            "components": [
                {"slice": "COMMENT_DT_SLICE", "width": COMMENT_DT_SLICE.stop - COMMENT_DT_SLICE.start},
                {"slice": "JV_NUMBER_SLICE", "width": JV_NUMBER_SLICE.stop - JV_NUMBER_SLICE.start},
                {"slice": "SECTION_ID_SLICE", "width": SECTION_ID_SLICE.stop - SECTION_ID_SLICE.start},
                {"slice": "LOAN_NUMBER_SLICE", "width": LOAN_NUMBER_SLICE.stop - LOAN_NUMBER_SLICE.start},
            ],
        }
        assert composite == oracle_width == 26
        # Composite slice [0:26] redefines the same 26 bytes.
        assert LOAN_DT_NR_SLICE.stop - LOAN_DT_NR_SLICE.start == 26

    def test_schedule_doc_no_is_10_bytes(
        self,
        oracle_tables: dict[str, OracleTable],
        parity_report: ParityReport,
    ):
        slice_width = SCHEDULE_DOC_NO_SLICE.stop - SCHEDULE_DOC_NO_SLICE.start
        oracle_width = (
            oracle_tables["JC_SUBMITTED_COMMENT_TBL"]
            .column("JC_SUBMITTED_SCHED_DOC_NO")
            .width
        )
        parity_report.byte_width_parity["JC_SUBMITTED_SCHED_DOC_NO"] = {
            "python_width": slice_width,
            "oracle_width": oracle_width,
            "matches": slice_width == oracle_width,
        }
        assert slice_width == oracle_width == 10

    def test_comment_hist_is_240_bytes(
        self,
        oracle_tables: dict[str, OracleTable],
        parity_report: ParityReport,
    ):
        slice_width = COMMENT_HIST_SLICE.stop - COMMENT_HIST_SLICE.start
        oracle_width = (
            oracle_tables["JC_SUBMITTED_COMMENT_TBL"]
            .column("JC_SUBMITTED_COMMENT_HIST")
            .width
        )
        parity_report.byte_width_parity["JC_SUBMITTED_COMMENT_HIST"] = {
            "python_width": slice_width,
            "oracle_width": oracle_width,
            "matches": slice_width == oracle_width,
        }
        assert slice_width == oracle_width == 240

    def test_requestor_is_20_bytes(
        self,
        oracle_tables: dict[str, OracleTable],
        parity_report: ParityReport,
    ):
        slice_width = REQUESTOR_SLICE.stop - REQUESTOR_SLICE.start
        oracle_width = (
            oracle_tables["JC_SUBMITTED_COMMENT_TBL"]
            .column("JC_SUBMITTED_COMMENT_REQUESTOR")
            .width
        )
        parity_report.byte_width_parity["JC_SUBMITTED_COMMENT_REQUESTOR"] = {
            "python_width": slice_width,
            "oracle_width": oracle_width,
            "matches": slice_width == oracle_width,
        }
        assert slice_width == oracle_width == 20

    def test_approver_known_mismatch_is_annotated(
        self,
        oracle_tables: dict[str, OracleTable],
        parity_report: ParityReport,
    ):
        """U-5: the APPROVER slice is 14 bytes (LABD20.pco line 55) but the
        Oracle column is CHAR(20). The modernized loader stores the 14-byte
        slice as-is; Oracle CHAR(20) would right-pad on the database side.
        This test verifies the mismatch is **detected** and surfaced as a
        known-issue annotation — it must NOT fail."""
        slice_width = APPROVER_SLICE.stop - APPROVER_SLICE.start
        oracle_width = (
            oracle_tables["JC_SUBMITTED_COMMENT_TBL"]
            .column("JC_SUBMITTED_COMMENT_APPROVER")
            .width
        )
        annotation = KNOWN_ISSUES[
            ("JC_SUBMITTED_COMMENT_TBL", "JC_SUBMITTED_COMMENT_APPROVER")
        ]
        parity_report.byte_width_parity["JC_SUBMITTED_COMMENT_APPROVER"] = {
            "python_width": slice_width,
            "oracle_width": oracle_width,
            "matches": slice_width == oracle_width,
            "known_issue": annotation,
        }
        # The mismatch is real.
        assert slice_width == 14
        assert oracle_width == 20
        # And it MUST be on the known-issue list. If it's ever silently
        # "fixed" (or undocumented), this assertion will catch the drift.
        assert "U-5" in annotation


# ---------------------------------------------------------------------------
# (f) Report sanity — ensure the JSON file actually gets written
# ---------------------------------------------------------------------------
def test_parity_report_writes_to_disk(parity_report: ParityReport):
    """Tests run in order; this is the final smoke check before the
    session-scope teardown writes the JSON file. We can't read the file
    yet (teardown hasn't run), but we can verify the in-memory model is
    populated and serializable."""
    payload = parity_report.to_dict()
    # At least 5 tables analyzed, with non-zero matched counts.
    assert set(payload["tables"]) == set(DESCRIBE_FILES)
    assert payload["totals"]["matched"] > 0
    # Round-trip through JSON to confirm everything is serializable.
    json.dumps(payload)
