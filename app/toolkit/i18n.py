"""Internationalization utilities.

Currently provides a simple English plural rule function. The function follows
the CLDR plural rules for English: it returns ``\"one\"`` when the count is
exactly ``1`` and ``\"other\"`` for all other integer counts.

The function validates its input type and raises :class:`TypeError` for any
non‑integer value.
"""

from __future__ import annotations


def plural_rule_en(count: int) -> str:
    """Return the English plural rule for *count*.

    Args:
        count: An integer count.

    Returns:
        ``\"one\"`` if *count* is exactly ``1``, otherwise ``\"other\"``.

    Raises:
        TypeError: If *count* is not an ``int``.
    """
    if not isinstance(count, int):
        raise TypeError("count must be an integer")
    return "one" if count == 1 else "other"
