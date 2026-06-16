# Packaging proposal — eliminating the factory's sys.path hacks

**Status:** Proposal only. No refactor performed; the inventory below is the
current state as of this document's commit.

## Problem

The factory's Python modules are flat files wired together at runtime by
`sys.path.insert(...)` calls. Current call sites:

| Location | What it patches in |
| --- | --- |
| `factory/icd/icd_builder.py` | the obligation/disbursement slice's `python/` dir |
| `factory/icd/tests/test_icd.py` | `factory/icd/` itself |
| `factory/interface-inventory/tests/test_inventory.py` | `factory/interface-inventory/` itself |
| `factory/conversion-datasets/*/python/conftest.py` (×3) | each slice's own `python/` dir (and, for jv-comment-load, `migration/converted-code/`) |
| `factory/conversion-datasets/jv-comment-load/python/extract.py` | `migration/converted-code/` (Phase-1 loader reuse) |
| `factory/demos/learning-agent-demo/run_learning_demo.py` | the GL slice's `python/` dir |
| `factory/demos/audit-trail-viewer/generate_audit_trail.py` | a slice `python/` dir chosen at runtime |
| `factory/demos/interface-portfolio/build_portfolio_data.py` | `factory/interface-inventory/` |

Consequences:

- **Conftest clashes.** Each slice's `conftest.py` injects its own dir, and the
  flat module names collide (`mapper`, `convert`, `reconciliation` exist in
  three slices), so `pytest` from the repo root fails; each slice suite must be
  run from its own `python/` directory.
- **Import-order fragility.** Whichever slice patched `sys.path` last wins;
  the demos re-patch per run to choose a slice.
- **No static analysis.** IDEs/type-checkers can't resolve the imports, and
  ruff/mypy can't follow cross-module references.
- **Hidden coupling.** `jv-comment-load` reaching into
  `migration/converted-code/` is invisible to dependency tooling.

## Proposal

### 1. One installable package with unique module paths

Add a single `pyproject.toml` at the repo root declaring an installable
`fmbt-factory` package, and move (or alias) the flat modules under a proper
namespace so module names stop colliding:

```
factory_lib/
  inventory/          # from factory/interface-inventory/inventory.py
  icd/                # icd_builder.py, validate.py, generate_icd.py
  slices/
    gl_journal/       # gl-journal-extract/python/*.py
    jv_comment/       # jv-comment-load/python/*.py
    obl_disbursement/ # obligation-disbursement/python/*.py
  legacy/             # re-export of migration/converted-code (labd20_loader, dateconv)
```

```toml
[project]
name = "fmbt-factory"
version = "0"
requires-python = ">=3.10"

[tool.setuptools.packages.find]
include = ["factory_lib*"]
```

Imports become absolute and unique — `from factory_lib.slices.gl_journal
import mapper` — and every `sys.path.insert` is deleted. The blueprint's
`maintenance` step gains one line: `pip install -e .`.

The non-Python slice assets (`data/`, `source/`, `target/`) stay where they
are; modules locate them via `importlib.resources` or a repo-root anchor
constant instead of `Path(__file__)` hops.

### 2. The `migration/` dependency becomes explicit

`jv-comment-load`'s reuse of the Phase-1 loader
(`migration/converted-code/python/labd20_loader.py`, `dateconv.py`) is
formalized as `factory_lib.legacy`, a thin re-export module. The "before"
tree under `migration/` stays untouched (it is demo evidence); only the
import path is wrapped, so the factory's dependency on Phase-1 code is
visible to tooling and greppable in one place.

### 3. Tests run from the repo root

With unique package paths, the three slice `conftest.py` files are deleted
and `pytest` works from the root:

```toml
[tool.pytest.ini_options]
testpaths = [
  "factory_lib",
  "factory/icd/tests",
  "factory/interface-inventory/tests",
  "factory/knowledge/tests",
]
```

This removes the "run each suite from its own `python/` directory"
constraint and lets CI run one `pytest -q`.

### 4. Migration plan (mechanical, reviewable steps)

1. Add `pyproject.toml` + empty `factory_lib/` package; CI installs `-e .`.
2. Move one slice (GL, the reference slice) under
   `factory_lib/slices/gl_journal/`; fix its imports; keep a deprecation
   shim at the old path for one PR cycle.
3. Repeat for the other two slices, then `icd/` and `interface-inventory/`.
4. Delete the conftests and all `sys.path.insert` lines; turn on a lint rule
   (`ruff` `flake8-tidy-imports` banned-api or a grep-based CI check) that
   forbids reintroducing `sys.path.insert` under `factory/`.

Each step is independently green; no behavior changes; the demos'
"choose a slice at runtime" logic becomes a dict of imported modules instead
of path surgery.

## Non-goals

- No change to `migration/` (frozen before/after demo evidence).
- No change to slice data layouts, contracts, or the eight-stage model.
- No new third-party dependencies — packaging metadata only.
