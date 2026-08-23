"""Utility functions for colour handling."""

from __future__ import annotations


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert a hex colour string to an ``(r, g, b)`` tuple.

    Accepts strings with or without a leading ``#`` and case‑insensitive.
    The string must contain exactly six hexadecimal digits; otherwise a
    :class:`ValueError` is raised.
    """
    if hex_color.startswith("#"):
        hex_color = hex_color[1:]
    if len(hex_color) != 6:
        raise ValueError("hex colour must be 6 hex digits")
    try:
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    except ValueError as exc:
        raise ValueError("invalid hex digit") from exc
    return (r, g, b)


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an ``(r, g, b)`` tuple to a hex colour string.

    Each component must be an integer in the range 0‑255 inclusive.
    Returns a string in the form ``#rrggbb`` using lower‑case hexadecimal
    digits.
    """
    if not isinstance(rgb, tuple) or len(rgb) != 3:
        raise TypeError("rgb must be a tuple of three integers")
    r, g, b = rgb
    for comp in (r, g, b):
        if not isinstance(comp, int):
            raise TypeError("rgb components must be integers")
        if not (0 <= comp <= 255):
            raise ValueError("rgb components must be in the range 0-255")
    return f"#{r:02x}{g:02x}{b:02x}"
