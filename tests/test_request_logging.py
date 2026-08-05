"""Test that the request logging middleware records method, path, and status."""

from __future__ import annotations

import logging

from fastapi.testclient import TestClient

from app.main import create_app


def test_request_logging_middleware_logs_method_path_status(caplog):
    """Ensure a GET request logs the expected line."""
    app = create_app()
    client = TestClient(app)

    # Capture logs from the middleware logger.
    caplog.set_level(logging.INFO, logger="app.request")
    response = client.get("/healthz")
    assert response.status_code == 200

    # Find a log entry from our logger.
    messages = [rec.message for rec in caplog.records if rec.name == "app.request"]
    assert any("GET /healthz 200" in msg for msg in messages)
