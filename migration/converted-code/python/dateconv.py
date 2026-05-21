"""
dateconv.py — Python port of source/cobol/DATECONV.cbl (42 DATESUB-FUNC codes,
40 active entry paragraphs; codes 29/30 reserved/unused per
source/copybooks/DATECONV-PD.cpy).

The customer's DATECONV.cbl was migrated to COBOL-85 intrinsics in 2012
(see MIGRTN comment column in source/cobol/DATECONV.cbl and the
JDN-RECORD-ACCESS / JDN-CONSTANTS-WS copybooks). All date math therefore
reduces to INTEGER-OF-DATE / DATE-OF-INTEGER / INTEGER-OF-DAY / DAY-OF-INTEGER,
which Python's datetime.date implements exactly (proleptic Gregorian).

The dispatch idiom (DATESUB-FUNC) is preserved so a SME can map every
method back to a DATECONV.cbl paragraph by code or by name.

Status codes mirror JDN-Con-Status-Codes (source/copybooks/JDN-CONSTANTS-WS.cpy):
  'OK'              JDN-Con-NoErr           (0)
  'OutOfRangeDD'    JDN-Con-OutOfRangeDD    (7)
  'OutOfRangeDDD'   JDN-Con-OutOfRangeDDD   (8)
  'OutOfRangeMM'    JDN-Con-OutOfRangeMM    (10)
  'OutOfRangeYYYY'  JDN-Con-OutOfRangeYYYY  (11)
  'Strange'         JDN-Con-Strange         (12)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Tuple

STATUS_OK = "OK"
STATUS_OOR_DD = "OutOfRangeDD"
STATUS_OOR_DDD = "OutOfRangeDDD"
STATUS_OOR_MM = "OutOfRangeMM"
STATUS_OOR_YYYY = "OutOfRangeYYYY"
STATUS_STRANGE = "Strange"

# COBOL INTEGER-OF-DATE epoch = 1601-01-01 (day 1).
# Source: source/copybooks/JDN-CONSTANTS-WS.cpy lines 35-38.
_EPOCH_ORDINAL = date(1601, 1, 1).toordinal() - 1  # so JDN-Int = ordinal - _EPOCH_ORDINAL


# ---------------------------------------------------------------------------
# Dataclass mirroring LINKAGE SECTION CONV-DATES (source/copybooks/DATECONV-WS.cpy).
# THRU-* aliases are added per the inventory naming convention; the COBOL
# field for the "second" input of DIF/RANGE operations is TO-*-DT, kept as
# the canonical field. THRU-* setters/getters point at the same storage.
# ---------------------------------------------------------------------------
@dataclass
class ConvDates:
    datesub_func: int = 0
    # FROM-* inputs
    from_cymd_dt: int = 0       # PIC 9(8)
    from_jul_dt: int = 0        # PIC 9(5)
    from_ymd_dt: int = 0        # PIC 9(6)
    from_mdy_dt: int = 0        # PIC 9(6)
    from_int_dt: int = 0        # PIC 9(10) COMP
    # TO-* outputs (also serve as the "thru" side of DIF/RANGE)
    to_cymd_dt: int = 0
    to_jul_dt: int = 0
    to_ymd_dt: int = 0
    to_mdy_dt: int = 0
    to_mdcy_dt: int = 0
    to_int_dt: int = 0
    # BETWEEN-* (the candidate point for RANGE operations)
    between_jul_dt: int = 0
    between_ymd_dt: int = 0
    between_mdy_dt: int = 0
    # arithmetic inputs
    months_to_add: int = 0
    days_dif: int = 0           # also DAYS-DIF result + 88888/77777 sentinels
    # output flags
    date_err_ind: str = "N"     # 'Y' / 'N' (DATE-IS-VALID = 'N')
    date_err_reason: int = 0    # 0..12 (see JDN-Con-Status-Codes)

    # THRU-* convenience aliases (read/write the same storage as TO-*).
    @property
    def thru_cymd_dt(self) -> int: return self.to_cymd_dt
    @thru_cymd_dt.setter
    def thru_cymd_dt(self, v: int) -> None: self.to_cymd_dt = v
    @property
    def thru_jul_dt(self) -> int: return self.to_jul_dt
    @thru_jul_dt.setter
    def thru_jul_dt(self, v: int) -> None: self.to_jul_dt = v
    @property
    def thru_ymd_dt(self) -> int: return self.to_ymd_dt
    @thru_ymd_dt.setter
    def thru_ymd_dt(self, v: int) -> None: self.to_ymd_dt = v
    @property
    def thru_mdy_dt(self) -> int: return self.to_mdy_dt
    @thru_mdy_dt.setter
    def thru_mdy_dt(self, v: int) -> None: self.to_mdy_dt = v
    @property
    def thru_int_dt(self) -> int: return self.to_int_dt
    @thru_int_dt.setter
    def thru_int_dt(self, v: int) -> None: self.to_int_dt = v


# ---------------------------------------------------------------------------
# Helpers — emulate the JDN-RECORD-ACCESS intrinsic-function core.
# Source: source/copybooks/JDN-RECORD-ACCESS.cpy.
# ---------------------------------------------------------------------------
def _cc_inferred(yy: int) -> int:
    # JDN-Acc-CC-Inferred (DATECONV.cbl 9920-CALC-YY-TO-YYYY): YY > 52 → 19xx.
    return 19 if yy > 52 else 20


def _split_cymd(cymd: int) -> Tuple[int, int, int]:
    return cymd // 10000, (cymd // 100) % 100, cymd % 100


def _split_ymd(ymd: int) -> Tuple[int, int, int]:
    return ymd // 10000, (ymd // 100) % 100, ymd % 100


def _split_mdy(mdy: int) -> Tuple[int, int, int]:
    return mdy // 10000, (mdy // 100) % 100, mdy % 100


def _split_jul(jul: int) -> Tuple[int, int]:
    return jul // 1000, jul % 1000


def _ymd_to_cymd(ymd: int) -> int:
    yy, mm, dd = _split_ymd(ymd)
    return _cc_inferred(yy) * 1000000 + yy * 10000 + mm * 100 + dd


def _mdy_to_cymd(mdy: int) -> int:
    mm, dd, yy = _split_mdy(mdy)
    return _cc_inferred(yy) * 1000000 + yy * 10000 + mm * 100 + dd


def _int_of_date(cymd: int) -> Tuple[str, int]:
    """COBOL FUNCTION INTEGER-OF-DATE on JDN-YYYYMMDD."""
    yyyy, mm, dd = _split_cymd(cymd)
    if yyyy < 1601:
        return STATUS_OOR_YYYY, 0
    if mm < 1 or mm > 12:
        return STATUS_OOR_MM, 0
    try:
        d = date(yyyy, mm, dd)
    except ValueError:
        return STATUS_OOR_DD, 0
    return STATUS_OK, d.toordinal() - _EPOCH_ORDINAL


def _int_of_day(jul_yyddd: int, century_hint: Optional[int] = None) -> Tuple[str, int, int]:
    """COBOL FUNCTION INTEGER-OF-DAY on JDN-YYYYDDD (5-digit YYDDD → infer CC).

    Returns (status, integer, yyyy).
    """
    yy, ddd = _split_jul(jul_yyddd)
    cc = century_hint if century_hint is not None else _cc_inferred(yy)
    yyyy = cc * 100 + yy
    if yyyy < 1601:
        return STATUS_OOR_YYYY, 0, yyyy
    if ddd < 1 or ddd > 366:
        return STATUS_OOR_DDD, 0, yyyy
    try:
        d = date(yyyy, 1, 1).toordinal() + ddd - 1
        # Bound by year-end (reject 366 in non-leap years).
        if date.fromordinal(d).year != yyyy:
            return STATUS_OOR_DDD, 0, yyyy
    except (OverflowError, ValueError):
        return STATUS_OOR_DDD, 0, yyyy
    return STATUS_OK, d - _EPOCH_ORDINAL, yyyy


def _date_of_int(jdn_int: int) -> Tuple[str, date]:
    if jdn_int < 1:
        return STATUS_OOR_YYYY, date(1601, 1, 1)
    try:
        d = date.fromordinal(jdn_int + _EPOCH_ORDINAL)
    except (OverflowError, ValueError):
        return STATUS_STRANGE, date(1601, 1, 1)
    return STATUS_OK, d


# ---------------------------------------------------------------------------
# DateConv class — dispatch on DATESUB-FUNC (source/cobol/DATECONV.cbl 000-SELECT).
# Each `_runNN_*` method corresponds 1:1 with a DATECONV.cbl paragraph
# (line ranges cited at the top of each method).
# ---------------------------------------------------------------------------
class DateConv:
    def dispatch(self, func_code: int, cd: ConvDates) -> ConvDates:
        cd.datesub_func = func_code
        cd.date_err_ind = "N"
        cd.date_err_reason = 0
        fn = _DISPATCH.get(func_code)
        if fn is None:
            cd.date_err_ind = "Y"
            cd.date_err_reason = 1  # JDN-Con-BadAction
            return cd
        fn(self, cd)
        return cd

    # -- Validators (DATESUB-FUNC 1, 9) ---------------------------------
    def _run01_check_cymd_dt(self, cd: ConvDates) -> None:
        # DATECONV.cbl:225-229 (100-CHECK-CYMD-DT).
        status, _ = _int_of_date(cd.from_cymd_dt)
        _apply_status(cd, status)

    def _run09_check_mdy_dt(self, cd: ConvDates) -> None:
        # DATECONV.cbl:369-376 (900-CHECK-MDY-DT).
        _apply_status(cd, _int_of_date(_mdy_to_cymd(cd.from_mdy_dt))[0])

    # -- YMD ↔ Julian (codes 2, 3) -------------------------------------
    def _run02_ymd_to_jul(self, cd: ConvDates) -> None:
        # DATECONV.cbl:231-245 (200-YMD-TO-JUL).
        status, _ = _int_of_date(_ymd_to_cymd(cd.from_ymd_dt))
        if status != STATUS_OK:
            cd.to_jul_dt = 0
            _apply_status(cd, status)
            return
        yyyy, _, _ = _split_cymd(_ymd_to_cymd(cd.from_ymd_dt))
        d = date(yyyy, (cd.from_ymd_dt // 100) % 100, cd.from_ymd_dt % 100)
        ddd = d.timetuple().tm_yday
        cd.from_int_dt = d.toordinal() - _EPOCH_ORDINAL
        cd.to_jul_dt = (yyyy % 100) * 1000 + ddd
        cd.date_err_ind = "N"

    def _run03_jul_to_ymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:247-261 (300-JUL-TO-YMD).
        status, jdn, yyyy = _int_of_day(cd.from_jul_dt)
        if status != STATUS_OK:
            cd.to_ymd_dt = 0
            _apply_status(cd, status)
            return
        cd.from_int_dt = jdn
        d = date.fromordinal(jdn + _EPOCH_ORDINAL)
        cd.to_ymd_dt = (d.year % 100) * 10000 + d.month * 100 + d.day
        cd.date_err_ind = "N"

    # -- MDY ↔ Julian (codes 10, 11) -----------------------------------
    def _run10_mdy_to_jul(self, cd: ConvDates) -> None:
        # DATECONV.cbl:378-394 (1000-MDY-TO-JUL).
        status, _ = _int_of_date(_mdy_to_cymd(cd.from_mdy_dt))
        if status != STATUS_OK:
            cd.to_jul_dt = 0
            _apply_status(cd, status)
            return
        yyyy, mm, dd = _split_cymd(_mdy_to_cymd(cd.from_mdy_dt))
        d = date(yyyy, mm, dd)
        cd.from_int_dt = d.toordinal() - _EPOCH_ORDINAL
        cd.to_jul_dt = (yyyy % 100) * 1000 + d.timetuple().tm_yday
        cd.date_err_ind = "N"

    def _run11_jul_to_mdy(self, cd: ConvDates) -> None:
        # DATECONV.cbl:396-410 (1100-JUL-TO-MDY).
        status, jdn, _ = _int_of_day(cd.from_jul_dt)
        if status != STATUS_OK:
            cd.to_mdy_dt = 0
            _apply_status(cd, status)
            return
        cd.from_int_dt = jdn
        d = date.fromordinal(jdn + _EPOCH_ORDINAL)
        cd.to_mdy_dt = d.month * 10000 + d.day * 100 + (d.year % 100)
        cd.date_err_ind = "N"

    # -- MDY ↔ YMD / MDCY / YMD (codes 12, 13, 27) ---------------------
    def _run12_mdy_to_ymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:412-418 (1200-MDY-TO-YMD). Pure rearrangement (no validation).
        mm, dd, yy = _split_mdy(cd.from_mdy_dt)
        cd.to_ymd_dt = yy * 10000 + mm * 100 + dd
        cd.date_err_ind = "N"

    def _run13_ymd_to_mdy(self, cd: ConvDates) -> None:
        # DATECONV.cbl:420-426 (1300-YMD-TO-MDY). Pure rearrangement.
        yy, mm, dd = _split_ymd(cd.from_ymd_dt)
        cd.to_mdy_dt = mm * 10000 + dd * 100 + yy
        cd.date_err_ind = "N"

    def _run27_mdy_to_mdcy(self, cd: ConvDates) -> None:
        # DATECONV.cbl:667-681 (2700-MDY-TO-MDCY).
        cymd = _mdy_to_cymd(cd.from_mdy_dt)
        status, _ = _int_of_date(cymd)
        if status != STATUS_OK:
            cd.to_mdcy_dt = 0
            _apply_status(cd, status)
            return
        yyyy, mm, dd = _split_cymd(cymd)
        cd.to_mdcy_dt = mm * 1000000 + dd * 10000 + yyyy
        cd.date_err_ind = "N"

    # -- YMD ↔ CYMD (code 18) ------------------------------------------
    def _run18_ymd_to_cymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:523-533 (1800-YMD-TO-CYMD).
        cymd = _ymd_to_cymd(cd.from_ymd_dt)
        status, _ = _int_of_date(cymd)
        if status != STATUS_OK:
            cd.to_cymd_dt = 0
            _apply_status(cd, status)
            return
        cd.to_cymd_dt = cymd
        cd.date_err_ind = "N"

    # -- Julian ↔ CYMD (codes 23, 24) ----------------------------------
    def _run23_jul_to_cymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:602-617 (2300-JUL-TO-CYMD).
        status, jdn, _ = _int_of_day(cd.from_jul_dt)
        if status != STATUS_OK:
            cd.to_cymd_dt = 0
            _apply_status(cd, status)
            return
        cd.from_int_dt = jdn
        d = date.fromordinal(jdn + _EPOCH_ORDINAL)
        cd.to_cymd_dt = d.year * 10000 + d.month * 100 + d.day
        cd.date_err_ind = "N"

    def _run24_cymd_to_jul(self, cd: ConvDates) -> None:
        # DATECONV.cbl:619-632 (2400-CYMD-TO-JUL).
        status, jdn = _int_of_date(cd.from_cymd_dt)
        if status != STATUS_OK:
            cd.to_jul_dt = 0
            _apply_status(cd, status)
            return
        cd.from_int_dt = jdn
        yyyy, mm, dd = _split_cymd(cd.from_cymd_dt)
        cd.to_jul_dt = (yyyy % 100) * 1000 + date(yyyy, mm, dd).timetuple().tm_yday
        cd.date_err_ind = "N"

    # -- CYMD ↔ INT (codes 25, 26) -------------------------------------
    def _run25_cymd_to_int(self, cd: ConvDates) -> None:
        # DATECONV.cbl:634-646 (2500-CYMD-TO-INT).
        status, jdn = _int_of_date(cd.from_cymd_dt)
        if status != STATUS_OK:
            cd.to_int_dt = 0
            _apply_status(cd, status)
            return
        cd.to_int_dt = jdn
        cd.date_err_ind = "N"

    def _run26_int_to_cymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:648-665 (2600-INT-TO-CYMD).  CH-645 gate: YYYY >= 1953.
        status, d = _date_of_int(cd.from_int_dt)
        if status != STATUS_OK or d.year < 1953:
            cd.to_cymd_dt = 0
            cd.date_err_ind = "Y"
            cd.date_err_reason = 11
            return
        cd.to_cymd_dt = d.year * 10000 + d.month * 100 + d.day
        cd.date_err_ind = "N"

    # -- INT ↔ Julian/YMD/MDY (codes 31, 32, 33, 34, 35, 36) ------------
    def _run31_jul_to_int(self, cd: ConvDates) -> None:
        # DATECONV.cbl:739-752 (3100-JUL-TO-INT).
        status, jdn, _ = _int_of_day(cd.from_jul_dt)
        if status != STATUS_OK:
            cd.to_int_dt = 0
            _apply_status(cd, status)
            return
        cd.to_int_dt = jdn
        cd.date_err_ind = "N"

    def _run32_int_to_jul(self, cd: ConvDates) -> None:
        # DATECONV.cbl:754-772 (3200-INT-TO-JUL). CH-645 gate: YYYY >= 1953.
        status, d = _date_of_int(cd.from_int_dt)
        if status != STATUS_OK or d.year < 1953:
            cd.to_jul_dt = 0
            cd.date_err_ind = "Y"
            cd.date_err_reason = 11
            return
        cd.to_jul_dt = (d.year % 100) * 1000 + d.timetuple().tm_yday
        cd.date_err_ind = "N"

    def _run33_ymd_to_int(self, cd: ConvDates) -> None:
        # DATECONV.cbl:774-787 (3300-YMD-TO-INT).
        cymd = _ymd_to_cymd(cd.from_ymd_dt)
        status, jdn = _int_of_date(cymd)
        if status != STATUS_OK:
            cd.to_int_dt = 0
            _apply_status(cd, status)
            return
        cd.to_int_dt = jdn
        cd.date_err_ind = "N"

    def _run34_int_to_ymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:789-806 (3400-INT-TO-YMD). CH-645 gate: YYYY >= 1953.
        status, d = _date_of_int(cd.from_int_dt)
        if status != STATUS_OK or d.year < 1953:
            cd.to_ymd_dt = 0
            cd.date_err_ind = "Y"
            cd.date_err_reason = 11
            return
        cd.to_ymd_dt = (d.year % 100) * 10000 + d.month * 100 + d.day
        cd.date_err_ind = "N"

    def _run35_mdy_to_int(self, cd: ConvDates) -> None:
        # DATECONV.cbl:808-823 (3500-MDY-TO-INT).
        cymd = _mdy_to_cymd(cd.from_mdy_dt)
        status, jdn = _int_of_date(cymd)
        if status != STATUS_OK:
            cd.to_int_dt = 0
            _apply_status(cd, status)
            return
        cd.to_int_dt = jdn
        cd.date_err_ind = "N"

    def _run36_int_to_mdy(self, cd: ConvDates) -> None:
        # DATECONV.cbl:825-845 (3600-INT-TO-MDY). CH-645 gate: YYYY >= 1953.
        status, d = _date_of_int(cd.from_int_dt)
        if status != STATUS_OK or d.year < 1953:
            cd.to_mdy_dt = 0
            cd.date_err_ind = "Y"
            cd.date_err_reason = 11
            return
        cd.to_mdy_dt = d.month * 10000 + d.day * 100 + (d.year % 100)
        cd.date_err_ind = "N"

    # -- DIF family (codes 4, 5, 6, 14, 15, 16, 19, 28, 37) -------------
    def _run04_dif_jul(self, cd: ConvDates) -> None:
        # DATECONV.cbl:263-287 (400-DIF-JUL). DAYS-DIF = TO - FROM.
        s1, a, _ = _int_of_day(cd.from_jul_dt)
        s2, b, _ = _int_of_day(cd.to_jul_dt)
        _set_dif(cd, s1, s2, a, b)

    def _run05_dif_ymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:289-313 (500-DIF-YMD).
        s1, a = _int_of_date(_ymd_to_cymd(cd.from_ymd_dt))
        s2, b = _int_of_date(_ymd_to_cymd(cd.to_ymd_dt))
        _set_dif(cd, s1, s2, a, b)

    def _run14_dif_mdy(self, cd: ConvDates) -> None:
        # DATECONV.cbl:428-456 (1400-DIF-MDY).
        s1, a = _int_of_date(_mdy_to_cymd(cd.from_mdy_dt))
        s2, b = _int_of_date(_mdy_to_cymd(cd.to_mdy_dt))
        _set_dif(cd, s1, s2, a, b)

    def _run19_dif_cymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:535-557 (1900-DIF-CYMD).
        s1, a = _int_of_date(cd.from_cymd_dt)
        s2, b = _int_of_date(cd.to_cymd_dt)
        _set_dif(cd, s1, s2, a, b)

    def _run28_dif_jul_no_check(self, cd: ConvDates) -> None:
        # DATECONV.cbl:683-737 (2800-DIF-JUL-NO-CHECK). Tolerates DDD overflow
        # (e.g. YYDDD=YY:400 → wrap 35 days into next year).
        a = _no_check_int_of_day(cd.from_jul_dt)
        b = _no_check_int_of_day(cd.to_jul_dt)
        cd.from_int_dt = a
        cd.to_int_dt = b
        cd.days_dif = b - a
        cd.date_err_ind = "N"
        cd.date_err_reason = 0

    def _run37_dif_fy(self, cd: ConvDates) -> None:
        # DATECONV.cbl:847-859 (4000-DIF-FY). Reads YY only from FROM-YMD-DT
        # and TO-YMD-DT, infers century, returns YYYY-diff.
        from_yy = cd.from_ymd_dt // 10000
        to_yy = cd.to_ymd_dt // 10000
        from_yyyy = _cc_inferred(from_yy) * 100 + from_yy
        to_yyyy = _cc_inferred(to_yy) * 100 + to_yy
        cd.days_dif = to_yyyy - from_yyyy
        cd.date_err_ind = "N"
        cd.date_err_reason = 0

    # -- 30-day-month DIF (codes 6, 15, 16) -----------------------------
    def _run06_dif_cymd_30(self, cd: ConvDates) -> None:
        # DATECONV.cbl:315-335 (600-DIF-CYMD-30). 30-day-month accounting.
        s1, a = _dif_cymd_30_int(cd.from_cymd_dt)
        s2, b = _dif_cymd_30_int(cd.to_cymd_dt)
        _set_dif(cd, s1, s2, a, b)

    def _run15_dif_jul_30(self, cd: ConvDates) -> None:
        # DATECONV.cbl:458-481 (1500-DIF-JUL-30). 30-day-month over Julian inputs.
        s1, a = _dif_jul_30_int(cd.from_jul_dt)
        s2, b = _dif_jul_30_int(cd.to_jul_dt)
        _set_dif(cd, s1, s2, a, b)

    def _run16_dif_mdy_30(self, cd: ConvDates) -> None:
        # DATECONV.cbl:483-503 (1600-DIF-MDY-30). 30-day-month over MDY inputs.
        s1, a = _dif_cymd_30_int(_mdy_to_cymd(cd.from_mdy_dt))
        s2, b = _dif_cymd_30_int(_mdy_to_cymd(cd.to_mdy_dt))
        _set_dif(cd, s1, s2, a, b)

    # -- ADD family (codes 7, 8, 17, 20) --------------------------------
    def _run07_add_jul(self, cd: ConvDates) -> None:
        # DATECONV.cbl:337-351 (700-ADD-JUL).
        status, jdn, _ = _int_of_day(cd.from_jul_dt)
        if status != STATUS_OK:
            cd.to_jul_dt = 0
            _apply_status(cd, status)
            return
        cd.from_int_dt = jdn + cd.days_dif
        s2, d = _date_of_int(cd.from_int_dt)
        if s2 != STATUS_OK:
            cd.to_jul_dt = 0
            _apply_status(cd, s2)
            return
        cd.to_jul_dt = (d.year % 100) * 1000 + d.timetuple().tm_yday
        cd.date_err_ind = "N"

    def _run08_add_ymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:353-367 (800-ADD-YMD).
        cymd = _ymd_to_cymd(cd.from_ymd_dt)
        status, jdn = _int_of_date(cymd)
        if status != STATUS_OK:
            cd.to_ymd_dt = 0
            _apply_status(cd, status)
            return
        cd.from_int_dt = jdn + cd.days_dif
        s2, d = _date_of_int(cd.from_int_dt)
        if s2 != STATUS_OK:
            cd.to_ymd_dt = 0
            _apply_status(cd, s2)
            return
        cd.to_ymd_dt = (d.year % 100) * 10000 + d.month * 100 + d.day
        cd.date_err_ind = "N"

    def _run17_add_mdy(self, cd: ConvDates) -> None:
        # DATECONV.cbl:505-521 (1700-ADD-MDY).
        cymd = _mdy_to_cymd(cd.from_mdy_dt)
        status, jdn = _int_of_date(cymd)
        if status != STATUS_OK:
            cd.to_mdy_dt = 0
            _apply_status(cd, status)
            return
        cd.from_int_dt = jdn + cd.days_dif
        s2, d = _date_of_int(cd.from_int_dt)
        if s2 != STATUS_OK:
            cd.to_mdy_dt = 0
            _apply_status(cd, s2)
            return
        cd.to_mdy_dt = d.month * 10000 + d.day * 100 + (d.year % 100)
        cd.date_err_ind = "N"

    def _run20_add_cymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:559-573 (2000-ADD-CYMD).
        status, jdn = _int_of_date(cd.from_cymd_dt)
        if status != STATUS_OK:
            cd.to_cymd_dt = 0
            _apply_status(cd, status)
            return
        cd.from_int_dt = jdn + cd.days_dif
        s2, d = _date_of_int(cd.from_int_dt)
        if s2 != STATUS_OK:
            cd.to_cymd_dt = 0
            _apply_status(cd, s2)
            return
        cd.to_cymd_dt = d.year * 10000 + d.month * 100 + d.day
        cd.date_err_ind = "N"

    # -- ADD-MONTHS family (codes 21, 22, 41, 42) -----------------------
    def _run21_add_months_to_ymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:575-587 (2100-ADD-MONTHS-TO-YMD).
        status, y, m, d = _add_months_cymd(_ymd_to_cymd(cd.from_ymd_dt), cd.months_to_add)
        if status != STATUS_OK:
            cd.to_ymd_dt = 0
            _apply_status(cd, status)
            return
        cd.to_ymd_dt = (y % 100) * 10000 + m * 100 + d
        cd.date_err_ind = "N"

    def _run22_add_months_to_cymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:589-600 (2200-ADD-MONTHS-TO-CYMD).
        status, y, m, d = _add_months_cymd(cd.from_cymd_dt, cd.months_to_add)
        if status != STATUS_OK:
            cd.to_cymd_dt = 0
            _apply_status(cd, status)
            return
        cd.to_cymd_dt = y * 10000 + m * 100 + d
        cd.date_err_ind = "N"

    def _run41_add_months_to_mdy(self, cd: ConvDates) -> None:
        # DATECONV.cbl:987-1003 (4400-ADD-MONTHS-TO-MDY).
        status, y, m, d = _add_months_cymd(_mdy_to_cymd(cd.from_mdy_dt), cd.months_to_add)
        if status != STATUS_OK:
            cd.to_mdy_dt = 0
            _apply_status(cd, status)
            return
        cd.to_mdy_dt = m * 10000 + d * 100 + (y % 100)
        cd.date_err_ind = "N"

    def _run42_add_months_end_jul(self, cd: ConvDates) -> None:
        # DATECONV.cbl:1005-1021 (4500-ADD-MONTHS-END-JUL).
        # JUL → CYMD → if month-end then snap to month-end → +months → JUL.
        status, jdn, _ = _int_of_day(cd.from_jul_dt)
        if status != STATUS_OK:
            cd.to_jul_dt = 0
            _apply_status(cd, status)
            return
        d = date.fromordinal(jdn + _EPOCH_ORDINAL)
        snap_to_eom = (d.day == _days_in_month(d.year, d.month))
        status, y, m, dd = _add_months_cymd(
            d.year * 10000 + d.month * 100 + d.day, cd.months_to_add, force_eom=snap_to_eom
        )
        if status != STATUS_OK:
            cd.to_jul_dt = 0
            _apply_status(cd, status)
            return
        dt2 = date(y, m, dd)
        cd.to_jul_dt = (y % 100) * 1000 + dt2.timetuple().tm_yday
        cd.date_err_ind = "N"

    # -- RANGE family (codes 38, 39, 40) --------------------------------
    def _run38_range_jul(self, cd: ConvDates) -> None:
        # DATECONV.cbl:861-899 (4100-RANGE-JUL).
        _range_check(
            cd,
            _int_of_day(cd.from_jul_dt)[1],
            _int_of_day(cd.to_jul_dt)[1],
            _int_of_day(cd.between_jul_dt)[1],
            _int_of_day(cd.from_jul_dt)[0],
            _int_of_day(cd.to_jul_dt)[0],
            _int_of_day(cd.between_jul_dt)[0],
        )

    def _run39_range_ymd(self, cd: ConvDates) -> None:
        # DATECONV.cbl:901-939 (4200-RANGE-YMD).
        s1, a = _int_of_date(_ymd_to_cymd(cd.from_ymd_dt))
        s2, b = _int_of_date(_ymd_to_cymd(cd.to_ymd_dt))
        s3, c = _int_of_date(_ymd_to_cymd(cd.between_ymd_dt))
        _range_check(cd, a, b, c, s1, s2, s3)

    def _run40_range_mdy(self, cd: ConvDates) -> None:
        # DATECONV.cbl:941-985 (4300-RANGE-MDY).
        s1, a = _int_of_date(_mdy_to_cymd(cd.from_mdy_dt))
        s2, b = _int_of_date(_mdy_to_cymd(cd.to_mdy_dt))
        s3, c = _int_of_date(_mdy_to_cymd(cd.between_mdy_dt))
        _range_check(cd, a, b, c, s1, s2, s3)


# ---------------------------------------------------------------------------
# Dispatch table — DATESUB-FUNC → DateConv method.
# Mirrors the IF/ELSE-IF chain at DATECONV.cbl:111-198 (000-SELECT).
# Codes 29 and 30 are intentionally absent (reserved per DATECONV-PD.cpy).
# ---------------------------------------------------------------------------
_DISPATCH = {
    1:  DateConv._run01_check_cymd_dt,
    2:  DateConv._run02_ymd_to_jul,
    3:  DateConv._run03_jul_to_ymd,
    4:  DateConv._run04_dif_jul,
    5:  DateConv._run05_dif_ymd,
    6:  DateConv._run06_dif_cymd_30,
    7:  DateConv._run07_add_jul,
    8:  DateConv._run08_add_ymd,
    9:  DateConv._run09_check_mdy_dt,
    10: DateConv._run10_mdy_to_jul,
    11: DateConv._run11_jul_to_mdy,
    12: DateConv._run12_mdy_to_ymd,
    13: DateConv._run13_ymd_to_mdy,
    14: DateConv._run14_dif_mdy,
    15: DateConv._run15_dif_jul_30,
    16: DateConv._run16_dif_mdy_30,
    17: DateConv._run17_add_mdy,
    18: DateConv._run18_ymd_to_cymd,
    19: DateConv._run19_dif_cymd,
    20: DateConv._run20_add_cymd,
    21: DateConv._run21_add_months_to_ymd,
    22: DateConv._run22_add_months_to_cymd,
    23: DateConv._run23_jul_to_cymd,
    24: DateConv._run24_cymd_to_jul,
    25: DateConv._run25_cymd_to_int,
    26: DateConv._run26_int_to_cymd,
    27: DateConv._run27_mdy_to_mdcy,
    28: DateConv._run28_dif_jul_no_check,
    31: DateConv._run31_jul_to_int,
    32: DateConv._run32_int_to_jul,
    33: DateConv._run33_ymd_to_int,
    34: DateConv._run34_int_to_ymd,
    35: DateConv._run35_mdy_to_int,
    36: DateConv._run36_int_to_mdy,
    37: DateConv._run37_dif_fy,
    38: DateConv._run38_range_jul,
    39: DateConv._run39_range_ymd,
    40: DateConv._run40_range_mdy,
    41: DateConv._run41_add_months_to_mdy,
    42: DateConv._run42_add_months_end_jul,
}


# ---------------------------------------------------------------------------
# Internal helpers (status mapping + 30-day-month math + ADD-MONTHS).
# ---------------------------------------------------------------------------
_REASON = {
    STATUS_OK: 0,
    STATUS_OOR_DD: 7,
    STATUS_OOR_DDD: 8,
    STATUS_OOR_MM: 10,
    STATUS_OOR_YYYY: 11,
    STATUS_STRANGE: 12,
}


def _apply_status(cd: ConvDates, status: str) -> None:
    if status == STATUS_OK:
        cd.date_err_ind = "N"
        cd.date_err_reason = 0
    else:
        cd.date_err_ind = "Y"
        cd.date_err_reason = _REASON.get(status, 12)


def _set_dif(cd: ConvDates, s1: str, s2: str, a: int, b: int) -> None:
    if s1 != STATUS_OK or s2 != STATUS_OK:
        cd.days_dif = 0
        cd.date_err_ind = "Y"
        cd.date_err_reason = _REASON.get(s1 if s1 != STATUS_OK else s2, 12)
        return
    cd.from_int_dt = a
    cd.to_int_dt = b
    cd.days_dif = b - a
    cd.date_err_ind = "N"


def _range_check(cd: ConvDates, a: int, b: int, c: int, s1: str, s2: str, s3: str) -> None:
    # 88888 = within, 77777 = outside (DATECONV.cbl:886-888).
    if s1 != STATUS_OK or s2 != STATUS_OK or s3 != STATUS_OK:
        cd.days_dif = 0
        cd.date_err_ind = "Y"
        for s in (s1, s2, s3):
            if s != STATUS_OK:
                cd.date_err_reason = _REASON.get(s, 12)
                break
        return
    cd.from_int_dt = a
    cd.to_int_dt = b
    cd.days_dif = 88888 if a <= c <= b else 77777
    cd.date_err_ind = "N"


def _days_in_month(yyyy: int, mm: int) -> int:
    if mm == 12:
        return 31
    return (date(yyyy, mm + 1, 1) - date(yyyy, mm, 1)).days


def _add_months_cymd(cymd: int, months: int, force_eom: bool = False) -> Tuple[str, int, int, int]:
    # DATECONV.cbl:1023-1052 (9910-ADD-MONTHS) — preserves snap-to-end-of-month.
    status, jdn = _int_of_date(cymd)
    if status != STATUS_OK:
        return status, 0, 0, 0
    yyyy, mm, dd = _split_cymd(cymd)
    total = (yyyy * 12 + (mm - 1)) + months
    new_y, new_m = divmod(total, 12)
    new_m += 1
    if new_y < 1601:
        return STATUS_OOR_YYYY, 0, 0, 0
    eom = _days_in_month(new_y, new_m)
    new_d = eom if (dd > eom or force_eom) else dd
    return STATUS_OK, new_y, new_m, new_d


def _no_check_int_of_day(jul_yyddd: int) -> int:
    # 2800-DIF-JUL-NO-CHECK tolerates DDD > 365 by carrying into the next year.
    yy, ddd = _split_jul(jul_yyddd)
    yyyy = _cc_inferred(yy) * 100 + yy
    if jul_yyddd == 0:
        return 0
    if ddd <= 365:
        return date(yyyy, 1, 1).toordinal() + ddd - 1 - _EPOCH_ORDINAL
    overflow = ddd - 365
    return date(yyyy, 1, 1).toordinal() + 365 - 1 + overflow - _EPOCH_ORDINAL


def _dif_cymd_30_int(cymd: int) -> Tuple[str, int]:
    # 30-day-month accounting: every full year = 360 days.
    yyyy, mm, dd = _split_cymd(cymd)
    if yyyy < 1601:
        return STATUS_OOR_YYYY, 0
    if mm < 1 or mm > 12:
        return STATUS_OOR_MM, 0
    if dd < 1 or dd > 31:
        return STATUS_OOR_DD, 0
    return STATUS_OK, yyyy * 360 + (mm - 1) * 30 + (dd - 1)


def _dif_jul_30_int(jul: int) -> Tuple[str, int]:
    # DATECONV.cbl:1074-1108 (9940-CONV-JUL-30): map DDD into 30-day-month equivalent.
    yy, ddd = _split_jul(jul)
    yyyy = _cc_inferred(yy) * 100 + yy
    if yyyy < 1601:
        return STATUS_OOR_YYYY, 0
    if ddd < 1 or ddd > 366:
        return STATUS_OOR_DDD, 0
    # Validate first; reject 366 in non-leap years.
    leap = _is_leap(yyyy)
    if ddd > (366 if leap else 365):
        return STATUS_OOR_DDD, 0
    # Convert to (mm, dd) via 30-day-month thresholds then to 360-day calendar.
    thresholds = (30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330, 360)
    eom_real = _cumulative_days(yyyy)
    # Map ddd → mm,dd in real calendar.
    mm = 1
    while mm <= 12 and ddd > eom_real[mm]:
        mm += 1
    if mm > 12:
        return STATUS_OOR_DDD, 0
    dd_real = ddd - eom_real[mm - 1]
    # 30-day-month equivalent: each month has 30 days.
    dd_30 = min(dd_real, 30)
    return STATUS_OK, yyyy * 360 + (mm - 1) * 30 + (dd_30 - 1)


def _is_leap(y: int) -> bool:
    return (y % 4 == 0 and y % 100 != 0) or (y % 400 == 0)


def _cumulative_days(yyyy: int) -> Tuple[int, ...]:
    base = (0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334, 365)
    if _is_leap(yyyy):
        return (0, 31, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335, 366)
    return base


# ---------------------------------------------------------------------------
# Module-level convenience functions.
# Each returns (status: str, result: <int | None>) matching the COBOL output
# of the corresponding paragraph. Inputs accept int or all-digit str.
# ---------------------------------------------------------------------------
def _to_int(v) -> Optional[int]:
    if isinstance(v, int):
        return v
    if isinstance(v, str) and v.isdigit():
        return int(v)
    return None


_ENGINE = DateConv()


def _dispatch_one(func: int, **kw) -> ConvDates:
    cd = ConvDates(**kw)
    _ENGINE.dispatch(func, cd)
    return cd


def _status(cd: ConvDates) -> str:
    if cd.date_err_ind == "N":
        return STATUS_OK
    for k, v in _REASON.items():
        if v == cd.date_err_reason:
            return k
    return STATUS_STRANGE


def check_cymd_dt(yyyymmdd) -> Tuple[str, bool]:
    """100-CHECK-CYMD-DT — validate 8-digit YYYYMMDD via Gregorian rules."""
    v = _to_int(yyyymmdd)
    if v is None or not _has_n_digits(yyyymmdd, 8):
        return STATUS_STRANGE, False
    cd = _dispatch_one(1, from_cymd_dt=v)
    s = _status(cd)
    return s, s == STATUS_OK


def check_mdy_dt(mmddyy) -> Tuple[str, bool]:
    """900-CHECK-MDY-DT — validate 6-digit MMDDYY."""
    v = _to_int(mmddyy)
    if v is None or not _has_n_digits(mmddyy, 6):
        return STATUS_STRANGE, False
    cd = _dispatch_one(9, from_mdy_dt=v)
    s = _status(cd)
    return s, s == STATUS_OK


def ymd_to_jul(yymmdd) -> Tuple[str, int]:
    v = _to_int(yymmdd) or 0
    cd = _dispatch_one(2, from_ymd_dt=v)
    return _status(cd), cd.to_jul_dt


def jul_to_ymd(yyddd) -> Tuple[str, int]:
    v = _to_int(yyddd) or 0
    cd = _dispatch_one(3, from_jul_dt=v)
    return _status(cd), cd.to_ymd_dt


def mdy_to_jul(mmddyy) -> Tuple[str, int]:
    v = _to_int(mmddyy) or 0
    cd = _dispatch_one(10, from_mdy_dt=v)
    return _status(cd), cd.to_jul_dt


def jul_to_mdy(yyddd) -> Tuple[str, int]:
    v = _to_int(yyddd) or 0
    cd = _dispatch_one(11, from_jul_dt=v)
    return _status(cd), cd.to_mdy_dt


def mdy_to_ymd(mmddyy) -> Tuple[str, int]:
    v = _to_int(mmddyy) or 0
    cd = _dispatch_one(12, from_mdy_dt=v)
    return _status(cd), cd.to_ymd_dt


def mdy_to_mdcy(mmddyy) -> Tuple[str, int]:
    v = _to_int(mmddyy) or 0
    cd = _dispatch_one(27, from_mdy_dt=v)
    return _status(cd), cd.to_mdcy_dt


def ymd_to_mdy(yymmdd) -> Tuple[str, int]:
    v = _to_int(yymmdd) or 0
    cd = _dispatch_one(13, from_ymd_dt=v)
    return _status(cd), cd.to_mdy_dt


def ymd_to_cymd(yymmdd) -> Tuple[str, int]:
    v = _to_int(yymmdd) or 0
    cd = _dispatch_one(18, from_ymd_dt=v)
    return _status(cd), cd.to_cymd_dt


def jul_to_cymd(yyddd) -> Tuple[str, int]:
    v = _to_int(yyddd) or 0
    cd = _dispatch_one(23, from_jul_dt=v)
    return _status(cd), cd.to_cymd_dt


def cymd_to_jul(yyyymmdd) -> Tuple[str, int]:
    v = _to_int(yyyymmdd) or 0
    cd = _dispatch_one(24, from_cymd_dt=v)
    return _status(cd), cd.to_jul_dt


def cymd_to_int(yyyymmdd) -> Tuple[str, int]:
    v = _to_int(yyyymmdd) or 0
    cd = _dispatch_one(25, from_cymd_dt=v)
    return _status(cd), cd.to_int_dt


def int_to_cymd(n) -> Tuple[str, int]:
    v = _to_int(n) or 0
    cd = _dispatch_one(26, from_int_dt=v)
    return _status(cd), cd.to_cymd_dt


def jul_to_int(yyddd) -> Tuple[str, int]:
    v = _to_int(yyddd) or 0
    cd = _dispatch_one(31, from_jul_dt=v)
    return _status(cd), cd.to_int_dt


def int_to_jul(n) -> Tuple[str, int]:
    v = _to_int(n) or 0
    cd = _dispatch_one(32, from_int_dt=v)
    return _status(cd), cd.to_jul_dt


def ymd_to_int(yymmdd) -> Tuple[str, int]:
    v = _to_int(yymmdd) or 0
    cd = _dispatch_one(33, from_ymd_dt=v)
    return _status(cd), cd.to_int_dt


def int_to_ymd(n) -> Tuple[str, int]:
    v = _to_int(n) or 0
    cd = _dispatch_one(34, from_int_dt=v)
    return _status(cd), cd.to_ymd_dt


def mdy_to_int(mmddyy) -> Tuple[str, int]:
    v = _to_int(mmddyy) or 0
    cd = _dispatch_one(35, from_mdy_dt=v)
    return _status(cd), cd.to_int_dt


def int_to_mdy(n) -> Tuple[str, int]:
    v = _to_int(n) or 0
    cd = _dispatch_one(36, from_int_dt=v)
    return _status(cd), cd.to_mdy_dt


def dif_jul(from_yyddd, thru_yyddd) -> Tuple[str, int]:
    cd = _dispatch_one(4, from_jul_dt=_to_int(from_yyddd) or 0, to_jul_dt=_to_int(thru_yyddd) or 0)
    return _status(cd), cd.days_dif


def dif_jul_no_check(from_yyddd, thru_yyddd) -> Tuple[str, int]:
    cd = _dispatch_one(28, from_jul_dt=_to_int(from_yyddd) or 0, to_jul_dt=_to_int(thru_yyddd) or 0)
    return _status(cd), cd.days_dif


def dif_ymd(from_yymmdd, thru_yymmdd) -> Tuple[str, int]:
    cd = _dispatch_one(5, from_ymd_dt=_to_int(from_yymmdd) or 0, to_ymd_dt=_to_int(thru_yymmdd) or 0)
    return _status(cd), cd.days_dif


def dif_mdy(from_mmddyy, thru_mmddyy) -> Tuple[str, int]:
    cd = _dispatch_one(14, from_mdy_dt=_to_int(from_mmddyy) or 0, to_mdy_dt=_to_int(thru_mmddyy) or 0)
    return _status(cd), cd.days_dif


def dif_cymd(from_yyyymmdd, thru_yyyymmdd) -> Tuple[str, int]:
    cd = _dispatch_one(19,
                       from_cymd_dt=_to_int(from_yyyymmdd) or 0,
                       to_cymd_dt=_to_int(thru_yyyymmdd) or 0)
    return _status(cd), cd.days_dif


def dif_fy(from_yymmdd, thru_yymmdd) -> Tuple[str, int]:
    cd = _dispatch_one(37, from_ymd_dt=_to_int(from_yymmdd) or 0, to_ymd_dt=_to_int(thru_yymmdd) or 0)
    return _status(cd), cd.days_dif


def dif_jul_30(from_yyddd, thru_yyddd) -> Tuple[str, int]:
    cd = _dispatch_one(15, from_jul_dt=_to_int(from_yyddd) or 0, to_jul_dt=_to_int(thru_yyddd) or 0)
    return _status(cd), cd.days_dif


def dif_cymd_30(from_yyyymmdd, thru_yyyymmdd) -> Tuple[str, int]:
    cd = _dispatch_one(6,
                       from_cymd_dt=_to_int(from_yyyymmdd) or 0,
                       to_cymd_dt=_to_int(thru_yyyymmdd) or 0)
    return _status(cd), cd.days_dif


def dif_mdy_30(from_mmddyy, thru_mmddyy) -> Tuple[str, int]:
    cd = _dispatch_one(16, from_mdy_dt=_to_int(from_mmddyy) or 0, to_mdy_dt=_to_int(thru_mmddyy) or 0)
    return _status(cd), cd.days_dif


def add_jul(from_yyddd, days) -> Tuple[str, int]:
    cd = _dispatch_one(7, from_jul_dt=_to_int(from_yyddd) or 0, days_dif=int(days))
    return _status(cd), cd.to_jul_dt


def add_ymd(from_yymmdd, days) -> Tuple[str, int]:
    cd = _dispatch_one(8, from_ymd_dt=_to_int(from_yymmdd) or 0, days_dif=int(days))
    return _status(cd), cd.to_ymd_dt


def add_mdy(from_mmddyy, days) -> Tuple[str, int]:
    cd = _dispatch_one(17, from_mdy_dt=_to_int(from_mmddyy) or 0, days_dif=int(days))
    return _status(cd), cd.to_mdy_dt


def add_cymd(from_yyyymmdd, days) -> Tuple[str, int]:
    cd = _dispatch_one(20, from_cymd_dt=_to_int(from_yyyymmdd) or 0, days_dif=int(days))
    return _status(cd), cd.to_cymd_dt


def add_months_to_ymd(from_yymmdd, months) -> Tuple[str, int]:
    cd = _dispatch_one(21, from_ymd_dt=_to_int(from_yymmdd) or 0, months_to_add=int(months))
    return _status(cd), cd.to_ymd_dt


def add_months_to_cymd(from_yyyymmdd, months) -> Tuple[str, int]:
    cd = _dispatch_one(22, from_cymd_dt=_to_int(from_yyyymmdd) or 0, months_to_add=int(months))
    return _status(cd), cd.to_cymd_dt


def add_months_to_mdy(from_mmddyy, months) -> Tuple[str, int]:
    cd = _dispatch_one(41, from_mdy_dt=_to_int(from_mmddyy) or 0, months_to_add=int(months))
    return _status(cd), cd.to_mdy_dt


def add_months_end_jul(from_yyddd, months) -> Tuple[str, int]:
    cd = _dispatch_one(42, from_jul_dt=_to_int(from_yyddd) or 0, months_to_add=int(months))
    return _status(cd), cd.to_jul_dt


def range_jul(from_yyddd, thru_yyddd, between_yyddd) -> Tuple[str, int]:
    cd = _dispatch_one(38,
                       from_jul_dt=_to_int(from_yyddd) or 0,
                       to_jul_dt=_to_int(thru_yyddd) or 0,
                       between_jul_dt=_to_int(between_yyddd) or 0)
    return _status(cd), cd.days_dif


def range_ymd(from_yymmdd, thru_yymmdd, between_yymmdd) -> Tuple[str, int]:
    cd = _dispatch_one(39,
                       from_ymd_dt=_to_int(from_yymmdd) or 0,
                       to_ymd_dt=_to_int(thru_yymmdd) or 0,
                       between_ymd_dt=_to_int(between_yymmdd) or 0)
    return _status(cd), cd.days_dif


def range_mdy(from_mmddyy, thru_mmddyy, between_mmddyy) -> Tuple[str, int]:
    cd = _dispatch_one(40,
                       from_mdy_dt=_to_int(from_mmddyy) or 0,
                       to_mdy_dt=_to_int(thru_mmddyy) or 0,
                       between_mdy_dt=_to_int(between_mmddyy) or 0)
    return _status(cd), cd.days_dif


def _has_n_digits(v, n: int) -> bool:
    if isinstance(v, str):
        return v.isdigit() and len(v) == n
    if isinstance(v, int) and v >= 0:
        return len(str(v).zfill(n)) <= n + 0 and (v < 10 ** n)
    return False
