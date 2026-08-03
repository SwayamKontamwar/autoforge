"""Storage backends for short links.

The seed ships a process-local in-memory store. A durable SQLite-backed store
is a backlog item, so this module is written to be swapped without touching the
route handlers.
"""

from __future__ import annotations

import secrets
import string
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

_ALPHABET = string.ascii_letters + string.digits


@dataclass
class Link:
    """A stored short link."""

    code: str
    url: str
    created_at: datetime
    hits: int = 0
    expires_at: Optional[datetime] = None


class InMemoryStore:
    """A simple dict-backed store, adequate for the seed and tests."""

    def __init__(self) -> None:
        self._links: dict[str, Link] = {}

    def _new_code(self, length: int = 7) -> str:
        while True:
            code = "".join(secrets.choice(_ALPHABET) for _ in range(length))
            if code not in self._links:
                return code

    def create(
        self,
        url: str,
        alias: str | None = None,
        expires_in_seconds: int | None = None,
    ) -> Link:
        """Create and store a link for ``url`` using ``alias`` if provided.

        Returns the created ``Link`` instance.
        """
        if alias is not None:
            if alias in self._links:
                # In a real system this would be a conflict; for now raise.
                raise ValueError("Alias already exists")
            code = alias
        else:
            code = self._new_code()
        expires_at: Optional[datetime] = None
        if expires_in_seconds is not None:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in_seconds)
        link = Link(
            code=code,
            url=url,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
        )
        self._links[code] = link
        return link

    def get(self, code: str) -> Link | None:
        """Return the link for ``code`` or ``None`` if it does not exist."""
        return self._links.get(code)

    def delete(self, code: str) -> bool:
        """Remove the link identified by ``code``.

        Returns True if the link existed and was removed, False otherwise.
        """
        if code in self._links:
            del self._links[code]
            return True
        return False

    def record_hit(self, code: str) -> None:
        """Increment the hit counter for ``code`` if it exists."""
        link = self._links.get(code)
        if link is not None:
            link.hits += 1

    def list_all(self) -> list[Link]:
        """Return a list of all stored links."""
        return list(self._links.values())

    def clear(self) -> None:
        """Drop every stored link.

        Mutates in place rather than rebinding, because the request handlers close
        over this exact object -- handing back a new one would leave them writing to
        the old store.
        """
        self._links.clear()
