# Momentum target contracts

> **Status:** the contract below is a **plausible reconstruction** built from
> public knowledge of federal core-financial import patterns, not CGI's actual
> Momentum ICD. The real layouts are Q-MOM-1 / Q-MOM-2 in
> `docs/va-fmbt-open-questions.md` and are the factory's critical-path dependency.

## What we know from open sources

- Momentum® is CGI's FM QSMO-approved federal core financial management suite
  (<https://www.cgi.com/en/momentum>); VA iFAMS is built on it.
- Federal core-financial imports are typically **batch, file-based**, with a
  header/detail/trailer structure, control totals in the trailer, and
  USSGL-posted double-entry journals. The factory assumes this shape until told
  otherwise.

## The reconstructed journal-import contract

The canonical target record the GL slice converts to is documented in
`factory/conversion-datasets/gl-journal-extract/target/MOMENTUM-JOURNAL-IMPORT.md`.
Summary of its rules:

- **Per-line rules:** numeric integrity; DR/CR indicator present; non-zero
  amount; USSGL on the approved chart; valid posting date; non-empty TAFS/fund.
- **Journal-level rules:** Σ debits == Σ credits per `journal_id`; control totals
  preserved; row accounting closed.
- **Wire format:** pipe-delimited, one line per `MomentumJournalLine`, header row
  naming columns.

## Open contract questions to resolve before production

1. Exact field names, types, lengths, and required/optional flags (Q-MOM-1).
2. Header/trailer/control-record structure and what control totals Momentum
   expects (Q-MOM-1).
3. Momentum's own validation + reject behavior, and whether partial batch loads
   are allowed (Q-MOM-2).
4. Transport: SFTP drop vs Azure storage vs Momentum API (Q-MOM-3).
5. Availability of a non-prod Momentum instance for real load rehearsal (Q-MOM-4).

## When the real ICD arrives

Replace the reconstructed contract file, re-point the mapper's field bindings,
and re-run the contract tests. Because the factory always targets an explicit
versioned contract (never "legacy → vibes"), swapping in the real ICD is a
localized change: the parser, reconciliation engine, and CI gate are unaffected.
