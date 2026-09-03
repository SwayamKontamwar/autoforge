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

import time
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

        If the cache
        """
        if key in self._data:
            # Update existing entry; reset frequency to 1 and update timestamp
            self._counter += 1
            self._data[key] = (value, 1, self._counter)
        else:
            if len(self._data) >= self.capacity:
                # Evict the least‑frequently used entry
                # Find minimum frequency
                min_freq = min(freq for _, freq, _ in self._data.values())
                # Among those, find the oldest timestamp
                candidates = [
                    (k, ts) for k, (_, freq, ts) in self._data.items() if freq == min_freq
                ]
                evict_key, _ = min(candidates, key=lambda item: item[1])
                del self._data[evict_key]
            self._counter += 1
            self._data[key] = (value, 1, self._counter)

    def __len__(self) -> int:
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        return key in self._data

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(capacity={self.capacity}, data={self._data})"


class TTLCache(Generic[K, V]):
    """Time‑to‑Live cache.

    Each entry expires *ttl* seconds after insertion.  Expired entries are
    treated as missing and are removed on access or when space is needed.

    Args:
        capacity: Positive integer defining the maximum number of items.
        ttl: Positive number of seconds an entry remains valid.

    Raises:
        ValueError: If *capacity* or *ttl* is not positive.
    """

    __slots__ = ("capacity", "ttl", "_data")

    def __init__(self, capacity: int, ttl: float) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be a positive integer")
        if ttl <= 0:
            raise ValueError("ttl must be a positive number")
        self.capacity: int = capacity
        self.ttl: float = float(ttl)
        # key -> (value, expiry_timestamp)
        self._data: dict[K, tuple[V, float]] = {}

    def _purge_expired(self) -> None:
        """Remove all expired entries."""
        now = time.monotonic()
        expired_keys = [k for k, (_, exp) in self._data.items() if exp <= now]
        for k in expired_keys:
            del self._data[k]

    def get(self, key: K) -> Optional[V]:
        """Return the value for *key* if present and not expired, otherwise ``None``."""
        self._purge_expired()
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expiry = entry
        if expiry <= time.monotonic():
            del self._data[key]
            return None
        return value

    def put(self, key: K, value: V) -> None:
        """Insert or update *key* with *value* and reset its TTL."""
        self._purge_expired()
        expiry = time.monotonic() + self.ttl
        self._data[key] = (value, expiry)
        if len(self._data) > self.capacity:
            # Evict the entry with the earliest expiry (i.e., the one that will
            # expire soonest).  If multiple share the same expiry, evict an
            # arbitrary one.
            oldest_key = min(self._data.items(), key=lambda item: item[1][1])[0]
            del self._data[oldest_key]

    def __len__(self) -> int:
        self._purge_expired()
        return len(self._data)

    def __contains__(self, key: object) -> bool:
        self._purge_expired()
        return key in self._data

    def __repr__(self) -> str:
        self._purge_expired()
        return (
            f"{self.__class__.__name__}(capacity={self.capacity}, ttl={self.ttl}, "
            f"data={list(self._data.items())})"
        )
