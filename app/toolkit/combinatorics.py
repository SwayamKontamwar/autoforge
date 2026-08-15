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


__all__ = ["nth_permutation"]
