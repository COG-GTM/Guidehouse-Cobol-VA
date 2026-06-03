package com.cognition.jvdemo.db;

import java.util.logging.Logger;

/**
 * Port of 5300-TRANSLATE-SQLCODE (source/procobol/DBIO.pco:374-398).
 *
 * <p>Legacy callers (LABA05, LABD20) check the 4-character DMS code (aliased as
 * ERROR-NUM), not the raw SQLCODE. The constants and mapping reproduce the
 * legacy table verbatim so behavior-equivalence reviews are unambiguous.
 */
public final class SqlCodeTranslator {
    private SqlCodeTranslator() {}

    private static final Logger LOG = Logger.getLogger(SqlCodeTranslator.class.getName());

    public static final String DMS_OK = "0000";            // SQLCODE 0     — DBIO.pco:377
    public static final String DMS_NOT_FOUND = "0013";     // SQLCODE 100   — DBIO.pco:379
    public static final String DMS_NOT_FOUND_SET = "0007"; // SQLCODE 100 + set — DBIO.pco:382
    public static final String DMS_BAD_FETCH = "0005";     // SQLCODE -1    — DBIO.pco:385
    public static final String DMS_CONTINUE_8103 = "0000"; // SQLCODE -8103 — DBIO.pco:387
    public static final String DMS_UNHANDLED = "9999";     // any other     — DBIO.pco:397

    public static String translate(int sqlcode) {
        return translate(sqlcode, "", "");
    }

    /**
     * Reproduce 5300-TRANSLATE-SQLCODE verbatim:
     * <pre>
     *   0     -> 0000
     *   100   -> 0013 (or 0007 if DB-SET-NAME non-blank AND func != 'FETCH OWNER')
     *   -1    -> 0005
     *   -8103 -> 0000 (with a logged DISPLAY block — DBIO.pco:387-395)
     *   other -> 9999
     * </pre>
     */
    public static String translate(int sqlcode, String setName, String functionType) {
        if (sqlcode == 0) {
            return DMS_OK;
        }
        if (sqlcode == 100) {
            if (setName != null && !setName.strip().isEmpty() && !"FETCH OWNER".equals(functionType)) {
                return DMS_NOT_FOUND_SET;
            }
            return DMS_NOT_FOUND;
        }
        if (sqlcode == -1) {
            return DMS_BAD_FETCH;
        }
        if (sqlcode == -8103) {
            // PLACEHOLDER: DBIO.pco:388-395 also displays table/function/key/rowid.
            LOG.warning("RECEIVED ORACLE ERROR -8103, CONTINUE...");
            return DMS_CONTINUE_8103;
        }
        return DMS_UNHANDLED;
    }
}
