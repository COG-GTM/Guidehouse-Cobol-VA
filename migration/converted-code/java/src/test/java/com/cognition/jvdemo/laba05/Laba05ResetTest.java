package com.cognition.jvdemo.laba05;

import com.cognition.jvdemo.db.DbDispatcher;
import com.cognition.jvdemo.db.DemoSchema;
import com.cognition.jvdemo.db.DispatcherResult;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** JUnit 5 port of tests/test_laba05_reset.py (LABA05 fiscal-year reset). */
class Laba05ResetTest {

    private static DbDispatcher freshDb() {
        DbDispatcher d = DbDispatcher.newSqlite(":memory:");
        DemoSchema.buildDemoSchema(d);
        return d;
    }

    // ---- byte layout / display conversion --------------------------------
    @Test void sliceIs24To30() {
        assertEquals(24, Laba05Reset.JV_NUMBER_START);
        assertEquals(30, Laba05Reset.JV_NUMBER_STOP);
    }

    @Test void dataBlobMustBe400Bytes() {
        assertThrows(IllegalArgumentException.class, () -> Laba05Reset.replaceJvNumber("X".repeat(399), 1));
    }

    @Test void extractHandlesZeroPaddedDigits() {
        String data = "0".repeat(24) + "000042" + " ".repeat(400 - 30);
        assertEquals(42, Laba05Reset.extractJvNumber(data));
    }

    @Test void replacePreservesSurroundingBytes() {
        String data = "A".repeat(24) + "999999" + "B".repeat(400 - 30);
        String n = Laba05Reset.replaceJvNumber(data, 1);
        assertTrue(n.startsWith("A".repeat(24)));
        assertEquals("000001", n.substring(Laba05Reset.JV_NUMBER_START, Laba05Reset.JV_NUMBER_STOP));
        assertEquals("B".repeat(400 - 30), n.substring(30));
        assertEquals(Laba05Reset.JV_CONTROL_DATA_LENGTH, n.length());
    }

    // ---- end-to-end reset -------------------------------------------------
    @Test void resetSucceedsWhenRowExists() {
        try (DbDispatcher db = freshDb()) {
            DemoSchema.seedControlRecord(db, 42);
            ResetOutcome outcome = Laba05Reset.run(db);
            assertTrue(outcome.ok());
            assertEquals(ResetOutcome.RC_OK, outcome.returnCode());
            assertEquals(42, outcome.beforeJvNumber());
            assertEquals(1, outcome.afterJvNumber());

            DispatcherResult res = db.selectOne(
                    "SELECT CONTROL_RECORD_DATA FROM CONTROL_RECORD_TABLE "
                    + "WHERE CONTROL_RECORD_NAME = ? AND CONTROL_RECORD_NUMBER = ?",
                    "JV-CONTROL-REC", 1);
            assertTrue(res.isOk());
            String data = (String) res.rows.get(0).get(0);
            assertEquals(1, Laba05Reset.extractJvNumber(data));
        }
    }

    @Test void returns99WhenRowMissing() {
        try (DbDispatcher db = freshDb()) {
            ResetOutcome outcome = Laba05Reset.run(db);
            assertEquals(ResetOutcome.RC_DB_ERROR, outcome.returnCode());
            assertNull(outcome.beforeJvNumber());
            assertNull(outcome.afterJvNumber());
        }
    }

    @Test void returns99OnSqlException() {
        try (DbDispatcher db = freshDb()) {
            DemoSchema.seedControlRecord(db, 42);
            db.update("DROP TABLE CONTROL_RECORD_TABLE");
            db.commit();
            ResetOutcome outcome = Laba05Reset.run(db);
            assertEquals(ResetOutcome.RC_DB_ERROR, outcome.returnCode());
        }
    }

    // ---- binary->display round trip --------------------------------------
    @Test void roundTrip() {
        try (DbDispatcher db = freshDb()) {
            for (int original : new int[] {1, 17, 999999}) {
                DemoSchema.seedControlRecord(db, original);
                ResetOutcome outcome = Laba05Reset.run(db);
                assertEquals(original, outcome.beforeJvNumber());
                assertEquals(1, outcome.afterJvNumber());
                db.delete("DELETE FROM CONTROL_RECORD_TABLE");
                db.commit();
            }
        }
    }
}
