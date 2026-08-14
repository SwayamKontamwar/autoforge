"""Mathematical utilities for the toolkit.

Provides functions that are not covered elsewhere in the standard‑library‑style
toolkit.  Currently includes:

* ``hypot`` – Euclidean norm (length) of an arbitrary number of components.
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
