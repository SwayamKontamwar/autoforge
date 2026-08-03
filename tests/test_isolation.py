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


def test_clear_empties_the_store_in_place():
    store = shared_app.state.store
    TestClient(shared_app).post("/links", json={"url": "http://x.example"})
    assert store.list_all()

    store.clear()

    # Same object, not a replacement: the route handlers closed over this one.
    assert store is shared_app.state.store
    assert store.list_all() == []
