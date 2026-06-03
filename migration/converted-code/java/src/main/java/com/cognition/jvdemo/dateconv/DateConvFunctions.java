package com.cognition.jvdemo.dateconv;

/**
 * Thin, typed convenience facade over {@link DateConv}, mirroring the
 * module-level helper functions at the bottom of dateconv.py
 * (check_cymd_dt, ymd_to_jul, dif_*, add_*, range_*, ...).
 *
 * <p>Each call builds a {@link ConvDates}, dispatches the matching
 * DATESUB-FUNC, and reads back the relevant field together with the mapped
 * status. Date-form arguments are passed as {@code String} (matching how the
 * fixed-width loader supplies them); day/month/integer arguments are
 * {@code long}.
 */
public final class DateConvFunctions {
    private DateConvFunctions() {}

    private static final DateConv ENGINE = new DateConv();

    /** (status, valid?) — for the CHECK validators. */
    public record Check(String status, boolean ok) {}

    /** (status, value) — for the value-producing conversions. */
    public record Conv(String status, long value) {}

    // ---- shared helpers (port of _to_int / _has_n_digits / _status) -------
    private static Long toInt(String v) {
        if (v == null || v.isEmpty()) {
            return null;
        }
        for (int i = 0; i < v.length(); i++) {
            if (!Character.isDigit(v.charAt(i))) {
                return null;
            }
        }
        return Long.parseLong(v);
    }

    private static long toIntOr0(String v) {
        Long r = toInt(v);
        return r == null ? 0 : r;
    }

    private static boolean hasNDigits(String v, int n) {
        if (v == null || v.length() != n) {
            return false;
        }
        for (int i = 0; i < v.length(); i++) {
            if (!Character.isDigit(v.charAt(i))) {
                return false;
            }
        }
        return true;
    }

    private static boolean hasNDigits(long v, int n) {
        if (v < 0) {
            return false;
        }
        long limit = 1;
        for (int i = 0; i < n; i++) {
            limit *= 10;
        }
        return v < limit;
    }

    private static String status(ConvDates cd) {
        if (cd.dateErrInd.equals("N")) {
            return Status.OK;
        }
        return DateConv.statusForReason(cd.dateErrReason);
    }

    private static ConvDates run(int func, java.util.function.Consumer<ConvDates> init) {
        ConvDates cd = new ConvDates();
        init.accept(cd);
        ENGINE.dispatch(func, cd);
        return cd;
    }

    // ---- validators (1, 9) ------------------------------------------------
    public static Check checkCymdDt(String yyyymmdd) {
        Long v = toInt(yyyymmdd);
        if (v == null || !hasNDigits(yyyymmdd, 8)) {
            return new Check(Status.STRANGE, false);
        }
        ConvDates cd = run(1, c -> c.fromCymdDt = v);
        String s = status(cd);
        return new Check(s, s.equals(Status.OK));
    }

    public static Check checkCymdDt(long yyyymmdd) {
        if (!hasNDigits(yyyymmdd, 8)) {
            return new Check(Status.STRANGE, false);
        }
        ConvDates cd = run(1, c -> c.fromCymdDt = yyyymmdd);
        String s = status(cd);
        return new Check(s, s.equals(Status.OK));
    }

    public static Check checkMdyDt(String mmddyy) {
        Long v = toInt(mmddyy);
        if (v == null || !hasNDigits(mmddyy, 6)) {
            return new Check(Status.STRANGE, false);
        }
        ConvDates cd = run(9, c -> c.fromMdyDt = v);
        String s = status(cd);
        return new Check(s, s.equals(Status.OK));
    }

    public static Check checkMdyDt(long mmddyy) {
        if (!hasNDigits(mmddyy, 6)) {
            return new Check(Status.STRANGE, false);
        }
        ConvDates cd = run(9, c -> c.fromMdyDt = mmddyy);
        String s = status(cd);
        return new Check(s, s.equals(Status.OK));
    }

    // ---- format conversions ----------------------------------------------
    public static Conv ymdToJul(String yymmdd) {
        ConvDates cd = run(2, c -> c.fromYmdDt = toIntOr0(yymmdd));
        return new Conv(status(cd), cd.toJulDt);
    }

    public static Conv julToYmd(String yyddd) {
        ConvDates cd = run(3, c -> c.fromJulDt = toIntOr0(yyddd));
        return new Conv(status(cd), cd.toYmdDt);
    }

    public static Conv mdyToJul(String mmddyy) {
        ConvDates cd = run(10, c -> c.fromMdyDt = toIntOr0(mmddyy));
        return new Conv(status(cd), cd.toJulDt);
    }

    public static Conv julToMdy(String yyddd) {
        ConvDates cd = run(11, c -> c.fromJulDt = toIntOr0(yyddd));
        return new Conv(status(cd), cd.toMdyDt);
    }

    public static Conv mdyToYmd(String mmddyy) {
        ConvDates cd = run(12, c -> c.fromMdyDt = toIntOr0(mmddyy));
        return new Conv(status(cd), cd.toYmdDt);
    }

    public static Conv mdyToMdcy(String mmddyy) {
        ConvDates cd = run(27, c -> c.fromMdyDt = toIntOr0(mmddyy));
        return new Conv(status(cd), cd.toMdcyDt);
    }

    public static Conv ymdToMdy(String yymmdd) {
        ConvDates cd = run(13, c -> c.fromYmdDt = toIntOr0(yymmdd));
        return new Conv(status(cd), cd.toMdyDt);
    }

    public static Conv ymdToCymd(String yymmdd) {
        ConvDates cd = run(18, c -> c.fromYmdDt = toIntOr0(yymmdd));
        return new Conv(status(cd), cd.toCymdDt);
    }

    public static Conv julToCymd(String yyddd) {
        ConvDates cd = run(23, c -> c.fromJulDt = toIntOr0(yyddd));
        return new Conv(status(cd), cd.toCymdDt);
    }

    public static Conv cymdToJul(String yyyymmdd) {
        ConvDates cd = run(24, c -> c.fromCymdDt = toIntOr0(yyyymmdd));
        return new Conv(status(cd), cd.toJulDt);
    }

    public static Conv cymdToInt(String yyyymmdd) {
        ConvDates cd = run(25, c -> c.fromCymdDt = toIntOr0(yyyymmdd));
        return new Conv(status(cd), cd.toIntDt);
    }

    public static Conv intToCymd(long n) {
        ConvDates cd = run(26, c -> c.fromIntDt = n);
        return new Conv(status(cd), cd.toCymdDt);
    }

    public static Conv julToInt(String yyddd) {
        ConvDates cd = run(31, c -> c.fromJulDt = toIntOr0(yyddd));
        return new Conv(status(cd), cd.toIntDt);
    }

    public static Conv intToJul(long n) {
        ConvDates cd = run(32, c -> c.fromIntDt = n);
        return new Conv(status(cd), cd.toJulDt);
    }

    public static Conv ymdToInt(String yymmdd) {
        ConvDates cd = run(33, c -> c.fromYmdDt = toIntOr0(yymmdd));
        return new Conv(status(cd), cd.toIntDt);
    }

    public static Conv intToYmd(long n) {
        ConvDates cd = run(34, c -> c.fromIntDt = n);
        return new Conv(status(cd), cd.toYmdDt);
    }

    public static Conv mdyToInt(String mmddyy) {
        ConvDates cd = run(35, c -> c.fromMdyDt = toIntOr0(mmddyy));
        return new Conv(status(cd), cd.toIntDt);
    }

    public static Conv intToMdy(long n) {
        ConvDates cd = run(36, c -> c.fromIntDt = n);
        return new Conv(status(cd), cd.toMdyDt);
    }

    // ---- DIF family -------------------------------------------------------
    public static Conv difJul(String from, String thru) {
        ConvDates cd = run(4, c -> { c.fromJulDt = toIntOr0(from); c.toJulDt = toIntOr0(thru); });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv difJulNoCheck(String from, String thru) {
        ConvDates cd = run(28, c -> { c.fromJulDt = toIntOr0(from); c.toJulDt = toIntOr0(thru); });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv difYmd(String from, String thru) {
        ConvDates cd = run(5, c -> { c.fromYmdDt = toIntOr0(from); c.toYmdDt = toIntOr0(thru); });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv difMdy(String from, String thru) {
        ConvDates cd = run(14, c -> { c.fromMdyDt = toIntOr0(from); c.toMdyDt = toIntOr0(thru); });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv difCymd(String from, String thru) {
        ConvDates cd = run(19, c -> { c.fromCymdDt = toIntOr0(from); c.toCymdDt = toIntOr0(thru); });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv difFy(String from, String thru) {
        ConvDates cd = run(37, c -> { c.fromYmdDt = toIntOr0(from); c.toYmdDt = toIntOr0(thru); });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv difJul30(String from, String thru) {
        ConvDates cd = run(15, c -> { c.fromJulDt = toIntOr0(from); c.toJulDt = toIntOr0(thru); });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv difCymd30(String from, String thru) {
        ConvDates cd = run(6, c -> { c.fromCymdDt = toIntOr0(from); c.toCymdDt = toIntOr0(thru); });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv difMdy30(String from, String thru) {
        ConvDates cd = run(16, c -> { c.fromMdyDt = toIntOr0(from); c.toMdyDt = toIntOr0(thru); });
        return new Conv(status(cd), cd.daysDif);
    }

    // ---- ADD family -------------------------------------------------------
    public static Conv addJul(String from, long days) {
        ConvDates cd = run(7, c -> { c.fromJulDt = toIntOr0(from); c.daysDif = days; });
        return new Conv(status(cd), cd.toJulDt);
    }

    public static Conv addYmd(String from, long days) {
        ConvDates cd = run(8, c -> { c.fromYmdDt = toIntOr0(from); c.daysDif = days; });
        return new Conv(status(cd), cd.toYmdDt);
    }

    public static Conv addMdy(String from, long days) {
        ConvDates cd = run(17, c -> { c.fromMdyDt = toIntOr0(from); c.daysDif = days; });
        return new Conv(status(cd), cd.toMdyDt);
    }

    public static Conv addCymd(String from, long days) {
        ConvDates cd = run(20, c -> { c.fromCymdDt = toIntOr0(from); c.daysDif = days; });
        return new Conv(status(cd), cd.toCymdDt);
    }

    public static Conv addMonthsToYmd(String from, long months) {
        ConvDates cd = run(21, c -> { c.fromYmdDt = toIntOr0(from); c.monthsToAdd = months; });
        return new Conv(status(cd), cd.toYmdDt);
    }

    public static Conv addMonthsToCymd(String from, long months) {
        ConvDates cd = run(22, c -> { c.fromCymdDt = toIntOr0(from); c.monthsToAdd = months; });
        return new Conv(status(cd), cd.toCymdDt);
    }

    public static Conv addMonthsToMdy(String from, long months) {
        ConvDates cd = run(41, c -> { c.fromMdyDt = toIntOr0(from); c.monthsToAdd = months; });
        return new Conv(status(cd), cd.toMdyDt);
    }

    public static Conv addMonthsEndJul(String from, long months) {
        ConvDates cd = run(42, c -> { c.fromJulDt = toIntOr0(from); c.monthsToAdd = months; });
        return new Conv(status(cd), cd.toJulDt);
    }

    // ---- RANGE family -----------------------------------------------------
    public static Conv rangeJul(String from, String thru, String between) {
        ConvDates cd = run(38, c -> {
            c.fromJulDt = toIntOr0(from);
            c.toJulDt = toIntOr0(thru);
            c.betweenJulDt = toIntOr0(between);
        });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv rangeYmd(String from, String thru, String between) {
        ConvDates cd = run(39, c -> {
            c.fromYmdDt = toIntOr0(from);
            c.toYmdDt = toIntOr0(thru);
            c.betweenYmdDt = toIntOr0(between);
        });
        return new Conv(status(cd), cd.daysDif);
    }

    public static Conv rangeMdy(String from, String thru, String between) {
        ConvDates cd = run(40, c -> {
            c.fromMdyDt = toIntOr0(from);
            c.toMdyDt = toIntOr0(thru);
            c.betweenMdyDt = toIntOr0(between);
        });
        return new Conv(status(cd), cd.daysDif);
    }
}
