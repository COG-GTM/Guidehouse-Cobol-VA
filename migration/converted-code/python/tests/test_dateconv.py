"""
test_dateconv.py — pytest suite for the modernized DATECONV port.

Covers all 40 DATESUB-FUNC entry paragraphs (codes 1..42 minus 29/30 unused),
plus dispatch behavior, edge cases (leap years 1900/2000/2024, century rollover,
DATE-ERR/DATE-IS-VALID semantics), and round-trip identities.

Source citations: see migration/converted-code/python/dateconv.py and
source/cobol/DATECONV.cbl line ranges noted at each method.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT / "migration" / "converted-code"))

from python import dateconv  # noqa: E402
from python.dateconv import (  # noqa: E402
    ConvDates,
    DateConv,
    STATUS_OK,
    STATUS_OOR_DD,
    STATUS_OOR_DDD,
    STATUS_OOR_MM,
    STATUS_OOR_YYYY,
    STATUS_STRANGE,
    add_cymd,
    add_jul,
    add_mdy,
    add_months_end_jul,
    add_months_to_cymd,
    add_months_to_mdy,
    add_months_to_ymd,
    add_ymd,
    check_cymd_dt,
    check_mdy_dt,
    cymd_to_int,
    cymd_to_jul,
    dif_cymd,
    dif_cymd_30,
    dif_fy,
    dif_jul,
    dif_jul_30,
    dif_jul_no_check,
    dif_mdy,
    dif_mdy_30,
    dif_ymd,
    int_to_cymd,
    int_to_jul,
    int_to_mdy,
    int_to_ymd,
    jul_to_cymd,
    jul_to_int,
    jul_to_mdy,
    jul_to_ymd,
    mdy_to_int,
    mdy_to_jul,
    mdy_to_mdcy,
    mdy_to_ymd,
    range_jul,
    range_mdy,
    range_ymd,
    ymd_to_cymd,
    ymd_to_int,
    ymd_to_jul,
    ymd_to_mdy,
)


# ---------------------------------------------------------------------------
# Validators (codes 1, 9) — DATE-ERR vs DATE-IS-VALID 88-level semantics
# ---------------------------------------------------------------------------
class TestCheckCYMD:
    def test_valid_date(self):
        assert check_cymd_dt("20251230") == (STATUS_OK, True)

    def test_invalid_month(self):
        assert check_cymd_dt("20251345")[0] == STATUS_OOR_MM

    def test_invalid_day(self):
        assert check_cymd_dt("20240230")[0] == STATUS_OOR_DD

    def test_year_below_1601(self):
        assert check_cymd_dt("16000101")[0] == STATUS_OOR_YYYY

    def test_leap_2000_400_rule(self):
        # 2000 is leap (divisible by 400).
        assert check_cymd_dt("20000229") == (STATUS_OK, True)

    def test_non_leap_1900_100_rule(self):
        # 1900 is NOT leap (divisible by 100, not by 400).
        assert check_cymd_dt("19000229")[0] == STATUS_OOR_DD

    def test_leap_2024(self):
        assert check_cymd_dt("20240229") == (STATUS_OK, True)

    def test_non_digit_string(self):
        assert check_cymd_dt("ABCDEFGH")[0] == STATUS_STRANGE

    def test_wrong_length(self):
        assert check_cymd_dt("2025123")[0] == STATUS_STRANGE

    def test_int_input(self):
        assert check_cymd_dt(20251230) == (STATUS_OK, True)


class TestCheckMDY:
    def test_valid_mdy(self):
        assert check_mdy_dt("022924") == (STATUS_OK, True)  # 2024-02-29 (leap)

    def test_non_leap(self):
        assert check_mdy_dt("022925")[1] is False  # 2025-02-29 invalid

    def test_century_inference_yy_le_52(self):
        # YY=00 → 2000 per 9920-CALC-YY-TO-YYYY.
        assert check_mdy_dt("010100") == (STATUS_OK, True)

    def test_century_inference_yy_gt_52(self):
        # YY=53 → 1953 per 9920-CALC-YY-TO-YYYY (CH-645 lowest).
        assert check_mdy_dt("010153") == (STATUS_OK, True)


# ---------------------------------------------------------------------------
# YMD ↔ Julian (codes 2, 3) + MDY ↔ Julian (codes 10, 11)
# ---------------------------------------------------------------------------
class TestYmdJul:
    def test_ymd_to_jul_jan1(self):
        assert ymd_to_jul("240101") == (STATUS_OK, 24001)

    def test_ymd_to_jul_leap_year_end(self):
        # 2024 is a leap year → DDD=366 on Dec 31.
        assert ymd_to_jul("241231") == (STATUS_OK, 24366)

    def test_jul_to_ymd_roundtrip(self):
        assert jul_to_ymd("24366") == (STATUS_OK, 241231)

    def test_jul_to_ymd_invalid_ddd(self):
        # DDD=366 in 2025 (non-leap) is invalid.
        assert jul_to_ymd("25366")[0] == STATUS_OOR_DDD

    def test_mdy_to_jul(self):
        assert mdy_to_jul("123124") == (STATUS_OK, 24366)

    def test_jul_to_mdy(self):
        assert jul_to_mdy("24366") == (STATUS_OK, 123124)


# ---------------------------------------------------------------------------
# Format-only rearrangement (codes 12, 13, 18, 27)
# ---------------------------------------------------------------------------
class TestFormatShuffles:
    def test_mdy_to_ymd_pure(self):
        # 1200-MDY-TO-YMD does no validation per DATECONV.cbl:412-418.
        assert mdy_to_ymd("122524") == (STATUS_OK, 241225)

    def test_ymd_to_mdy_pure(self):
        assert ymd_to_mdy("241225") == (STATUS_OK, 122524)

    def test_ymd_to_cymd(self):
        # YY=24 → century 20.
        assert ymd_to_cymd("241225") == (STATUS_OK, 20241225)

    def test_ymd_to_cymd_century_19(self):
        # YY=99 > 52 → century 19.
        assert ymd_to_cymd("990401") == (STATUS_OK, 19990401)

    def test_mdy_to_mdcy(self):
        assert mdy_to_mdcy("122524") == (STATUS_OK, 12252024)


# ---------------------------------------------------------------------------
# CYMD ↔ Julian / INT (codes 23, 24, 25, 26)
# ---------------------------------------------------------------------------
class TestCymdConversions:
    def test_jul_to_cymd(self):
        assert jul_to_cymd("24366") == (STATUS_OK, 20241231)

    def test_cymd_to_jul(self):
        assert cymd_to_jul("20240101") == (STATUS_OK, 24001)

    def test_cymd_to_int_epoch(self):
        # 1601-01-01 = JDN 1 per JDN-CONSTANTS-WS.cpy.
        assert cymd_to_int("16010101") == (STATUS_OK, 1)

    def test_int_to_cymd_below_ch645_rejected(self):
        # CH-645 (DATECONV.cbl 9990) gates output at YYYY >= 1953.
        assert int_to_cymd(1)[0] == STATUS_OOR_YYYY

    def test_int_to_cymd_modern(self):
        s, n = cymd_to_int("20240115")
        assert s == STATUS_OK
        assert int_to_cymd(n) == (STATUS_OK, 20240115)

    def test_cymd_int_round_trip(self):
        for cymd in ("19530101", "20000229", "20240229", "20991231"):
            s1, n = cymd_to_int(cymd)
            assert s1 == STATUS_OK
            assert int_to_cymd(n) == (STATUS_OK, int(cymd))


# ---------------------------------------------------------------------------
# INT ↔ Julian/YMD/MDY (codes 31..36)
# ---------------------------------------------------------------------------
class TestIntConversions:
    def test_jul_to_int(self):
        assert jul_to_int("24001")[0] == STATUS_OK

    def test_int_to_jul_round_trip(self):
        s, n = jul_to_int("24001")
        assert int_to_jul(n) == (STATUS_OK, 24001)

    def test_ymd_to_int_and_back(self):
        s, n = ymd_to_int("240101")
        assert s == STATUS_OK
        assert int_to_ymd(n) == (STATUS_OK, 240101)

    def test_mdy_to_int_and_back(self):
        s, n = mdy_to_int("010124")
        assert s == STATUS_OK
        assert int_to_mdy(n) == (STATUS_OK, 10124)


# ---------------------------------------------------------------------------
# DIF family (codes 4, 5, 6, 14, 15, 16, 19, 28, 37)
# ---------------------------------------------------------------------------
class TestDifFamily:
    def test_dif_jul_full_year(self):
        # Distance from 2024-001 to 2024-366 = 365 days.
        assert dif_jul("24001", "24366") == (STATUS_OK, 365)

    def test_dif_jul_negative(self):
        assert dif_jul("25001", "24001") == (STATUS_OK, -366)

    def test_dif_ymd(self):
        assert dif_ymd("240101", "240201") == (STATUS_OK, 31)

    def test_dif_mdy(self):
        assert dif_mdy("010124", "020124") == (STATUS_OK, 31)

    def test_dif_cymd(self):
        assert dif_cymd("20240101", "20250101") == (STATUS_OK, 366)

    def test_dif_fy_same_year(self):
        assert dif_fy("240101", "240901") == (STATUS_OK, 0)

    def test_dif_fy_century_rollover(self):
        # YY=99 → 1999, YY=01 → 2001 per 9920-CALC-YY-TO-YYYY.
        assert dif_fy("990101", "010101") == (STATUS_OK, 2)

    def test_dif_jul_30_full_year(self):
        # 30-day-month calendar: full year = 360 days.
        assert dif_jul_30("24001", "25001") == (STATUS_OK, 360)

    def test_dif_cymd_30(self):
        assert dif_cymd_30("20240115", "20240215") == (STATUS_OK, 30)

    def test_dif_mdy_30(self):
        assert dif_mdy_30("011524", "021524") == (STATUS_OK, 30)

    def test_dif_jul_no_check_overflow(self):
        # 2800-DIF-JUL-NO-CHECK tolerates DDD > 365 by carrying.
        s, days = dif_jul_no_check("24001", "24370")
        assert s == STATUS_OK
        assert days == 369


# ---------------------------------------------------------------------------
# ADD family (codes 7, 8, 17, 20)
# ---------------------------------------------------------------------------
class TestAddFamily:
    def test_add_jul_wrap(self):
        # 2024 is leap → 24366 + 1 → 25001.
        assert add_jul("24366", 1) == (STATUS_OK, 25001)

    def test_add_jul_backward(self):
        assert add_jul("25001", -1) == (STATUS_OK, 24366)

    def test_add_ymd_month_boundary(self):
        assert add_ymd("240131", 1) == (STATUS_OK, 240201)

    def test_add_mdy(self):
        assert add_mdy("013124", 1) == (STATUS_OK, 20124)

    def test_add_cymd_year_wrap(self):
        assert add_cymd("20241231", 1) == (STATUS_OK, 20250101)


# ---------------------------------------------------------------------------
# ADD-MONTHS family (codes 21, 22, 41, 42)
# ---------------------------------------------------------------------------
class TestAddMonthsFamily:
    def test_add_months_to_cymd_eom_snap_leap(self):
        # Jan 31 + 1 month → Feb 29 (leap year).
        assert add_months_to_cymd("20240131", 1) == (STATUS_OK, 20240229)

    def test_add_months_to_cymd_eom_snap_non_leap(self):
        assert add_months_to_cymd("20230131", 1) == (STATUS_OK, 20230228)

    def test_add_months_to_cymd_year_wrap(self):
        assert add_months_to_cymd("20240115", 12) == (STATUS_OK, 20250115)

    def test_add_months_to_ymd(self):
        assert add_months_to_ymd("240131", 1) == (STATUS_OK, 240229)

    def test_add_months_to_mdy(self):
        assert add_months_to_mdy("013124", 1) == (STATUS_OK, 22924)

    def test_add_months_end_jul_force_eom(self):
        # 240031 → not valid; use a real EOM: 2024-01-31 in YYDDD = 24031.
        # Force EOM: Jan31 + 1 month → Feb 29 = YYDDD 24060.
        assert add_months_end_jul("24031", 1) == (STATUS_OK, 24060)


# ---------------------------------------------------------------------------
# RANGE family (codes 38, 39, 40) — 88888 within / 77777 outside
# ---------------------------------------------------------------------------
class TestRangeFamily:
    def test_range_jul_inside(self):
        assert range_jul("24001", "24365", "24180") == (STATUS_OK, 88888)

    def test_range_jul_outside(self):
        assert range_jul("24001", "24180", "24365") == (STATUS_OK, 77777)

    def test_range_jul_boundary(self):
        # Inclusive boundary per a <= c <= b.
        assert range_jul("24001", "24365", "24001") == (STATUS_OK, 88888)

    def test_range_ymd_inside(self):
        assert range_ymd("240101", "241231", "240615") == (STATUS_OK, 88888)

    def test_range_mdy_outside(self):
        assert range_mdy("010124", "063024", "070124") == (STATUS_OK, 77777)


# ---------------------------------------------------------------------------
# Dispatch idiom — DATESUB-FUNC routing through DateConv class.
# Mirrors source/cobol/DATECONV.cbl:111-198 (000-SELECT IF/ELSE chain).
# ---------------------------------------------------------------------------
class TestDispatch:
    def test_func1_dispatch(self):
        cd = ConvDates(from_cymd_dt=20240229)
        DateConv().dispatch(1, cd)
        assert cd.date_err_ind == "N"
        assert cd.datesub_func == 1

    def test_func1_invalid_sets_err_ind(self):
        cd = ConvDates(from_cymd_dt=20240230)
        DateConv().dispatch(1, cd)
        assert cd.date_err_ind == "Y"
        assert cd.date_err_reason == 7  # OutOfRangeDD

    def test_func2_dispatch_populates_to_jul(self):
        cd = ConvDates(from_ymd_dt=240101)
        DateConv().dispatch(2, cd)
        assert cd.to_jul_dt == 24001

    def test_unknown_func_sets_err(self):
        cd = ConvDates()
        DateConv().dispatch(999, cd)
        assert cd.date_err_ind == "Y"

    def test_func29_unused_returns_err(self):
        # DATESUB-FUNC 29 + 30 are reserved per DATECONV-PD.cpy.
        cd = ConvDates()
        DateConv().dispatch(29, cd)
        assert cd.date_err_ind == "Y"

    def test_thru_alias_reads_to(self):
        cd = ConvDates(to_jul_dt=24180)
        assert cd.thru_jul_dt == 24180
        cd.thru_jul_dt = 24365
        assert cd.to_jul_dt == 24365


# ---------------------------------------------------------------------------
# Edge cases — DATE-ERR / DATE-IS-VALID semantics matching COBOL 88-levels.
# ---------------------------------------------------------------------------
class TestEdgeCases:
    def test_month_13_rejected(self):
        assert check_cymd_dt("20241301")[0] == STATUS_OOR_MM

    def test_day_zero_rejected(self):
        assert check_cymd_dt("20240100")[0] == STATUS_OOR_DD

    def test_feb_30_rejected(self):
        assert check_cymd_dt("20240230")[0] == STATUS_OOR_DD

    def test_year_zero_rejected(self):
        assert check_cymd_dt("00000101")[0] == STATUS_OOR_YYYY

    def test_century_rollover_yy_99_to_01(self):
        # YY=99 → 1999, YY=01 → 2001. DIF-FY returns 2.
        assert dif_fy("990101", "010101") == (STATUS_OK, 2)

    def test_status_codes_mirror_jdn_constants(self):
        # JDN-Con-Status-Codes mapping per JDN-CONSTANTS-WS.cpy.
        assert STATUS_OK == "OK"
        assert STATUS_OOR_DD == "OutOfRangeDD"
        assert STATUS_OOR_DDD == "OutOfRangeDDD"
        assert STATUS_OOR_MM == "OutOfRangeMM"
        assert STATUS_OOR_YYYY == "OutOfRangeYYYY"
        assert STATUS_STRANGE == "Strange"

    def test_invalid_propagates_through_dif(self):
        # If either side of DIF-CYMD is invalid, status flows through.
        assert dif_cymd("20240230", "20240501")[0] == STATUS_OOR_DD


# ---------------------------------------------------------------------------
# Module-level sanity — every convenience function is exported and callable.
# ---------------------------------------------------------------------------
def test_all_40_convenience_functions_exist():
    names = [
        "check_cymd_dt", "check_mdy_dt", "ymd_to_jul", "jul_to_ymd",
        "mdy_to_jul", "jul_to_mdy", "mdy_to_ymd", "mdy_to_mdcy",
        "ymd_to_mdy", "ymd_to_cymd", "jul_to_cymd", "cymd_to_jul",
        "cymd_to_int", "int_to_cymd", "jul_to_int", "int_to_jul",
        "ymd_to_int", "int_to_ymd", "mdy_to_int", "int_to_mdy",
        "dif_jul", "dif_jul_no_check", "dif_ymd", "dif_mdy",
        "dif_cymd", "dif_fy", "dif_jul_30", "dif_cymd_30",
        "dif_mdy_30", "add_jul", "add_ymd", "add_mdy",
        "add_cymd", "add_months_to_ymd", "add_months_to_cymd",
        "add_months_to_mdy", "add_months_end_jul",
        "range_jul", "range_ymd", "range_mdy",
    ]
    assert len(names) == 40
    for n in names:
        assert callable(getattr(dateconv, n))


def test_labd20_loader_uses_dateconv():
    # Verify the labd20_loader stub now delegates here (not a duplicate impl).
    from python import labd20_loader

    assert labd20_loader.check_cymd_dt("20240229") is True
    assert labd20_loader.check_cymd_dt("20240230") is False
    assert labd20_loader.check_cymd_dt("19000229") is False  # 100-rule
    assert labd20_loader.check_cymd_dt("20000229") is True   # 400-rule
