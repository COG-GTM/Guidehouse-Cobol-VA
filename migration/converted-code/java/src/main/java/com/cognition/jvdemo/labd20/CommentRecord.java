package com.cognition.jvdemo.labd20;

/**
 * Parsed view over the 300-byte TST123-COMMENT-REC
 * (source/procobol/LABD20.pco:43-55). Byte offsets are 0-based, end-exclusive,
 * matching the Python {@code CommentRecord}.
 *
 * <p>Total length = 8+6+2+10 (TST123-LOAN-DT-NR composite) + 10+230 (HIST) + 20
 * + 14 = 300 bytes. APPROVER is 14 bytes per the active LABD20.pco line 55 (the
 * commented 20-byte line 54 is deprecated — see RISKS-AND-GAPS.md Risk 5).
 */
public record CommentRecord(
        String raw,
        String commentDt,
        String jvNumber,
        String sectionId,
        String loanNumber,
        String loanDtNr,
        String scheduleDocNo,
        String commentText,
        String commentHist,
        String requestor,
        String approver) {

    public static final int TST123_RECORD_LENGTH = 300;

    // Byte offsets (0-based, end-exclusive) — match LABD20.pco:43-55.
    static final int COMMENT_DT_START = 0, COMMENT_DT_STOP = 8;        // PIC 9(008)
    static final int JV_NUMBER_START = 8, JV_NUMBER_STOP = 14;         // PIC 9(006)
    static final int SECTION_ID_START = 14, SECTION_ID_STOP = 16;      // PIC 9(002)
    static final int LOAN_NUMBER_START = 16, LOAN_NUMBER_STOP = 26;    // PIC 9(010)
    static final int LOAN_DT_NR_START = 0, LOAN_DT_NR_STOP = 26;       // composite redefine
    static final int SCHEDULE_DOC_NO_START = 26, SCHEDULE_DOC_NO_STOP = 36; // PIC X(010)
    static final int COMMENT_TEXT_START = 36, COMMENT_TEXT_STOP = 266; // PIC X(230)
    static final int COMMENT_HIST_START = 26, COMMENT_HIST_STOP = 266; // SCHED_DOC_NO + TEXT
    static final int REQUESTOR_START = 266, REQUESTOR_STOP = 286;      // PIC X(020)
    static final int APPROVER_START = 286, APPROVER_STOP = 300;        // PIC X(014)

    /** Parse a single 300-byte raw record (LABD20.pco:43-55). */
    public static CommentRecord parse(String raw) {
        if (raw.length() != TST123_RECORD_LENGTH) {
            throw new IllegalArgumentException(
                    "TST123-COMMENT-REC must be " + TST123_RECORD_LENGTH + " bytes; got " + raw.length());
        }
        return new CommentRecord(
                raw,
                raw.substring(COMMENT_DT_START, COMMENT_DT_STOP),
                raw.substring(JV_NUMBER_START, JV_NUMBER_STOP),
                raw.substring(SECTION_ID_START, SECTION_ID_STOP),
                raw.substring(LOAN_NUMBER_START, LOAN_NUMBER_STOP),
                raw.substring(LOAN_DT_NR_START, LOAN_DT_NR_STOP),
                raw.substring(SCHEDULE_DOC_NO_START, SCHEDULE_DOC_NO_STOP),
                raw.substring(COMMENT_TEXT_START, COMMENT_TEXT_STOP),
                raw.substring(COMMENT_HIST_START, COMMENT_HIST_STOP),
                raw.substring(REQUESTOR_START, REQUESTOR_STOP),
                raw.substring(APPROVER_START, APPROVER_STOP));
    }

    /** 26-byte composite PK for JC_SUBMITTED_COMMENT_TBL (LABD20.pco:329). */
    public String submittedKey() {
        return loanDtNr;
    }

    /** WS-CONTROL-NUM = JV-NUMBER(6) + SECTION-ID(2) = 8 bytes (LABD20.pco:160-165). */
    public String controlNum() {
        return jvNumber + sectionId;
    }
}
