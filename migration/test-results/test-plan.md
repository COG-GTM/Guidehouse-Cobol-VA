# Test plan — JV COBOL modernization demo (PR #2)

**Scope:** prove the four user-visible deliverables actually do what the PR description claims, in a way a broken implementation could not fake.

| # | Deliverable | Trigger |
|---|-------------|---------|
| 1 | CLI demo | `python3 migration/converted-code/python/demo_app.py run` |
| 2 | Pytest suite | `python3 -m pytest migration/converted-code/python/tests/ -v` |
| 3 | HTML dashboard | `python3 migration/converted-code/python/demo_app.py serve` → http://127.0.0.1:8765 |
| 4 | Executive HTML report | open `migration/executive-report.html` in Chrome via `file://` |

---

## Test 1 — CLI demo produces exact expected counts

**Command:** `python3 migration/converted-code/python/demo_app.py run`

**Expected stdout must contain EVERY ONE of these literal lines:**
- `Process date           : 20260115`
- `  return code          : 0`
- `  JV-NUMBER before     : 99`
- `  JV-NUMBER after      : 1`
- `  records read         : 21`
- `  inserted             : 7`
- `  duplicates           : 2`
- `  rejected             : 12`
- `  submitted total      : 7`

**Why this would catch a break:** if the loader's byte offsets were off, the validation rules misordered, the dispatcher silently no-op'd, or the synthetic data corrupted, at least one of these specific counts would shift. The fiscal-year reset specifically must show 99 → 1 because that is the entire purpose of LABA05.

**Pass:** all 9 lines present, exit code 0.
**Fail:** any count off, exit code non-zero, or any line missing.

---

## Test 2 — Pytest suite green

**Command:** `python3 -m pytest migration/converted-code/python/tests/ -v`

**Expected:** final line reads exactly `52 passed in <time>s`.

**Why this would catch a break:** any change to byte slices, validation rules, or SQLCODE→DMS translation would flip at least one specific test (the suite tests each rule individually plus 6 SQLCODE cases plus a 21-record end-to-end). A naive shortcut implementation would either fail end-to-end or fail one of the byte-layout asserts (e.g. `test_approver_is_14_not_20`).

**Pass:** `52 passed` exactly, exit code 0.
**Fail:** fewer than 52 passed, any failures, errors, or warnings about collection.

---

## Test 3 — HTML dashboard renders in Chrome with live data

**Setup:** start `python3 migration/converted-code/python/demo_app.py serve` in the background, navigate Chrome to http://127.0.0.1:8765.

**Visual assertions (all must hold simultaneously):**
1. **Black header banner** with the text `Cognition / JV demo` and the right-side pill `Demo output — pending SME review`.
2. Title `JV COBOL modernization — live demo`.
3. Subtitle includes the bold text `20260115` (the process date).
4. Under "LABA05 — fiscal-year JV-NUMBER reset" three cards:
   - return code: `0` (with a green/ok pill)
   - JV-number before: `99`
   - JV-number after: `1`
5. Under "LABD20 — daily comment loader" five cards with values **exactly**: read=`21`, inserted=`7`, duplicates=`2`, rejected=`12`, submitted total=`7`.
6. "Rejection reasons (sampled)" list visible with multiple bullets (≥ 5 items).
7. "JC_SUBMITTED_COMMENT_TBL — final rows" table present with headers and 7 data rows visible (or scrollable to 7).
8. "Run log" `<pre>` block visible with log text.
9. Footer text `Cognition — federal modernization preview. All data synthetic; no real customer information used.`

**Why this would catch a break:** these numeric values are computed at request-time by the same code path as the CLI test. A template that hard-coded a value would not match a CLI run that produced a different value (we cross-check with Test 1). If `serve` returned a 500 or an empty page, Chrome would show nothing. If the HTML was malformed, the stat cards or table would render broken.

**Pass:** all 9 assertions hold visually.
**Fail:** any value mismatch, any missing section, Chrome shows an error.

---

## Test 4 — Executive HTML report renders with full Cognition branding

**Setup:** open `file:///home/ubuntu/repos/Guidehouse-Cobol/migration/executive-report.html` in Chrome.

**Visual assertions (all must hold simultaneously):**
1. **Sticky top header** with the Cognition sprocket SVG + the text `Cognition / JV COBOL modernization`.
2. Status pill `Demo output · pending SME review` visible on the right of the top bar.
3. Hero h1 reads: `From legacy Pro*COBOL to a runnable, testable, traceable modern stack — in one session.`
4. "Quantitative snapshot" section shows 8 stat cards including `1,633`, `1,640`, `30`, `14`, `21`, `52`, `11`, `4`.
5. "Execution board" table shows 6 phase rows (0 through 5) each with a green `done` pill.
6. "Blockers & what's missing" section shows 11 risk cards with severity pills (`high`/`medium`/`low`).
7. "Artifacts" section shows 6 cards (Plan & registers, Analysis, Converted code, Tests & data, Customer-facing, Live demo) — each card has clickable links.
8. "Live demo" section shows two black code blocks with the two `python3 …` commands.
9. Honeycomb decoration SVG visible top-right of the hero area.
10. Footer at bottom reads `Confidential. Demo output, pending SME review. All test data synthetic. No real customer information.`

**Why this would catch a break:** an HTML file with broken CSS, missing SVG, or missing sections would visibly miss one or more of these elements. The 8 specific stat values are hard-coded in the report and must reflect the actual artifact counts.

**Pass:** all 10 assertions hold visually.
**Fail:** any missing element, branding broken, page renders as raw text.

---

## What I am NOT testing (and why)

- Each of the 22 markdown docs — they are documentation artifacts; scanning every section in a recording would be tedious and wouldn't reveal much. The executive HTML report links to them and rendering of representative markdown is implicit.
- The `--json` flag of the demo — same code path as the text output; the text path is sufficient signal.
- Production Oracle wiring — explicitly out of scope (the demo uses an in-memory sqlite mock by design).
- Source COBOL — not modified in this PR, no regression risk.
