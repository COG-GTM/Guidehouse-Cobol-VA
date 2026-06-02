# Source record layout — `TST123-COMMENT-REC` (300 bytes, fixed-width)

This slice does **not** copy the legacy copybook. It reuses the real artifacts
already in this repository so there is exactly one source of truth:

| Artifact | Path | Role |
| --- | --- | --- |
| Legacy program | `source/procobol/LABD20.pco` | Daily JV-comment ingestion (the "before"). |
| Record layout | `source/procobol/LABD20.pco:43-55` | `TST123-COMMENT-REC` field definitions. |
| Date subprogram | `source/cobol/DATECONV.cbl` + `source/copybooks/DATECONV-*.cpy` | `CHECK-CYMD-DT` calendar validation. |
| Modernized parser | `migration/converted-code/python/labd20_loader.py:95-141` | Phase-1 Python port (byte offsets + `CommentRecord`). |
| Modernized date check | `migration/converted-code/python/dateconv.py` | Phase-1 port of `DATECONV`. |
| Real fixture | `migration/test-data/synthetic_comments.dat` | 21 synthetic non-production records. |

## Byte map (cited to `labd20_loader.py:95-104`, which cites `LABD20.pco:43-55`)

| Field | Offset `[start, end)` | PIC | Notes |
| --- | --- | --- | --- |
| `COMMENT-DT` | `[0, 8)` | `9(008)` | YYYYMMDD; validated by DATECONV `CHECK-CYMD-DT`. |
| `JV-NUMBER` | `[8, 14)` | `9(006)` | Must be numeric and > 0. |
| `SECTION-ID` | `[14, 16)` | `9(002)` | Must be numeric. |
| `LOAN-NUMBER` | `[16, 26)` | `9(010)` | Must be numeric. |
| `LOAN-DT-NR` | `[0, 26)` | redefine | **26-byte composite key** = `JC_SUBMITTED` (LABD20.pco:329). |
| `SCHEDULE-DOC-NO` | `[26, 36)` | `X(010)` | |
| `COMMENT-TEXT` | `[36, 266)` | `X(230)` | Must be non-blank. |
| `COMMENT-HIST` | `[26, 266)` | redefine | `SCHED-DOC-NO` + `TEXT`. |
| `REQUESTOR` | `[266, 286)` | `X(020)` | Must be non-blank. |
| `APPROVER` | `[286, 300)` | `X(014)` | 14 bytes (LABD20.pco:55 — **not** the commented 20-byte line 54). |

## The eight legacy edits (reused verbatim from Phase-1)

`determine_disposition` (`labd20_loader.py`, port of `LABD20.pco:261-307`) applies,
in order: blank-record, comment-date numeric, comment-date valid calendar
(DATECONV), JV-number numeric & non-zero, section-id numeric, loan-number numeric,
comment-text non-blank, requestor non-blank, approver non-blank. The factory maps
each prose reason to a typed reject code (see `factory/knowledge/reject-taxonomy.md`).

## Duplicate handling (reused dedup semantics)

The legacy program checks `JC_SUBMITTED_COMMENT_TBL` for an existing row on the
26-byte `JC_SUBMITTED` key before insert (LABD20.pco:317-339). The factory mirrors
this: within a batch, the first record for a key is loaded and later records with
the same key are held in the duplicate ledger — never loaded twice.

> All data referenced here is synthetic / non-production (per `AGENTS.md`).
