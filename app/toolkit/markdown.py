"""Markdown helper utilities.

This module provides small functions for generating markdown snippets.
"""

from __future__ import annotations


def md_bold(text: str) -> str:
    """Return **text**."""
    return f"**{text}**"


def md_italic(text: str) -> str:
    """Return *text*."""
    return f"*{text}*"


def md_link(text: str, url: str) -> str:
    """Return a markdown link."""
    return f"[{text}]({url})"


def md_image(alt: str, url: str) -> str:
    """Return a markdown image."""
    return f"![{alt}]({url})"


def md_code(text: str) -> str:
    """Return an inline code snippet, handling backticks.

    If the text contains backticks, they are stripped and the snippet is
    wrapped in double backticks to avoid delimiter collision.
    """
    if "`" in text:
        cleaned = text.replace("`", "")
        return f"``{cleaned}``"
    return f"`{text}`"


def md_code_block(text: str, language: str = "") -> str:
    """Return a fenced code block with an optional language specifier.

    The block is formatted as:

        ```<language>
    <text>
    ```

    If ``language`` is empty or only whitespace, the opening fence is just
    three backticks. ``text`` may be empty; the function will still produce
    a valid fenced block.
    """
    lang = language.strip()
    opening = f"```{lang}" if lang else "```"
    return f"{opening}\n{text}\n```"
