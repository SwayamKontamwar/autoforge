"""FastAPI application factory for the URL-shortener API."""

from __future__ import annotations

from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from app.models import LinkCreate, LinkInfoOut, LinkOut
from app.storage import InMemoryStore


def _validate_url(url: str) -> None:
    """Validate that ``url`` has http/https scheme and a non‑empty host.

    Raises:
        HTTPException: with status 422 if validation fails.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=422, detail="Invalid URL")


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
        _validate_url(payload.url)
        link = store.create(payload.url)
        # Ensure the URL is a plain string for Pydantic validation.
        return LinkOut(code=link.code, url=str(link.url))

    @app.get("/{code}")
    def redirect(code: str) -> RedirectResponse:
        """Redirect a short code to its destination URL."""
        link = store.get(code)
        if link is None:
            raise HTTPException(status_code=404, detail="Unknown short code")
        return RedirectResponse(url=link.url, status_code=307)

    @app.get("/links/{code}/info", response_model=LinkInfoOut)
    def link_info(code: str) -> LinkInfoOut:
        """Return detailed information about a short link without redirect."""
        link = store.get(code)
        if link is None:
            raise HTTPException(status_code=404, detail="Unknown short code")
        return LinkInfoOut(code=link.code, url=link.url, created_at=link.created_at)

    return app


app = create_app()
