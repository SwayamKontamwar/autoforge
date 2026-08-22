"""Algorithm utilities.

Provides ``binary_search`` for sorted sequences.
"""

from __future__ import annotations

from typing import Sequence, TypeVar

T = TypeVar("T")


def binary_search(seq: Sequence[T], target: T) -> int:
    """Return the index of *target* in *seq* or -1 if not present.

    *seq* must be sorted in ascending order. The function works with any
    sequence supporting ``__len__`` and element access via ``[]``.
    """
    lo = 0
    hi = len(seq) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        mid_val = seq[mid]
        if mid_val == target:
            return mid
        if mid_val < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def bisect_left(seq: Sequence[T], target: T) -> int:
    """Return the leftmost insertion point for *target* in a sorted *seq*.

    The function returns an index ``i`` such that all elements before ``i`` are
    less than ``target`` and all elements at or after ``i`` are greater than or
    equal to ``target``. If *target* is greater than all elements, ``i`` will be
    ``len(seq)``. Works with any sequence supporting ``__len__`` and ``[]``.
    """
    lo = 0
    hi = len(seq)
    while lo < hi:
        mid = (lo + hi) // 2
        if seq[mid] < target:
            lo = mid + 1
        else:
            hi = mid
    return lo
