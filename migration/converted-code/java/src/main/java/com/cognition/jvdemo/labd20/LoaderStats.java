package com.cognition.jvdemo.labd20;

import java.util.ArrayList;
import java.util.List;

/**
 * Mirrors the LABD20 reporting accumulators (working-storage WS-COUNTERS,
 * LABD20.pco:60-105, used in the reporting block LABD20.pco:448-486). Port of
 * the {@code LoaderStats} dataclass.
 */
public final class LoaderStats {
    public int totalRead = 0;        // WS-JV-COMMENTS-CNT
    public int accepted = 0;         // WS-JV-COUNTER increments
    public int rejected = 0;         // WS-TST123-RECS-ERR-CNT
    public int duplicates = 0;
    public int inserted = 0;
    public int submittedTotal = 0;   // WS-TOTAL-SUBMIT-END-CNT
    public int rejectedTotal = 0;    // WS-TOTAL-REJECT-END-CNT
    public int appliedTotal = 0;     // WS-TOTAL-APPLIED-END-CNT
    public String processDate = "";
    public final List<String> rejectedReasons = new ArrayList<>();

    /** Human-readable summary; replaces the LABD20 DISPLAY block (LABD20.pco:448-486). */
    public String formatReport() {
        return String.join("\n",
                "*** COMMENT PROCESSING ***",
                "PROCESS DATE              : " + processDate,
                "COMMENTS READ             : " + totalRead,
                "COMMENTS ACCEPTED         : " + accepted,
                "COMMENTS REJECTED         : " + rejected,
                "COMMENTS DUPLICATE        : " + duplicates,
                "COMMENTS INSERTED         : " + inserted,
                "JC_SUBMITTED TOTAL        : " + submittedTotal,
                "JC_REJECTED TOTAL         : " + rejectedTotal,
                "JC_APPLIED  TOTAL         : " + appliedTotal);
    }
}
