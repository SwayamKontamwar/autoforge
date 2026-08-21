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


class LFUCache(Generic[K, V]):
    """Fixed‑capacity Least‑Frequently‑Used (LFU) cache.

    Items are evicted based on usage frequency; the item with the lowest
    access count is removed first.  When frequencies tie, the least‑recently
    used among them is evicted.

    Args:
        capacity: Positive integer defining the maximum number of items.

    Raises:
        ValueError: If *capacity* is not a positive integer.
    """

    __slots__ = ("capacity", "_data", "_counter")

    def __init__(self, capacity: int) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        self.capacity: int = capacity
        # key -> (value, freq, timestamp)
        self._data: dict[K, tuple[V, int, int]] = {}
        self._counter: int = 0  # monotonically increasing to track recency

    def _touch(self, key: K) -> None:
        """Increment frequency and update timestamp for *key*."""
        value, freq, _ = self._data[key]
        self._counter += 1
        self._data[key] = (value, freq + 1, self._counter)

    def get(self, key: K) -> Optional[V]:
        """Return the value for *key* if present, otherwise ``None``.

        The access increments the usage frequency.
        """
        if key not in self._data:
            return None
        self._touch(key)
        return self._data[key][0]

    def put(self, key: K, value: V) -> None:
        """Insert or update *key* with *value*.

        If the cache exceeds its capacity the LFU entry is evicted.
        Updating an existing key also counts as an access.
        """
        if key in self._data:
            # Update value and treat as access
            _, freq, _ = self._data[key]
            self._counter += 1
            self._data[key] = (value, freq + 1, self._counter)
        else:
            if len(self._data) >= self.capacity:
                # Evict the key with lowest (freq, timestamp)
                evict_key = min(
                    self._data.items(),
                    key=lambda item: (item[1][1], item[1][2]),
                )[0]
                del self._data[evict_key]
            self._counter += 1
            # New entries start with frequency 1
            self._data[key] = (value, 1, self._counter)

    # Optional convenience methods ------------------------------------------------
    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        items = [(k, v[0], v[1]) for k, v in self._data.items()]
        return f"{self.__class__.__name__}(capacity={self.capacity}, data={items})"
