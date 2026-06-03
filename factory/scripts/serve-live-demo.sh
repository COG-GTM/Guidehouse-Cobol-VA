#!/usr/bin/env bash
# serve-live-demo.sh
# Launches the FMBT Factory executive report with a *live* embedded terminal.
#
# - python -m http.server  serves the static report on :${HTTP_PORT} (default 8787)
# - ttyd                   serves an interactive shell on :${TTY_PORT}  (default 7681)
#   The shell is bound to 127.0.0.1, writable, restricted to this repo,
#   and pre-loaded with the demo virtualenv on PATH.
#
# Stop with Ctrl-C; both servers exit together.
#
# Requires: python3, ttyd (brew install ttyd).

set -euo pipefail

HTTP_PORT="${HTTP_PORT:-8787}"
TTY_PORT="${TTY_PORT:-7681}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

if ! command -v ttyd >/dev/null 2>&1; then
  echo "ERROR: ttyd not found. Install with:  brew install ttyd" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found." >&2
  exit 1
fi

# Bootstrap demo venv if missing so the live terminal can run pytest/convert.py.
if [ ! -x ".venv-demo/bin/python" ]; then
  echo "[serve-live-demo] creating .venv-demo and installing pytest..."
  python3 -m venv .venv-demo
  .venv-demo/bin/pip install --quiet --upgrade pip
  .venv-demo/bin/pip install --quiet pytest
fi

# Free ports if previously held.
for port in "${HTTP_PORT}" "${TTY_PORT}"; do
  pids="$(lsof -ti:"${port}" 2>/dev/null || true)"
  if [ -n "${pids}" ]; then
    echo "[serve-live-demo] freeing port ${port} (killing: ${pids})"
    kill -9 ${pids} 2>/dev/null || true
  fi
done

# Per-session welcome shell. ttyd will spawn this for each new browser tab.
WELCOME_SH="${SCRIPT_DIR}/_welcome.sh"
cat > "${WELCOME_SH}" <<'WELCOME'
#!/usr/bin/env bash
clear
cat <<'BANNER'
================================================================
  VA FMBT Integration & Conversion Factory  --  live terminal
  Sandbox: this repo only. Synthetic data only. Localhost only.
================================================================

Try these commands (also shown in the static panel above):

  # full test suite for the GL slice (19 tests)
  cd factory/conversion-datasets/gl-journal-extract/python
  python -m pytest -q

  # full test suite for the JV-comment slice (13 tests)
  cd factory/conversion-datasets/jv-comment-load/python
  python -m pytest -q

  # GL: clean fixture (exit 0, load_ready=True)
  python factory/conversion-datasets/gl-journal-extract/python/convert.py \
    factory/conversion-datasets/gl-journal-extract/data/gl_extract_clean.dat

  # GL: unbalanced fixture (exit 1, gate trips)
  python factory/conversion-datasets/gl-journal-extract/python/convert.py \
    factory/conversion-datasets/gl-journal-extract/data/gl_extract_unbalanced.dat

  # JV-comment: real LABD20 fixture
  python factory/conversion-datasets/jv-comment-load/python/convert.py \
    migration/test-data/synthetic_comments.dat

BANNER
exec bash
WELCOME
chmod +x "${WELCOME_SH}"

# Put the demo venv first on PATH so `python` and `pytest` resolve correctly.
export PATH="${REPO_ROOT}/.venv-demo/bin:${PATH}"
export PYTHONDONTWRITEBYTECODE=1

echo "[serve-live-demo] HTTP   http://localhost:${HTTP_PORT}/factory/executive-report.html"
echo "[serve-live-demo] SHELL  http://localhost:${TTY_PORT}/  (embedded as iframe in the report)"

# Start the static file server.
python3 -m http.server "${HTTP_PORT}" --bind 127.0.0.1 >/tmp/fmbt-http.log 2>&1 &
HTTP_PID=$!

# Start the terminal server. -W = writable, -i 127.0.0.1 = localhost only,
# -t = xterm.js options, -p = port.
ttyd \
  -p "${TTY_PORT}" \
  -i 127.0.0.1 \
  -W \
  -t 'fontSize=13' \
  -t 'theme={"background":"#0e0e0e","foreground":"#e8e8e8","cursor":"#4ade80"}' \
  -t 'titleFixed=FMBT Factory live terminal' \
  -t 'disableLeaveAlert=true' \
  "${WELCOME_SH}" \
  >/tmp/fmbt-ttyd.log 2>&1 &
TTY_PID=$!

cleanup() {
  echo
  echo "[serve-live-demo] shutting down..."
  kill "${HTTP_PID}" "${TTY_PID}" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

sleep 1

# Open the browser to the report (best effort; skip if headless).
if command -v open >/dev/null 2>&1; then
  open "http://localhost:${HTTP_PORT}/factory/executive-report.html" || true
fi

echo "[serve-live-demo] ready. Press Ctrl-C to stop."
wait
