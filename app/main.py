"""FastAPI application factory for the URL-shortener API."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from app.models import LinkCreate, LinkInfoOut, LinkOut, StatsOut
from app.storage import InMemoryStore

# URL‑safe characters per RFC 3986 (unreserved)
_ALIAS_REGEX = re.compile(r"^[A-Za-z0-9\-\._~]{3,32}$")

# Default maximum URL length; can be overridden via environment variable or
# ``create_app`` argument.
_DEFAULT_MAX_URL_LENGTH = int(os.getenv("MAX_URL_LENGTH", "2048"))

# Logger for request logging middleware
_logger = logging.getLogger("app.request")


def _validate_url(url: str, max_length: int) -> None:
    """Validate that ``url`` has http/https scheme, a non‑empty host,
    and does not exceed ``max_length`` characters.

    Raises:
        HTTPException: with status 422 if validation fails.
    """
    if len(url) > max_length:
        raise HTTPException(status_code=422, detail="URL too long")
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


def _order_routes(app: FastAPI) -> None:
    """Let static paths win over parameterised ones, whatever order they were added.

    Starlette matches routes in definition order, so ``/{code}`` silently swallows
    every static top-level path declared after it: a request for ``/stats`` reaches
    the redirect handler, which looks up a short code named "stats", finds none and
    returns 404. Nothing raises, so the endpoint simply appears not to exist.

    The sort is stable and keyed only on whether a route has path parameters at all,
    so routes that cannot collide keep the order they were written in and only the
    genuinely ambiguous pairs move. An exact static path is unambiguously more
    specific than a parameterised one; most routers apply this precedence for you,
    and Starlette leaves it to the application.
    """
    app.router.routes.sort(key=lambda route: bool(getattr(route, "param_convertors", None)))


def create_app(max_url_length: int = _DEFAULT_MAX_URL_LENGTH) -> FastAPI:
    """Build and return the FastAPI application.

    Args:
        max_url_length: Maximum allowed length for target URLs. Defaults to
            the value of ``MAX_URL_LENGTH`` environment variable or 2048.

    A fresh store is bound per application instance so tests are isolated.
    """
    app = FastAPI(title="autoforge URL shortener", version="0.1.0")
    store = InMemoryStore()
    # Published so tests can reset between cases. The handlers close over `store`,
    # so this must stay the same object, never a copy.
    app.state.store = store
    # Record the time the application started for uptime reporting.
    app.state.start_time = datetime.now(timezone.utc)
    # Store the configured maximum URL length for validation.
    app.state.max_url_length = max_url_length

    @app.middleware("http")
    async def _log_requests(request: Request, call_next):
        """Log HTTP method, path, and response status code."""
        response = await call_next(request)
        _logger.info("%s %s %s", request.method, request.url.path, response.status_code)
        return response

    @app.get(
        "/healthz",
        summary="Health check",
        description="Liveness probe.",
    )
    def healthz() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok"}

    @app.get(
        "/healthz/details",
        summary="Readiness probe",
        description="Readiness probe with uptime and link count.",
    )
    def healthz_details() -> dict[str, int]:
        """Readiness probe with uptime and link count."""
        now = datetime.now(timezone.utc)
        uptime_seconds = int((now - app.state.start_time).total_seconds())
        total_links = len(app.state.store.list_all())
        return {"uptime_seconds": uptime_seconds, "total_links": total_links}

    @app.post(
        "/links",
        response_model=LinkOut,
        status_code=201,
        summary="Create a short link",
        description="Create a short link for the supplied URL.",
    )
    def create_link(
        payload: LinkCreate = Body(
            ...,
            example={"url": "https://example.com", "alias": "myalias"},
        ),
    ) -> LinkOut:
        """Create a short link for the supplied URL."""
        _validate_url(payload.url, app.state.max_url_length)
        if payload.alias is not None:
            _validate_alias(payload.alias)
        try:
            link = store.create(payload.url, payload.alias, payload.expires_in_seconds)
        except ValueError as exc:
            # Alias already exists – treat as a conflict.
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        # Ensure the URL is a plain string for Pydantic validation.
        return LinkOut(code=link.code, url=str(link.url))

    @app.get(
        "/links",
        response_model=list[LinkInfoOut],
        summary="List stored links",
        description="Return a paginated list of stored links with their details.",
    )
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

    @app.get(
        "/{code}",
        summary="Redirect short code",
        description="Redirect a short code to its destination URL.",
    )
    def redirect(code: str) -> RedirectResponse:
        """Redirect a short code to its destination URL."""
        link = store.get(code)
        if link is None:
            raise HTTPException(status_code=404, detail="Unknown short code")
        # Expiry handling
        if link.expires_at is not None and datetime.now(timezone.utc) > link.expires_at:
            raise HTTPException(status_code=410, detail="Link expired")
        store.record_hit(code)
        return RedirectResponse(url=link.url, status_code=307)

    @app.get(
        "/links/{code}/info",
        response_model=LinkInfoOut,
        summary="Link information",
        description="Return detailed information about a short link without redirect.",
    )
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

    @app.delete(
        "/links/{code}",
        status_code=204,
        summary="Delete a short link",
        description="Delete a short link identified by ``code``.",
    )
    def delete_link(code: str) -> None:
        """Delete a short link identified by ``code``."""
        if not store.delete(code):
            raise HTTPException(status_code=404, detail="Unknown short code")
        # FastAPI will return a 204 No Content response automatically.

    @app.get(
        "/stats",
        response_model=StatsOut,
        summary="Aggregate statistics",
        description="Return aggregate statistics about stored links.",
    )
    def get_stats() -> StatsOut:
        """Return aggregate statistics about stored links."""
        links = store.list_all()
        total_links = len(links)
        total_redirects = sum(link.hits for link in links)
        most_visited: str | None = None
        if links:
            most_visited = max(links, key=lambda item: item.hits).code
        return StatsOut(
            total_links=total_links,
            total_redirects=total_redirects,
            most_visited=most_visited,
        )

    _order_routes(app)
    return app


app = create_app()
