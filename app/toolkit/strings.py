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


def truncate(text: str, max_length: int) -> str:
    """Return ``text`` shortened to at most ``max_length`` characters.

    If ``text`` exceeds ``max_length``, it is cut and an ellipsis (U+2026) is
    appended. The ellipsis is only added when truncation occurs and counts as
    a single character towards the limit.
    """
    if max_length <= 0:
        return ""
    if len(text) <= max_length:
        return text
    # Reserve space for the ellipsis.
    cut_len = max_length - 1
    if cut_len < 0:
        cut_len = 0
    return text[:cut_len] + "…"
