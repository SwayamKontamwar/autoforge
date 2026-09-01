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


def word_wrap(text: str, width: int) -> str:
    """Wrap *text* to lines of at most *width* characters without breaking words.

    Returns a string containing the wrapped lines separated by newline characters.
    If *width* is less than or equal to zero, an empty string is returned.
    Words longer than *width* are placed on a line by themselves.
    """
    if width <= 0:
        return ""
    words = text.split()
    if not words:
        return ""
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        # If adding the next word would exceed the width, start a new line.
        if len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return "\n".join(lines)


_SMALL_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "but",
    "by",
    "for",
    "in",
    "nor",
    "of",
    "on",
    "or",
    "the",
    "to",
    "up",
    "via",
    "with",
}


def title_case(text: str) -> str:
    """Return *text* in title case.

    The first character of each word is capitalised, except for small words
    (articles, prepositions, etc.) which remain lower‑case unless they are the
    first word in the string.
    """
    if not text:
        return ""
    words = text.split()
    result: list[str] = []
    for i, word in enumerate(words):
        low = word.lower()
        if i == 0 or low not in _SMALL_WORDS:
            result.append(low.capitalize())
        else:
            result.append(low)
    return " ".join(result)
