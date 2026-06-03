"""Smoke-test the embedded live terminal.

Verifies:
  1. The factory executive report loads at :8787.
  2. The #term-frame iframe is visible and the #term-fallback overlay is hidden
     (i.e. the no-cors probe to ttyd succeeded).
  3. The iframe's document contains xterm.js DOM nodes (ttyd's UI mounted).
  4. The iframe issues a WebSocket request to ttyd, indicating a real shell
     session was established.

Run with the launcher already running:
    factory/scripts/serve-live-demo.sh &
    .venv-demo/bin/python factory/scripts/_smoke_test_live_terminal.py
"""

from __future__ import annotations

import sys
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

REPORT_URL = "http://localhost:8787/factory/executive-report.html"


def main() -> int:
    failures: list[str] = []
    ws_urls: list[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.on("websocket", lambda ws: ws_urls.append(ws.url))

        page.goto(REPORT_URL, wait_until="networkidle")

        # (1) report loaded
        title = page.title()
        if "FMBT" not in title:
            failures.append(f"unexpected page title: {title!r}")

        # (2) iframe visible, fallback hidden
        page.wait_for_selector("#term-frame", state="attached", timeout=5000)
        frame_visible = page.is_visible("#term-frame")
        fb_visible = page.is_visible("#term-fallback")
        if not frame_visible:
            failures.append("#term-frame is not visible")
        if fb_visible:
            failures.append("#term-fallback overlay is visible (probe failed)")

        # (3) ttyd UI mounted inside iframe
        try:
            term_frame = page.frame_locator("#term-frame")
            term_frame.locator(".xterm").wait_for(state="attached", timeout=8000)
        except PWTimeout:
            failures.append("xterm.js DOM did not mount inside the iframe")

        # (4) WebSocket established to ttyd
        # Give the WS handshake a moment beyond networkidle.
        page.wait_for_timeout(1500)
        ttyd_ws = [u for u in ws_urls if "7681" in u and "ws" in u]
        if not ttyd_ws:
            failures.append(f"no WebSocket to ttyd observed (saw: {ws_urls})")

        browser.close()

    if failures:
        print("LIVE TERMINAL SMOKE: FAIL")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("LIVE TERMINAL SMOKE: PASS")
    print(f"  report      : {REPORT_URL}")
    print(f"  ttyd ws url : {ttyd_ws[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
