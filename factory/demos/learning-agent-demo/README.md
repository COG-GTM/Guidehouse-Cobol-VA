# Learning-agent demo — the S8 knowledge-fabric feedback loop

This demo answers the question *"does the factory actually get smarter, or do you
just re-prompt it every time?"* It shows the **S8 feedback loop** closing on a
real conversion: a first pass rejects records because the reference data is
incomplete, an SME confirms the rejects are valid, the knowledge fabric is
updated, and a second pass over the **same input** accepts them.

Nothing here is mocked at the conversion layer — it drives the real GL/journal
slice (`factory/conversion-datasets/gl-journal-extract/`) end to end, twice.

## Run it

```bash
cd factory/demos/learning-agent-demo
python run_learning_demo.py          # human-readable before/after table
python run_learning_demo.py --json   # machine-readable summary
```

Exit code is `0` only if the second pass is provably better than the first
(fewer rejects, higher coverage, and a batch that flips from *not* load-ready to
load-ready). Re-running is idempotent.

## What you'll see

```
  metric                       PASS 1 (seed)  PASS 2 (learned)
  ------------------------------------------------------------
  lines in                                 6                 6
  accepted (loaded)                        3                 6
  rejected                                 3                 0
  mapping coverage                       0.5               1.0
  all journals balanced                False              True
  LOAD READY                           False              True
  reference data entries                  11                13

  Pass 1 reject reasons : {'BAD_FUND': 2, 'BAD_USSGL': 1}
  Pass 2 reject reasons : {}
```

## The loop, stage by stage

```
   PASS 1 (seed knowledge)            LEARN (S8)                 PASS 2 (grown knowledge)
   ----------------------            ----------                 ------------------------
   parse → map → reconcile           inspect reject queue       parse → map → reconcile
   3 lines reject:                   SME confirms each reject   same 6 lines, 0 reject
     BAD_FUND  (fund 8180)            is a VALID posting the    every journal balances
     BAD_USSGL (acct 490200)          chart was missing         LOAD_READY = True
   LOAD_READY = False                extend crosswalk +
                                      whitelist; append the
                                      correction to the
                                      reject taxonomy
```

The reference data (`USSGL_WHITELIST`, `FUND_CROSSWALK`) is **injected into the
mapper as context**, not hard-coded — which is the whole point. The factory reads
the knowledge fabric at run time, so growing the fabric changes behavior with no
code change.

## Why these two gaps (they're realistic, not toy)

| Gap in pass 1 | What it really is | Why the fix generalizes |
| --- | --- | --- |
| Legacy fund `8180` → `BAD_FUND` | VA **General Post Fund** (real trust fund, 36X8180), simply absent from the seed crosswalk | One crosswalk entry fixes every future record on that fund |
| USSGL `490200` → `BAD_USSGL` | **Delivered Orders – Obligations, Paid** (a real USSGL account) | The **obligation/disbursement slice already knows this account** — the loop teaches the GL slice the same thing, showing knowledge learned on one interface transfers to another |

## What grows (the persistent knowledge fabric)

1. **`factory/knowledge/reject-taxonomy.md`** — the demo rewrites the managed
   block between `<!-- BEGIN LEARNED -->` / `<!-- END LEARNED -->` with the SME
   findings and resolutions. This is the canonical, human-readable fabric and it
   is version-controlled, so every correction is a reviewable Git diff.
2. **`knowledge/learned-reference-data.json`** — the machine-readable seed +
   corrections the second pass consumes (regenerated each run; git-ignored).

## Honesty note (so the demo survives scrutiny)

The **loop is real**: real conversion code, real reject reasons, real control
totals, real before/after. The single simulated element is the *human decision* —
the `SME_RESOLUTIONS` table in `run_learning_demo.py` stands in for an analyst
clearing the reject queue, so the demo is deterministic. In production that
decision comes from the SME review queue (confidence-scored, Git-inspected), and
the same machinery records and applies it. The demo will only "learn" a
correction for a reject reason it actually observed in pass 1 — it cannot invent
improvements.

## Files

| Path | Role |
| --- | --- |
| `run_learning_demo.py` | The demo: builds the fixture, runs pass 1, grows the fabric, runs pass 2, prints before/after. |
| `knowledge/base-reference-data.json` | Committed seed — deliberately missing fund 8180 and USSGL 490200. |
| `knowledge/learned-reference-data.json` | Generated each run: seed + SME-confirmed corrections (git-ignored). |
| `data/gl_extract_learning.dat` | Generated synthetic GL fixture (3 balanced journals) exercising the two gaps. |
