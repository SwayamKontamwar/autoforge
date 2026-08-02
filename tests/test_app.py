"""Tests for the seed URL-shortener API.

Every backlog item the bot completes must add or extend tests here (or in a
sibling ``tests/`` module) proving the new behaviour.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def client() -> TestClient:
    return TestClient(create_app(), follow_redirects=False)


def test_healthz_ok() -> None:
    response = client().get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_link_returns_code_and_url() -> None:
    response = client().post("/links", json={"url": "https://example.com/page"})
    assert response.status_code == 201
    body = response.json()
    assert body["url"] == "https://example.com/page"
    assert isinstance(body["code"], str) and body["code"]


def test_redirect_sends_to_destination() -> None:
    api = client()
    code = api.post("/links", json={"url": "https://example.com/dest"}).json()["code"]
    response = api.get(f"/{code}")
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/dest"


def test_unknown_code_is_404() -> None:
    response = client().get("/does-not-exist")
    assert response.status_code == 404
