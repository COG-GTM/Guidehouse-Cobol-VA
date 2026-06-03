"""Make the flat slice modules and the reused Phase-1 package importable.

Puts this directory on sys.path so `from extract import ...` resolves, and the
Phase-1 modernization package (`migration/converted-code`) so the reused
`from python.labd20_loader import ...` resolves, regardless of where pytest is
invoked from.
"""

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# HERE = .../factory/conversion-datasets/jv-comment-load/python
# parents[3] is the repo root.
REPO_ROOT = HERE.parents[3]

sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO_ROOT / "migration" / "converted-code"))
