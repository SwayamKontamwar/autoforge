"""Utility functions for working with iterables and streams.

This module currently provides a ``batched`` function that groups items from an
iterable into tuples of a specified maximum size.
"""

from __future__ import annotations

from typing import Callable, Iterable, Iterator, Tuple, TypeVar

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


def iterate(start: T, f: Callable[[T], T]) -> Iterator[T]:
    """Yield an infinite lazy sequence: start, f(start), f(f(start)), ...

    Args:
        start: The initial value of the sequence.
        f: A function that computes the next value from the current one.

    Yields:
        The successive values of the sequence.
    """
    value = start
    while True:
        yield value
        value = f(value)
