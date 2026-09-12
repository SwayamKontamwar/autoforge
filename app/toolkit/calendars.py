"""Utility functions for calendar calculations.

This module currently provides a function to compute the date of Easter
Sunday for a given Gregorian year using the Meeus/Jones/Butcher algorithm.
"""

from __future__ import annotations

import calendar
import datetime
from typing import Final

__all__: Final = ["easter_date", "nth_weekday_of_month", "last_weekday_of_month"]


def easter_date(year: int) -> datetime.date:
    """Return the Gregorian date of Easter Sunday for *year*.

    The implementation follows the Meeus/Jones/Butcher algorithm, which is
    valid for all years in the Gregorian calendar (i.e. year >= 1583).

    Args:
        year: Gregorian year for which to compute Easter.

    Returns:
        A :class:`datetime.date` representing Easter Sunday.

    Raises:
        ValueError: If *year* is less than 1583 (the start of the Gregorian
            calendar).
    """
    if year < 1583:
        raise ValueError("year must be >= 1583 for Gregorian Easter calculation")

    # Computation steps as described in the algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l_val = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l_val) // 451
    month = (h + l_val - 7 * m + 114) // 31  # 3 = March, 4 = April
    day = ((h + l_val - 7 * m + 114) % 31) + 1

    return datetime.date(year, month, day)


def nth_weekday_of_month(year: int, month: int, weekday: int, n: int) -> datetime.date:
    """Return the date of the *n*‑th *weekday* in a given month.

    Parameters
    ----------
    year: int
        Gregorian year.
    month: int
        Month number, 1‑12.
    weekday: int
        Desired weekday where Monday is ``0`` and Sunday is ``6`` (as used by
        :meth:`datetime.date.weekday`).
    n: int
        1‑based occurrence index (e.g., ``1`` for the first occurrence).

    Returns
    -------
    datetime.date
        The calculated date.

    Raises
    ------
    ValueError
        If the requested occurrence does not exist in the month.
    """
    if not 1 <= month <= 12:
        raise ValueError("month must be in 1..12")
    if not 0 <= weekday <= 6:
        raise ValueError("weekday must be in 0..6")
    if n < 1:
        raise ValueError("n must be >= 1")

    first_day = datetime.date(year, month, 1)
    first_weekday = first_day.weekday()
    # Days to add to get to the first desired weekday
    days_until_weekday = (weekday - first_weekday) % 7
    day = 1 + days_until_weekday + (n - 1) * 7
    _, days_in_month = calendar.monthrange(year, month)
    if day > days_in_month:
        raise ValueError("The requested weekday occurrence does not exist in this month")
    return datetime.date(year, month, day)


def last_weekday_of_month(year: int, month: int, weekday: int) -> datetime.date:
    """Return the date of the last *weekday* in a given month.

    Parameters
    ----------
    year: int
        Gregorian year.
    month: int
        Month number, 1‑12.
    weekday: int
        Desired weekday where Monday is ``0`` and Sunday is ``6`` (as used by
        :meth:`datetime.date.weekday`).

    Returns
    -------
    datetime.date
        The calculated date.

    Raises
    ------
    ValueError
        If *month* or *weekday* are out of their valid ranges.
    """
    if not 1 <= month <= 12:
        raise ValueError("month must be in 1..12")
    if not 0 <= weekday <= 6:
        raise ValueError("weekday must be in 0..6")

    _, days_in_month = calendar.monthrange(year, month)
    last_day = datetime.date(year, month, days_in_month)
    # Walk backwards until we hit the desired weekday
    offset = (last_day.weekday() - weekday) % 7
    target_day = days_in_month - offset
    return datetime.date(year, month, target_day)
