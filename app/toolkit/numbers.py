"""Number‑related utility functions for the autoforge toolkit.

Currently provides:
* ``clamp`` – constrain a numeric value to an inclusive ``min_``/``max_`` range.
* ``lerp`` – linearly interpolate between two numbers by a fraction.
* ``inverse_lerp`` – compute the fraction of a value between two bounds.
* ``round_to`` – round a number to the nearest multiple of a given step.
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

    ``fraction`` of ``0`` returns ``start``; ``1`` returns ``end``.
    Values outside ``[0, 1]`` extrapolate linearly.

    Args:
        start: Starting value.
        end: Ending value.
        fraction: Interpolation factor.

    Returns:
        Interpolated value.
    """
    return start + (end - start) * fraction


def inverse_lerp(start: Number, end: Number, value: Number) -> Number:
    """Calculate the fraction that ``value`` represents between ``start`` and ``end``.

    ``start`` and ``end`` must not be equal.

    Args:
        start: Lower bound.
        end: Upper bound.
        value: Value to locate.

    Returns:
        Fraction representing ``value``'s position.

    Raises:
        ValueError: If ``start`` equals ``end``.
    """
    if start == end:
        raise ValueError("start and end must not be equal")
    return (value - start) / (end - start)


def round_to(value: Number, step: Number) -> Number:
    """Round ``value`` to the nearest multiple of ``step``.

    ``step`` must be non‑zero. The sign of ``step`` is ignored; rounding is
    performed using the absolute magnitude of ``step``.

    Args:
        value: The number to round.
        step: The step size to round to.

    Returns:
        ``value`` rounded to the nearest multiple of ``step``.

    Raises:
        ValueError: If ``step`` is zero.
    """
    if step == 0:
        raise ValueError("step must not be zero")
    abs_step = abs(step)
    return round(value / abs_step) * abs_step
