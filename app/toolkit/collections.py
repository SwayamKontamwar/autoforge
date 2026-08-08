"""Collection utilities for the autoforge toolkit.

Provides ``chunk`` – split an iterable into consecutive sub‑lists of a fixed
size.

The function is deliberately simple and pure: it does not modify the input
iterable and returns a list of lists, each containing up to ``size`` elements.
If ``size`` is not a positive integer a ``ValueError`` is raised.
"""

from __future__ import annotations

from typing import Iterable, List, TypeVar

_T = TypeVar("_T")


def chunk(iterable: Iterable[_T], size: int) -> List[List[_T]]:
    """Split *iterable* into consecutive sub‑lists of length *size*.

    Args:
        iterable: Any iterable source of items.
        size: Desired maximum length of each chunk; must be a positive integer.

    Returns:
        A list where each element is a list containing up to ``size`` items from
        *iterable* in the original order.

    Raises:
        ValueError: If ``size`` is less than 1.
    """
    if size < 1:
        raise ValueError("size must be a positive integer")
    result: List[List[_T]] = []
    buffer: List[_T] = []
    for item in iterable:
        buffer.append(item)
        if len(buffer) == size:
            result.append(buffer)
            buffer = []
    if buffer:
        result.append(buffer)
    return result
