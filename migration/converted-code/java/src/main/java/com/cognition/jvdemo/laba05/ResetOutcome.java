package com.cognition.jvdemo.laba05;

/**
 * Structured result of the LABA05 reset — useful for tests and the demo CLI.
 * Port of the {@code ResetOutcome} dataclass in laba05_reset.py. The
 * {@code before}/{@code after} JV numbers are {@code null} when unavailable.
 */
public record ResetOutcome(int returnCode, Integer beforeJvNumber, Integer afterJvNumber, String message) {

    public static final int RC_OK = 0;
    public static final int RC_DB_ERROR = 99;  // LABA05.cbl: any DBIO non-zero -> 99

    public boolean ok() {
        return returnCode == RC_OK;
    }
}
