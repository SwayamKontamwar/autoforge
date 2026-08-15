"""Number‑theoretic utilities.

This module currently provides a single function:

* :func:`euler_totient` – compute Euler's totient φ(n) for a positive integer.
"""

from __future__ import annotations

import math


def euler_totient(n: int) -> int:
    """Return Euler's totient φ(n) for a positive integer *n*.

    The totient counts the integers in the range ``1..n`` that are coprime to *n*.

    Args:
        n: Positive integer whose totient is to be computed.

    Returns:
        The value of φ(n).

    Raises:
        ValueError: If *n* is not a positive integer.
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")
    result = n
    # Use a copy of n for factorisation
    temp = n
    # Iterate over possible prime factors up to sqrt(temp)
    for p in range(2, math.isqrt(temp) + 1):
        if temp % p == 0:
            # p is a prime factor; remove all occurrences
            while temp % p == 0:
                temp //= p
            result -= result // p
    # If a prime factor larger than sqrt remains, it is temp itself
    if temp > 1:
        result -= result // temp
    return result
