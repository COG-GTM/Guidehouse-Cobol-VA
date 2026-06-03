"""Put this package directory on sys.path so the flat module imports
(`from gl_extract import ...`) resolve when pytest is run from anywhere.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
