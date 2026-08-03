"""Test that the in‑memory store conforms to the Storage protocol."""

from app.storage import InMemoryStore, Storage


def test_inmemory_store_implements_storage() -> None:
    store = InMemoryStore()
    assert isinstance(store, Storage)
