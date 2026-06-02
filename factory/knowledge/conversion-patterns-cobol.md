# Conversion patterns: COBOL fixed-width data

> These are the patterns the factory uses when parsing legacy COBOL-defined
> records. Accumulated from the GL slice and the upstream migration work.

## Fixed-width record parsing

COBOL `FD`/`01` copybooks define fixed-length records byte-by-byte. The parser
must:

- **Tile exactly.** Field offsets + widths must sum to the declared record
  length, with no gaps or overlaps. The GL slice has a test for this.
- **Pad short records.** If a file delivers records shorter than declared, the
  parser pads with spaces to record length before slicing — avoids index errors
  on ragged files while preserving the real data.
- **Strip trailing spaces, preserve leading content.** Trailing spaces are
  filler; leading characters (including zeros) are significant.

## Numeric conventions

| Convention | COBOL PIC | How to parse |
| --- | --- | --- |
| Zoned numeric | `PIC 9(n)` / `PIC 9(n)V9(m)` | ASCII digits; implied decimal means the last `m` digits are fractional. Use `Decimal`, never `float`. |
| Packed decimal (COMP-3) | `PIC S9(n)V9(m) COMP-3` | Each byte is two BCD digits; low nibble of last byte is sign (`C`/`D`/`F`). Length = `ceil((n+m+1)/2)` bytes. |
| Binary (COMP/COMP-5) | `PIC S9(n) COMP` | Big-endian 2/4/8-byte integer. |
| Display numeric (signed) | `PIC S9(n)` | Sign is overpunch on the last digit (EBCDIC zone). |

The GL slice uses zoned numeric (`PIC 9(13)V99`). If you encounter COMP-3 or
binary, decode them before mapping — they are not printable ASCII.

## REDEFINES

A `REDEFINES` gives an alternative layout over the same byte range. The parser
must pick the right redefinition based on a discriminator field (record-type
indicator). Parse both layouts and select downstream.

## Date conventions

| Convention | COBOL field | Conversion |
| --- | --- | --- |
| Julian ordinal `CCYYDDD` | `PIC 9(07)` | `datetime.date.fromordinal(ddd)` in year `CCYY`. Valid range: 1–365 (366 in leap year). The GL slice and `dateconv.py` both handle this. |
| Calendar `CCYYMMDD` | `PIC 9(08)` | Direct parse. Validate month 1–12, day 1–{28,29,30,31}. |
| Julian 5-digit `YYDDD` | `PIC 9(05)` | 2-digit year windowing (>50 = 19xx, else 20xx). |

Always validate before converting — an invalid date becomes a `BAD_DATE` reject,
not a runtime exception.

## EBCDIC vs ASCII

If the legacy extract lands as EBCDIC (not yet code-page-converted), the parser
must apply EBCDIC→ASCII translation *before* field slicing. The GL slice assumes
already-landed ASCII; confirm per Q-GL-2.

## Lessons from the upstream migration

- `DATECONV.cbl` implements 42 date functions via a `DATESUB-FUNC` dispatch code
  (`analysis/dateconv-function-inventory.md`). The Python port is in
  `migration/converted-code/python/dateconv.py` and passes 130+ edge-case tests.
- `LABD20`'s fixed-width parsing of `TST123-COMMENT-REC` is the same pattern as
  the GL extract parser — same principles, different layout.
- Duplicate detection (LABD20's `JC_SUBMITTED_COMMENT_TBL` check) maps to the
  factory's duplicate/replay detection (test angle #9).
