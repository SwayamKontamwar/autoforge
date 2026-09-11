"""Markdown helper utilities.

This module provides small functions for generating markdown snippets.
"""

from __future__ import annotations


def md_bold(text: str) -> str:
    """Return *text* wrapped in markdown bold markers.

    Args:
        text: The string to be bolded.

    Returns:
        The input string surrounded by double asterisks, e.g. ``**text**``.
    """
    return f"**{text}**"


def md_italic(text: str) -> str:
    """Return *text* wrapped in markdown italic markers.

    Args:
        text: The string to be italicized.

    Returns:
        The input string surrounded by single asterisks, e.g. ``*text*``.
    """
    return f"*{text}*"


def md_link(text: str, url: str) -> str:
    """Return a markdown link constructed from *text* and *url*.

    The function simply formats the two arguments into the standard markdown
    link syntax ``[text](url)``. No validation or escaping is performed; the
    caller is responsible for providing appropriate values.

    Args:
        text: The link text that will appear between the brackets.
        url: The target URL that will appear inside the parentheses.

    Returns:
        A string representing a markdown link, e.g. ``[example](https://example.com)``.
    """
    return f"[{text}]({url})"
