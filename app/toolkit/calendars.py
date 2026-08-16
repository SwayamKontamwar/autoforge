"""Utility functions for calendar calculations.

This module currently provides a function to compute the date of Easter
Sunday for a given Gregorian year using the Meeus/Jones/Butcher algorithm.
"""

from __future__ import annotations

import datetime
from typing import Final

__all__: Final = ["easter_date"]


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
