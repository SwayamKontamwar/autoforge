import pytest

from app.toolkit.structures import LRUCache


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
