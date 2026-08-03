import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_healthz_details_initial_and_after_creation(client: TestClient) -> None:
    # Initial call should report zero stored links.
    resp = client.get("/healthz/details")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["uptime_seconds"], int)
    assert data["total_links"] == 0

    # Create a new short link.
    payload = {"url": "https://example.com"}
    create_resp = client.post("/links", json=payload)
    assert create_resp.status_code == 201

    # After creation, total_links should be 1.
    resp2 = client.get("/healthz/details")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total_links"] == 1
    # Uptime should be non‑negative.
    assert isinstance(data2["uptime_seconds"], int)
    assert data2["uptime_seconds"] >= 0
