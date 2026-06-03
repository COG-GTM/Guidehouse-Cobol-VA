# JV COBOL modernization — Java 21 port

Java 21 + Maven port of the JV comment-processing workflow, functionally
equivalent to the Python port under `migration/converted-code/python/`. Source
COBOL lives under `source/cobol/`; this is reviewed demo code (see `AGENTS.md`).

## Modules

| COBOL source        | Java package / class                                   | Role |
|---------------------|--------------------------------------------------------|------|
| `DATECONV.cbl`      | `com.cognition.jvdemo.dateconv.DateConv` (+ `ConvDates`, `Status`) | 42 DATESUB-FUNC date routines via a dispatch engine |
| (convenience API)   | `com.cognition.jvdemo.dateconv.DateConvFunctions`      | Typed wrappers (`checkCymdDt`, `ymdToJul`, `difFy`, `addMonthsToCymd`, …) |
| `DBIO.pco`          | `com.cognition.jvdemo.db.DbDispatcher` (+ `DispatcherResult`, `SqlCodeTranslator`, `DemoSchema`) | JDBC abstraction + SQLCODE→DMS translation |
| `LABA05.cbl`        | `com.cognition.jvdemo.laba05.Laba05Reset` (+ `ResetOutcome`) | Fiscal-year JV-NUMBER reset |
| `LABD20.pco`        | `com.cognition.jvdemo.labd20.Labd20Loader` (+ `CommentRecord`, `LoaderStats`, `LoaderConfig`) | Daily 300-byte JV-comment loader |
| `demo_app.py`       | `com.cognition.jvdemo.DemoApp`                          | Zero-setup CLI demo (in-memory sqlite) |

## Build & test

```bash
cd migration/converted-code/java
mvn test          # 123 JUnit 5 tests
```

## Run the demo

```bash
mvn -q dependency:build-classpath -Dmdep.outputFile=/tmp/cp.txt
java -cp "target/classes:$(cat /tmp/cp.txt)" com.cognition.jvdemo.DemoApp run
```

The demo builds an in-memory sqlite mock of Oracle, runs LABA05 (FY reset) then
LABD20 (loader) over the synthetic fixture in `migration/test-data/`, and prints
a report identical to the Python `demo_app.py run`.

## Fidelity notes

- One COBOL paragraph → one Java method (camelCase) for traceability.
- `PIC 9(n)` → `long`; no floating point in date/financial math.
- Fixed-width `TST123-COMMENT-REC` parsed by explicit byte offsets (0-based,
  end-exclusive) matching the Python slices.
- Status codes (`OK`/`OutOfRange*`/`Strange`) and DMS codes
  (`0000`/`0013`/`0007`/`0005`/`9999`) preserved verbatim.
- `java.time.LocalDate` (proleptic Gregorian) anchored on the COBOL
  `INTEGER-OF-DATE` epoch (1601-01-01 = day 1).
- 30-day-month accounting: years = 360 days, months = 30 days.
```
