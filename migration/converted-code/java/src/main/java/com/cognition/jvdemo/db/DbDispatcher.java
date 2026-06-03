package com.cognition.jvdemo.db;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.logging.Logger;

/**
 * Java port of source/procobol/DBIO.pco — a generic Oracle Pro*COBOL dispatcher
 * that LABA05 / LABD20 call for SELECT / INSERT / UPDATE / DELETE / COMMIT /
 * ROLLBACK, mapping SQLCODE to four-character DMS return codes.
 *
 * <p>This preserves the same contract (one method per DB verb, DMS-style return
 * code) but replaces the dynamic-dispatch + Oracle runtime with plain JDBC. The
 * demo wires it to sqlite; production would point {@code JV_DB_BACKEND=oracle}
 * at the Oracle JDBC driver. Faithful port of db_dispatcher.py.
 *
 * <p>The dynamic IO-routine name construction (DBIO.pco:228-260) is intentionally
 * NOT reproduced (see migration/RISKS-AND-GAPS.md Risk 4); callers use typed
 * methods.
 */
public final class DbDispatcher implements AutoCloseable {

    private static final Logger LOG = Logger.getLogger(DbDispatcher.class.getName());

    // count_rows() interpolates the table name (Oracle cannot bind identifiers),
    // so it is restricted to this allowlist to remove any injection vector.
    private static final Set<String> ALLOWED_TABLES = Set.of(
            "JC_SUBMITTED_COMMENT_TBL",
            "JC_REJECTED_COMMENT_TBL",
            "JC_APPLIED_COMMENT_TBL",
            "JC_COUNT_TBL",
            "CONTROL_RECORD_TABLE");

    // Env-var configuration — mirrors db_dispatcher.from_env (ASSUMPTION A-1:
    // credentials never come from disk files like /tst/.oralogin).
    public static final String ENV_DB_BACKEND = "JV_DB_BACKEND";
    public static final String ENV_DB_DSN = "JV_DB_DSN";
    public static final String ENV_DB_USER = "JV_DB_USER";
    public static final String ENV_DB_PASSWORD = "JV_DB_PASSWORD";

    private final Connection conn;

    public DbDispatcher(Connection connection) {
        this.conn = connection;
    }

    public Connection connection() {
        return conn;
    }

    /** Build a dispatcher from JV_DB_* environment variables. */
    public static DbDispatcher fromEnv() {
        String backend = System.getenv().getOrDefault(ENV_DB_BACKEND, "sqlite").toLowerCase();
        String dsn = System.getenv().getOrDefault(ENV_DB_DSN, ":memory:");
        if ("sqlite".equals(backend)) {
            return newSqlite(dsn);
        }
        // PLACEHOLDER: Oracle wiring is documented but not exercised in the demo
        // (no Oracle JDBC driver on the classpath). SME-REVIEW required.
        if ("oracle".equals(backend)) {
            throw new UnsupportedOperationException(
                    "JV_DB_BACKEND=oracle requires an Oracle JDBC driver and managed "
                    + "credentials; not exercised in the demo (see RISKS-AND-GAPS.md Risk 3).");
        }
        throw new IllegalArgumentException("Unknown " + ENV_DB_BACKEND + "=" + backend);
    }

    /** Open an in-memory ({@code :memory:}) or file-backed sqlite database. */
    public static DbDispatcher newSqlite(String dsn) {
        try {
            String url = ":memory:".equals(dsn) ? "jdbc:sqlite::memory:" : "jdbc:sqlite:" + dsn;
            Connection c = DriverManager.getConnection(url);
            c.setAutoCommit(false);  // so commit()/rollback() reproduce COMMIT WORK / ROLLBACK
            return new DbDispatcher(c);
        } catch (SQLException e) {
            throw new RuntimeException("Failed to open sqlite connection: " + dsn, e);
        }
    }

    // ------- read paths -----------------------------------------------------
    public DispatcherResult selectOne(String sql, Object... params) {
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            bind(ps, params);
            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    return new DispatcherResult(SqlCodeTranslator.DMS_NOT_FOUND, 100, "",
                            new ArrayList<>(), 0);
                }
                List<Object> row = readRow(rs);
                List<List<Object>> rows = new ArrayList<>();
                rows.add(row);
                return new DispatcherResult(SqlCodeTranslator.DMS_OK, 0, "", rows, 1);
            }
        } catch (SQLException e) {
            return error(e);
        }
    }

    public int countRows(String table) {
        return countRows(table, "1=1");
    }

    public int countRows(String table, String where, Object... params) {
        if (!ALLOWED_TABLES.contains(table)) {
            throw new IllegalArgumentException(
                    "countRows: table '" + table + "' is not in the allowlist; add it to "
                    + "ALLOWED_TABLES if it is a legitimate target.");
        }
        String sql = "SELECT COUNT(*) FROM " + table + " WHERE " + where;
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            bind(ps, params);
            try (ResultSet rs = ps.executeQuery()) {
                return rs.next() ? rs.getInt(1) : 0;
            }
        } catch (SQLException e) {
            throw new RuntimeException("countRows failed for " + table, e);
        }
    }

    // ------- write paths ----------------------------------------------------
    public DispatcherResult insert(String sql, Object... params) {
        return execWrite(sql, params);
    }

    public DispatcherResult update(String sql, Object... params) {
        return execWrite(sql, params);
    }

    public DispatcherResult delete(String sql, Object... params) {
        return execWrite(sql, params);
    }

    private DispatcherResult execWrite(String sql, Object[] params) {
        try (PreparedStatement ps = conn.prepareStatement(sql)) {
            bind(ps, params);
            int n = ps.executeUpdate();
            return new DispatcherResult(SqlCodeTranslator.DMS_OK, 0, "", new ArrayList<>(), n);
        } catch (SQLException e) {
            return error(e);
        }
    }

    // ------- transaction control -------------------------------------------
    public DispatcherResult commit() {
        try {
            conn.commit();
            return DispatcherResult.ok();
        } catch (SQLException e) {
            return error(e);
        }
    }

    public DispatcherResult rollback() {
        try {
            conn.rollback();
            return DispatcherResult.ok();
        } catch (SQLException e) {
            return error(e);
        }
    }

    @Override
    public void close() {
        try {
            conn.close();
        } catch (SQLException e) {
            LOG.warning("Error closing DB connection: " + e.getMessage());
        }
    }

    /** Commit on clean exit, rollback + rethrow on failure (LABD20 semantics). */
    public void transaction(Runnable work) {
        try {
            work.run();
            commit();
        } catch (RuntimeException ex) {
            rollback();
            throw ex;
        }
    }

    // ------- helpers --------------------------------------------------------
    private static void bind(PreparedStatement ps, Object[] params) throws SQLException {
        if (params == null) {
            return;
        }
        for (int i = 0; i < params.length; i++) {
            ps.setObject(i + 1, params[i]);
        }
    }

    private static List<Object> readRow(ResultSet rs) throws SQLException {
        ResultSetMetaData md = rs.getMetaData();
        int cols = md.getColumnCount();
        List<Object> row = new ArrayList<>(cols);
        for (int i = 1; i <= cols; i++) {
            row.add(rs.getObject(i));
        }
        return row;
    }

    private DispatcherResult error(SQLException exc) {
        int sqlcode = deriveSqlcode(exc);
        String dms = SqlCodeTranslator.translate(sqlcode);
        LOG.severe("DBIO-equivalent error: sqlcode=" + sqlcode + " dms=" + dms + " err=" + exc);
        return new DispatcherResult(dms, sqlcode, String.valueOf(exc.getMessage()), new ArrayList<>(), 0);
    }

    /**
     * Pull a SQLCODE-equivalent out of the driver exception. The sqlite driver
     * has no Oracle SQLCODE, so we synthesize -1 (DMS_BAD_FETCH) — matching
     * db_dispatcher._derive_sqlcode. SME-REVIEW: add real Oracle codes in prod.
     */
    private static int deriveSqlcode(SQLException exc) {
        return -1;
    }

    /** Convenience accessor for the count_rows allowlist (tests / docs). */
    public static Set<String> allowedTables() {
        return ALLOWED_TABLES;
    }
}
