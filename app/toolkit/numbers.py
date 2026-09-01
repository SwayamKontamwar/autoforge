"""Number‑related utility functions for the autoforge toolkit.

Currently provides:
* ``clamp`` – constrain a numeric value to an inclusive ``min_``/``max_`` range.
* ``lerp`` – linearly interpolate between two numbers by a fraction.
* ``inverse_lerp`` – compute the fraction of a value between two bounds.
"""

from __future__ import annotations

from typing import Union

Number = Union[int, float]


def clamp(value: Number, min_: Number, max_: Number) -> Number:
    """Return ``value`` constrained to the inclusive range ``[min_, max_]``.

    If ``value`` is less than ``min_``, ``min_`` is returned.
    If ``value`` is greater than ``max_``, ``max_`` is returned.
    Otherwise ``value`` is returned unchanged.

    Args:
        value: The numeric value to clamp.
        min_: The lower bound of the allowed range.
        max_: The upper bound of the allowed range.

    Raises:
        ValueError: If ``min_`` is greater than ``max_``.
    """
    if min_ > max_:
        raise ValueError("min_ must not be greater than max_")
    if value < min_:
        return min_
    if value > max_:
        return max_
    return value


def lerp(start: Number, end: Number, fraction: Number) -> Number:
    """Linearly interpolate between ``start`` and ``end`` by ``fraction``.

    The result is ``start + (end - start) * fraction``.  ``fraction`` may be
    outside the ``[0, 1]`` interval; values less than 0 extrapolate before
    ``start`` and values greater than 1 extrapolate beyond ``end``.

    Args:
        start: The starting numeric value.
        end: The ending numeric value.
        fraction: The interpolation fraction.

    Returns:
        The interpolated numeric value.
    """
    return start + (end - start) * fraction


def inverse_lerp(start: Number, end: Number, value: Number) -> Number:
    """Return the fractional position of ``value`` between ``start`` and ``end``.

    The result is ``(value - start) / (end - start)``.  If ``start`` and ``end``
    are equal, a ``ValueError`` is raised because the fraction is undefined.

    Args:
        start: The lower bound of the range.
        end: The upper bound of the range.
        value: The value whose fractional position is desired.

    Returns:
        The fraction representing ``value``'s position between ``start`` and ``end``.

    Raises:
        ValueError: If ``start`` equals ``end``.
    """
    if start == end:
        raise ValueError("start and end must not be equal")
    return (value - start) / (end - start)


__all__ = ["clamp", "lerp", "inverse_lerp"]
