"""Run each conversion-dataset slice suite in an isolated subprocess.

The slices share flat module names by design, so they cannot be collected in
one pytest process (see the root ``conftest.py``). Each suite runs from its
own ``python/`` directory with a clean interpreter, and the expected pass
count is asserted as a control total so a silently-skipped suite fails loudly.
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DATASETS = _REPO_ROOT / "factory" / "conversion-datasets"

_SLICES = [
    ("gl-journal-extract", 19),
    ("jv-comment-load", 13),
    ("obligation-disbursement", 20),
]


@pytest.mark.parametrize(("slice_name", "expected_passed"), _SLICES)
def test_slice_suite_passes(slice_name: str, expected_passed: int) -> None:
    slice_dir = _DATASETS / slice_name / "python"
    assert slice_dir.is_dir(), f"missing slice directory: {slice_dir}"

    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-q"],
        cwd=slice_dir,
        capture_output=True,
        text=True,
        timeout=300,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, f"{slice_name} suite failed:\n{output}"

    match = re.search(r"(\d+) passed", output)
    assert match, f"could not find pass count in {slice_name} output:\n{output}"
    assert int(match.group(1)) == expected_passed, (
        f"{slice_name}: expected {expected_passed} passing tests, "
        f"got {match.group(1)} — update the control total deliberately"
    )
