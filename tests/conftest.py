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

The reset is deliberately defensive. ``app/storage.py`` is rewritten wholesale by
the builder like any other application file, and a rewrite that happens not to
carry ``clear`` forward used to turn one missing method into 325 collection
errors -- every test in the suite, including every test of the builder, failing
with the same unrelated AttributeError. The patch was correctly rejected, but the
report said nothing useful about what was actually wrong. Emptying the store
generically keeps a rewrite to the failures it really caused, and
``test_isolation.py`` states the requirement once, in one readable line.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.main import app as shared_app
from app.main import create_app


def empty_store(store: object) -> None:
    """Empty a store in place, without depending on how it is implemented.

    In place matters: the route handlers close over the exact object built at
    import time, so replacing it leaves them writing to the old one.
    """
    clear = getattr(store, "clear", None)
    if callable(clear):
        clear()
        return
    for value in vars(store).values():
        if isinstance(value, (dict, list, set)):
            value.clear()


@pytest.fixture(autouse=True)
def reset_shared_store() -> None:
    """Empty the shared application's store before every test."""
    store = getattr(shared_app.state, "store", None)
    if store is not None:
        empty_store(store)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A client bound to its own application, isolated from every other test."""
    with TestClient(create_app()) as test_client:
        yield test_client
