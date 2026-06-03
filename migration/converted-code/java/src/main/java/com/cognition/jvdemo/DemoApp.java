package com.cognition.jvdemo;

import com.cognition.jvdemo.db.DbDispatcher;
import com.cognition.jvdemo.db.DemoSchema;
import com.cognition.jvdemo.laba05.Laba05Reset;
import com.cognition.jvdemo.laba05.ResetOutcome;
import com.cognition.jvdemo.labd20.Labd20Loader;
import com.cognition.jvdemo.labd20.LoaderConfig;
import com.cognition.jvdemo.labd20.LoaderStats;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/**
 * Runnable demo entrypoint for the modernized JV comment loader and FY-reset
 * utilities — Java analog of demo_app.py (the {@code run} sub-command).
 *
 * <p>Zero-setup: it builds an in-memory sqlite mock of Oracle, seeds the demo
 * schema + control record, runs LABA05 (FY reset) then LABD20 (comment loader)
 * against the bundled synthetic data, and prints a structured report.
 *
 * <pre>
 *   mvn -q exec:java -Dexec.mainClass=com.cognition.jvdemo.DemoApp -Dexec.args="run"
 *   java -cp ... com.cognition.jvdemo.DemoApp run [--card P] [--comments P] [--work-dir D]
 * </pre>
 *
 * <p>The HTML {@code serve} dashboard from the Python demo is intentionally not
 * ported; the {@code run} report covers the same workflow.
 */
public final class DemoApp {

    private DemoApp() {}

    /** Tables surfaced in the demo's post-run summary (static literals). */
    private static final String[] DISPLAY_TABLES = {
        "CONTROL_RECORD_TABLE",
        "JC_SUBMITTED_COMMENT_TBL",
        "JC_COUNT_TBL",
    };

    public static void main(String[] args) {
        int rc = run(args);
        if (rc != 0) {
            System.exit(rc);
        }
    }

    static int run(String[] args) {
        if (args.length == 0 || !"run".equals(args[0])) {
            System.err.println("usage: DemoApp run [--card PATH] [--comments PATH] [--work-dir DIR]");
            return 2;
        }

        Path card = null;
        Path comments = null;
        Path workDir = null;
        for (int i = 1; i < args.length; i++) {
            switch (args[i]) {
                case "--card" -> card = Path.of(args[++i]);
                case "--comments" -> comments = Path.of(args[++i]);
                case "--work-dir" -> workDir = Path.of(args[++i]);
                default -> {
                    System.err.println("unknown argument: " + args[i]);
                    return 2;
                }
            }
        }

        Path testData = locateTestData();
        if (card == null) {
            card = testData.resolve("synthetic_card.ctl");
        }
        if (comments == null) {
            comments = testData.resolve("synthetic_comments.dat");
        }
        if (workDir == null) {
            workDir = testData.resolveSibling("test-results").resolve("demo-run-java");
        }

        Path commentsCopy = copyComments(comments, workDir);

        try (DbDispatcher dispatcher = buildDispatcherWithSeed(99)) {
            ResetOutcome reset = Laba05Reset.run(dispatcher);

            Labd20Loader loader = new Labd20Loader(dispatcher);
            LoaderStats stats = loader.run(new LoaderConfig(card, commentsCopy, true));

            printReport(dispatcher, reset, stats);
        }
        return 0;
    }

    private static DbDispatcher buildDispatcherWithSeed(int seedJv) {
        DbDispatcher dispatcher = DbDispatcher.newSqlite(":memory:");
        DemoSchema.buildDemoSchema(dispatcher);
        DemoSchema.seedControlRecord(dispatcher, seedJv);
        // Seed JC_COUNT_TBL row for section 'MA' so post-process has a baseline (A-10).
        dispatcher.insert("INSERT INTO JC_COUNT_TBL (JC_SECTION, JC_COUNT_NUM) VALUES (?, ?)", "MA", 0);
        dispatcher.commit();
        return dispatcher;
    }

    private static void printReport(DbDispatcher dispatcher, ResetOutcome reset, LoaderStats stats) {
        String line = "=".repeat(72);
        System.out.println(line);
        System.out.println("Cognition x Guidehouse — JV COBOL modernization demo (Java)");
        System.out.println(line);
        System.out.println("Process date           : " + stats.processDate);
        System.out.println();
        System.out.println("LABA05 fiscal-year reset");
        System.out.println("  return code          : " + reset.returnCode());
        System.out.println("  JV-NUMBER before     : " + reset.beforeJvNumber());
        System.out.println("  JV-NUMBER after      : " + reset.afterJvNumber());
        System.out.println("  message              : " + reset.message());
        System.out.println();
        System.out.println("LABD20 comment loader");
        System.out.println("  records read         : " + stats.totalRead);
        System.out.println("  inserted             : " + stats.inserted);
        System.out.println("  duplicates           : " + stats.duplicates);
        System.out.println("  rejected             : " + stats.rejected);
        System.out.println("  submitted total      : " + stats.submittedTotal);
        System.out.println();
        System.out.println("Rejection reasons (first 12):");
        List<String> reasons = stats.rejectedReasons;
        for (int i = 0; i < Math.min(12, reasons.size()); i++) {
            System.out.println("  - " + reasons.get(i));
        }
        System.out.println();
        System.out.println("Mock-DB final state:");
        for (String table : DISPLAY_TABLES) {
            System.out.println("  [" + table + "]: " + dispatcher.countRows(table) + " row(s)");
        }
        System.out.println();
        System.out.println(stats.formatReport());
    }

    private static Path copyComments(Path source, Path workDir) {
        try {
            Files.createDirectories(workDir);
            Path target = workDir.resolve("comments.dat");
            Files.write(target, Files.readAllBytes(source));
            return target;
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    /** Walk up from the working directory to find migration/test-data. */
    private static Path locateTestData() {
        Path cur = Path.of("").toAbsolutePath();
        for (int i = 0; i < 8 && cur != null; i++) {
            Path candidate = cur.resolve("migration").resolve("test-data");
            if (Files.isDirectory(candidate)) {
                return candidate;
            }
            cur = cur.getParent();
        }
        // Fallback: relative path from repo root.
        return Path.of("migration", "test-data");
    }
}
