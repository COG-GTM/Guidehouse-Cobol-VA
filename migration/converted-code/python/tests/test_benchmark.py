"""dateconv dispatch-throughput benchmark.

These are *not* parity tests — those live in test_dateconv.py and the
GnuCOBOL parity harness at migration/test-results/build/run-parity.sh.
This file exists to assert that the optimizations applied in this PR
(caching _int_of_day in _run38_range_jul, hoisting cumulative-day tuples,
reverse-lookup for _status, etc.) leave the dispatch hot path
fast enough that future regressions are caught by CI.

The throughput ceiling (5 seconds for 50k mixed dispatches) is intentionally
generous so the test does not become flaky under CI load. The call-count
assertion in test_range_jul_no_double_call is the precise post-condition
for Issue #1.
"""
from __future__ import annotations

import time
import unittest.mock as mock

from python import dateconv
from python.dateconv import ConvDates, DateConv, _int_of_day


def test_dateconv_throughput():
    """Exercise the dispatch hot path 10,000 times across five funcs (50k total).

    Asserts a generous wall-clock ceiling so CI catches catastrophic
    regressions (e.g. an accidental re-introduction of a 6x _int_of_day
    call pattern) without failing under contention.
    """
    start = time.perf_counter()
    for _ in range(10_000):
        dateconv.check_cymd_dt("20240229")
        dateconv.ymd_to_jul("240101")
        dateconv.dif_jul("24001", "24366")
        dateconv.add_months_to_cymd("20240131", 1)
        dateconv.range_jul("24001", "24365", "24180")
    elapsed = time.perf_counter() - start
    print(f"\n  dateconv 50,000 dispatches in {elapsed:.3f}s")
    assert elapsed < 5.0, f"Too slow: {elapsed:.3f}s for 50k dispatches"


def test_range_jul_no_double_call():
    """Issue #1 regression guard: _run38_range_jul makes 3 _int_of_day calls.

    Before the fix the dispatch indexed each return tuple twice
    (status and integer separately), invoking _int_of_day six times for
    the three Julian inputs. The fix caches each call into a local tuple,
    so the count drops to three.
    """
    cd = ConvDates(from_jul_dt=24001, to_jul_dt=24365, between_jul_dt=24180)
    with mock.patch("python.dateconv._int_of_day", wraps=_int_of_day) as m:
        DateConv().dispatch(38, cd)
        assert m.call_count == 3, f"Expected 3 calls, got {m.call_count}"


def test_split_aliases_share_implementation():
    """Issue #10 regression guard: _split_cymd/_split_ymd/_split_mdy alias.

    All three names must point at the same underlying callable so that
    a future refactor that updates one does not silently fork the math.
    """
    assert dateconv._split_cymd is dateconv._split_ymd
    assert dateconv._split_cymd is dateconv._split_mdy
    assert dateconv._split_cymd is dateconv._split_date_int


def test_cumulative_days_returns_module_constants():
    """Issue #5 regression guard: hoisted tuples are not rebuilt per call."""
    # Common-year and leap-year invocations must each return the exact
    # module-level tuple (identity, not equality) so no per-call allocation
    # is performed in the hot path.
    assert dateconv._cumulative_days(2023) is dateconv._CUMDAYS_COMMON
    assert dateconv._cumulative_days(2024) is dateconv._CUMDAYS_LEAP
    # 1900 is NOT a leap year under the Gregorian rule (year % 100 == 0
    # and year % 400 != 0).
    assert dateconv._cumulative_days(1900) is dateconv._CUMDAYS_COMMON
    assert dateconv._cumulative_days(2000) is dateconv._CUMDAYS_LEAP


def test_status_reverse_lookup_is_o1():
    """Issue #7 regression guard: _status() uses the prebuilt reverse dict."""
    # Hitting every non-OK status reason should resolve via the reverse
    # map without falling through to STATUS_STRANGE.
    for status_name, reason in dateconv._REASON.items():
        cd = ConvDates(date_err_ind="Y", date_err_reason=reason)
        # OK has reason 0 but date_err_ind 'N' would mask it; for the OK
        # row we test the happy path explicitly.
        if status_name == dateconv.STATUS_OK:
            cd.date_err_ind = "N"
        assert dateconv._status(cd) == status_name


def test_no_check_int_of_day_overflow_branch_collapsed():
    """Issue #6 regression guard: ddd > 365 and ddd <= 365 agree at the seam.

    The pre-fix code had two branches that computed the same expression
    via different arithmetic. The fix collapses to a single expression,
    so the values at ddd=365 and ddd=366 must remain monotone +1.
    """
    a = dateconv._no_check_int_of_day(24365)
    b = dateconv._no_check_int_of_day(24366)
    assert b - a == 1, f"Expected b-a=1 at seam, got {b - a}"
