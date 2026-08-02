"""Tests for URL validation on link creation."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def client() -> TestClient:
    return TestClient(create_app(), follow_redirects=False)


def test_create_link_rejects_invalid_scheme() -> None:
    response = client().post("/links", json={"url": "ftp://example.com/resource"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid URL"


def test_create_link_rejects_missing_host() -> None:
    response = client().post("/links", json={"url": "http:///nohost"})
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid URL"
