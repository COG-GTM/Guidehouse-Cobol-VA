"""Keep the executive report's headline tiles in sync with the live model.

The tiles in ``executive-report.html`` are populated at view time from the
generated ``executive-report.data.js`` sidecar; the numbers hard-coded in the
HTML are only a no-JS fallback. These tests assert both the committed sidecar
and the HTML fallbacks match a fresh derivation, in both directions, so a
model change cannot leave either stale.
"""

import importlib.util
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_FACTORY = _REPO_ROOT / "factory"
_BUILDER = _FACTORY / "demos" / "interface-portfolio" / "build_portfolio_data.py"

_TILE_IDS = {
    "m-systems-total": "systems_total",
    "m-factory-scope": "factory_scope",
    "m-waves": "waves",
    "m-icd-violations": "icd_violations",
}


def _load_builder():
    spec = importlib.util.spec_from_file_location("build_portfolio_data", _BUILDER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fresh_metrics() -> dict[str, int]:
    return _load_builder().report_metrics()


def _committed_sidecar() -> dict[str, int]:
    text = (_FACTORY / "executive-report.data.js").read_text()
    return json.loads(text.removeprefix("window.REPORT_DATA = ").rstrip().rstrip(";"))


def _html_fallbacks() -> dict[str, int]:
    html = (_FACTORY / "executive-report.html").read_text()
    values: dict[str, int] = {}
    for tile_id, key in _TILE_IDS.items():
        match = re.search(rf'id="{tile_id}">(\d+)<', html)
        assert match, f"tile {tile_id!r} not found in executive-report.html"
        values[key] = int(match.group(1))
    return values


def test_committed_sidecar_matches_live_model() -> None:
    assert _committed_sidecar() == _fresh_metrics()


def test_html_fallbacks_match_live_model() -> None:
    assert _html_fallbacks() == _fresh_metrics()


def test_control_totals() -> None:
    assert _fresh_metrics() == {
        "systems_total": 125,
        "factory_scope": 62,
        "waves": 7,
        "icd_violations": 0,
    }
