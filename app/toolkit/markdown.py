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
