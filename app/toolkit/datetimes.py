"""Date‑time utilities for the autoforge toolkit.

The module currently provides a single public function:

* ``parse_iso`` – Parse an ISO‑8601 string into a timezone‑aware ``datetime``.
* ``to_iso`` – Format a ``datetime`` as an ISO‑8601 string in UTC.
* ``now_utc`` – Return the current timezone‑aware UTC datetime.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Final

__all__: Final = ["parse_iso", "to_iso", "now_utc"]


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
    # Normalise the UTC designator ``Z`` to ``+00:00`` which ``fromisoformat`` can
    # understand. ``fromisoformat`` also handles offsets like ``+02:00``.
    iso = value.rstrip()
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(iso)
    except Exception as exc:
        raise ValueError(f"Invalid ISO‑8601 datetime string: {value!r}") from exc

    # Ensure the result is timezone‑aware; treat naive datetimes as UTC.
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def to_iso(dt: datetime) -> str:
    """Return an ISO‑8601 string representing ``dt`` in UTC.

    Naive ``datetime`` objects are assumed to be UTC. Aware objects are
    converted to UTC before formatting. The resulting string uses the ``Z``
    suffix to denote UTC.

    Args:
        dt: The datetime to format.

    Returns:
        An ISO‑8601 formatted string ending with ``Z``.
    """
    if dt.tzinfo is None:
        utc_dt = dt.replace(tzinfo=timezone.utc)
    else:
        utc_dt = dt.astimezone(timezone.utc)
    # isoformat produces ``+00:00`` for UTC; replace with ``Z`` for brevity.
    return utc_dt.isoformat().replace("+00:00", "Z")


def now_utc() -> datetime:
    """Return the current UTC datetime, timezone‑aware."""
    return datetime.now(timezone.utc)
