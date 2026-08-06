"""Test that OpenAPI schema includes descriptions and examples."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app


def test_openapi_post_links_example() -> None:
    """Ensure POST /links has a description and request body example."""
    client = TestClient(create_app(), follow_redirects=False)
    schema = client.get("/openapi.json").json()
    post = schema["paths"]["/links"]["post"]
    # Description should contain the summary text.
    assert "Create a short link" in post.get("description", "")
    # Example payload should be present.
    example = post["requestBody"]["content"]["application/json"]["example"]
    assert example["url"] == "https://example.com"
    assert example["alias"] == "myalias"
