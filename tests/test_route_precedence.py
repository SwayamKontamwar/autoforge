"""A static path must never be swallowed by the ``/{code}`` catch-all.

This is the trap that quietly killed the ``/stats`` task. Starlette matches routes
in definition order, so any static top-level path declared after ``/{code}`` is
routed to the redirect handler instead, which reports 404 for a short code that was
never a short code. Nothing errors; the endpoint just seems not to exist.

Every future task that adds a top-level endpoint walks into this, so the invariant
is pinned here: the guardrail runs these tests on every patch, which means the
ordering fix cannot be dropped without the run being rejected.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import _order_routes, create_app


def test_a_static_route_declared_after_the_catch_all_still_resolves():
    app = create_app()

    # Exactly what a backlog task does: append a new endpoint at the end, long
    # after `/{code}` was registered.
    @app.get("/stats-probe")
    def probe() -> dict[str, bool]:
        return {"reached": True}

    _order_routes(app)

    response = TestClient(app).get("/stats-probe")
    assert response.status_code == 200
    assert response.json() == {"reached": True}


def test_the_catch_all_still_serves_real_short_codes():
    client = TestClient(create_app())
    created = client.post("/links", json={"url": "http://example.com"})
    code = created.json()["code"]

    response = client.get(f"/{code}", follow_redirects=False)
    assert response.status_code in {301, 302, 307, 308}
    assert response.headers["location"] == "http://example.com"


def test_an_unknown_short_code_is_still_a_404():
    response = TestClient(create_app()).get("/definitely-not-a-code")
    assert response.status_code == 404


def test_ordering_is_stable_for_routes_that_cannot_collide():
    app = FastAPI()

    @app.get("/a")
    def first() -> None: ...

    @app.get("/b")
    def second() -> None: ...

    @app.get("/c")
    def third() -> None: ...

    before = [route.path for route in app.router.routes]
    _order_routes(app)
    assert [route.path for route in app.router.routes] == before
