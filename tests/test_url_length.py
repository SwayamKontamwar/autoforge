"""Tests for maximum URL length validation on link creation."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_create_link_rejects_overly_long_url() -> None:
    """A URL longer than the configured maximum should be rejected with 422."""
    # Set a very small max length to trigger the validation easily.
    app = create_app(max_url_length=10)
    client = TestClient(app, follow_redirects=False)
    # This URL is longer than 10 characters.
    response = client.post("/links", json={"url": "http://ex.com/long"})
    assert response.status_code == 422
    assert response.json()["detail"] == "URL too long"
