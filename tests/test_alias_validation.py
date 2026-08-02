"""Tests for custom alias validation on link creation."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

client = TestClient(create_app(), follow_redirects=False)


@pytest.mark.parametrize(
    "alias",
    [
        "my-alias",
        "my_alias",
        "my.alias",
        "my~alias",
        "ABC123",
        "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5",  # 32 chars
    ],
)
def test_create_link_accepts_valid_alias(alias: str) -> None:
    response = client.post("/links", json={"url": "https://example.com", "alias": alias})
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == alias
    assert data["url"] == "https://example.com"


@pytest.mark.parametrize(
    "alias",
    [
        "ab",  # too short
        "a" * 33,  # too long
        "invalid alias!",  # space and exclamation
        "slash/alias",  # slash not allowed
        "question?mark",  # question mark not allowed
        "percent%sign",  # percent not allowed
    ],
)
def test_create_link_rejects_invalid_alias(alias: str) -> None:
    response = client.post("/links", json={"url": "https://example.com", "alias": alias})
    assert response.status_code == 422
    assert response.json()["detail"] == "Invalid alias"
