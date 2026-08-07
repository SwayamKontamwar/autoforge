"""A self-building standard library — the toolkit autoforge grows over years.

Each backlog item adds one small, well-specified, independently tested utility to
a module here and exports it below. Starting from a single seed (``slugify``),
the collection is designed to expand indefinitely: strings, numbers, dates,
collections, encoding, validation, data structures, algorithms, and more.
"""

from __future__ import annotations

from app.toolkit.strings import slugify, truncate

__all__ = ["slugify", "truncate"]
