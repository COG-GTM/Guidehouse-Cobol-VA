#!/usr/bin/env bash
# Compile + drive the DATECONV parity harness end-to-end.
#
# Steps:
#   1. Compile the customer's COBOL subprogram + our stdin/stdout driver under
#      GnuCOBOL. The customer source under source/cobol/ is treated as
#      read-only; the only generated COBOL artifact lives next to this script
#      (DATECONV-DRIVER.cob).
#   2. Run the test vectors through the compiled binary and capture the
#      golden COBOL output (cobol-driver-output.txt).
#   3. Hand the same vectors to the Python diff harness, which renders the
#      Python port's output and produces cobol-parity-report.html plus
#      cobol-parity-summary.json.
#
# Exits non-zero if any vector mismatches byte-for-byte.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../../.." && pwd)"
SRC_COBOL="$REPO/source/cobol/DATECONV.cbl"
CPY_DIR="$REPO/source/copybooks"
DRIVER_SRC="$HERE/DATECONV-DRIVER.cob"
DRIVER_BIN="$HERE/dateconv-driver"
VECTORS="$REPO/migration/test-results/dateconv-test-vectors.txt"
COBOL_OUT="$REPO/migration/test-results/cobol-driver-output.txt"

command -v cobc >/dev/null 2>&1 || {
  echo "ERROR: GnuCOBOL (cobc) is not installed. apt-get install -y gnucobol" >&2
  exit 2
}

echo "[1/3] Compiling DATECONV.cbl + driver under GnuCOBOL..."
cobc --version | head -1
cobc -x -fixed -I "$CPY_DIR" -ext cpy \
     -o "$DRIVER_BIN" \
     "$DRIVER_SRC" "$SRC_COBOL"

echo "[2/3] Running ${VECTORS##*/} through compiled binary..."
grep -E '^N\|' "$VECTORS" | "$DRIVER_BIN" > "$COBOL_OUT"
echo "    -> $COBOL_OUT ($(wc -l < "$COBOL_OUT") rows)"

echo "[3/3] Diffing against migration/converted-code/python/dateconv.py..."
python3 "$REPO/migration/test-results/run_cobol_parity.py"
