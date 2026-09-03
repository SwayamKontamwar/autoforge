import time

from app.toolkit.structures import TTLCache


def test_ttlcache_basic_expiration() -> None:
    cache = TTLCache[int, str](capacity=2, ttl=0.1)
    cache.put(1, "one")
    cache.put(2, "two")
    # Both entries should be present immediately
    assert cache.get(1) == "one"
    assert cache.get(2) == "two"
    # Wait for them to expire
    time.sleep(0.15)
    assert cache.get(1) is None
    assert cache.get(2) is None
    # After expiration we can add new items without eviction errors
    cache.put(3, "three")
    cache.put(4, "four")
    assert len(cache) == 2
    assert 3 in cache
    assert 4 in cache
