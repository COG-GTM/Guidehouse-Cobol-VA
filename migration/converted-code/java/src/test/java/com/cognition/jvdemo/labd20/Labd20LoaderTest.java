package com.cognition.jvdemo.labd20;

import com.cognition.jvdemo.db.DbDispatcher;
import com.cognition.jvdemo.db.DemoSchema;
import com.cognition.jvdemo.db.DispatcherResult;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * JUnit 5 port of tests/test_labd20_loader.py. Exercises the 300-byte record
 * layout, validation rules, card-file parsing, and the end-to-end loader
 * against the bundled synthetic dataset (21 records).
 */
class Labd20LoaderTest {

    private static final Path TEST_DATA = locateTestData();
    private static final Path SYNTHETIC_DATA = TEST_DATA.resolve("synthetic_comments.dat");
    private static final Path SYNTHETIC_CARD = TEST_DATA.resolve("synthetic_card.ctl");

    private static Path locateTestData() {
        // Tests run with CWD = module dir; resources are under src/test/resources.
        Path res = Path.of("src", "test", "resources", "test-data");
        if (Files.isDirectory(res)) {
            return res.toAbsolutePath();
        }
        Path cur = Path.of("").toAbsolutePath();
        for (int i = 0; i < 8 && cur != null; i++) {
            Path c = cur.resolve("migration").resolve("test-data");
            if (Files.isDirectory(c)) {
                return c;
            }
            cur = cur.getParent();
        }
        return res.toAbsolutePath();
    }

    private static DbDispatcher freshDb() {
        DbDispatcher d = DbDispatcher.newSqlite(":memory:");
        DemoSchema.buildDemoSchema(d);
        d.insert("INSERT INTO JC_COUNT_TBL (JC_SECTION, JC_COUNT_NUM) VALUES (?, ?)", "MA", 0);
        d.commit();
        return d;
    }

    private static String pad(String s, int width) {
        StringBuilder sb = new StringBuilder(s == null ? "" : s);
        while (sb.length() < width) {
            sb.append(' ');
        }
        return sb.length() > width ? sb.substring(0, width) : sb.toString();
    }

    private static String makeRecord(String date, String jv, String section, String loan,
                                     String sched, String text, String requestor, String approver) {
        String s = pad(date, 8) + pad(jv, 6) + pad(section, 2) + pad(loan, 10)
                + pad(sched, 10) + pad(text, 230) + pad(requestor, 20) + pad(approver, 14);
        if (s.length() != CommentRecord.TST123_RECORD_LENGTH) {
            throw new IllegalStateException("makeRecord length=" + s.length());
        }
        return s;
    }

    private static String defaultRecord() {
        return makeRecord("20260101", "000100", "01", "9000000001",
                "SCH0000001", "Demo comment", "ALICE.SUBMITTER", "BOB.APPROVER");
    }

    // ---- record layout ----------------------------------------------------
    @Test void totalLengthIs300() {
        assertEquals(300, CommentRecord.TST123_RECORD_LENGTH);
    }

    @Test void sliceBoundariesAreContiguous() {
        int[][] b = {
            {CommentRecord.COMMENT_DT_START, CommentRecord.COMMENT_DT_STOP, 0, 8},
            {CommentRecord.JV_NUMBER_START, CommentRecord.JV_NUMBER_STOP, 8, 14},
            {CommentRecord.SECTION_ID_START, CommentRecord.SECTION_ID_STOP, 14, 16},
            {CommentRecord.LOAN_NUMBER_START, CommentRecord.LOAN_NUMBER_STOP, 16, 26},
            {CommentRecord.SCHEDULE_DOC_NO_START, CommentRecord.SCHEDULE_DOC_NO_STOP, 26, 36},
            {CommentRecord.COMMENT_TEXT_START, CommentRecord.COMMENT_TEXT_STOP, 36, 266},
            {CommentRecord.REQUESTOR_START, CommentRecord.REQUESTOR_STOP, 266, 286},
            {CommentRecord.APPROVER_START, CommentRecord.APPROVER_STOP, 286, 300},
        };
        for (int[] row : b) {
            assertEquals(row[2], row[0]);
            assertEquals(row[3], row[1]);
        }
    }

    @Test void compositeLoanDtNrCoversFirst26Bytes() {
        assertEquals(0, CommentRecord.LOAN_DT_NR_START);
        assertEquals(26, CommentRecord.LOAN_DT_NR_STOP);
    }

    @Test void approverIs14Not20Bytes() {
        assertEquals(14, CommentRecord.APPROVER_STOP - CommentRecord.APPROVER_START);
    }

    // ---- parse ------------------------------------------------------------
    @Test void parsesEachFieldAtCorrectOffset() {
        CommentRecord rec = CommentRecord.parse(defaultRecord());
        assertEquals("20260101", rec.commentDt());
        assertEquals("000100", rec.jvNumber());
        assertEquals("01", rec.sectionId());
        assertEquals("9000000001", rec.loanNumber());
        assertEquals("20260101000100019000000001", rec.loanDtNr());
        assertEquals("SCH0000001", rec.scheduleDocNo());
        assertEquals("Demo comment", rec.commentText().strip());
        assertEquals("ALICE.SUBMITTER", rec.requestor().strip());
        assertEquals("BOB.APPROVER", rec.approver().strip());
    }

    @Test void rejectsWrongLength() {
        assertThrows(IllegalArgumentException.class, () -> CommentRecord.parse("X".repeat(299)));
    }

    @Test void controlNumConcatenatesJvAndSection() {
        CommentRecord rec = CommentRecord.parse(makeRecord("20260101", "000123", "07",
                "9000000001", "SCH0000001", "Demo", "ALICE", "BOB"));
        assertEquals("00012307", rec.controlNum());
    }

    @Test void submittedKeyIsFirst26Bytes() {
        CommentRecord rec = CommentRecord.parse(defaultRecord());
        assertEquals(rec.raw().substring(0, 26), rec.submittedKey());
    }

    // ---- validation rules -------------------------------------------------
    @Test void blankRecordRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(" ".repeat(300)));
        assertFalse(r.isEmpty());
        assertTrue(r.contains("blank record"));
    }

    @Test void happyPathAccepted() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(defaultRecord()));
        assertTrue(r.isEmpty(), r.toString());
    }

    @Test void nonNumericDateRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(
                makeRecord("20XXXXXX", "000100", "01", "9000000001", "SCH0000001",
                        "Demo", "ALICE", "BOB")));
        assertTrue(r.stream().anyMatch(x -> x.contains("comment date")));
    }

    @Test void invalidCalendarDateRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(
                makeRecord("20261345", "000100", "01", "9000000001", "SCH0000001",
                        "Demo", "ALICE", "BOB")));
        assertTrue(r.stream().anyMatch(x -> x.contains("calendar")));
    }

    @Test void jvNumberZeroRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(
                makeRecord("20260101", "000000", "01", "9000000001", "SCH0000001",
                        "Demo", "ALICE", "BOB")));
        assertTrue(r.stream().anyMatch(x -> x.contains("JV number")));
    }

    @Test void jvNumberNonNumericRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(
                makeRecord("20260101", "ABC123", "01", "9000000001", "SCH0000001",
                        "Demo", "ALICE", "BOB")));
        assertTrue(r.stream().anyMatch(x -> x.contains("JV number")));
    }

    @Test void nonNumericSectionRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(
                makeRecord("20260101", "000100", "MA", "9000000001", "SCH0000001",
                        "Demo", "ALICE", "BOB")));
        assertTrue(r.stream().anyMatch(x -> x.contains("section id")));
    }

    @Test void nonNumericLoanRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(
                makeRecord("20260101", "000100", "01", "ABCDE12345", "SCH0000001",
                        "Demo", "ALICE", "BOB")));
        assertTrue(r.stream().anyMatch(x -> x.contains("loan number")));
    }

    @Test void blankCommentRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(
                makeRecord("20260101", "000100", "01", "9000000001", "SCH0000001",
                        "", "ALICE", "BOB")));
        assertTrue(r.stream().anyMatch(x -> x.contains("comment text")));
    }

    @Test void blankRequestorRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(
                makeRecord("20260101", "000100", "01", "9000000001", "SCH0000001",
                        "Demo", "", "BOB")));
        assertTrue(r.stream().anyMatch(x -> x.contains("requestor")));
    }

    @Test void blankApproverRejected() {
        List<String> r = Labd20Loader.determineDisposition(CommentRecord.parse(
                makeRecord("20260101", "000100", "01", "9000000001", "SCH0000001",
                        "Demo", "ALICE", "")));
        assertTrue(r.stream().anyMatch(x -> x.contains("approver")));
    }

    // ---- check_cymd_dt ----------------------------------------------------
    @Test void checkCymdValidDate() { assertTrue(Labd20Loader.checkCymdDt("20260101")); }

    @Test void checkCymdInvalidMonth() { assertFalse(Labd20Loader.checkCymdDt("20261301")); }

    @Test void checkCymdInvalidDay() { assertFalse(Labd20Loader.checkCymdDt("20260132")); }

    @Test void checkCymdLeapDayValid() { assertTrue(Labd20Loader.checkCymdDt("20240229")); }

    @Test void checkCymdNonLeapFeb29Invalid() { assertFalse(Labd20Loader.checkCymdDt("20250229")); }

    @Test void checkCymdNonNumeric() { assertFalse(Labd20Loader.checkCymdDt("2026010A")); }

    @Test void checkCymdWrongLength() { assertFalse(Labd20Loader.checkCymdDt("2026101")); }

    // ---- read process date ------------------------------------------------
    @Test void reshufflesMmddccyyToYyyymmdd(@TempDir Path tmp) throws IOException {
        Path card = tmp.resolve("card.ctl");
        Files.writeString(card, "03/15/2026\n", StandardCharsets.UTF_8);
        assertEquals("20260315", Labd20Loader.readProcessDate(card));
    }

    @Test void syntheticCardFileParses() {
        assertEquals("20260115", Labd20Loader.readProcessDate(SYNTHETIC_CARD));
    }

    @Test void rejectsMalformedCard(@TempDir Path tmp) throws IOException {
        Path card = tmp.resolve("card.ctl");
        Files.writeString(card, "2026-01-15\n", StandardCharsets.UTF_8);
        assertThrows(IllegalArgumentException.class, () -> Labd20Loader.readProcessDate(card));
    }

    // ---- end-to-end -------------------------------------------------------
    @Test void runsSyntheticDataset(@TempDir Path tmp) throws IOException {
        Path comments = tmp.resolve("comments.dat");
        Files.write(comments, Files.readAllBytes(SYNTHETIC_DATA));

        try (DbDispatcher db = freshDb()) {
            Labd20Loader loader = new Labd20Loader(db);
            LoaderStats stats = loader.run(new LoaderConfig(SYNTHETIC_CARD, comments, true));

            assertEquals(21, stats.totalRead);
            assertEquals(7, stats.inserted);
            assertEquals(2, stats.duplicates);
            assertEquals(21 - 7 - 2, stats.rejected);
            assertEquals(7, stats.submittedTotal);
            assertEquals(0, Files.size(comments));
        }
    }

    @Test void insertParameterMappingUsesAllNineColumns(@TempDir Path tmp) throws IOException {
        Path comments = tmp.resolve("one.dat");
        Files.writeString(comments,
                makeRecord("20260101", "000100", "01", "9000000001", "SCH0000001",
                        "single insert", "ALICE.SUBMITTER", "BOB.APPROVER") + "\n",
                StandardCharsets.UTF_8);

        try (DbDispatcher db = freshDb()) {
            new Labd20Loader(db).run(new LoaderConfig(SYNTHETIC_CARD, comments, false));

            DispatcherResult row = db.selectOne(
                    "SELECT JC_SUBMITTED, JC_SUBMITTED_NUMBER, JC_SUBMITTED_SCHED_DOC_NO, "
                    + "JC_SUBMITTED_COMMENT_HIST, JC_SUBMITTED_COMMENT_REQUESTOR, "
                    + "JC_SUBMITTED_COMMENT_APPROVER, JC_SUBMITTED_CONTROL_NUM, "
                    + "JC_SUBMITTED_UPDT_PROG_ID, JC_SUBMITTED_UPDT_PROG_DT "
                    + "FROM JC_SUBMITTED_COMMENT_TBL");
            assertTrue(row.isOk());
            List<Object> r = row.rows.get(0);
            assertTrue(((String) r.get(0)).startsWith("20260101000100019000000001"));
            assertEquals(1, ((Number) r.get(1)).intValue());
            assertEquals("SCH0000001", r.get(2));
            assertTrue(((String) r.get(3)).contains("single insert"));
            assertEquals("ALICE.SUBMITTER", ((String) r.get(4)).strip());
            assertEquals("BOB.APPROVER", ((String) r.get(5)).strip());
            assertEquals("00010001", r.get(6));
            assertEquals("LABD20", r.get(7));
            assertEquals("2026-01-15", r.get(8));
            assertEquals(1, db.countRows("JC_SUBMITTED_COMMENT_TBL"));
        }
    }

    @Test void duplicateRecordDoesNotInsertTwice(@TempDir Path tmp) throws IOException {
        Path comments = tmp.resolve("dupes.dat");
        String rec = defaultRecord();
        Files.writeString(comments, rec + "\n" + rec + "\n", StandardCharsets.UTF_8);

        try (DbDispatcher db = freshDb()) {
            LoaderStats stats = new Labd20Loader(db)
                    .run(new LoaderConfig(SYNTHETIC_CARD, comments, false));
            assertEquals(1, stats.inserted);
            assertEquals(1, stats.duplicates);
        }
    }

    @Test void rollbackOnInsertFailure(@TempDir Path tmp) throws IOException {
        Path comments = tmp.resolve("one.dat");
        Files.writeString(comments, defaultRecord() + "\n", StandardCharsets.UTF_8);

        try (DbDispatcher db = freshDb()) {
            db.update("DROP TABLE JC_SUBMITTED_COMMENT_TBL");
            db.commit();
            Labd20Loader loader = new Labd20Loader(db);
            assertThrows(Labd20Loader.LoaderAbortedException.class,
                    () -> loader.run(new LoaderConfig(SYNTHETIC_CARD, comments, false)));
        }
    }

    // ---- truncate ---------------------------------------------------------
    @Test void truncateFileZerosIt(@TempDir Path tmp) throws IOException {
        Path f = tmp.resolve("data.dat");
        Files.writeString(f, "not empty\n", StandardCharsets.UTF_8);
        Labd20Loader.truncateFile(f);
        assertEquals("", Files.readString(f, StandardCharsets.UTF_8));
    }
}
