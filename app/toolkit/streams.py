"""Utility functions for working with iterables and streams.

This module currently provides a ``batched`` function that groups items from an
iterable into tuples of a specified maximum size.
"""

from __future__ import annotations

from typing import Iterable, Iterator, Tuple, TypeVar

T = TypeVar("T")


def batched(iterable: Iterable[T], n: int) -> Iterator[Tuple[T, ...]]:
    """Yield successive tuples of up to *n* items from *iterable*.

    Args:
        iterable: Source of items.
        n: Maximum size of each batch; must be a positive integer.

    Yields:
        Tuples containing between 1 and *n* items. The final tuple may be
        shorter if the iterable is exhausted.

    Raises:
        ValueError: If *n* is not a positive integer.
    """
    if n <= 0:
        raise ValueError("n must be a positive integer")
    it = iter(iterable)
    while True:
        # Collect up to n items from the iterator.
        batch = tuple(item for _, item in zip(range(n), it))
        if not batch:
            break
        yield batch
