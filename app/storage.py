"""Storage backends for short links.

The seed ships a process-local in-memory store. A durable SQLite-backed store
is a backlog item, so this module is written to be swapped without touching the
route handlers.
"""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from datetime import datetime

_ALPHABET = string.ascii_letters + string.digits


@dataclass
class Link:
    """A stored short link."""

    code: str
    url: str
    created_at: datetime


class InMemoryStore:
    """A simple dict-backed store, adequate for the seed and tests."""

    def __init__(self) -> None:
        self._links: dict[str, Link] = {}

    def _new_code(self, length: int = 7) -> str:
        while True:
            code = "".join(secrets.choice(_ALPHABET) for _ in range(length))
            if code not in self._links:
                return code

    def create(self, url: str) -> Link:
        """Create and store a link for ``url``, returning it."""
        code = self._new_code()
        link = Link(code=code, url=url, created_at=datetime.utcnow())
        self._links[code] = link
        return link

    def get(self, code: str) -> Link | None:
        """Return the link for ``code`` or ``None`` if it does not exist."""
        return self._links.get(code)
