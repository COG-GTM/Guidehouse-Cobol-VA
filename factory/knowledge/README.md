# Knowledge Fabric

This directory is the factory's **learning memory**: domain knowledge, conversion
patterns, and reject corrections that grow with every run. Each file is a
knowledge note that Devin sessions read at startup and append to after
processing — this is stage S8 ("learn") from `factory/design/FACTORY-DESIGN.md`.

| File | Purpose |
| --- | --- |
| `domain-ussgl-tafs-funds.md` | USSGL, TAFS, fund conventions for VA financials. |
| `conversion-patterns-cobol.md` | Patterns for fixed-width, REDEFINES, COMP, dates. |
| `reject-taxonomy.md` | The growing taxonomy of reject reasons + resolutions. |
| `momentum-target-contracts.md` | Notes on Momentum's import formats/rules. |

## Why this structure

A child session converting interface #47 should start with all the patterns
learned from interfaces #1–46, without re-discovering them. That accumulated
knowledge, injected as context, is why the factory speeds up — fewer rejects,
higher first-pass coverage, less SME time per wave.

## How to use

- **Read first.** At the top of any conversion session, read the relevant
  knowledge files before writing any mapper logic.
- **Append after.** After a run, record any new reject pattern, SME correction,
  or mapping decision that generalizes.
- **Don't delete.** Even superseded patterns may resurface with a layout change
  in a later wave. Archive rather than remove.
