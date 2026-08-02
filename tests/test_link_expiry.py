import time

from fastapi.testclient import TestClient

from app.main import app


def test_link_expires_and_returns_410():
    client = TestClient(app)

    # Create a link that expires in 1 second
    response = client.post(
        "/links",
        json={"url": "https://example.com", "expires_in_seconds": 1},
    )
    assert response.status_code == 201
    data = response.json()
    code = data["code"]

    # Immediate redirect should succeed (307)
    redirect_resp = client.get(f"/{code}", follow_redirects=False)
    assert redirect_resp.status_code == 307

    # Wait for expiry
    time.sleep(2)

    # Redirect after expiry should return 410 Gone
    expired_resp = client.get(f"/{code}", follow_redirects=False)
    assert expired_resp.status_code == 410
