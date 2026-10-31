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

    Args:
        text: The link text.
        url: The URL the link points to.

    Returns:
        A markdown link, e.g. ``[text](url)``.
    """
    return f"[{text}]({url})"


def md_image(alt: str, url: str) -> str:
    """Return a markdown image snippet.

    Args:
        alt: Alt text for the image.
        url: Image URL.

    Returns:
        A markdown image tag, e.g. ``![alt](url)``.
    """
    return f"![{alt}]({url})"


def md_code(text: str) -> str:
    """Return *text* wrapped in markdown inline code markers.

    Args:
        text: The code snippet to be wrapped.

    Returns:
        The input string surrounded by backticks, e.g. ```text` ``.
    """
    return f"`{text}`"
