"""Date‑time utilities for the autoforge toolkit.

The module currently provides public functions:

* ``parse_iso`` – Parse an ISO‑8601 string into a timezone‑aware ``datetime``.
* ``to_iso`` – Format a ``datetime`` as an ISO‑8601 string in UTC.
* ``now_utc`` – Return the current timezone‑aware UTC datetime.
* ``humanize_delta`` – Convert a ``timedelta`` to a human‑readable description
  such as ``\"3 hours ago\"`` or ``\"in 5 minutes\"``.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Final

__all__: Final = ["parse_iso", "to_iso", "now_utc", "humanize_delta"]


def parse_iso(value: str) -> datetime:
    """Parse an ISO‑8601 string into a timezone‑aware ``datetime``.

    The function accepts the formats produced by ``datetime.isoformat`` as well
    as the common ``Z`` suffix for UTC. If the input does not contain any
    timezone information, the result is assumed to be UTC.

    Args:
        value: An ISO‑8601 formatted date‑time string.

    Returns:
        A ``datetime`` instance that is always timezone‑aware.

    Raises:
        ValueError: If the string cannot be parsed as an ISO‑8601 datetime.
    """
    iso = value.rstrip()
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(iso)
    except Exception as exc:
        raise ValueError(f"Invalid ISO‑8601 string: {value!r}") from exc

    if dt.tzinfo is None:
        # Naïve datetime – assume UTC
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        # Ensure the tzinfo is a proper timezone object (fromisoformat already does)
        dt = dt

    return dt


def to_iso(dt: datetime) -> str:
    """Format a ``datetime`` as an ISO‑8601 string in UTC with a ``Z`` suffix.

    Naïve datetimes are assumed to be UTC.

    Args:
        dt: The datetime to format.

    Returns:
        An ISO‑8601 string ending with ``Z``.
    """
    if dt.tzinfo is None:
        utc_dt = dt.replace(tzinfo=timezone.utc)
    else:
        utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def now_utc() -> datetime:
    """Return the current UTC datetime, timezone‑aware."""
    return datetime.now(timezone.utc)


def humanize_delta(delta: timedelta) -> str:
    """Return a human‑readable description of a ``timedelta``.

    For positive deltas the description ends with ``\"ago\"`` (e.g. ``\"3 hours
    ago\"``). For negative deltas it is prefixed with ``\"in\"`` (e.g. ``\"in 5
    minutes\"``). A zero delta returns ``\"just now\"``.

    The function chooses the largest appropriate unit among years, months,
    weeks, days, hours, minutes, and seconds, using integer rounding down.

    Args:
        delta: The time difference to describe.

    Returns:
        A human‑readable string.
    """
    total_seconds = int(delta.total_seconds())
    if total_seconds == 0:
        return "just now"

    past = total_seconds > 0
    secs = abs(total_seconds)

    # Approximate month and year lengths
    minute = 60
    hour = 60 * minute
    day = 24 * hour
    week = 7 * day
    month = 30 * day
    year = 365 * day

    if secs >= year:
        count = secs // year
        unit = "year"
    elif secs >= month:
        count = secs // month
        unit = "month"
    elif secs >= week:
        count = secs // week
        unit = "week"
    elif secs >= day:
        count = secs // day
        unit = "day"
    elif secs >= hour:
        count = secs // hour
        unit = "hour"
    elif secs >= minute:
        count = secs // minute
        unit = "minute"
    else:
        count = secs
        unit = "second"

    plural = "s" if count != 1 else ""
    if past:
        return f"{count} {unit}{plural} ago"
    else:
        return f"in {count} {unit}{plural}"
