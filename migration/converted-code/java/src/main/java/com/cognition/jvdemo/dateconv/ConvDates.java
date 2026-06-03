package com.cognition.jvdemo.dateconv;

/**
 * Mirrors the LINKAGE SECTION CONV-DATES record
 * (source/copybooks/DATECONV-WS.cpy).
 *
 * <p>THRU-* aliases point at the same storage as TO-* (the COBOL field for the
 * "second" input of DIF/RANGE operations is TO-*-DT, kept as the canonical
 * field). Faithful port of the {@code ConvDates} dataclass in dateconv.py.
 */
public final class ConvDates {
    public int datesubFunc = 0;

    // FROM-* inputs
    public long fromCymdDt = 0;   // PIC 9(8)
    public long fromJulDt = 0;    // PIC 9(5)
    public long fromYmdDt = 0;    // PIC 9(6)
    public long fromMdyDt = 0;    // PIC 9(6)
    public long fromIntDt = 0;    // PIC 9(10) COMP

    // TO-* outputs (also serve as the "thru" side of DIF/RANGE)
    public long toCymdDt = 0;
    public long toJulDt = 0;
    public long toYmdDt = 0;
    public long toMdyDt = 0;
    public long toMdcyDt = 0;
    public long toIntDt = 0;

    // BETWEEN-* (the candidate point for RANGE operations)
    public long betweenJulDt = 0;
    public long betweenYmdDt = 0;
    public long betweenMdyDt = 0;

    // arithmetic inputs
    public long monthsToAdd = 0;
    public long daysDif = 0;      // also DAYS-DIF result + 88888/77777 sentinels

    // output flags
    public String dateErrInd = "N";   // 'Y' / 'N' (DATE-IS-VALID = 'N')
    public int dateErrReason = 0;     // 0..12 (see JDN-Con-Status-Codes)

    public ConvDates() {}

    // THRU-* convenience aliases (read/write the same storage as TO-*).
    public long thruCymdDt() { return toCymdDt; }
    public void thruCymdDt(long v) { toCymdDt = v; }
    public long thruJulDt() { return toJulDt; }
    public void thruJulDt(long v) { toJulDt = v; }
    public long thruYmdDt() { return toYmdDt; }
    public void thruYmdDt(long v) { toYmdDt = v; }
    public long thruMdyDt() { return toMdyDt; }
    public void thruMdyDt(long v) { toMdyDt = v; }
    public long thruIntDt() { return toIntDt; }
    public void thruIntDt(long v) { toIntDt = v; }
}
