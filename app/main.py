"""FastAPI application factory for the URL-shortener API."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse

from app.models import LinkCreate, LinkInfoOut, LinkOut
from app.storage import InMemoryStore

# URL‑safe characters per RFC 3986 (unreserved)
_ALIAS_REGEX = re.compile(r"^[A-Za-z0-9\-\._~]{3,32}$")


def _validate_url(url: str) -> None:
    """Validate that ``url`` has http/https scheme and a non‑empty host.

    Raises:
        HTTPException: with status 422 if validation fails.
    """
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise HTTPException(status_code=422, detail="Invalid URL")


def _validate_alias(alias: str) -> None:
    """Validate that ``alias`` contains only URL‑safe characters and length 3‑32.

    Raises:
        HTTPException: with status 422 if validation fails.
    """
    if not _ALIAS_REGEX.fullmatch(alias):
        raise HTTPException(status_code=422, detail="Invalid alias")


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
        if payload.alias is not None:
            _validate_alias(payload.alias)
        link = store.create(payload.url, payload.alias)
        # Ensure the URL is a plain string for Pydantic validation.
        return LinkOut(code=link.code, url=str(link.url))

    @app.get("/links", response_model=list[LinkInfoOut])
    def list_links(
        limit: int = Query(100, ge=1, le=1000),
        offset: int = Query(0, ge=0),
    ) -> list[LinkInfoOut]:
        """Return a paginated list of stored links with their details.

        Args:
            limit: Maximum number of items to return (default 100, max 1000).
            offset: Number of items to skip before starting to collect the result set.

        Returns:
            A list of ``LinkInfoOut`` objects respecting the pagination parameters.
        """
        all_links = store.list_all()
        sliced = all_links[offset : offset + limit]
        return [
            LinkInfoOut(
                code=link.code,
                url=link.url,
                created_at=link.created_at,
                hits=link.hits,
            )
            for link in sliced
        ]

    @app.get("/{code}")
    def redirect(code: str) -> RedirectResponse:
        """Redirect a short code to its destination URL."""
        link = store.get(code)
        if link is None:
            raise HTTPException(status_code=404, detail="Unknown short code")
        store.record_hit(code)
        return RedirectResponse(url=link.url, status_code=307)

    @app.get("/links/{code}/info", response_model=LinkInfoOut)
    def link_info(code: str) -> LinkInfoOut:
        """Return detailed information about a short link without redirect."""
        link = store.get(code)
        if link is None:
            raise HTTPException(status_code=404, detail="Unknown short code")
        return LinkInfoOut(
            code=link.code,
            url=link.url,
            created_at=link.created_at,
            hits=link.hits,
        )

    @app.delete("/links/{code}", status_code=204)
    def delete_link(code: str) -> None:
        """Delete a short link identified by ``code``."""
        if not store.delete(code):
            raise HTTPException(status_code=404, detail="Unknown short code")
        # FastAPI will return a 204 No Content response automatically.

    return app


app = create_app()
