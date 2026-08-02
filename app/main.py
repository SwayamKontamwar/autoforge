"""FastAPI application factory for the URL-shortener API."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from app.models import LinkCreate, LinkOut
from app.storage import InMemoryStore


def create_app() -> FastAPI:
    """Build and return the FastAPI application.

    A fresh store is bound per application instance so tests are isolated.
    """
    app = FastAPI(title="autoforge URL shortener", version="0.1.0")
    store = InMemoryStore()

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok"}

    @app.post("/links", response_model=LinkOut, status_code=201)
    def create_link(payload: LinkCreate) -> LinkOut:
        """Create a short link for the supplied URL."""
        link = store.create(payload.url)
        return LinkOut(code=link.code, url=link.url)

    @app.get("/{code}")
    def redirect(code: str) -> RedirectResponse:
        """Redirect a short code to its destination URL."""
        link = store.get(code)
        if link is None:
            raise HTTPException(status_code=404, detail="Unknown short code")
        return RedirectResponse(url=link.url, status_code=307)

    return app


app = create_app()
