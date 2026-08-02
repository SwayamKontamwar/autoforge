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


def test_link_info_returns_details() -> None:
    api = client()
    payload = {"url": "https://example.com/info"}
    create_resp = api.post("/links", json=payload)
    assert create_resp.status_code == 201
    code = create_resp.json()["code"]
    info_resp = api.get(f"/links/{code}/info")
    assert info_resp.status_code == 200
    info = info_resp.json()
    assert info["code"] == code
    assert info["url"] == payload["url"]
    assert "created_at" in info
    # Ensure the timestamp is parseable ISO format
    from datetime import datetime

    datetime.fromisoformat(info["created_at"])
