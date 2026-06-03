package com.cognition.jvdemo.dateconv;

/**
 * Status codes mirroring JDN-Con-Status-Codes
 * (source/copybooks/JDN-CONSTANTS-WS.cpy):
 *
 * <pre>
 *   OK              JDN-Con-NoErr           (0)
 *   OutOfRangeDD    JDN-Con-OutOfRangeDD    (7)
 *   OutOfRangeDDD   JDN-Con-OutOfRangeDDD   (8)
 *   OutOfRangeMM    JDN-Con-OutOfRangeMM    (10)
 *   OutOfRangeYYYY  JDN-Con-OutOfRangeYYYY  (11)
 *   Strange         JDN-Con-Strange         (12)
 * </pre>
 *
 * Faithful port of the constants used by dateconv.py.
 */
public final class Status {
    private Status() {}

    public static final String OK = "OK";
    public static final String OOR_DD = "OutOfRangeDD";
    public static final String OOR_DDD = "OutOfRangeDDD";
    public static final String OOR_MM = "OutOfRangeMM";
    public static final String OOR_YYYY = "OutOfRangeYYYY";
    public static final String STRANGE = "Strange";
}
