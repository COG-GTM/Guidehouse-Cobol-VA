---
name: cobol-modernization-demo-execution
description: Use during a live or rehearsed walkthrough of the JV COBOL modernization demo for Guidehouse/VA (executive report, live dashboard, parity console, CLI proof). Covers the exact run order, talk-track guardrails, honest-framing language, and the four artifacts that must reconcile.
---

# COBOL modernization demo — execution skill

Use this when **running** the demo (not when building it). For building new artifacts, see `cobol-modernization-demo` and `AGENTS.md`.

## What the customer sees (4 artifacts, in this order)

1. `migration/executive-report.html` — branded executive walkthrough (open in browser).
2. `python3 migration/converted-code/python/demo_app.py serve` → `http://127.0.0.1:8765/` live dashboard.
3. `http://127.0.0.1:8765/parity` — 28-BR parity console with per-BR expandable COBOL+Python source.
4. CLI proof: `demo_app.py run`, `demo_app.py parity`, `pytest`.

These four must reconcile. If they don't, stop and fix before the demo.

## Pre-demo sanity check (run all of these once before the call)

```bash
cd <repo-root>
python3 -m pytest migration/converted-code/python/tests/ -v
python3 migration/converted-code/python/demo_app.py run
python3 migration/converted-code/python/demo_app.py parity
python3 migration/converted-code/python/demo_app.py serve &  # leave running
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8765/parity
```

Expected (do NOT proceed if any of these is wrong):

- pytest: `52 passed`.
- `demo_app.py run`: `21 records read · 7 inserted · 2 duplicates · 12 rejected · JV-NUMBER reset 99 → 1`.
- `demo_app.py parity`: `PASS=28 FAIL=0 UNRESOLVED=0`.
- Both curl checks return `200`.
- Open `executive-report.html` in Chrome and confirm: sticky header, 5 SVG diagrams (not raw `graph TD` text), parity hero reads `28 / 28`, Q&A board renders 21 cards.

If any number drifts (e.g. parity hero reads `0/28`, or a diagram is a red error box), the renderer / server is broken — do not demo until fixed.

## Run order in front of the customer

1. **Open `executive-report.html`** first. Anchor the customer with the branded header + quantitative snapshot. Scroll once top-to-bottom so they see the execution board, the 5 diagrams, the parity hero, the 11 risks, the 21-question board, and the traceability matrix.
2. **Switch to the live dashboard** `http://127.0.0.1:8765/`. Point at the JV-NUMBER 99→1 cell and the 21/7/2/12 counters. Note the realistic synthetic names in `JC_SUBMITTED_COMMENT_TBL` (e.g. ALICE.SUBMITTER / BOB.APPROVER) — that's the "this isn't a toy" signal.
3. **Open `/parity`** and expand `BR-LABA05-001`. Show the COBOL source pane, the Python conversion pane, and the expected-vs-actual block. This is the customer's "show me proof" moment.
4. **(Optional) CLI proof** — run `demo_app.py parity` and `pytest` in a terminal next to the browser to show the same numbers come from a real run, not screenshots.

## Honest-framing language (say this out loud)

The parity console's *expected* column is a COBOL-source-derived golden output — not a live mainframe execution — because this VM has no Pro*COBOL precompiler or Oracle.

Use the in-page phrasing verbatim: "in a real engagement, flip one config switch and the expected column becomes a live mainframe execution against the same synthetic input, producing the byte-for-byte diff that SBA question 2 / 14 describes."

The *actual* column is always a live Python run against an in-memory mock Oracle.

This is already disclosed in the yellow callout at the top of `/parity` and in the "Honest framing" paragraph of the executive report. Saying it out loud removes any chance of a customer engineer feeling misled.

## Two placeholders that are intentional (don't apologize for them)

- `labd20_loader.check_cymd_dt` — `DATECONV-WS/PD` copybooks were not supplied; stub uses a Gregorian-calendar fallback and is grep-able with `rg "# PLACEHOLDER" migration/converted-code`.
- `laba05_reset._extract_jv_number` — JV-NUMBER USAGE BINARY conversion (`struct.unpack('>I', ...)`) against a real Oracle is the production-mode swap; demo uses the display form.

These are flagged on the parity console as the 4 "flagged" items in the `28 / 0 / 4` badge, in the risk register, and in the "what's next" section. They are evidence that the platform doesn't silently invent semantics — frame them as a strength.

## Aspirational vs source-grounded answers

On the 21-question board, **gray chips = file/line citation from this PR**; **amber chips = aspirational / platform-level claim** (security posture, FedRAMP timeline, Windsurf IDE — Margarita's questions). If a customer asks about an amber-chipped answer, route it to the account team — don't try to prove it from the four files in this PR.

## Numbers that must reconcile across all four artifacts

| Number | Where it shows up |
|---|---|
| 52 passed | exec report verification section · `pytest` |
| 28 PASS / 0 FAIL | exec report parity hero · `/parity` header · `demo_app.py parity` |
| 21 read / 7 inserted / 2 dups / 12 rejected | exec report live-demo section · `/` dashboard · `demo_app.py run` |
| JV-NUMBER 99 → 1 | exec report live-demo section · `/` dashboard · `demo_app.py run` |
| 21 / 21 questions answered | exec report quantitative snapshot · Q&A board count |

If any one of these diverges, the demo is broken — fix before proceeding.

## Common pitfalls during live execution

- Don't kill the `serve` process between artifacts. Keep it running in a background shell so `/` and `/parity` stay reachable.
- Don't open `migration/test-results/parity-console.html` as a substitute for `/parity` unless the server is down. The static console and the live one have the same content, but the live one matches the "served by demo_app" story the executive report tells.
- If the customer asks "did this actually run against Oracle?" → no, the demo uses an in-memory mock Oracle (SQLite in-memory). The Python is the modernized path; the COBOL was not re-executed. Use the in-page yellow callout's exact wording.
- Don't open `RISKS-AND-GAPS.md` in a separate tab during the demo — the executive report's risks section already summarizes all 11 and links out for SMEs. Save the raw markdown for the SME review session after the demo.

## Where to look when something breaks

- Server returns non-200 on `/` or `/parity`: kill and restart `demo_app.py serve`.
- A diagram in `executive-report.html` shows as a red box: Mermaid CDN didn't load. Open browser devtools → Network and confirm the Mermaid script. If offline, the static `migration/test-results/parity-console.html` still works for the parity portion of the demo.
- Parity hero shows `0 / 28`: the parity engine didn't run. Re-run `demo_app.py parity` to confirm `PASS=28`, then refresh the dashboard.

## Devin secrets needed

None for the demo path itself. The repo is private and demo-only; no live Oracle, no real customer data, no auth.

## Out of scope for this skill

- Modifying customer-supplied source files under `source/` (forbidden by `AGENTS.md`).
- Generating new business requirements or lineage — that's `cobol-modernization-demo`'s job.
- Claiming Pro*COBOL or Oracle ran. They didn't.
