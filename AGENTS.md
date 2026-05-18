# Agent Instructions

This repo is a private Guidehouse/VA COBOL modernization demo workspace.

## Priorities

- Preserve original supplied source semantics; do not rewrite source files unless explicitly asked.
- For analysis tasks, cite source paths and line ranges when deriving requirements or conversion logic.
- Treat `source/` and `database/descriptions/` as the authoritative customer-provided inputs.
- Put generated analysis in `analysis/`, requirements in `business-requirements/`, and generated code in `converted-code/`.

## COBOL Modernization Notes

- Resolve copybooks and embedded SQL before deriving behavior.
- Pay close attention to fixed-width layouts, `REDEFINES`, numeric formats, and binary/COMP usage.
- Track missing dependencies explicitly; `DATECONV-WS` and `DATECONV-PD` are referenced but not supplied.
- Prefer minimal, auditable conversion examples over broad rewrites.

## Security Constraints

- Do not commit credentials, customer secrets, or runtime Oracle login files.
- Modernized DB code must use parameterized queries and managed configuration/secrets.
- Generated services must default-deny access, use generic external errors, and include audit logging for security-relevant operations.
