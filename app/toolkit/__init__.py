"""A self-building standard library — the toolkit autoforge grows over years.

Each backlog item adds one small, well‑specified, independently tested utility to
a module here and exports it below. Starting from a single seed (``slugify``),
the collection is designed to expand indefinitely: strings, numbers, dates,
collections, encoding, validation, data structures, algorithms, and more.
"""

from __future__ import annotations

from app.toolkit.algorithms import binary_search
from app.toolkit.collections import chunk
from app.toolkit.datetimes import parse_iso
from app.toolkit.encoding import base62_encode
from app.toolkit.functional import compose
from app.toolkit.hashing import md5_hex
from app.toolkit.numbers import clamp
from app.toolkit.parsing import parse_semver
from app.toolkit.strings import slugify, truncate
from app.toolkit.structures import LRUCache
from app.toolkit.validation import is_email

__all__ = [
    "slugify",
    "truncate",
    "clamp",
    "parse_iso",
    "chunk",
    "compose",
    "base62_encode",
    "md5_hex",
    "is_email",
    "parse_semver",
    "LRUCache",
    "binary_search",
]
