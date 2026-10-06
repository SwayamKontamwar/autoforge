"""Vector utilities for three‑dimensional space.

The module currently provides a small set of helper functions for 3‑vectors.
All functions accept any iterable (list, tuple, etc.) of exactly three numeric
components and return a tuple of three numbers.

Only the functionality required by the backlog item is implemented here.
"""

from __future__ import annotations

from typing import Iterable, Tuple


def _validate_vector(v: Iterable[float]) -> Tuple[float, float, float]:
    """Validate that *v* is a 3‑component iterable of numbers.

    Returns the components as a tuple of three floats. Raises ``ValueError`` if
    the length is not three.
    """
    try:
        components = tuple(v)
    except TypeError as exc:
        raise ValueError("Vector must be an iterable") from exc

    if len(components) != 3:
        raise ValueError("Vector must contain exactly three components")
    return components  # type: ignore[return-value]


def v3_add(v1: Iterable[float], v2: Iterable[float]) -> Tuple[float, float, float]:
    """Add two 3‑vectors component‑wise.

    Parameters
    ----------
    v1, v2:
        Iterables with exactly three numeric components each.

    Returns
    -------
    tuple[float, float, float]
        The component‑wise sum of the two vectors.
    """
    a = _validate_vector(v1)
    b = _validate_vector(v2)
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def v3_sub(v1: Iterable[float], v2: Iterable[float]) -> Tuple[float, float, float]:
    """Subtract two 3‑vectors component‑wise (v1 - v2).

    Parameters
    ----------
    v1, v2:
        Iterables with exactly three numeric components each.

    Returns
    -------
    tuple[float, float, float]
        The component‑wise difference of the two vectors.
    """
    a = _validate_vector(v1)
    b = _validate_vector(v2)
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def v3_dot(v1: Iterable[float], v2: Iterable[float]) -> float:
    """Return the dot product of two 3‑vectors.

    Parameters
    ----------
    v1, v2:
        Iterables with exactly three numeric components each.

    Returns
    -------
    float
        The scalar dot product of the two vectors.
    """
    a = _validate_vector(v1)
    b = _validate_vector(v2)
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
