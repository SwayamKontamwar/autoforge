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
    """Return the lexicographic index of *perm* relative to *seq*.

    Both *seq* and *perm* must contain the same distinct items.  The index is
    zero‑based, meaning that if *perm* equals *seq* the function returns ``0``.
    The ordering used is the order of items in *seq*.

    Args:
        seq: The reference sequence defining the ordering.
        perm: A permutation of ``seq`` whose index is desired.

    Returns:
        The zero‑based lexicographic index of ``perm`` among all permutations
        of ``seq``.

    Raises:
        ValueError: If ``perm`` is not a permutation of ``seq``.
    """
    if len(seq) != len(perm):
        raise ValueError("seq and perm must have the same length")

    # Map each item to its position in the original sequence for ordering.
    order = {item: idx for idx, item in enumerate(seq)}
    if set(seq) != set(perm):
        raise ValueError("perm must be a permutation of seq")

    index = 0
    remaining_items = list(seq)  # mutable list of items not yet placed
    factorial = math.factorial

    for i, p in enumerate(perm):
        # Determine how many remaining items are less than the current one
        # according to the original ordering.
        less_count = sum(1 for item in remaining_items if order[item] < order[p])
        remaining_len = len(remaining_items)
        index += less_count * factorial(remaining_len - 1)
        # Remove the used item.
        remaining_items.remove(p)

    return index


__all__ = ["nth_permutation", "permutation_index"]
