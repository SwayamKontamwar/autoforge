"""Statistical utility functions.

This module currently provides a small collection of statistical helpers.
Additional functions may be added over time.
"""

from __future__ import annotations

import math
from typing import Iterable, Sequence


def geometric_mean(values: Iterable[float] | Sequence[float]) -> float:
    """Return the geometric mean of *values*.

    The geometric mean is defined only for positive numbers.  An empty
    *values* iterable or any non‑positive element raises :class:`ValueError`.

    Args:
        values: An iterable of positive numbers.

    Returns:
        The geometric mean of the supplied numbers.

    Example:
        >>> geometric_mean([1, 3, 9])
        3.0
    """
    # Convert to a list to allow multiple passes and length calculation.
    vals = list(values)

    if not vals:
        raise ValueError("geometric_mean requires at least one value")
    # Ensure all numbers are positive.
    for v in vals:
        if v <= 0:
            raise ValueError("geometric_mean is defined only for positive numbers")

    # Compute the product safely using logarithms to avoid overflow for large lists.
    # For small lists the direct product is fine, but the log method works universally.
    log_sum = sum(math.log(v) for v in vals)
    mean_log = log_sum / len(vals)
    return math.exp(mean_log)


def harmonic_mean(values: Iterable[float] | Sequence[float]) -> float:
    """Return the harmonic mean of *values*.

    The harmonic mean is defined only for positive numbers.  An empty
    *values* iterable or any non‑positive element raises :class:`ValueError`.

    Args:
        values: An iterable of positive numbers.

    Returns:
        The harmonic mean of the supplied numbers.

    Example:
        >>> harmonic_mean([1, 2, 4])
        1.7142857142857142
    """
    vals = list(values)

    if not vals:
        raise ValueError("harmonic_mean requires at least one value")
    for v in vals:
        if v <= 0:
            raise ValueError("harmonic_mean is defined only for positive numbers")

    return len(vals) / sum(1.0 / v for v in vals)


def weighted_mean(
    values: Iterable[float] | Sequence[float],
    weights: Iterable[float] | Sequence[float],
) -> float:
    """Return the weighted mean of *values* with corresponding *weights*.

    Both iterables must have the same non‑empty length.  All weights must be
    non‑negative and the total weight must be positive.  An empty iterable or a
    mismatch raises :class:`ValueError`.

    Example:
        >>> weighted_mean([1, 2, 3], [0.2, 0.3, 0.5])
        2.3
    """
    vals = list(values)
    wts = list(weights)

    if not vals or not wts:
        raise ValueError("weighted_mean requires non‑empty values and weights")
    if len(vals) != len(wts):
        raise ValueError("values and weights must have the same length")
    total_weight = sum(wts)
    if total_weight <= 0:
        raise ValueError("total weight must be positive")
    for w in wts:
        if w < 0:
            raise ValueError("weights must be non‑negative")
    weighted_sum = sum(v * w for v, w in zip(vals, wts))
    return weighted_sum / total_weight
