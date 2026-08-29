"""Internationalization utilities.

Currently provides a simple English plural rule function. The function follows
the CLDR plural rules for English: it returns ``"one"`` when the count is
exactly ``1`` and ``"other"`` for all other integer counts.

The function validates its input type and raises :class:`TypeError` for any
non‑integer value.
"""

from __future__ import annotations

from typing import Any, Sequence


def plural_rule_en(count: int) -> str:
    """Return the English plural rule for *count*.

    Args:
        count: An integer count.

    Returns:
        ``"one"`` if *count* is exactly ``1``, otherwise ``"other"``.

    Raises:
        TypeError: If *count* is not an ``int``.
    """
    if not isinstance(count, int):
        raise TypeError("count must be an integer")
    return "one" if count == 1 else "other"


def format_list(items: Sequence[Any]) -> str:
    """Return a human‑readable English list joined with commas and ``and``.

    The function follows typical English list formatting:
    * Zero items → ``""`` (empty string).
    * One item  → the item itself.
    * Two items → ``"a and b"``.
    * Three or more → ``"a, b, and c"`` (Oxford comma).

    Args:
        items: An iterable of items to join.

    Returns:
        A formatted string representation of the list.
    """
    # Convert to list to allow multiple passes and length checks.
    items_list = list(items)
    if not items_list:
        return ""
    # Convert each element to its string representation.
    strs = [str(item) for item in items_list]
    if len(strs) == 1:
        return strs[0]
    if len(strs) == 2:
        return f"{strs[0]} and {strs[1]}"
    # For three or more items, join all but the last with commas,
    # then add an Oxford comma before the final ``and``.
    *head, last = strs
    return f"{', '.join(head)}, and {last}"
