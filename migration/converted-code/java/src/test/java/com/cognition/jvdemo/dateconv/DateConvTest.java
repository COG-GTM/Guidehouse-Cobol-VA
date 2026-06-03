package com.cognition.jvdemo.dateconv;

import org.junit.jupiter.api.Test;

import static com.cognition.jvdemo.dateconv.DateConvFunctions.*;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * JUnit 5 port of tests/test_dateconv.py. Covers all 40 active DATESUB-FUNC
 * entry paragraphs (codes 1..42 minus reserved 29/30), dispatch behavior, leap
 * years (1900/2000/2024), century rollover, and round-trip identities.
 */
class DateConvTest {

    private static void assertConv(String expStatus, long expValue, Conv actual) {
        assertEquals(expStatus, actual.status());
        assertEquals(expValue, actual.value());
    }

    // ---- validators (codes 1, 9) -----------------------------------------
    @Test void checkCymdValid() {
        Check c = checkCymdDt("20251230");
        assertEquals(Status.OK, c.status());
        assertTrue(c.ok());
    }

    @Test void checkCymdInvalidMonth() {
        assertEquals(Status.OOR_MM, checkCymdDt("20251345").status());
    }

    @Test void checkCymdInvalidDay() {
        assertEquals(Status.OOR_DD, checkCymdDt("20240230").status());
    }

    @Test void checkCymdYearBelow1601() {
        assertEquals(Status.OOR_YYYY, checkCymdDt("16000101").status());
    }

    @Test void checkCymdLeap2000_400Rule() {
        Check c = checkCymdDt("20000229");
        assertEquals(Status.OK, c.status());
        assertTrue(c.ok());
    }

    @Test void checkCymdNonLeap1900_100Rule() {
        assertEquals(Status.OOR_DD, checkCymdDt("19000229").status());
    }

    @Test void checkCymdLeap2024() {
        Check c = checkCymdDt("20240229");
        assertEquals(Status.OK, c.status());
        assertTrue(c.ok());
    }

    @Test void checkCymdNonDigit() {
        assertEquals(Status.STRANGE, checkCymdDt("ABCDEFGH").status());
    }

    @Test void checkCymdWrongLength() {
        assertEquals(Status.STRANGE, checkCymdDt("2025123").status());
    }

    @Test void checkCymdIntInput() {
        Check c = checkCymdDt(20251230L);
        assertEquals(Status.OK, c.status());
        assertTrue(c.ok());
    }

    @Test void checkMdyValid() {
        Check c = checkMdyDt("022924");  // 2024-02-29 (leap)
        assertEquals(Status.OK, c.status());
        assertTrue(c.ok());
    }

    @Test void checkMdyNonLeap() {
        assertFalse(checkMdyDt("022925").ok());  // 2025-02-29 invalid
    }

    @Test void checkMdyCenturyYyLe52() {
        assertEquals(Status.OK, checkMdyDt("010100").status());  // YY=00 -> 2000
    }

    @Test void checkMdyCenturyYyGt52() {
        assertEquals(Status.OK, checkMdyDt("010153").status());  // YY=53 -> 1953
    }

    // ---- YMD <-> Julian (codes 2,3) + MDY <-> Julian (codes 10,11) -------
    @Test void ymdToJulJan1() { assertConv(Status.OK, 24001, ymdToJul("240101")); }

    @Test void ymdToJulLeapYearEnd() { assertConv(Status.OK, 24366, ymdToJul("241231")); }

    @Test void julToYmdRoundtrip() { assertConv(Status.OK, 241231, julToYmd("24366")); }

    @Test void julToYmdInvalidDdd() {
        assertEquals(Status.OOR_DDD, julToYmd("25366").status());  // 2025 non-leap
    }

    @Test void mdyToJulTest() { assertConv(Status.OK, 24366, mdyToJul("123124")); }

    @Test void julToMdyTest() { assertConv(Status.OK, 123124, julToMdy("24366")); }

    // ---- format-only rearrangement (codes 12,13,18,27) -------------------
    @Test void mdyToYmdPure() { assertConv(Status.OK, 241225, mdyToYmd("122524")); }

    @Test void ymdToMdyPure() { assertConv(Status.OK, 122524, ymdToMdy("241225")); }

    @Test void ymdToCymdTest() { assertConv(Status.OK, 20241225, ymdToCymd("241225")); }

    @Test void ymdToCymdCentury19() { assertConv(Status.OK, 19990401, ymdToCymd("990401")); }

    @Test void mdyToMdcyTest() { assertConv(Status.OK, 12252024, mdyToMdcy("122524")); }

    // ---- CYMD <-> Julian/INT (codes 23,24,25,26) -------------------------
    @Test void julToCymdTest() { assertConv(Status.OK, 20241231, julToCymd("24366")); }

    @Test void cymdToJulTest() { assertConv(Status.OK, 24001, cymdToJul("20240101")); }

    @Test void cymdToIntEpoch() { assertConv(Status.OK, 1, cymdToInt("16010101")); }

    @Test void intToCymdBelowCh645Rejected() {
        assertEquals(Status.OOR_YYYY, intToCymd(1).status());
    }

    @Test void intToCymdModern() {
        Conv n = cymdToInt("20240115");
        assertEquals(Status.OK, n.status());
        assertConv(Status.OK, 20240115, intToCymd(n.value()));
    }

    @Test void cymdIntRoundTrip() {
        for (String cymd : new String[] {"19530101", "20000229", "20240229", "20991231"}) {
            Conv n = cymdToInt(cymd);
            assertEquals(Status.OK, n.status());
            assertConv(Status.OK, Long.parseLong(cymd), intToCymd(n.value()));
        }
    }

    // ---- INT <-> Julian/YMD/MDY (codes 31..36) ---------------------------
    @Test void julToIntTest() { assertEquals(Status.OK, julToInt("24001").status()); }

    @Test void intToJulRoundTrip() {
        Conv n = julToInt("24001");
        assertConv(Status.OK, 24001, intToJul(n.value()));
    }

    @Test void ymdToIntAndBack() {
        Conv n = ymdToInt("240101");
        assertEquals(Status.OK, n.status());
        assertConv(Status.OK, 240101, intToYmd(n.value()));
    }

    @Test void mdyToIntAndBack() {
        Conv n = mdyToInt("010124");
        assertEquals(Status.OK, n.status());
        assertConv(Status.OK, 10124, intToMdy(n.value()));
    }

    // ---- DIF family (codes 4,5,6,14,15,16,19,28,37) ----------------------
    @Test void difJulFullYear() { assertConv(Status.OK, 365, difJul("24001", "24366")); }

    @Test void difJulNegative() { assertConv(Status.OK, -366, difJul("25001", "24001")); }

    @Test void difYmdTest() { assertConv(Status.OK, 31, difYmd("240101", "240201")); }

    @Test void difMdyTest() { assertConv(Status.OK, 31, difMdy("010124", "020124")); }

    @Test void difCymdTest() { assertConv(Status.OK, 366, difCymd("20240101", "20250101")); }

    @Test void difFySameYear() { assertConv(Status.OK, 0, difFy("240101", "240901")); }

    @Test void difFyCenturyRollover() { assertConv(Status.OK, 2, difFy("990101", "010101")); }

    @Test void difJul30FullYear() { assertConv(Status.OK, 360, difJul30("24001", "25001")); }

    @Test void difCymd30Test() { assertConv(Status.OK, 30, difCymd30("20240115", "20240215")); }

    @Test void difMdy30Test() { assertConv(Status.OK, 30, difMdy30("011524", "021524")); }

    @Test void difJulNoCheckOverflow() {
        Conv r = difJulNoCheck("24001", "24370");
        assertEquals(Status.OK, r.status());
        assertEquals(369, r.value());
    }

    // ---- ADD family (codes 7,8,17,20) ------------------------------------
    @Test void addJulWrap() { assertConv(Status.OK, 25001, addJul("24366", 1)); }

    @Test void addJulBackward() { assertConv(Status.OK, 24366, addJul("25001", -1)); }

    @Test void addYmdMonthBoundary() { assertConv(Status.OK, 240201, addYmd("240131", 1)); }

    @Test void addMdyTest() { assertConv(Status.OK, 20124, addMdy("013124", 1)); }

    @Test void addCymdYearWrap() { assertConv(Status.OK, 20250101, addCymd("20241231", 1)); }

    // ---- ADD-MONTHS family (codes 21,22,41,42) ---------------------------
    @Test void addMonthsToCymdEomSnapLeap() {
        assertConv(Status.OK, 20240229, addMonthsToCymd("20240131", 1));
    }

    @Test void addMonthsToCymdEomSnapNonLeap() {
        assertConv(Status.OK, 20230228, addMonthsToCymd("20230131", 1));
    }

    @Test void addMonthsToCymdYearWrap() {
        assertConv(Status.OK, 20250115, addMonthsToCymd("20240115", 12));
    }

    @Test void addMonthsToYmdTest() { assertConv(Status.OK, 240229, addMonthsToYmd("240131", 1)); }

    @Test void addMonthsToMdyTest() { assertConv(Status.OK, 22924, addMonthsToMdy("013124", 1)); }

    @Test void addMonthsEndJulForceEom() {
        assertConv(Status.OK, 24060, addMonthsEndJul("24031", 1));
    }

    // ---- RANGE family (codes 38,39,40) -----------------------------------
    @Test void rangeJulInside() { assertConv(Status.OK, 88888, rangeJul("24001", "24365", "24180")); }

    @Test void rangeJulOutside() { assertConv(Status.OK, 77777, rangeJul("24001", "24180", "24365")); }

    @Test void rangeJulBoundary() { assertConv(Status.OK, 88888, rangeJul("24001", "24365", "24001")); }

    @Test void rangeYmdInside() { assertConv(Status.OK, 88888, rangeYmd("240101", "241231", "240615")); }

    @Test void rangeMdyOutside() { assertConv(Status.OK, 77777, rangeMdy("010124", "063024", "070124")); }

    // ---- dispatch idiom (DATECONV.cbl:111-198) ---------------------------
    @Test void func1Dispatch() {
        ConvDates cd = new ConvDates();
        cd.fromCymdDt = 20240229;
        new DateConv().dispatch(1, cd);
        assertEquals("N", cd.dateErrInd);
        assertEquals(1, cd.datesubFunc);
    }

    @Test void func1InvalidSetsErrInd() {
        ConvDates cd = new ConvDates();
        cd.fromCymdDt = 20240230;
        new DateConv().dispatch(1, cd);
        assertEquals("Y", cd.dateErrInd);
        assertEquals(7, cd.dateErrReason);  // OutOfRangeDD
    }

    @Test void func2DispatchPopulatesToJul() {
        ConvDates cd = new ConvDates();
        cd.fromYmdDt = 240101;
        new DateConv().dispatch(2, cd);
        assertEquals(24001, cd.toJulDt);
    }

    @Test void unknownFuncSetsErr() {
        ConvDates cd = new ConvDates();
        new DateConv().dispatch(999, cd);
        assertEquals("Y", cd.dateErrInd);
    }

    @Test void func29UnusedReturnsErr() {
        ConvDates cd = new ConvDates();
        new DateConv().dispatch(29, cd);
        assertEquals("Y", cd.dateErrInd);
    }

    @Test void thruAliasReadsTo() {
        ConvDates cd = new ConvDates();
        cd.toJulDt = 24180;
        assertEquals(24180, cd.thruJulDt());
        cd.thruJulDt(24365);
        assertEquals(24365, cd.toJulDt);
    }

    // ---- edge cases -------------------------------------------------------
    @Test void month13Rejected() { assertEquals(Status.OOR_MM, checkCymdDt("20241301").status()); }

    @Test void dayZeroRejected() { assertEquals(Status.OOR_DD, checkCymdDt("20240100").status()); }

    @Test void feb30Rejected() { assertEquals(Status.OOR_DD, checkCymdDt("20240230").status()); }

    @Test void yearZeroRejected() { assertEquals(Status.OOR_YYYY, checkCymdDt("00000101").status()); }

    @Test void statusCodesMirrorJdnConstants() {
        assertEquals("OK", Status.OK);
        assertEquals("OutOfRangeDD", Status.OOR_DD);
        assertEquals("OutOfRangeDDD", Status.OOR_DDD);
        assertEquals("OutOfRangeMM", Status.OOR_MM);
        assertEquals("OutOfRangeYYYY", Status.OOR_YYYY);
        assertEquals("Strange", Status.STRANGE);
    }

    @Test void invalidPropagatesThroughDif() {
        assertEquals(Status.OOR_DD, difCymd("20240230", "20240501").status());
    }
}
