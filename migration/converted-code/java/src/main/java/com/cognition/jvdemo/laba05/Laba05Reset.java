package com.cognition.jvdemo.laba05;

import com.cognition.jvdemo.db.DbDispatcher;
import com.cognition.jvdemo.db.DispatcherResult;

import java.util.List;
import java.util.logging.Logger;

/**
 * Java port of source/cobol/LABA05.cbl — the fiscal-year JV control-number
 * reset utility. It:
 * <ol>
 *   <li>FETCHes the JV-CONTROL-REC row from CONTROL_RECORD_TABLE keyed by
 *       name='JV-CONTROL-REC' and number=1 (FETCH-CTRL-REC, LABA05.cbl:152-174);</li>
 *   <li>decodes JV-NUMBER from the 400-byte CONTROL_RECORD_DATA blob;</li>
 *   <li>MOVEs 1 TO JV-NUMBER and UPDATEs (MODIFY-CTRL-REC, LABA05.cbl:176-205);</li>
 *   <li>returns 0 on success, 99 on any DBIO error.</li>
 * </ol>
 *
 * <p>Faithful port of laba05_reset.py. ASSUMPTION A-2: JV-NUMBER is USAGE BINARY
 * in production; the demo uses a 6-byte zoned-display form (see
 * migration/RISKS-AND-GAPS.md Risk 2).
 */
public final class Laba05Reset {

    private static final Logger LOG = Logger.getLogger(Laba05Reset.class.getName());

    public static final String CONTROL_RECORD_NAME = "JV-CONTROL-REC";
    public static final int CONTROL_RECORD_NUMBER = 1;
    public static final int TARGET_JV_NUMBER = 1;  // LABA05.cbl:184-189

    // Byte offsets inside CONTROL_RECORD_DATA (400 bytes), 0-based, end-exclusive.
    static final int JV_NUMBER_START = 24;  // 6 bytes; legacy USAGE BINARY (Risk 2)
    static final int JV_NUMBER_STOP = 30;
    static final int JV_CONTROL_DATA_LENGTH = 400;

    private Laba05Reset() {}

    /**
     * Decode JV-NUMBER from CONTROL_RECORD_DATA. Demo data is the display form,
     * so we parse 6 ASCII digits. PLACEHOLDER for production: unpack the legacy
     * USAGE BINARY form (e.g. big-endian unsigned int) instead.
     */
    static int extractJvNumber(String data) {
        return Integer.parseInt(data.substring(JV_NUMBER_START, JV_NUMBER_STOP));
    }

    /** Write a new JV-NUMBER back, preserving the surrounding bytes exactly. */
    static String replaceJvNumber(String data, int newValue) {
        if (data.length() != JV_CONTROL_DATA_LENGTH) {
            throw new IllegalArgumentException(
                    "CONTROL_RECORD_DATA must be " + JV_CONTROL_DATA_LENGTH
                    + " bytes; got " + data.length());
        }
        String encoded = String.format("%06d", newValue);
        if (encoded.length() != 6) {
            throw new IllegalArgumentException("JV_NUMBER must fit in 6 zoned-display digits");
        }
        return data.substring(0, JV_NUMBER_START) + encoded + data.substring(JV_NUMBER_STOP);
    }

    /**
     * Execute the reset against the supplied dispatcher (caller owns its
     * lifecycle). Returns a {@link ResetOutcome} with returnCode 0 (success) or
     * 99 (any DBIO non-zero).
     */
    public static ResetOutcome run(DbDispatcher dispatcher) {
        // Step 1: FETCH the control record (LABA05.cbl:152-174).
        DispatcherResult fetch = dispatcher.selectOne(
                "SELECT CONTROL_RECORD_DATA FROM CONTROL_RECORD_TABLE "
                + "WHERE CONTROL_RECORD_NAME = ? AND CONTROL_RECORD_NUMBER = ?",
                CONTROL_RECORD_NAME, CONTROL_RECORD_NUMBER);
        if (!fetch.isOk() || fetch.rows.isEmpty()) {
            LOG.severe("LABA05: fetch failed dms=" + fetch.rtncodeDms + " msg=" + fetch.message);
            return new ResetOutcome(ResetOutcome.RC_DB_ERROR, null, null,
                    "fetch failed: dms=" + fetch.rtncodeDms + " sqlcode=" + fetch.sqlcode);
        }

        String data = (String) fetch.rows.get(0).get(0);
        int before = extractJvNumber(data);
        LOG.info(() -> String.format("LABA05: PRIOR JV NUMBER WAS %06d", before));

        // Step 2: MOVE 1 TO JV-NUMBER and UPDATE (LABA05.cbl:184-205).
        String newData = replaceJvNumber(data, TARGET_JV_NUMBER);
        DispatcherResult update = dispatcher.update(
                "UPDATE CONTROL_RECORD_TABLE SET CONTROL_RECORD_DATA = ? "
                + "WHERE CONTROL_RECORD_NAME = ? AND CONTROL_RECORD_NUMBER = ?",
                newData, CONTROL_RECORD_NAME, CONTROL_RECORD_NUMBER);
        if (!update.isOk()) {
            dispatcher.rollback();
            LOG.severe("LABA05: update failed dms=" + update.rtncodeDms + " msg=" + update.message);
            return new ResetOutcome(ResetOutcome.RC_DB_ERROR, before, null,
                    "update failed: dms=" + update.rtncodeDms + " sqlcode=" + update.sqlcode);
        }

        dispatcher.commit();
        int after = extractJvNumber(newData);
        LOG.info(() -> String.format("LABA05: JV NUMBER IS NOW %06d", after));
        return new ResetOutcome(ResetOutcome.RC_OK, before, after, "JV-NUMBER reset to 1");
    }
}
