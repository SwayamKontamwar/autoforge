"""Least‑Recently‑Used (LRU) cache implementation.

The cache has a fixed *capacity* defined at construction time.  When the number
of stored items exceeds the capacity the least‑recently accessed entry is
evicted.  Accesses are performed via :meth:`get` and :meth:`put`; both
operations update the recency order.

Typical usage::

    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1   # 'a' becomes most‑recent
    cache.put("c", 3)            # evicts 'b'
    assert cache.get("b") is None
"""

from __future__ import annotations

from collections import OrderedDict
from typing import Generic, Hashable, Optional, TypeVar

K = TypeVar("K", bound=Hashable)
V = TypeVar("V")


class LRUCache(Generic[K, V]):
    """Fixed‑capacity LRU cache.

    Args:
        capacity: Positive integer defining the maximum number of items.

    Raises:
        ValueError: If *capacity* is not a positive integer.
    """

    __slots__ = ("capacity", "_data")

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity: int = capacity
        self._data: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K) -> Optional[V]:
        """Return the value for *key* if present, otherwise ``None``.

        The accessed entry becomes the most‑recently used.
        """
        if key not in self._data:
            return None
        value = self._data.pop(key)
        self._data[key] = value
        return value

    def put(self, key: K, value: V) -> None:
        """Insert or update *key* with *value*.

        If the cache exceeds its capacity the least‑recently used entry is
        evicted.
        """
        if key in self._data:
            self._data.pop(key)
        self._data[key] = value
        if len(self._data) > self.capacity:
            # popitem(last=False) removes the first (least‑recent) item
            self._data.popitem(last=False)

    # Optional convenience methods ------------------------------------------------
    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(capacity={self.capacity}, data={list(self._data.items())})"
        )
