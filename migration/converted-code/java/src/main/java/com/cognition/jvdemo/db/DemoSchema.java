package com.cognition.jvdemo.db;

import java.sql.SQLException;
import java.sql.Statement;

/**
 * Demo schema + seed helpers — port of build_demo_schema / seed_control_record
 * from db_dispatcher.py.
 *
 * <p>ASSUMPTION A-7: the table shapes reflect database/descriptions/*.txt. Oracle
 * DDL types are simplified to sqlite-compatible affinities for the demo runtime.
 */
public final class DemoSchema {
    private DemoSchema() {}

    public static final String[] DEMO_SCHEMA_DDL = {
        """
        CREATE TABLE IF NOT EXISTS JC_SUBMITTED_COMMENT_TBL (
            JC_SUBMITTED                TEXT PRIMARY KEY,    -- 26 chars composite
            JC_SUBMITTED_SCHED_DOC_NO   TEXT,
            JC_SUBMITTED_COMMENT_HIST   TEXT,
            JC_SUBMITTED_COMMENT_REQUESTOR TEXT,
            JC_SUBMITTED_COMMENT_APPROVER  TEXT,
            JC_SUBMITTED_CONTROL_NUM    TEXT,
            JC_SUBMITTED_UPDT_PROG_ID   TEXT,
            JC_SUBMITTED_UPDT_PROG_DT   TEXT,                -- YYYY-MM-DD as text
            JC_SUBMITTED_NUMBER         INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS JC_COUNT_TBL (
            JC_SECTION                  TEXT PRIMARY KEY,    -- legacy describe-file PK typo; see RISKS-AND-GAPS.md
            JC_COUNT_NUM                INTEGER
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS JC_REJECTED_COMMENT_TBL (
            JC_REJECTED                 TEXT PRIMARY KEY,
            JC_REJECTED_REASON          TEXT
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS JC_APPLIED_COMMENT_TBL (
            JC_APPLIED                  TEXT PRIMARY KEY
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS CONTROL_RECORD_TABLE (
            CONTROL_RECORD_NAME         TEXT,
            CONTROL_RECORD_NUMBER       INTEGER,
            CONTROL_RECORD_DATA         TEXT,                -- CHAR(400) in Oracle
            PRIMARY KEY (CONTROL_RECORD_NAME, CONTROL_RECORD_NUMBER)
        )
        """,
    };

    /** Create the demo tables. Idempotent. */
    public static void buildDemoSchema(DbDispatcher dispatcher) {
        try (Statement st = dispatcher.connection().createStatement()) {
            for (String ddl : DEMO_SCHEMA_DDL) {
                st.execute(ddl);
            }
        } catch (SQLException e) {
            throw new RuntimeException("Failed to build demo schema", e);
        }
        dispatcher.commit();
    }

    /**
     * Insert a JV-CONTROL-REC row so LABA05 has something to reset.
     *
     * <p>The 400-byte CONTROL_RECORD_DATA layout reflects JV-CONTROL-REC.cpy:
     * bytes 1-6 JV-CONTROL-1, 7-12 JV-CONTROL-2, 13-18 JV-CONTROL-3,
     * 19-24 JV-CONTROL-4, 25-30 JV-NUMBER (legacy USAGE BINARY; here display
     * 6-digit), 31-39 filler, 40-45 JV-CONTROL-5, 46+ filler.
     *
     * <p>ASSUMPTION A-2: the demo uses a display (6-char zoned) JV-NUMBER;
     * production must reproduce USAGE BINARY (see RISKS-AND-GAPS.md Risk 2).
     */
    public static void seedControlRecord(DbDispatcher dispatcher, int jvNumber) {
        String data = "000001"          // JV-CONTROL-1
                + "000002"              // JV-CONTROL-2
                + "000003"              // JV-CONTROL-3
                + "000004"              // JV-CONTROL-4
                + String.format("%06d", jvNumber)  // JV-NUMBER (display)
                + " ".repeat(9)         // filler
                + "000005"              // JV-CONTROL-5
                + " ".repeat(355);      // remaining filler up to 400 bytes
        if (data.length() != 400) {
            throw new IllegalStateException(
                    "CONTROL_RECORD_DATA must be 400 bytes, got " + data.length());
        }
        dispatcher.insert(
                "INSERT INTO CONTROL_RECORD_TABLE "
                + "(CONTROL_RECORD_NAME, CONTROL_RECORD_NUMBER, CONTROL_RECORD_DATA) "
                + "VALUES (?, ?, ?)",
                "JV-CONTROL-REC", 1, data);
        dispatcher.commit();
    }

    public static void seedControlRecord(DbDispatcher dispatcher) {
        seedControlRecord(dispatcher, 42);
    }
}
