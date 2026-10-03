"""Combinatorial utilities for the toolkit.

This module currently provides a function to compute the *n*‑th lexicographic
permutation of a sequence.
"""

from __future__ import annotations

import math
from typing import List, Sequence, TypeVar

T = TypeVar("T")


def nth_permutation(seq: Sequence[T], n: int) -> List[T]:
    """Return the *n*‑th lexicographic permutation of *seq*.

    The function treats *seq* as an ordered collection of distinct items.
    ``n`` is zero‑based: ``n == 0`` returns the items in their original order.
    If ``n`` is negative or greater than or equal to the total number of
    permutations, a :class:`ValueError` is raised.

    Args:
        seq: The input sequence (e.g., list, tuple, or any ``Sequence``).
        n: The zero‑based index of the desired permutation.

    Returns:
        A list containing the *n*‑th permutation of the input items.

    Raises:
        ValueError: If ``n`` is out of the valid range.
    """
    items = list(seq)
    length = len(items)
    total = math.factorial(length)

    if n < 0 or n >= total:
        raise ValueError("n out of range for the given sequence")

    result: List[T] = []
    available = items[:]
    remaining = n

    for i in range(length, 0, -1):
        f = math.factorial(i - 1)
        index = remaining // f
        remaining = remaining % f
        result.append(available.pop(index))

    return result


def permutation_index(seq: Sequence[T], perm: Sequence[T]) -> int:
    """Return the lexicographic index of *perm* within all permutations of *seq*.

    Both *seq* and *perm* must contain the same distinct elements. The index is
    zero‑based, matching the behaviour of :func:`nth_permutation`.

    Args:
        seq: The original sequence of distinct items.
        perm: A permutation of ``seq``.

    Returns:
        The zero‑based index of ``perm`` in the lexicographic ordering.

    Raises:
        ValueError: If ``perm`` is not a valid permutation of ``seq``.
    """
    if len(seq) != len(perm):
        raise ValueError("seq and perm must have the same length")

    # Ensure both contain the same elements (no duplicates, no missing)
    if set(seq) != set(perm):
        raise ValueError("perm is not a valid permutation of seq")

    index = 0
    remaining = list(seq)

    for p in perm:
        pos = remaining.index(p)
        f = math.factorial(len(remaining) - 1)
        index += pos * f
        remaining.pop(pos)

    return index


def multinomial(counts: Sequence[int]) -> int:
    """Return the multinomial coefficient for the given *counts*.

    The multinomial coefficient is defined as::

        (sum(counts))! / (c1! * c2! * ... * ck!)

    where ``counts`` is a sequence of non‑negative integers. An empty ``counts``
    sequence yields ``1`` (the coefficient of the empty partition).

    Args:
        counts: A sequence of non‑negative integer counts.

    Returns:
        The multinomial coefficient as an integer.

    Raises:
        ValueError: If any count is negative.
    """
    if any(c < 0 for c in counts):
        raise ValueError("multinomial counts must be non‑negative")

    total = sum(counts)
    numerator = math.factorial(total)

    denominator = 1
    for c in counts:
        denominator *= math.factorial(c)

    return numerator // denominator
