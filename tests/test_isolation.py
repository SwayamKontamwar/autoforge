"""Tests must not inherit each other's data.

Two tests below deliberately use the shared ``app.main.app`` singleton, the same way
a generated test naturally would. The first fills it; the second asserts it starts
empty. Without the autouse reset in ``conftest.py`` the second fails, because pytest
runs them in file order and the store outlives both.

This is what rejected a correct ``/stats`` implementation: it created two links and
asserted a total of two, and got three.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app as shared_app
from tests.conftest import empty_store


def test_first_case_fills_the_shared_store():
    client = TestClient(shared_app)
    client.post("/links", json={"url": "http://first.example"})
    client.post("/links", json={"url": "http://second.example"})
    assert len(client.get("/links").json()) == 2


def test_second_case_does_not_inherit_them():
    client = TestClient(shared_app)
    assert client.get("/links").json() == []

    client.post("/links", json={"url": "http://mine.example"})
    assert len(client.get("/links").json()) == 1


def test_the_client_fixture_is_isolated_too(client):
    assert client.get("/links").json() == []
    client.post("/links", json={"url": "http://fixture.example"})
    assert len(client.get("/links").json()) == 1


def test_the_shared_store_can_be_emptied_in_place():
    """The property the autouse reset depends on, stated once.

    Deliberately about emptying rather than about ``clear`` existing: the builder
    rewrites ``app/storage.py`` wholesale, so pinning a method name would fail a
    rename that kept the behaviour, and every such failure costs an attempt.
    """
    store = shared_app.state.store
    TestClient(shared_app).post("/links", json={"url": "http://x.example"})
    assert store.list_all()

    empty_store(store)

    # Same object, not a replacement: the route handlers closed over this one.
    assert store is shared_app.state.store
    assert store.list_all() == []


def test_a_store_without_clear_is_still_emptied():
    """A rewrite that drops ``clear`` must cost one failure, not the whole suite.

    When the reset raised, a single missing method became 325 collection errors:
    every test in the project, including the builder's own, reporting the same
    unrelated AttributeError and saying nothing about the actual mistake.
    """

    class BareStore:
        def __init__(self) -> None:
            self._links = {"a": 1}
            self._hits = ["x"]

    bare = BareStore()
    empty_store(bare)
    assert bare._links == {}
    assert bare._hits == []
