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


def test_delete_link_removes_and_returns_204() -> None:
    api = client()
    payload = {"url": "https://example.com/delete"}
    create_resp = api.post("/links", json=payload)
    assert create_resp.status_code == 201
    code = create_resp.json()["code"]

    delete_resp = api.delete(f"/links/{code}")
    assert delete_resp.status_code == 204

    # Subsequent redirect should be 404
    get_resp = api.get(f"/{code}")
    assert get_resp.status_code == 404

    # Info endpoint should also be 404
    info_resp = api.get(f"/links/{code}/info")
    assert info_resp.status_code == 404


def test_redirect_hits_are_counted_in_info() -> None:
    api = client()
    payload = {"url": "https://example.com/hits"}
    create_resp = api.post("/links", json=payload)
    assert create_resp.status_code == 201
    code = create_resp.json()["code"]

    # Initial info should show 0 hits
    info0 = api.get(f"/links/{code}/info").json()
    assert info0["hits"] == 0

    # Perform three redirects
    for _ in range(3):
        api.get(f"/{code}")

    # Info should now reflect three hits
    info1 = api.get(f"/links/{code}/info").json()
    assert info1["hits"] == 3


def test_get_links_returns_all_links() -> None:
    api = client()
    payload1 = {"url": "https://example.com/one"}
    payload2 = {"url": "https://example.com/two"}
    resp1 = api.post("/links", json=payload1)
    resp2 = api.post("/links", json=payload2)
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    code1 = resp1.json()["code"]
    code2 = resp2.json()["code"]

    list_resp = api.get("/links")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert isinstance(data, list)
    codes = {item["code"] for item in data}
    assert {code1, code2} == codes
    for item in data:
        assert "url" in item
        assert "hits" in item
        assert item["hits"] == 0
        assert "created_at" in item
