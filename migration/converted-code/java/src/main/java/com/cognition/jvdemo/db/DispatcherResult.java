package com.cognition.jvdemo.db;

import java.util.ArrayList;
import java.util.List;

/**
 * Mirrors the (DB-RTNCODE-DMS, DB-SQLCODE-NUM, DB-MESSAGE) tuple DBIO.pco
 * writes back to its callers (cf. 9999-ERROR at DBIO.pco:402-405).
 */
public final class DispatcherResult {
    public final String rtncodeDms;
    public final int sqlcode;
    public final String message;
    public final List<List<Object>> rows;
    public final int rowcount;

    public DispatcherResult(String rtncodeDms, int sqlcode, String message,
                            List<List<Object>> rows, int rowcount) {
        this.rtncodeDms = rtncodeDms;
        this.sqlcode = sqlcode;
        this.message = message;
        this.rows = rows == null ? new ArrayList<>() : rows;
        this.rowcount = rowcount;
    }

    public static DispatcherResult ok() {
        return new DispatcherResult(SqlCodeTranslator.DMS_OK, 0, "", new ArrayList<>(), 0);
    }

    public boolean isOk() {
        return SqlCodeTranslator.DMS_OK.equals(rtncodeDms);
    }
}
