"""Shared test fixtures.

The module-level ``app`` in ``app.main`` is a single long-lived instance holding one
in-memory store, so every test that reaches for it inherits whatever links the
previously-run test files happened to leave behind. That makes any assertion about
totals, listings or "most visited" depend on the alphabetical order of test files --
correct code fails, and it fails differently as the suite grows.

That is not a hypothetical: a task adding ``/stats`` was rejected for asserting
``total_links == 2`` after creating exactly two links, because an earlier file had
already put one there.

``reset_shared_store`` removes the trap for good, whichever style a test is written
in. ``client`` is the tidier option and is offered so new tests have an obvious
isolated default to reach for.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app as shared_app
from app.main import create_app


@pytest.fixture(autouse=True)
def reset_shared_store() -> None:
    """Empty the shared application's store before every test."""
    store = getattr(shared_app.state, "store", None)
    if store is not None:
        store.clear()


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A client bound to its own application, isolated from every other test."""
    with TestClient(create_app()) as test_client:
        yield test_client
