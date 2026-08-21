import pytest

from app.toolkit.structures import LFUCache, LRUCache


def test_lru_cache_basic_eviction() -> None:
    cache = LRUCache[int, int](2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1  # 'a' becomes most‑recent
    cache.put("c", 3)  # should evict 'b'
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_lru_cache_update_moves_to_recent() -> None:
    cache = LRUCache[int, int](2)
    cache.put("x", 10)
    cache.put("y", 20)
    cache.put("x", 15)  # update 'x', now most‑recent
    cache.put("z", 30)  # evicts 'y'
    assert cache.get("y") is None
    assert cache.get("x") == 15
    assert cache.get("z") == 30


def test_lru_cache_capacity_one() -> None:
    cache = LRUCache[int, int](1)
    cache.put("a", 1)
    assert cache.get("a") == 1
    cache.put("b", 2)  # evicts 'a'
    assert cache.get("a") is None
    assert cache.get("b") == 2


def test_lru_cache_invalid_capacity() -> None:
    with pytest.raises(ValueError):
        LRUCache(0)


def test_lfu_cache_basic_eviction() -> None:
    cache = LFUCache[int, int](2)
    cache.put("a", 1)  # freq=1
    cache.put("b", 2)  # freq=1
    # Access 'a' twice, increasing its frequency
    assert cache.get("a") == 1
    assert cache.get("a") == 1
    # 'b' has freq=1, 'a' has freq=3 now
    cache.put("c", 3)  # should evict 'b' (lowest freq)
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3


def test_lfu_cache_tie_breaker_lru() -> None:
    cache = LFUCache[int, int](2)
    cache.put("x", 10)  # freq=1, ts=1
    cache.put("y", 20)  # freq=1, ts=2
    # No accesses, frequencies equal; inserting new key should evict the older ('x')
    cache.put("z", 30)
    assert cache.get("x") is None
    assert cache.get("y") == 20
    assert cache.get("z") == 30


def test_lfu_cache_invalid_capacity() -> None:
    with pytest.raises(ValueError):
        LFUCache(0)
