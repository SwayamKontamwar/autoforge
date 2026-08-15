"""Probability utilities for the toolkit.

Currently provides the binomial probability mass function.
"""

from __future__ import annotations

import math


def binomial_pmf(k: int, n: int, p: float) -> float:
    """Return the probability mass function of the binomial distribution.

    Args:
        k: Number of successes (0 ≤ k ≤ n).
        n: Number of independent Bernoulli trials (n ≥ 0).
        p: Probability of success on each trial (0 ≤ p ≤ 1).

    Returns:
        Probability of observing exactly *k* successes.

    Raises:
        ValueError: If any argument is out of its valid range or of the wrong type.
    """
    if not isinstance(k, int) or not isinstance(n, int):
        raise ValueError("k and n must be integers")
    if n < 0:
        raise ValueError("n must be a non‑negative integer")
    if k < 0 or k > n:
        raise ValueError("k must satisfy 0 ≤ k ≤ n")
    if not isinstance(p, (int, float)):
        raise ValueError("p must be a numeric type")
    if not (0.0 <= p <= 1.0):
        raise ValueError("p must be between 0 and 1 inclusive")

    # Using the standard binomial formula: C(n, k) * p**k * (1-p)**(n-k)
    combination = math.comb(n, k)
    return combination * (p**k) * ((1.0 - p) ** (n - k))


__all__: list[str] = ["binomial_pmf"]
