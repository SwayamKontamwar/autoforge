from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.main import app


def test_created_at_is_utc_isoformat() -> None:
    client = TestClient(app)
    # Create a new link
    resp = client.post(
        "/links",
        json={"url": "http://example.com"},
    )
    assert resp.status_code == 201
    # List links and inspect the created_at field
    list_resp = client.get("/links")
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert isinstance(data, list) and len(data) > 0
    created_at = data[0]["created_at"]
    # Should be a string in ISO‑8601 with UTC offset
    assert isinstance(created_at, str)
    parsed = datetime.fromisoformat(created_at)
    assert parsed.tzinfo is not None
    # Ensure it is UTC (offset zero)
    assert parsed.tzinfo == timezone.utc
