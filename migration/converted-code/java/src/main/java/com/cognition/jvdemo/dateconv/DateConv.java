package com.cognition.jvdemo.dateconv;

import java.time.DateTimeException;
import java.time.LocalDate;
import java.time.YearMonth;

/**
 * Java port of source/cobol/DATECONV.cbl (42 DATESUB-FUNC codes, 40 active
 * entry paragraphs; codes 29/30 reserved/unused per
 * source/copybooks/DATECONV-PD.cpy).
 *
 * <p>The customer's DATECONV.cbl was migrated to COBOL-85 intrinsics in 2012,
 * so all date math reduces to INTEGER-OF-DATE / DATE-OF-INTEGER /
 * INTEGER-OF-DAY / DAY-OF-INTEGER, which {@link java.time.LocalDate} implements
 * exactly (proleptic Gregorian). Faithful 1:1 port of dateconv.py; each
 * {@code runNN_*} method maps to a DATECONV.cbl paragraph (line ranges cited).
 *
 * <p>The dispatch idiom (DATESUB-FUNC) is preserved so a SME can map every
 * method back to a DATECONV.cbl paragraph by code or by name.
 */
public final class DateConv {

    // COBOL INTEGER-OF-DATE epoch = 1601-01-01 (day 1).
    // Source: source/copybooks/JDN-CONSTANTS-WS.cpy lines 35-38.
    private static final long EPOCH_1601 = LocalDate.of(1601, 1, 1).toEpochDay();

    // ---- internal result holders (Python returned tuples) -----------------
    private record IntResult(String status, long value) {}
    private record DayResult(String status, long value, int yyyy) {}
    private record DateResult(String status, LocalDate date) {}
    private record AddMonthsResult(String status, int y, int m, int d) {}
    private record StatusInt(String status, long value) {}

    // ---- epoch helpers ----------------------------------------------------
    private static long dateToInt(LocalDate d) {
        return d.toEpochDay() - EPOCH_1601 + 1;
    }

    private static LocalDate intToDate(long jdn) {
        return LocalDate.ofEpochDay(jdn - 1 + EPOCH_1601);
    }

    // ---- century-inference helpers ----------------------------------------
    // Rule A: DATECONV.cbl:1054-1059 (9920-CALC-YY-TO-YYYY): YY > 52 -> 19xx.
    private static int ccInferred(long yy) {
        return yy > 52 ? 19 : 20;
    }

    // Rule B: JDN-RECORD-ACCESS.cpy:74-79 (JDN-Acc-CC-Inferred, CHG-002):
    // YY > 72 -> 19xx. Applies inside JDN-ACC-INT-OF-DATE/-DAY with JDN-CC=0.
    private static int ccInferredJdn(long yy) {
        return yy > 72 ? 19 : 20;
    }

    // ---- splitters --------------------------------------------------------
    private static long[] splitDateInt(long v) {
        return new long[] {v / 10000, (v / 100) % 100, v % 100};
    }

    private static long[] splitJul(long jul) {
        return new long[] {jul / 1000, jul % 1000};
    }

    private static long ymdToCymd(long ymd, boolean viaJdn) {
        long[] p = splitDateInt(ymd);
        long yy = p[0], mm = p[1], dd = p[2];
        long cc = viaJdn ? ccInferredJdn(yy) : ccInferred(yy);
        return cc * 1000000 + yy * 10000 + mm * 100 + dd;
    }

    private static long mdyToCymd(long mdy, boolean viaJdn) {
        long[] p = splitDateInt(mdy);
        long mm = p[0], dd = p[1], yy = p[2];
        long cc = viaJdn ? ccInferredJdn(yy) : ccInferred(yy);
        return cc * 1000000 + yy * 10000 + mm * 100 + dd;
    }

    // ---- intrinsic equivalents -------------------------------------------
    private static IntResult intOfDate(long cymd) {
        long[] p = splitDateInt(cymd);
        long yyyy = p[0], mm = p[1], dd = p[2];
        if (yyyy < 1601) {
            return new IntResult(Status.OOR_YYYY, 0);
        }
        if (mm < 1 || mm > 12) {
            return new IntResult(Status.OOR_MM, 0);
        }
        try {
            LocalDate d = LocalDate.of((int) yyyy, (int) mm, (int) dd);
            return new IntResult(Status.OK, dateToInt(d));
        } catch (DateTimeException e) {
            return new IntResult(Status.OOR_DD, 0);
        }
    }

    private static DayResult intOfDay(long julYyddd) {
        long[] p = splitJul(julYyddd);
        long yy = p[0], ddd = p[1];
        int yyyy = ccInferredJdn(yy) * 100 + (int) yy;
        if (yyyy < 1601) {
            return new DayResult(Status.OOR_YYYY, 0, yyyy);
        }
        if (ddd < 1 || ddd > 366) {
            return new DayResult(Status.OOR_DDD, 0, yyyy);
        }
        LocalDate jan1 = LocalDate.of(yyyy, 1, 1);
        if (ddd > jan1.lengthOfYear()) {  // reject 366 in non-leap years
            return new DayResult(Status.OOR_DDD, 0, yyyy);
        }
        long jdn = dateToInt(jan1) + ddd - 1;
        return new DayResult(Status.OK, jdn, yyyy);
    }

    private static DateResult dateOfInt(long jdnInt) {
        if (jdnInt < 1) {
            return new DateResult(Status.OOR_YYYY, LocalDate.of(1601, 1, 1));
        }
        try {
            return new DateResult(Status.OK, intToDate(jdnInt));
        } catch (DateTimeException e) {
            return new DateResult(Status.STRANGE, LocalDate.of(1601, 1, 1));
        }
    }

    // -----------------------------------------------------------------------
    // Dispatch on DATESUB-FUNC (DATECONV.cbl 000-SELECT, lines 111-198).
    // -----------------------------------------------------------------------
    public ConvDates dispatch(int funcCode, ConvDates cd) {
        cd.datesubFunc = funcCode;
        cd.dateErrInd = "N";
        cd.dateErrReason = 0;
        switch (funcCode) {
            case 1 -> run01CheckCymdDt(cd);
            case 2 -> run02YmdToJul(cd);
            case 3 -> run03JulToYmd(cd);
            case 4 -> run04DifJul(cd);
            case 5 -> run05DifYmd(cd);
            case 6 -> run06DifCymd30(cd);
            case 7 -> run07AddJul(cd);
            case 8 -> run08AddYmd(cd);
            case 9 -> run09CheckMdyDt(cd);
            case 10 -> run10MdyToJul(cd);
            case 11 -> run11JulToMdy(cd);
            case 12 -> run12MdyToYmd(cd);
            case 13 -> run13YmdToMdy(cd);
            case 14 -> run14DifMdy(cd);
            case 15 -> run15DifJul30(cd);
            case 16 -> run16DifMdy30(cd);
            case 17 -> run17AddMdy(cd);
            case 18 -> run18YmdToCymd(cd);
            case 19 -> run19DifCymd(cd);
            case 20 -> run20AddCymd(cd);
            case 21 -> run21AddMonthsToYmd(cd);
            case 22 -> run22AddMonthsToCymd(cd);
            case 23 -> run23JulToCymd(cd);
            case 24 -> run24CymdToJul(cd);
            case 25 -> run25CymdToInt(cd);
            case 26 -> run26IntToCymd(cd);
            case 27 -> run27MdyToMdcy(cd);
            case 28 -> run28DifJulNoCheck(cd);
            case 31 -> run31JulToInt(cd);
            case 32 -> run32IntToJul(cd);
            case 33 -> run33YmdToInt(cd);
            case 34 -> run34IntToYmd(cd);
            case 35 -> run35MdyToInt(cd);
            case 36 -> run36IntToMdy(cd);
            case 37 -> run37DifFy(cd);
            case 38 -> run38RangeJul(cd);
            case 39 -> run39RangeYmd(cd);
            case 40 -> run40RangeMdy(cd);
            case 41 -> run41AddMonthsToMdy(cd);
            case 42 -> run42AddMonthsEndJul(cd);
            default -> {
                // Unknown / reserved (29, 30) -> JDN-Con-BadAction.
                cd.dateErrInd = "Y";
                cd.dateErrReason = 1;
            }
        }
        return cd;
    }

    // -- Validators (DATESUB-FUNC 1, 9) ------------------------------------
    void run01CheckCymdDt(ConvDates cd) {
        // DATECONV.cbl:225-229 (100-CHECK-CYMD-DT).
        applyStatus(cd, intOfDate(cd.fromCymdDt).status());
    }

    void run09CheckMdyDt(ConvDates cd) {
        // DATECONV.cbl:369-376 (900-CHECK-MDY-DT).
        applyStatus(cd, intOfDate(mdyToCymd(cd.fromMdyDt, false)).status());
    }

    // -- YMD <-> Julian (codes 2, 3) --------------------------------------
    void run02YmdToJul(ConvDates cd) {
        // DATECONV.cbl:231-245 (200-YMD-TO-JUL). JDN-CC=0 -> JDN threshold (>72).
        long cymd = ymdToCymd(cd.fromYmdDt, true);
        IntResult r = intOfDate(cymd);
        if (!r.status().equals(Status.OK)) {
            cd.toJulDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        long[] p = splitDateInt(cymd);
        int yyyy = (int) p[0];
        LocalDate d = LocalDate.of(yyyy, (int) ((cd.fromYmdDt / 100) % 100), (int) (cd.fromYmdDt % 100));
        long ddd = d.getDayOfYear();
        cd.fromIntDt = dateToInt(d);
        cd.toJulDt = (yyyy % 100) * 1000 + ddd;
        cd.dateErrInd = "N";
    }

    void run03JulToYmd(ConvDates cd) {
        // DATECONV.cbl:247-261 (300-JUL-TO-YMD).
        DayResult r = intOfDay(cd.fromJulDt);
        if (!r.status().equals(Status.OK)) {
            cd.toYmdDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.fromIntDt = r.value();
        LocalDate d = intToDate(r.value());
        cd.toYmdDt = (long) (d.getYear() % 100) * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        cd.dateErrInd = "N";
    }

    // -- MDY <-> Julian (codes 10, 11) ------------------------------------
    void run10MdyToJul(ConvDates cd) {
        // DATECONV.cbl:378-394 (1000-MDY-TO-JUL). JDN-CC=0 -> JDN threshold (>72).
        long cymd = mdyToCymd(cd.fromMdyDt, true);
        IntResult r = intOfDate(cymd);
        if (!r.status().equals(Status.OK)) {
            cd.toJulDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        long[] p = splitDateInt(cymd);
        LocalDate d = LocalDate.of((int) p[0], (int) p[1], (int) p[2]);
        cd.fromIntDt = dateToInt(d);
        cd.toJulDt = (long) (d.getYear() % 100) * 1000 + d.getDayOfYear();
        cd.dateErrInd = "N";
    }

    void run11JulToMdy(ConvDates cd) {
        // DATECONV.cbl:396-410 (1100-JUL-TO-MDY).
        DayResult r = intOfDay(cd.fromJulDt);
        if (!r.status().equals(Status.OK)) {
            cd.toMdyDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.fromIntDt = r.value();
        LocalDate d = intToDate(r.value());
        cd.toMdyDt = (long) d.getMonthValue() * 10000 + d.getDayOfMonth() * 100L + (d.getYear() % 100);
        cd.dateErrInd = "N";
    }

    // -- MDY <-> YMD / MDCY (codes 12, 13, 27) ----------------------------
    void run12MdyToYmd(ConvDates cd) {
        // DATECONV.cbl:412-418 (1200-MDY-TO-YMD). Pure rearrangement.
        long[] p = splitDateInt(cd.fromMdyDt);
        long mm = p[0], dd = p[1], yy = p[2];
        cd.toYmdDt = yy * 10000 + mm * 100 + dd;
        cd.dateErrInd = "N";
    }

    void run13YmdToMdy(ConvDates cd) {
        // DATECONV.cbl:420-426 (1300-YMD-TO-MDY). Pure rearrangement.
        long[] p = splitDateInt(cd.fromYmdDt);
        long yy = p[0], mm = p[1], dd = p[2];
        cd.toMdyDt = mm * 10000 + dd * 100 + yy;
        cd.dateErrInd = "N";
    }

    void run27MdyToMdcy(ConvDates cd) {
        // DATECONV.cbl:667-681 (2700-MDY-TO-MDCY).
        long cymd = mdyToCymd(cd.fromMdyDt, false);
        IntResult r = intOfDate(cymd);
        if (!r.status().equals(Status.OK)) {
            cd.toMdcyDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        long[] p = splitDateInt(cymd);
        long yyyy = p[0], mm = p[1], dd = p[2];
        cd.toMdcyDt = mm * 1000000 + dd * 10000 + yyyy;
        cd.dateErrInd = "N";
    }

    // -- YMD -> CYMD (code 18) --------------------------------------------
    void run18YmdToCymd(ConvDates cd) {
        // DATECONV.cbl:523-533 (1800-YMD-TO-CYMD).
        long cymd = ymdToCymd(cd.fromYmdDt, false);
        IntResult r = intOfDate(cymd);
        if (!r.status().equals(Status.OK)) {
            cd.toCymdDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.toCymdDt = cymd;
        cd.dateErrInd = "N";
    }

    // -- Julian <-> CYMD (codes 23, 24) -----------------------------------
    void run23JulToCymd(ConvDates cd) {
        // DATECONV.cbl:602-617 (2300-JUL-TO-CYMD). Also writes TO-YMD-DT.
        DayResult r = intOfDay(cd.fromJulDt);
        if (!r.status().equals(Status.OK)) {
            cd.toCymdDt = 0;
            cd.toYmdDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.fromIntDt = r.value();
        LocalDate d = intToDate(r.value());
        cd.toCymdDt = (long) d.getYear() * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        cd.toYmdDt = (long) (d.getYear() % 100) * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        cd.dateErrInd = "N";
    }

    void run24CymdToJul(ConvDates cd) {
        // DATECONV.cbl:619-632 (2400-CYMD-TO-JUL).
        IntResult r = intOfDate(cd.fromCymdDt);
        if (!r.status().equals(Status.OK)) {
            cd.toJulDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.fromIntDt = r.value();
        long[] p = splitDateInt(cd.fromCymdDt);
        LocalDate d = LocalDate.of((int) p[0], (int) p[1], (int) p[2]);
        cd.toJulDt = (long) (d.getYear() % 100) * 1000 + d.getDayOfYear();
        cd.dateErrInd = "N";
    }

    // -- CYMD <-> INT (codes 25, 26) --------------------------------------
    void run25CymdToInt(ConvDates cd) {
        // DATECONV.cbl:634-646 (2500-CYMD-TO-INT).
        IntResult r = intOfDate(cd.fromCymdDt);
        if (!r.status().equals(Status.OK)) {
            cd.toIntDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.toIntDt = r.value();
        cd.dateErrInd = "N";
    }

    void run26IntToCymd(ConvDates cd) {
        // DATECONV.cbl:648-665 (2600-INT-TO-CYMD). CH-645 gate: YYYY >= 1953.
        DateResult r = dateOfInt(cd.fromIntDt);
        if (!r.status().equals(Status.OK) || r.date().getYear() < 1953) {
            cd.toCymdDt = 0;
            cd.dateErrInd = "Y";
            cd.dateErrReason = 11;
            return;
        }
        LocalDate d = r.date();
        cd.toCymdDt = (long) d.getYear() * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        cd.dateErrInd = "N";
    }

    // -- INT <-> Julian/YMD/MDY (codes 31..36) ----------------------------
    void run31JulToInt(ConvDates cd) {
        // DATECONV.cbl:739-752 (3100-JUL-TO-INT).
        DayResult r = intOfDay(cd.fromJulDt);
        if (!r.status().equals(Status.OK)) {
            cd.toIntDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.toIntDt = r.value();
        cd.dateErrInd = "N";
    }

    void run32IntToJul(ConvDates cd) {
        // DATECONV.cbl:754-772 (3200-INT-TO-JUL). CH-645 gate: YYYY >= 1953.
        DateResult r = dateOfInt(cd.fromIntDt);
        if (!r.status().equals(Status.OK) || r.date().getYear() < 1953) {
            cd.toJulDt = 0;
            cd.dateErrInd = "Y";
            cd.dateErrReason = 11;
            return;
        }
        LocalDate d = r.date();
        cd.toJulDt = (long) (d.getYear() % 100) * 1000 + d.getDayOfYear();
        cd.dateErrInd = "N";
    }

    void run33YmdToInt(ConvDates cd) {
        // DATECONV.cbl:774-787 (3300-YMD-TO-INT). JDN-CC=0 -> JDN threshold (>72).
        long cymd = ymdToCymd(cd.fromYmdDt, true);
        IntResult r = intOfDate(cymd);
        if (!r.status().equals(Status.OK)) {
            cd.toIntDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.toIntDt = r.value();
        cd.dateErrInd = "N";
    }

    void run34IntToYmd(ConvDates cd) {
        // DATECONV.cbl:789-806 (3400-INT-TO-YMD). CH-645 gate: YYYY >= 1953.
        DateResult r = dateOfInt(cd.fromIntDt);
        if (!r.status().equals(Status.OK) || r.date().getYear() < 1953) {
            cd.toYmdDt = 0;
            cd.dateErrInd = "Y";
            cd.dateErrReason = 11;
            return;
        }
        LocalDate d = r.date();
        cd.toYmdDt = (long) (d.getYear() % 100) * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        cd.dateErrInd = "N";
    }

    void run35MdyToInt(ConvDates cd) {
        // DATECONV.cbl:808-823 (3500-MDY-TO-INT). JDN-CC=0 -> JDN threshold (>72).
        long cymd = mdyToCymd(cd.fromMdyDt, true);
        IntResult r = intOfDate(cymd);
        if (!r.status().equals(Status.OK)) {
            cd.toIntDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.toIntDt = r.value();
        cd.dateErrInd = "N";
    }

    void run36IntToMdy(ConvDates cd) {
        // DATECONV.cbl:825-845 (3600-INT-TO-MDY). CH-645 gate: YYYY >= 1953.
        DateResult r = dateOfInt(cd.fromIntDt);
        if (!r.status().equals(Status.OK) || r.date().getYear() < 1953) {
            cd.toMdyDt = 0;
            cd.dateErrInd = "Y";
            cd.dateErrReason = 11;
            return;
        }
        LocalDate d = r.date();
        cd.toMdyDt = (long) d.getMonthValue() * 10000 + d.getDayOfMonth() * 100L + (d.getYear() % 100);
        cd.dateErrInd = "N";
    }

    // -- DIF family (codes 4, 5, 14, 19) ----------------------------------
    void run04DifJul(ConvDates cd) {
        // DATECONV.cbl:263-287 (400-DIF-JUL). DAYS-DIF = TO - FROM.
        DayResult a = intOfDay(cd.fromJulDt);
        DayResult b = intOfDay(cd.toJulDt);
        setDif(cd, a.status(), b.status(), a.value(), b.value());
    }

    void run05DifYmd(ConvDates cd) {
        // DATECONV.cbl:289-313 (500-DIF-YMD). JDN-CC=0 -> JDN threshold (>72).
        IntResult a = intOfDate(ymdToCymd(cd.fromYmdDt, true));
        IntResult b = intOfDate(ymdToCymd(cd.toYmdDt, true));
        setDif(cd, a.status(), b.status(), a.value(), b.value());
    }

    void run14DifMdy(ConvDates cd) {
        // DATECONV.cbl:428-456 (1400-DIF-MDY). JDN-CC=0 -> JDN threshold (>72).
        IntResult a = intOfDate(mdyToCymd(cd.fromMdyDt, true));
        IntResult b = intOfDate(mdyToCymd(cd.toMdyDt, true));
        setDif(cd, a.status(), b.status(), a.value(), b.value());
    }

    void run19DifCymd(ConvDates cd) {
        // DATECONV.cbl:535-557 (1900-DIF-CYMD).
        IntResult a = intOfDate(cd.fromCymdDt);
        IntResult b = intOfDate(cd.toCymdDt);
        setDif(cd, a.status(), b.status(), a.value(), b.value());
    }

    void run28DifJulNoCheck(ConvDates cd) {
        // DATECONV.cbl:683-737 (2800-DIF-JUL-NO-CHECK). Tolerates DDD overflow.
        long a = noCheckIntOfDay(cd.fromJulDt);
        long b = noCheckIntOfDay(cd.toJulDt);
        cd.fromIntDt = a;
        cd.toIntDt = b;
        cd.daysDif = b - a;
        cd.dateErrInd = "N";
        cd.dateErrReason = 0;
    }

    void run37DifFy(ConvDates cd) {
        // DATECONV.cbl:847-859 (4000-DIF-FY). Reads YY only, infers century.
        long fromYy = cd.fromYmdDt / 10000;
        long toYy = cd.toYmdDt / 10000;
        long fromYyyy = ccInferred(fromYy) * 100L + fromYy;
        long toYyyy = ccInferred(toYy) * 100L + toYy;
        cd.fromCymdDt = fromYyyy * 10000;
        cd.toCymdDt = toYyyy * 10000;
        cd.daysDif = toYyyy - fromYyyy;
        cd.dateErrInd = "N";
        cd.dateErrReason = 0;
    }

    // -- 30-day-month DIF (codes 6, 15, 16) -------------------------------
    void run06DifCymd30(ConvDates cd) {
        // DATECONV.cbl:315-335 (600-DIF-CYMD-30). 30-day-month accounting.
        StatusInt a = difCymd30Int(cd.fromCymdDt);
        StatusInt b = difCymd30Int(cd.toCymdDt);
        setDif(cd, a.status(), b.status(), a.value(), b.value());
        if (b.status().equals(Status.OK)) {
            long[] p = splitDateInt(cd.toCymdDt);
            try {
                LocalDate dToJul = LocalDate.of((int) p[0], (int) p[1], (int) p[2]);
                cd.toJulDt = (long) (dToJul.getYear() % 100) * 1000 + dToJul.getDayOfYear();
            } catch (DateTimeException e) {
                cd.toJulDt = 0;
            }
        }
    }

    void run15DifJul30(ConvDates cd) {
        // DATECONV.cbl:458-481 (1500-DIF-JUL-30). 30-day-month over Julian inputs.
        StatusInt a = difJul30Int(cd.fromJulDt);
        StatusInt b = difJul30Int(cd.toJulDt);
        setDif(cd, a.status(), b.status(), a.value(), b.value());
    }

    void run16DifMdy30(ConvDates cd) {
        // DATECONV.cbl:483-503 (1600-DIF-MDY-30). JDN-CC=0 -> JDN threshold (>72).
        long cymdTo = mdyToCymd(cd.toMdyDt, true);
        StatusInt a = difCymd30Int(mdyToCymd(cd.fromMdyDt, true));
        StatusInt b = difCymd30Int(cymdTo);
        setDif(cd, a.status(), b.status(), a.value(), b.value());
        if (b.status().equals(Status.OK)) {
            long[] p = splitDateInt(cymdTo);
            try {
                LocalDate dToJul = LocalDate.of((int) p[0], (int) p[1], (int) p[2]);
                cd.toJulDt = (long) (dToJul.getYear() % 100) * 1000 + dToJul.getDayOfYear();
            } catch (DateTimeException e) {
                cd.toJulDt = 0;
            }
        }
    }

    // -- ADD family (codes 7, 8, 17, 20) ----------------------------------
    void run07AddJul(ConvDates cd) {
        // DATECONV.cbl:337-351 (700-ADD-JUL).
        DayResult r = intOfDay(cd.fromJulDt);
        if (!r.status().equals(Status.OK)) {
            cd.toJulDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.fromIntDt = r.value() + cd.daysDif;
        DateResult d2 = dateOfInt(cd.fromIntDt);
        if (!d2.status().equals(Status.OK)) {
            cd.toJulDt = 0;
            applyStatus(cd, d2.status());
            return;
        }
        LocalDate d = d2.date();
        cd.toJulDt = (long) (d.getYear() % 100) * 1000 + d.getDayOfYear();
        cd.dateErrInd = "N";
    }

    void run08AddYmd(ConvDates cd) {
        // DATECONV.cbl:353-367 (800-ADD-YMD). JDN-CC=0 -> JDN threshold (>72).
        IntResult r = intOfDate(ymdToCymd(cd.fromYmdDt, true));
        if (!r.status().equals(Status.OK)) {
            cd.toYmdDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.fromIntDt = r.value() + cd.daysDif;
        DateResult d2 = dateOfInt(cd.fromIntDt);
        if (!d2.status().equals(Status.OK)) {
            cd.toYmdDt = 0;
            applyStatus(cd, d2.status());
            return;
        }
        LocalDate d = d2.date();
        cd.toYmdDt = (long) (d.getYear() % 100) * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        cd.dateErrInd = "N";
    }

    void run17AddMdy(ConvDates cd) {
        // DATECONV.cbl:505-521 (1700-ADD-MDY). JDN-CC=0 -> JDN threshold (>72).
        IntResult r = intOfDate(mdyToCymd(cd.fromMdyDt, true));
        if (!r.status().equals(Status.OK)) {
            cd.toMdyDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.fromIntDt = r.value() + cd.daysDif;
        DateResult d2 = dateOfInt(cd.fromIntDt);
        if (!d2.status().equals(Status.OK)) {
            cd.toMdyDt = 0;
            applyStatus(cd, d2.status());
            return;
        }
        LocalDate d = d2.date();
        cd.toMdyDt = (long) d.getMonthValue() * 10000 + d.getDayOfMonth() * 100L + (d.getYear() % 100);
        cd.dateErrInd = "N";
    }

    void run20AddCymd(ConvDates cd) {
        // DATECONV.cbl:559-573 (2000-ADD-CYMD). Also writes TO-YMD-DT.
        IntResult r = intOfDate(cd.fromCymdDt);
        if (!r.status().equals(Status.OK)) {
            cd.toCymdDt = 0;
            cd.toYmdDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.fromIntDt = r.value() + cd.daysDif;
        DateResult d2 = dateOfInt(cd.fromIntDt);
        if (!d2.status().equals(Status.OK)) {
            cd.toCymdDt = 0;
            cd.toYmdDt = 0;
            applyStatus(cd, d2.status());
            return;
        }
        LocalDate d = d2.date();
        cd.toCymdDt = (long) d.getYear() * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        cd.toYmdDt = (long) (d.getYear() % 100) * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        cd.dateErrInd = "N";
    }

    // -- ADD-MONTHS family (codes 21, 22, 41, 42) -------------------------
    void run21AddMonthsToYmd(ConvDates cd) {
        // DATECONV.cbl:575-587 (2100-ADD-MONTHS-TO-YMD). JDN threshold (>72).
        AddMonthsResult r = addMonthsCymd(ymdToCymd(cd.fromYmdDt, true), cd.monthsToAdd, false);
        if (!r.status().equals(Status.OK)) {
            cd.toYmdDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.toYmdDt = (long) (r.y() % 100) * 10000 + r.m() * 100L + r.d();
        cd.dateErrInd = "N";
    }

    void run22AddMonthsToCymd(ConvDates cd) {
        // DATECONV.cbl:589-600 (2200-ADD-MONTHS-TO-CYMD).
        AddMonthsResult r = addMonthsCymd(cd.fromCymdDt, cd.monthsToAdd, false);
        if (!r.status().equals(Status.OK)) {
            cd.toCymdDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.toCymdDt = (long) r.y() * 10000 + r.m() * 100L + r.d();
        cd.dateErrInd = "N";
    }

    void run41AddMonthsToMdy(ConvDates cd) {
        // DATECONV.cbl:987-1003 (4400-ADD-MONTHS-TO-MDY). JDN threshold (>72).
        AddMonthsResult r = addMonthsCymd(mdyToCymd(cd.fromMdyDt, true), cd.monthsToAdd, false);
        if (!r.status().equals(Status.OK)) {
            cd.toMdyDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        cd.toMdyDt = (long) r.m() * 10000 + r.d() * 100L + (r.y() % 100);
        cd.dateErrInd = "N";
    }

    void run42AddMonthsEndJul(ConvDates cd) {
        // DATECONV.cbl:1005-1021 (4500-ADD-MONTHS-END-JUL).
        DayResult r = intOfDay(cd.fromJulDt);
        if (!r.status().equals(Status.OK)) {
            cd.toJulDt = 0;
            cd.toCymdDt = 0;
            cd.toYmdDt = 0;
            applyStatus(cd, r.status());
            return;
        }
        LocalDate d = intToDate(r.value());
        cd.toCymdDt = (long) d.getYear() * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        cd.toYmdDt = (long) (d.getYear() % 100) * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth();
        boolean snapToEom = d.getDayOfMonth() == daysInMonth(d.getYear(), d.getMonthValue());
        AddMonthsResult am = addMonthsCymd(
                (long) d.getYear() * 10000 + d.getMonthValue() * 100L + d.getDayOfMonth(),
                cd.monthsToAdd, snapToEom);
        if (!am.status().equals(Status.OK)) {
            cd.toJulDt = 0;
            applyStatus(cd, am.status());
            return;
        }
        LocalDate dt2 = LocalDate.of(am.y(), am.m(), am.d());
        cd.toJulDt = (long) (am.y() % 100) * 1000 + dt2.getDayOfYear();
        cd.dateErrInd = "N";
    }

    // -- RANGE family (codes 38, 39, 40) ----------------------------------
    void run38RangeJul(ConvDates cd) {
        // DATECONV.cbl:861-899 (4100-RANGE-JUL).
        DayResult a = intOfDay(cd.fromJulDt);
        DayResult b = intOfDay(cd.toJulDt);
        DayResult c = intOfDay(cd.betweenJulDt);
        rangeCheck(cd, a.value(), b.value(), c.value(), a.status(), b.status(), c.status());
    }

    void run39RangeYmd(ConvDates cd) {
        // DATECONV.cbl:901-939 (4200-RANGE-YMD). JDN threshold (>72).
        IntResult a = intOfDate(ymdToCymd(cd.fromYmdDt, true));
        IntResult b = intOfDate(ymdToCymd(cd.toYmdDt, true));
        IntResult c = intOfDate(ymdToCymd(cd.betweenYmdDt, true));
        rangeCheck(cd, a.value(), b.value(), c.value(), a.status(), b.status(), c.status());
    }

    void run40RangeMdy(ConvDates cd) {
        // DATECONV.cbl:941-985 (4300-RANGE-MDY). JDN threshold (>72).
        IntResult a = intOfDate(mdyToCymd(cd.fromMdyDt, true));
        IntResult b = intOfDate(mdyToCymd(cd.toMdyDt, true));
        IntResult c = intOfDate(mdyToCymd(cd.betweenMdyDt, true));
        rangeCheck(cd, a.value(), b.value(), c.value(), a.status(), b.status(), c.status());
    }

    // -----------------------------------------------------------------------
    // Internal helpers (status mapping + 30-day-month math + ADD-MONTHS).
    // -----------------------------------------------------------------------
    static int reasonFor(String status) {
        return switch (status) {
            case Status.OK -> 0;
            case Status.OOR_DD -> 7;
            case Status.OOR_DDD -> 8;
            case Status.OOR_MM -> 10;
            case Status.OOR_YYYY -> 11;
            case Status.STRANGE -> 12;
            default -> 12;
        };
    }

    static String statusForReason(int reason) {
        return switch (reason) {
            case 0 -> Status.OK;
            case 7 -> Status.OOR_DD;
            case 8 -> Status.OOR_DDD;
            case 10 -> Status.OOR_MM;
            case 11 -> Status.OOR_YYYY;
            case 12 -> Status.STRANGE;
            default -> Status.STRANGE;
        };
    }

    private static void applyStatus(ConvDates cd, String status) {
        if (status.equals(Status.OK)) {
            cd.dateErrInd = "N";
            cd.dateErrReason = 0;
        } else {
            cd.dateErrInd = "Y";
            cd.dateErrReason = reasonFor(status);
        }
    }

    private static void setDif(ConvDates cd, String s1, String s2, long a, long b) {
        // COBOL DIF paragraphs write FROM-INT-DT only and never assign TO-INT-DT.
        if (!s1.equals(Status.OK) || !s2.equals(Status.OK)) {
            cd.daysDif = 0;
            cd.dateErrInd = "Y";
            cd.dateErrReason = reasonFor(!s1.equals(Status.OK) ? s1 : s2);
            return;
        }
        cd.fromIntDt = a;
        cd.daysDif = b - a;
        cd.dateErrInd = "N";
    }

    private static void rangeCheck(ConvDates cd, long a, long b, long c,
                                   String s1, String s2, String s3) {
        // 88888 = within, 77777 = outside (DATECONV.cbl:886-888).
        if (!s1.equals(Status.OK)) {
            cd.daysDif = 0;
            cd.dateErrInd = "Y";
            cd.dateErrReason = reasonFor(s1);
            return;
        }
        cd.fromIntDt = a;
        if (!s2.equals(Status.OK)) {
            cd.daysDif = 0;
            cd.dateErrInd = "Y";
            cd.dateErrReason = reasonFor(s2);
            return;
        }
        cd.toIntDt = b;
        long between = s3.equals(Status.OK) ? c : 0;
        cd.daysDif = (a <= between && between <= b) ? 88888 : 77777;
        cd.dateErrInd = "N";
    }

    private static int daysInMonth(long yyyy, long mm) {
        return YearMonth.of((int) yyyy, (int) mm).lengthOfMonth();
    }

    private static AddMonthsResult addMonthsCymd(long cymd, long months, boolean forceEom) {
        // DATECONV.cbl:1023-1052 (9910-ADD-MONTHS) — snap-to-end-of-month.
        IntResult r = intOfDate(cymd);
        if (!r.status().equals(Status.OK)) {
            return new AddMonthsResult(r.status(), 0, 0, 0);
        }
        long[] p = splitDateInt(cymd);
        long yyyy = p[0], mm = p[1], dd = p[2];
        long total = (yyyy * 12 + (mm - 1)) + months;
        long newY = Math.floorDiv(total, 12);
        long newM = Math.floorMod(total, 12) + 1;
        if (newY < 1601) {
            return new AddMonthsResult(Status.OOR_YYYY, 0, 0, 0);
        }
        int eom = daysInMonth(newY, newM);
        long newD = (dd > eom || forceEom) ? eom : dd;
        return new AddMonthsResult(Status.OK, (int) newY, (int) newM, (int) newD);
    }

    private static long noCheckIntOfDay(long julYyddd) {
        // 2800-DIF-JUL-NO-CHECK tolerates DDD > 365 by carrying into next year.
        long[] p = splitJul(julYyddd);
        long yy = p[0], ddd = p[1];
        int yyyy = ccInferredJdn(yy) * 100 + (int) yy;
        if (julYyddd == 0) {
            return 0;
        }
        return dateToInt(LocalDate.of(yyyy, 1, 1)) + ddd - 1;
    }

    private static StatusInt difCymd30Int(long cymd) {
        // 30-day-month accounting: every full year = 360 days.
        long[] p = splitDateInt(cymd);
        long yyyy = p[0], mm = p[1], dd = p[2];
        if (yyyy < 1601) {
            return new StatusInt(Status.OOR_YYYY, 0);
        }
        if (mm < 1 || mm > 12) {
            return new StatusInt(Status.OOR_MM, 0);
        }
        if (dd < 1 || dd > 31) {
            return new StatusInt(Status.OOR_DD, 0);
        }
        long ddCapped = Math.min(dd, 30);
        return new StatusInt(Status.OK, yyyy * 360 + (mm - 1) * 30 + (ddCapped - 1));
    }

    private static final int[] CUMDAYS_COMMON =
            {0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365};
    private static final int[] CUMDAYS_LEAP =
            {0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366};

    private static boolean isLeap(int y) {
        return (y % 4 == 0 && y % 100 != 0) || (y % 400 == 0);
    }

    private static int[] cumulativeDays(int yyyy) {
        return isLeap(yyyy) ? CUMDAYS_LEAP : CUMDAYS_COMMON;
    }

    private static StatusInt difJul30Int(long jul) {
        // DATECONV.cbl:1074-1108 (9940-CONV-JUL-30): map DDD into 30-day-month.
        long[] p = splitJul(jul);
        long yy = p[0], ddd = p[1];
        int yyyy = ccInferred(yy) * 100 + (int) yy;
        if (yyyy < 1601) {
            return new StatusInt(Status.OOR_YYYY, 0);
        }
        if (ddd < 1 || ddd > 366) {
            return new StatusInt(Status.OOR_DDD, 0);
        }
        boolean leap = isLeap(yyyy);
        if (ddd > (leap ? 366 : 365)) {
            return new StatusInt(Status.OOR_DDD, 0);
        }
        int[] eomReal = cumulativeDays(yyyy);
        int mm = 1;
        while (mm <= 12 && ddd > eomReal[mm]) {
            mm++;
        }
        if (mm > 12) {
            return new StatusInt(Status.OOR_DDD, 0);
        }
        long ddReal = ddd - eomReal[mm - 1];
        long dd30 = Math.min(ddReal, 30);
        return new StatusInt(Status.OK, (long) yyyy * 360 + (mm - 1) * 30 + (dd30 - 1));
    }
}
