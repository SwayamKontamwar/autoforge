"""Collection utilities for the autoforge toolkit.

Provides ``chunk`` – split an iterable into consecutive sub‑lists of a fixed
size.

The function is deliberately simple and pure: it does not modify the input
iterable and returns a list of lists, each containing up to ``size`` elements.
If ``size`` is not a positive integer a ``ValueError`` is raised.

Also provides ``flatten`` (one‑level flatten), ``flatten_deep`` (recursive
flatten), ``unique`` (deduplicate while preserving order), and ``group_by``
(which groups items by a key function into a dict of lists).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, List, Set, TypeVar

_T = TypeVar("_T")
_K = TypeVar("_K")


def chunk(iterable: Iterable[_T], size: int) -> List[List[_T]]:
    """Split *iterable* into consecutive sub‑lists of length *size*.

    Raises:
        ValueError: If *size* is not a positive integer.
    """
    if size <= 0:
        raise ValueError("size must be a positive integer")
    result: List[List[_T]] = []
    it = iter(iterable)
    while True:
        batch: List[_T] = []
        try:
            for _ in range(size):
                batch.append(next(it))
        except StopIteration:
            pass
        if not batch:
            break
        result.append(batch)
    return result


def _is_iterable_but_not_str(obj: Any) -> bool:
    return isinstance(obj, (list, tuple, set, frozenset)) and not isinstance(obj, (str, bytes))


def flatten(iterable: Iterable[Any]) -> List[Any]:
    """Flatten one level of nesting, leaving strings and bytes untouched."""
    result: List[Any] = []
    for item in iterable:
        if _is_iterable_but_not_str(item):
            result.extend(item)  # type: ignore[arg-type]
        else:
            result.append(item)
    return result


def flatten_deep(iterable: Iterable[Any]) -> List[Any]:
    """Recursively flatten nested iterables, treating strings and bytes as atomic."""
    result: List[Any] = []

    def _extend(inner: Any) -> None:
        if _is_iterable_but_not_str(inner):
            for sub in inner:
                _extend(sub)
        else:
            result.append(inner)

    _extend(iterable)
    return result


def unique(iterable: Iterable[_T]) -> List[_T]:
    """Return a list of unique items preserving the original order."""
    seen: Set[_T] = set()
    result: List[_T] = []
    for item in iterable:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def group_by(iterable: Iterable[_T], key: Callable[[_T], _K]) -> Dict[_K, List[_T]]:
    """Group items from *iterable* into a dict of lists keyed by *key*.

    The *key* function is applied to each element; elements producing the same
    key are collected together in a list preserving their original order.

    An empty *iterable* yields an empty dict.
    """
    result: Dict[_K, List[_T]] = {}
    for item in iterable:
        k = key(item)
        if k in result:
            result[k].append(item)
        else:
            result[k] = [item]
    return result
