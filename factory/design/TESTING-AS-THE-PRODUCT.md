# Testing is the product

The customer's instinct was that conversion is the deliverable and testing is a
phase at the end. We invert that. For a financial conversion, **the
reconciliation evidence *is* the deliverable** — the converted file is just the
thing that produces the evidence. A conversion that "ran successfully" but can't
prove the money survived is worthless to an auditor. So the factory is built
testing-first, and every claim below is something the GL reference slice already
demonstrates on synthetic data.

## The control layers

### 1. Reconciliation engine (row + dollar control totals)

`reconciliation.py`. For every batch:

- **Row accounting** — `lines_in == lines_loaded + lines_rejected`. No silent
  drops, ever. This single invariant catches the most dangerous conversion bug:
  data that quietly disappears.
- **Dollar control totals** — Σ legacy amount (accepted) == Σ target amount, to
  the cent, using `Decimal` (never floats) so there is no rounding drift.
- **Per-document balance** — for each journal, Σ debits == Σ credits. An
  unbalanced journal fails the gate even when every individual line is valid.
- **Mapping coverage %** — accepted ÷ in. A coverage drop between waves is an
  early warning that the source changed.

### 2. Schema / contract tests

Every conversion targets an explicit, versioned **target contract**
(`target/MOMENTUM-JOURNAL-IMPORT.md`), not an implicit format. The contract is
what the tests assert against, so a change to the target layout breaks tests
loudly instead of producing a silently malformed load file.

### 3. Momentum import simulator + post-load transaction tests

`convert.py:simulate_momentum_import`. The emitted file is re-read as an **opaque
inbound interface** — exactly as Momentum's own import would see it — and the
journal-level rules are re-asserted independent of the in-memory objects. That
round trip is a *load rehearsal*: a green result means the file would actually
post and balance, not merely that it is well-formed.

### 4. Golden-file regression

Each interface keeps a committed golden output for a fixed synthetic input. A
diff against the golden on every run turns "did our last change alter any
posting?" into a one-line CI answer. (In this repo, the COBOL↔Python parity work
under `migration/test-results/` is the same idea applied to the upstream given.)

### 5. CI reconciliation gate

`convert.py` exits non-zero when a batch is not load-ready. Wired into CI, "is
the conversion correct?" becomes a build status. The `gl_extract_unbalanced.dat`
fixture exists specifically to prove the gate **fails** when it should.

### 6. Synthetic data at realistic volume & shape

Fixtures cover the clean path, every reject reason, and an intentionally
unbalanced journal. Production scales the generator to fiscal-year-end volumes
and real period/fund distributions so performance and edge density are tested
before cutover, not during it.

## Eleven test angles the customer's design did not call out

These are the ones that separate "we converted the data" from "we can stand
behind the conversion in an audit and a cutover window." Each is a concrete,
buildable check.

1. **Round-trip / reverse reconciliation.** Don't only prove legacy→Momentum
   balances. Regenerate the legacy view *from* the Momentum target and diff it
   back against the original extract. Catches transforms that balance in
   aggregate but corrupt individual records.
2. **Cutover-window performance proof.** The conversion has to finish inside a
   real maintenance window. Benchmark throughput at fiscal-year-end volume and
   publish the projected wall-clock for the largest wave *before* cutover night.
3. **Schema-drift detection across waves.** Hash each interface's source layout
   per wave; alert when a "stable" interface's structure shifts so a downstream
   wave doesn't silently mis-map.
4. **Idempotent restart / exactly-once.** Prove that re-running a half-loaded
   batch neither double-posts nor drops records. Cutovers get interrupted; the
   factory must be safe to resume.
5. **Mapping-coverage as a tracked metric.** Treat coverage % as a release gate
   that can only go up. A regression means the source changed or a crosswalk
   went stale.
6. **Reject-reason taxonomy & trend.** Every reject is typed (`BAD_USSGL`,
   `ZERO_AMOUNT`, …) and counted per run, so SMEs triage *categories* and watch
   whether a category is growing wave over wave.
7. **Boundary & fiscal-calendar cases.** Period 13/14 adjustments, leap-year
   ordinal dates (the slice tests 2024-366), fiscal-year rollover JV-number
   reset, and `$0`/negative/overflow amounts — the cases that only appear at
   year-end.
8. **Referential-integrity checks against Momentum master data.** Validate
   fund/TAFS/object-class/vendor against the *target's* reference data, not just
   format. A perfectly formatted posting to a fund Momentum doesn't recognize is
   still a failed load.
9. **Duplicate / replay detection across files.** Detect the same posting
   arriving in two extracts (a real hazard when legacy jobs are re-run), reusing
   the duplicate-detection pattern already proven in the `LABD20` port.
10. **Confidence scoring on every mapping.** Each field mapping carries a
    confidence (deterministic crosswalk = high; inferred = low). Low-confidence
    maps are routed to SME review instead of being trusted silently.
11. **Audit/provenance trail per record.** Every target record can name the
    source byte-row, the rules applied, and the wave/run that produced it — so a
    finding can be traced to its origin in seconds.

## How a reviewer verifies all of this in 60 seconds

```bash
cd factory/conversion-datasets/gl-journal-extract/python
python -m pytest -q                              # 18 control tests, all green
python convert.py ../data/gl_extract_clean.dat        ; echo exit=$?   # 0, load-ready
python convert.py ../data/gl_extract_unbalanced.dat   ; echo exit=$?   # 1, gate trips
```

If the unbalanced fixture ever exits `0`, the gate is broken — that is the whole
point of keeping a deliberately failing fixture in the suite.
