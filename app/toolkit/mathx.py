"""Mathematical utilities for the toolkit.

Provides functions that are not covered elsewhere in the standard‑library‑style
toolkit.  Currently includes:

* ``hypot`` – Euclidean norm (length) of an arbitrary number of components.
* ``clamp_angle`` – Wrap an angle into the range -π to π.
"""

from __future__ import annotations

import math
from typing import Union

Number = Union[int, float]


def hypot(*components: Number) -> float:
    """Return the Euclidean norm of the given components.

    The Euclidean norm (also known as the *L2* norm) of a vector
    ``(x₁, x₂, …, xₙ)`` is defined as ``sqrt(x₁² + x₂² + … + xₙ²)``.
    When called with no components the function returns ``0.0``.

    Args:
        *components: A variable number of numeric values (int or float).

    Returns:
        The Euclidean norm as a ``float``.
    """
    if not components:
        return 0.0
    # Use math.fsum for better precision when summing squares.
    total = math.fsum(c * c for c in components)
    return math.sqrt(total)


def clamp_angle(angle: Number) -> float:
    """Wrap *angle* into the interval ``[-π, π]``.

    The function returns an equivalent angle such that the result lies
    between ``-math.pi`` and ``math.pi`` (inclusive).  It works for any
    real numeric input, handling large magnitudes by using modular arithmetic.

    Args:
        angle: The angle in radians to be wrapped.

    Returns:
        The wrapped angle as a ``float`` within ``[-π, π]``.
    """
    two_pi = 2.0 * math.pi
    # Shift by π, take modulus, then shift back.
    wrapped = (float(angle) + math.pi) % two_pi - math.pi
    # Correct possible negative zero to positive zero for consistency.
    return 0.0 if wrapped == -0.0 else wrapped
