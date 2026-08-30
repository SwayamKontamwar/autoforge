"""Cron‑style scheduling helper.

Provides :func:`next_cron_time` which returns the next ``datetime`` after a
reference point that matches a simple five‑field cron expression.  The
implementation supports the ``*`` wildcard and single integer values for each
field.  More complex syntax (lists, ranges, steps) is intentionally omitted to
keep the utility lightweight and deterministic for the test suite.

The cron format is ``minute hour day month weekday`` where:

* minute – 0‑59
* hour   – 0‑23
* day    – 1‑31
* month  – 1‑12
* weekday – 0‑6 (0 = Sunday, 1 = Monday, …, 6 = Saturday)

If a field is ``*`` it matches any value.  The function always returns a time
strictly later than *from_dt*; if *from_dt* itself matches the expression the
next occurrence is returned.
"""

from __future__ import annotations

import datetime
from typing import Iterator, Set


def _parse_field(field: str, min_val: int, max_val: int) -> Set[int]:
    """Parse a single cron field.

    Currently only ``*`` (wildcard) and a single integer are supported.
    """
    if field == "*":
        return set(range(min_val, max_val + 1))
    try:
        value = int(field)
    except ValueError as exc:
        raise ValueError(f"Unsupported cron field: {field!r}") from exc
    if not (min_val <= value <= max_val):
        raise ValueError(f"Cron field {field!r} out of range [{min_val}, {max_val}]")
    return {value}


def _weekday_to_python(cron_weekday: int) -> int:
    """Convert cron weekday (0=Sunday) to Python's ``datetime.weekday`` (0=Monday)."""
    return (cron_weekday + 6) % 7  # Sunday -> 6, Monday -> 0, …


def next_cron_time(cron_expr: str, from_dt: datetime.datetime) -> datetime.datetime:
    """Return the next ``datetime`` after *from_dt* that matches *cron_expr*.

    Args:
        cron_expr: Five‑field cron expression (minute hour day month weekday).
        from_dt:   Reference ``datetime`` (naïve or timezone‑aware).  The result
                   will have the same tzinfo as *from_dt*.

    Returns:
        A ``datetime`` strictly later than *from_dt* matching the expression.

    Raises:
        ValueError: If the expression cannot be parsed or no matching time is
                    found within a reasonable search window (5 years).
    """
    minute_f, hour_f, day_f, month_f, weekday_f = cron_expr.strip().split()

    minute_set = _parse_field(minute_f, 0, 59)
    hour_set = _parse_field(hour_f, 0, 23)
    day_set = _parse_field(day_f, 1, 31)
    month_set = _parse_field(month_f, 1, 12)
    weekday_set_raw = _parse_field(weekday_f, 0, 6)
    weekday_set = {_weekday_to_python(w) for w in weekday_set_raw}

    # Start searching one minute after the reference point.
    candidate = from_dt + datetime.timedelta(minutes=1)

    # Limit search to 5 years to avoid infinite loops.
    limit = from_dt + datetime.timedelta(days=5 * 366)

    while candidate <= limit:
        if (
            candidate.minute in minute_set
            and candidate.hour in hour_set
            and candidate.day in day_set
            and candidate.month in month_set
            and candidate.weekday() in weekday_set
        ):
            return candidate
        candidate += datetime.timedelta(minutes=1)

    raise ValueError("No matching datetime found within 5‑year window")


def cron_iter(cron_expr: str, start_dt: datetime.datetime) -> Iterator[datetime.datetime]:
    """Yield successive datetimes matching *cron_expr* after *start_dt*.

    The first yielded value is the first match **strictly later** than
    ``start_dt``.  The iterator is infinite; callers should break when they have
    collected enough values.

    Args:
        cron_expr: Five‑field cron expression (minute hour day month weekday).
        start_dt:  Reference ``datetime`` (naïve or timezone‑aware).

    Yields:
        ``datetime`` objects matching the expression, preserving ``tzinfo``.
    """
    current = start_dt
    while True:
        nxt = next_cron_time(cron_expr, current)
        yield nxt
        current = nxt
