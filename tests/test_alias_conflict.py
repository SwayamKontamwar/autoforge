"""Tests for alias conflict handling on link creation."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app(), follow_redirects=False)


def test_create_link_conflict_returns_409() -> None:
    """Creating a link with an already‑used alias should return 409."""
    payload = {"url": "https://example.com", "alias": "duplicate"}
    first = client.post("/links", json=payload)
    assert first.status_code == 201

    second = client.post("/links", json=payload)
    assert second.status_code == 409
    assert second.json()["detail"] == "Alias already exists"
