"""String utilities."""

from __future__ import annotations

import re
import unicodedata

_NON_SLUG = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    """Return a lowercase, hyphen-separated ASCII slug of ``text``.

    Accents are stripped, runs of non-alphanumeric characters collapse to a
    single hyphen, and leading/trailing hyphens are removed.
    """
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return _NON_SLUG.sub("-", ascii_text.lower().strip()).strip("-")
