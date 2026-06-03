package com.cognition.jvdemo.labd20;

import com.cognition.jvdemo.dateconv.DateConvFunctions;
import com.cognition.jvdemo.dateconv.Status;
import com.cognition.jvdemo.db.DbDispatcher;
import com.cognition.jvdemo.db.DispatcherResult;
import com.cognition.jvdemo.db.SqlCodeTranslator;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

/**
 * Java port of source/procobol/LABD20.pco — the daily JV comment ingestion
 * program. It reads a process date from CARDFILE, streams fixed-width 300-byte
 * TST123-COMMENT-REC records, validates each, skips duplicates, INSERTs accepted
 * rows into JC_SUBMITTED_COMMENT_TBL, updates JC_COUNT_TBL, commits, and reports.
 *
 * <p>Faithful port of labd20_loader.py. On any DB error it rolls back and raises
 * {@link LoaderAbortedException}, mirroring the 9999-ROLL-BACK section.
 */
public final class Labd20Loader {

    private static final Logger LOG = Logger.getLogger(Labd20Loader.class.getName());

    static final String INSERT_SQL =
            "INSERT INTO JC_SUBMITTED_COMMENT_TBL ("
            + "JC_SUBMITTED, JC_SUBMITTED_NUMBER, JC_SUBMITTED_SCHED_DOC_NO, "
            + "JC_SUBMITTED_COMMENT_HIST, JC_SUBMITTED_COMMENT_REQUESTOR, "
            + "JC_SUBMITTED_COMMENT_APPROVER, JC_SUBMITTED_CONTROL_NUM, "
            + "JC_SUBMITTED_UPDT_PROG_ID, JC_SUBMITTED_UPDT_PROG_DT) "
            + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)";  // LABD20.pco:352-372

    static final String SELECT_DUPE_SQL =
            "SELECT JC_SUBMITTED_NUMBER FROM JC_SUBMITTED_COMMENT_TBL "
            + "WHERE JC_SUBMITTED = ?";  // LABD20.pco:325-330

    static final String UPDATE_COUNT_SQL =
            "UPDATE JC_COUNT_TBL SET JC_COUNT_NUM = ? WHERE JC_SECTION = ?";  // LABD20.pco:398-401

    static final String SELECT_COUNT_FOR_SECTION_SQL =
            "SELECT JC_COUNT_NUM FROM JC_COUNT_TBL WHERE JC_SECTION = ?";

    private final DbDispatcher dispatcher;
    private final LoaderStats stats = new LoaderStats();

    public Labd20Loader(DbDispatcher dispatcher) {
        this.dispatcher = dispatcher;
    }

    public LoaderStats stats() {
        return stats;
    }

    /** Raised by the fatal-rollback path (LABD20.pco:489+) after rollback. */
    public static final class LoaderAbortedException extends RuntimeException {
        public LoaderAbortedException(String message) {
            super(message);
        }
    }

    // -----------------------------------------------------------------------
    // Mainline (LABD20.pco:208-220).
    // -----------------------------------------------------------------------
    public LoaderStats run(LoaderConfig config) {
        String processDate = readProcessDate(config.cardPath());
        stats.processDate = processDate;
        LOG.info("PROCESS DATE = " + processDate);

        try {
            for (String raw : iterRecords(config.commentPath())) {
                handleRecord(raw, processDate);
            }
            postProcess(config.sectionForCount());
            commitEnvironment();

            if (config.truncateAfterProcessing()) {
                truncateFile(config.commentPath());
            }
        } catch (LoaderAbortedException ex) {
            // Already rolled back in fatalRollback(); bubble up.
            throw ex;
        } catch (RuntimeException exc) {
            // Mirror the 9999-ROLL-BACK fall-through behavior.
            LOG.severe("LABD20: unexpected error — rolling back: " + exc);
            dispatcher.rollback();
            throw new LoaderAbortedException("LABD20 aborted: " + exc.getMessage());
        }
        return stats;
    }

    // ------- per-record processing -----------------------------------------
    private void handleRecord(String raw, String processDate) {
        stats.totalRead += 1;
        CommentRecord record;
        try {
            record = CommentRecord.parse(raw);
        } catch (IllegalArgumentException exc) {
            stats.rejected += 1;
            stats.rejectedReasons.add("parse error: " + exc.getMessage());
            return;
        }

        List<String> reasons = determineDisposition(record);
        if (!reasons.isEmpty()) {
            stats.rejected += 1;
            stats.rejectedReasons.addAll(reasons);
            LOG.info("REJECTED " + record.submittedKey() + " reasons=" + reasons);
            return;
        }

        // Duplicate check (LABD20.pco:317-339).
        DispatcherResult dupe = dispatcher.selectOne(SELECT_DUPE_SQL, record.submittedKey());
        if (!SqlCodeTranslator.DMS_OK.equals(dupe.rtncodeDms)
                && !SqlCodeTranslator.DMS_NOT_FOUND.equals(dupe.rtncodeDms)) {
            fatalRollback("duplicate-check failed dms=" + dupe.rtncodeDms + " sqlcode=" + dupe.sqlcode);
        }

        if (dupe.isOk()) {
            stats.duplicates += 1;
            LOG.info("DUPLICATE ENTRY " + record.submittedKey());
            return;
        }

        insert(record, processDate);
    }

    private void insert(CommentRecord record, String processDate) {
        // CREATE-COMMENT-RECORD path (LABD20.pco:342-389).
        stats.accepted += 1;
        // ASSUMPTION A-7: JC_SUBMITTED_NUMBER is a monotonic in-batch counter
        // equal to the accepted count, mirroring WS-JV-COUNTER (LABD20.pco:345).
        int jcNumber = stats.accepted;
        DispatcherResult result = dispatcher.insert(INSERT_SQL,
                record.submittedKey(),
                jcNumber,
                record.scheduleDocNo(),
                record.commentHist(),
                record.requestor(),
                record.approver(),
                record.controlNum(),
                "LABD20",
                formatProcessDate(processDate));
        if (!result.isOk()) {
            fatalRollback("INSERT failed dms=" + result.rtncodeDms + " sqlcode=" + result.sqlcode);
        }
        stats.inserted += 1;
    }

    // ------- post-process (LABD20.pco:392-405) -----------------------------
    private void postProcess(String section) {
        DispatcherResult existing = dispatcher.selectOne(SELECT_COUNT_FOR_SECTION_SQL, section);
        int prior = (existing.isOk() && !existing.rows.isEmpty())
                ? ((Number) existing.rows.get(0).get(0)).intValue() : 0;
        if (stats.accepted <= prior) {
            LOG.info("POST-PROCESS: counter " + stats.accepted + " not greater than prior "
                    + prior + " — skip update");
            return;
        }
        DispatcherResult result = dispatcher.update(UPDATE_COUNT_SQL, stats.accepted, section);
        if (!result.isOk()) {
            fatalRollback("JC_COUNT_TBL UPDATE failed dms=" + result.rtncodeDms
                    + " sqlcode=" + result.sqlcode);
        }
    }

    // ------- close-sql-environment + stats (LABD20.pco:408-446) ------------
    private void commitEnvironment() {
        DispatcherResult commit = dispatcher.commit();
        if (!commit.isOk()) {
            fatalRollback("COMMIT failed dms=" + commit.rtncodeDms + " sqlcode=" + commit.sqlcode);
        }
        stats.submittedTotal = dispatcher.countRows("JC_SUBMITTED_COMMENT_TBL");
        stats.rejectedTotal = dispatcher.countRows("JC_REJECTED_COMMENT_TBL");
        stats.appliedTotal = dispatcher.countRows("JC_APPLIED_COMMENT_TBL");
        LOG.info("\n" + stats.formatReport());
    }

    private void fatalRollback(String message) {
        // Mirror the 9999-ROLL-BACK section (LABD20.pco:489+).
        LOG.severe("LABD20: " + message + " — rolling back");
        dispatcher.rollback();
        throw new LoaderAbortedException(message);
    }

    // -----------------------------------------------------------------------
    // Parsing, validation, and file helpers (static, mirror module functions).
    // -----------------------------------------------------------------------

    /** CHECK-CYMD-DT (PERFORM at LABD20.pco:267) → DATECONV func 1. */
    public static boolean checkCymdDt(String yyyymmdd) {
        return DateConvFunctions.checkCymdDt(yyyymmdd).status().equals(Status.OK);
    }

    /** Apply the validation rules from LABD20.pco:261-307. Empty list = valid. */
    public static List<String> determineDisposition(CommentRecord record) {
        List<String> reasons = new ArrayList<>();

        if (record.raw().strip().isEmpty()) {
            reasons.add("blank record");
        }

        if (!isDigits(record.commentDt())) {
            reasons.add("comment date is non-numeric");
        } else if (!checkCymdDt(record.commentDt())) {
            reasons.add("comment date is not a valid YYYYMMDD calendar date");
        }

        if (!(isDigits(record.jvNumber()) && Long.parseLong(record.jvNumber()) > 0)) {
            reasons.add("JV number is non-numeric or zero");
        }

        if (!isDigits(record.sectionId())) {
            reasons.add("section id is non-numeric");
        }

        if (!isDigits(record.loanNumber())) {
            reasons.add("loan number is non-numeric");
        }

        if (record.commentText().strip().isEmpty()) {
            reasons.add("comment text is blank");
        }

        if (record.requestor().strip().isEmpty()) {
            reasons.add("requestor is blank");
        }

        if (record.approver().strip().isEmpty()) {
            reasons.add("approver is blank");
        }

        return reasons;
    }

    /** Read the MM/DD/CCYY date from CARDFILE and reshuffle to YYYYMMDD (LABD20.pco:224-232). */
    public static String readProcessDate(Path cardPath) {
        String text;
        try {
            text = Files.readString(cardPath, StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        String firstLine = text.strip().split("\n", -1)[0];
        String mmDdCcyy = firstLine.length() >= 10 ? firstLine.substring(0, 10) : firstLine;
        String[] parts = mmDdCcyy.split("/");
        if (parts.length != 3) {
            throw new IllegalArgumentException("CARDFILE date must be MM/DD/CCYY; got '" + mmDdCcyy + "'");
        }
        String mm = parts[0], dd = parts[1], ccyy = parts[2];
        if (!(isDigits(mm) && isDigits(dd) && isDigits(ccyy))) {
            throw new IllegalArgumentException(
                    "CARDFILE date components must be numeric; got [" + mm + ", " + dd + ", " + ccyy + "]");
        }
        return ccyy + mm + dd;
    }

    /** Yield each 300-byte fixed-width record in COMMENT-FILE (LABD20.pco:247-253). */
    public static List<String> iterRecords(Path commentPath) {
        List<String> out = new ArrayList<>();
        List<String> lines;
        try {
            lines = Files.readAllLines(commentPath, StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
        for (String raw : lines) {
            raw = stripTrailingNewlines(raw);
            if (raw.isEmpty()) {
                continue;
            }
            if (raw.length() < CommentRecord.TST123_RECORD_LENGTH) {
                raw = padRight(raw, CommentRecord.TST123_RECORD_LENGTH);
            } else if (raw.length() > CommentRecord.TST123_RECORD_LENGTH) {
                raw = raw.substring(0, CommentRecord.TST123_RECORD_LENGTH);
            }
            out.add(raw);
        }
        return out;
    }

    /** Mirror the OPEN OUTPUT / CLOSE truncate at LABD20.pco:215-218. */
    public static void truncateFile(Path commentPath) {
        try {
            Files.writeString(commentPath, "", StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    static String formatProcessDate(String yyyymmdd) {
        // LABD20.pco:371 uses TO_DATE(:WS-PROCESS-DATE,'YYYYMMDD'); demo stores ISO text.
        if (yyyymmdd.length() != 8 || !isDigits(yyyymmdd)) {
            return yyyymmdd;
        }
        return yyyymmdd.substring(0, 4) + "-" + yyyymmdd.substring(4, 6) + "-" + yyyymmdd.substring(6, 8);
    }

    private static boolean isDigits(String s) {
        if (s == null || s.isEmpty()) {
            return false;
        }
        for (int i = 0; i < s.length(); i++) {
            if (!Character.isDigit(s.charAt(i))) {
                return false;
            }
        }
        return true;
    }

    private static String stripTrailingNewlines(String s) {
        int end = s.length();
        while (end > 0 && (s.charAt(end - 1) == '\n')) {
            end--;
        }
        while (end > 0 && (s.charAt(end - 1) == '\r')) {
            end--;
        }
        return s.substring(0, end);
    }

    private static String padRight(String s, int len) {
        StringBuilder sb = new StringBuilder(s);
        while (sb.length() < len) {
            sb.append(' ');
        }
        return sb.toString();
    }
}
