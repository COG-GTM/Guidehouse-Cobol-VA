# Test report — JV COBOL modernization demo (PR #2)

**PR:** https://github.com/COG-GTM/Guidehouse-Cobol/pull/2
**Session:** https://app.devin.ai/sessions/7360ac8b3bff442a949c59affa3adf59
**Branch:** `demo/full-migration-execution`
**Recording:** `migration/test-results/recording.mp4` (also attached to the PR comment)

---

## Summary

Tested the four user-visible deliverables of PR #2 end-to-end. Two shell-only tests (CLI + pytest) ran in the terminal. Two visual tests (HTML dashboard + executive report) were exercised in Chrome with a screen recording. **All four passed.** No issues, no degraded behavior, no missing assets.

| # | Test | Result |
|---|------|--------|
| 1 | CLI demo produces exact expected counts | passed |
| 2 | Pytest suite green (52/52) | passed |
| 3 | HTML dashboard renders at localhost:8765 with live data | passed |
| 4 | Executive HTML report renders with full Cognition branding | passed |

---

## Test 1 — CLI demo (`demo_app.py run`)

**Command:** `python3 migration/converted-code/python/demo_app.py run` · exit 0.

Output included every assertion from the plan:

```
Process date           : 20260115

LABA05 fiscal-year reset
  return code          : 0
  JV-NUMBER before     : 99
  JV-NUMBER after      : 1
  message              : JV-NUMBER reset to 1

LABD20 comment loader
  records read         : 21
  inserted             : 7
  duplicates           : 2
  rejected             : 12
  submitted total      : 7
```

Followed by the full COMMENT PROCESSING report (`COMMENTS READ 21 / ACCEPTED 7 / REJECTED 12 / DUPLICATE 2 / INSERTED 7`) — i.e. the loader walked all 21 synthetic records, applied all 8 validation rules, deduped against the seeded rows, and the LABA05 reset round-tripped 99→1 in the same in-memory DB. Full text: `migration/test-results/cli-output.txt`.

---

## Test 2 — Pytest suite

**Command:** `python3 -m pytest migration/converted-code/python/tests/ -v` · exit 0.

Final line: `============================== 52 passed in 0.14s ==============================`

Coverage spans byte-layout asserts (300-byte record, approver=14 not 20), all 8 LABD20 validation rules individually, calendar-validity (leap years + Feb 29 non-leap), duplicate detection, INSERT-9-column parameter mapping, post-process count update, rollback, SQLCODE→DMS translation (6 cases), the LABA05 JV-NUMBER extract/replace round-trip, and an end-to-end synthetic-data run. Full output: `migration/test-results/pytest-output.txt`.

---

## Test 3 — HTML dashboard at http://127.0.0.1:8765

**Setup:** ran `python3 migration/converted-code/python/demo_app.py serve &`, waited 2s, confirmed `curl http://127.0.0.1:8765/` → `HTTP 200`, then loaded the page in Chrome.

### Top of page — branding + LABA05 + LABD20 cards + rejection list

![Dashboard top](https://app.devin.ai/attachments/7f21e319-2196-4712-a878-2b6e63875615/screenshot_e8e98a8bed274cc09e9801601b707407.png)

Visible:
- Black header bar with `▰ Cognition / JV demo` wordmark and `Demo output — pending SME review` pill on the right.
- Hero h1 `JV COBOL modernization — live demo`, subtitle with process date `20260115` bolded.
- **LABA05 row:** `return code: 0` (green success pill), `JV-number before: 99`, `JV-number after: 1`.
- **LABD20 row:** `read: 21`, `inserted: 7`, `duplicates: 2`, `rejected: 12`, `submitted total: 7` — exactly matching the CLI in Test 1.
- Rejection-reasons card showing every reason emitted by the loader.

### Bottom of page — submitted rows table + run log + footer

![Dashboard bottom](https://app.devin.ai/attachments/2c6921ab-89ef-4ead-82d4-3e38bee3f2d5/screenshot_6f99fb531eba4055a0bd9d0c6c9e6cca.png)

Visible:
- `JC_SUBMITTED_COMMENT_TBL — final rows` table with all **7 inserted** rows (including the leap-day, long-comment, and section-99 boundary records).
- `Run log` `<pre>` block with `LABA05: PRIOR JV NUMBER WAS 000099`, `LABA05: JV NUMBER IS NOW 000001`, every `REJECTED …` line, both `DUPLICATE ENTRY …` lines, and the COMMENT PROCESSING report.
- Footer `Cognition — federal modernization preview. All data synthetic; no real customer information used.`

---

## Test 4 — Executive HTML report (`migration/executive-report.html`)

**Setup:** opened `file:///home/ubuntu/repos/Guidehouse-Cobol/migration/executive-report.html` in Chrome.

### Hero + quantitative snapshot

![Executive report — hero](https://app.devin.ai/attachments/049eb9fd-1917-4802-9760-c98647076923/screenshot_57f1d0f9a29143c8ad3a333749c74008.png)

Visible:
- Sticky top bar with **Cognition sprocket SVG + `Cognition / JV COBOL modernization`** wordmark, and the `Demo output · pending SME review` pill on the right.
- Hero h1 `From legacy Pro*COBOL to a runnable, testable, traceable modern stack — in one session.`
- Honeycomb decoration SVG (faint hex pattern) to the right of the hero copy.
- **Quantitative snapshot** with all 8 stat cards: `1,633` lines analyzed, `1,640` lines generated, `30` BRs, `14` SQL statements, `21` test records, `52` tests, `11` risks · 17 assumptions, `4` Mermaid diagrams.

### Blockers & what's missing — 11 risk cards

![Executive report — risk cards](https://app.devin.ai/attachments/8149bc52-c2aa-4d2c-8fae-3fba36c1a692/screenshot_3edecace6d90432896a569a1b9eabf7f.png)

All 11 risk cards visible with severity pills (HIGH × 3: missing DATECONV copybooks, binary↔display JV-NUMBER, credential files; MEDIUM × 5; LOW × 3) and per-risk mitigations citing the exact Python function or test that addresses each one.

### Artifacts grid + live demo + verification

![Executive report — artifacts + live demo + verification](https://app.devin.ai/attachments/f73c2274-e31d-408e-801b-b0841f9aa9d4/screenshot_b1308ac318a1484dbc7a6d155be8891d.png)

Visible:
- Artifacts grid completing the 6-card layout (Tests & Data, Customer-facing, Live demo on this row).
- `Live demo — Bring it up in under thirty seconds` with the two black command blocks (`run` and `serve`) and the bolded expected output line.
- `Verification — 52 tests, all passing` block showing the pytest one-liner.

### Traceability matrix + path forward + footer

![Executive report — traceability + footer](https://app.devin.ai/attachments/07060c77-5d5d-43cf-809f-bd130d704c6d/screenshot_7fb6e2026b7d41208bfb9611e69632dc.png)

Visible:
- Full 8-row traceability matrix (BR-LABA05 6/6 Python and tests, BR-LABD20 19/22 Python and 17/22 tests, 4 unresolvable, 52 passing assertions, 11 risks, 17 assumptions).
- `What's next` 6-step recommended path forward.
- Footer with Cognition sprocket + `Cognition · Confidential. Demo output, pending SME review. All test data synthetic. No real customer information.`

---

## Not tested (intentionally)

- Each of the 22 markdown docs individually — they are documentation artifacts and the executive HTML report's links into them are the primary access path. Scanning each in a recording wouldn't add signal.
- The `--json` flag of `demo_app.py` — same code path as the text output, so the text path is sufficient.
- Real Oracle wiring — explicitly out of scope; the demo uses an in-memory sqlite mock by design (and the README + executive report both call this out).
- Source COBOL — not modified in this PR.

---

## Notes for the live demo

The dashboard renders the **same values** computed by the CLI in real time on every request (it executes the loader and reset per page-load against a fresh in-memory DB), so the demo is naturally reproducible. The executive report is a single static HTML file that opens straight from disk — no server needed.
