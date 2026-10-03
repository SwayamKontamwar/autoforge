"""Number‑theoretic utilities.

Provides functions for divisor counting, divisor summation, Euler's totient,
Möbius function, and related number‑theoretic calculations.
"""

from __future__ import annotations

import math


def _validate_positive_int(n: int) -> None:
    """Validate that *n* is a positive integer."""
    if n <= 0:
        raise ValueError("n must be a positive integer")


def divisor_count(n: int) -> int:
    """Return the number of positive divisors of *n*.

    Args:
        n: Positive integer.

    Returns:
        The count of divisors of *n*.

    Raises:
        ValueError: If *n* is not a positive integer.
    """
    _validate_positive_int(n)
    count = 0
    root = math.isqrt(n)
    for i in range(1, root + 1):
        if n % i == 0:
            count += 2  # i and n//i
    if root * root == n:
        count -= 1  # perfect square correction
    return count


def divisor_sum(n: int) -> int:
    """Return the sum of all positive divisors of *n*.

    Args:
        n: Positive integer.

    Returns:
        The sum of divisors of *n*.

    Raises:
        ValueError: If *n* is not a positive integer.
    """
    _validate_positive_int(n)
    total = 0
    root = math.isqrt(n)
    for i in range(1, root + 1):
        if n % i == 0:
            total += i
            counterpart = n // i
            if counterpart != i:
                total += counterpart
    return total


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
    _validate_positive_int(n)
    result = n
    temp = n
    for p in range(2, math.isqrt(temp) + 1):
        if temp % p == 0:
            while temp % p == 0:
                temp //= p
            result -= result // p
    if temp > 1:
        result -= result // temp
    return result


def mobius(n: int) -> int:
    """Return the Möbius function μ(n) for a positive integer *n*.

    The Möbius function is defined as:
    * μ(1) = 1
    * μ(n) = 0 if *n* has a squared prime factor
    * μ(n) = (-1)^k where *k* is the number of distinct prime factors of *n*

    Args:
        n: Positive integer.

    Returns:
        The Möbius value for *n*.

    Raises:
        ValueError: If *n* is not a positive integer.
    """
    _validate_positive_int(n)
    if n == 1:
        return 1
    prime_factors = 0
    temp = n
    for p in range(2, math.isqrt(temp) + 1):
        if temp % p == 0:
            if (temp // p) % p == 0:
                return 0  # squared factor
            prime_factors += 1
            while temp % p == 0:
                temp //= p
    if temp > 1:
        prime_factors += 1
    return -1 if prime_factors % 2 else 1
