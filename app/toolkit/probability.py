"""Probability utilities for the toolkit.

Provides probability mass functions for binomial and Poisson distributions,
as well as a generic expected value calculator.
"""

from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Sequence


def binomial_pmf(k: int, n: int, p: float) -> float:
    """Return the probability mass for k successes in n Bernoulli trials.

    Args:
        k: Number of successes (must be 0 ≤ k ≤ n).
        n: Number of trials (must be non‑negative).
        p: Success probability per trial (0 ≤ p ≤ 1).

    Raises:
        ValueError: If any argument is out of its valid range.
    """
    if not isinstance(k, int) or not isinstance(n, int):
        raise ValueError("k and n must be integers")
    if k < 0 or n < 0:
        raise ValueError("k and n must be non‑negative")
    if k > n:
        raise ValueError("k cannot be greater than n")
    if not isinstance(p, (int, float)):
        raise ValueError("p must be numeric")
    if p < 0.0 or p > 1.0:
        raise ValueError("p must be between 0 and 1 inclusive")

    if n == 0:
        return 1.0 if k == 0 else 0.0

    return math.comb(n, k) * (p**k) * ((1.0 - p) ** (n - k))


def poisson_pmf(k: int, lam: float) -> float:
    """Return the Poisson probability mass for k occurrences given rate λ.

    Args:
        k: Number of occurrences (must be a non‑negative integer).
        lam: Rate parameter λ (must be non‑negative).

    Raises:
        ValueError: If any argument is out of its valid range.
    """
    if not isinstance(k, int):
        raise ValueError("k must be an integer")
    if k < 0:
        raise ValueError("k must be non‑negative")
    if not isinstance(lam, (int, float)):
        raise ValueError("λ must be numeric")
    if lam < 0.0:
        raise ValueError("λ must be non‑negative")

    if lam == 0.0:
        return 1.0 if k == 0 else 0.0

    return math.exp(-lam) * (lam**k) / math.factorial(k)


def expected_value(
    outcomes: Sequence[float] | Iterable[float],
    probabilities: Sequence[float] | Iterable[float],
) -> float:
    """Calculate the expected value of a discrete distribution.

    The function expects *outcomes* and *probabilities* to be sequences of the
    same length where each probability corresponds to the outcome at the same
    index. Probabilities must be non‑negative and sum to 1 (within a small
    tolerance).

    Args:
        outcomes: Iterable of outcome values.
        probabilities: Iterable of probabilities for each outcome.

    Returns:
        The expected value as a float.

    Raises:
        ValueError: If the inputs are of mismatched lengths, contain invalid
            probabilities, or the probabilities do not sum to 1.
    """
    outcomes_list = list(outcomes)
    probs_list = list(probabilities)

    if len(outcomes_list) != len(probs_list):
        raise ValueError("outcomes and probabilities must have the same length")

    if not outcomes_list:
        return 0.0

    total_prob = sum(probs_list)
    if not math.isclose(total_prob, 1.0, rel_tol=1e-9, abs_tol=1e-12):
        raise ValueError("probabilities must sum to 1")

    exp_val = 0.0
    for o, p in zip(outcomes_list, probs_list):
        if not isinstance(p, (int, float)):
            raise ValueError("probability values must be numeric")
        if p < 0.0:
            raise ValueError("probability values must be non‑negative")
        exp_val += o * p

    return exp_val
