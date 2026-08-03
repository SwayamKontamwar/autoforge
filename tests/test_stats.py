from fastapi.testclient import TestClient

from app.main import app


def test_stats_endpoint_counts_and_most_visited() -> None:
    client = TestClient(app)

    # Create two distinct links.
    resp_a = client.post("/links", json={"url": "http://example.com"})
    assert resp_a.status_code == 201
    code_a = resp_a.json()["code"]

    resp_b = client.post("/links", json={"url": "http://example.org"})
    assert resp_b.status_code == 201
    code_b = resp_b.json()["code"]

    # Hit the first link twice and the second once.
    client.get(f"/{code_a}")
    client.get(f"/{code_a}")
    client.get(f"/{code_b}")

    # Retrieve statistics.
    stats_resp = client.get("/stats")
    assert stats_resp.status_code == 200
    data = stats_resp.json()
    assert data["total_links"] == 2
    assert data["total_redirects"] == 3
    # The most‑visited code should be the one with two hits.
    assert data["most_visited"] == code_a
