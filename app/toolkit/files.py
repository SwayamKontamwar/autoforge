"""Utility functions for filesystem path handling.

The primary function, :func:`human_path`, converts absolute paths to a more
human‑readable form by:

* Replacing the current user's home directory with a leading ``~``.
* Shortening overly long paths with an ellipsis (``…``) while preserving the
  start and end of the path.

Typical usage::

    from app.toolkit.files import human_path

    print(human_path("/home/alice/projects/very/long/path/file.txt"))
    # → "~/projects/.../file.txt"
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Union


def human_path(path: Union[str, os.PathLike], max_len: int = 30) -> str:
    """Return a shortened, human‑readable representation of *path*.

    The function performs two transformations:

    1. If *path* starts with the current user's home directory, that prefix is
       replaced with ``~`` (preserving the following separator, if any).
    2. If the resulting string is longer than *max_len*, the middle portion is
       replaced with an ellipsis (U+2026) so that the final length equals
       *max_len*. The start and end of the path are kept as evenly as possible.

    Args:
        path: A string or ``os.PathLike`` object representing a filesystem path.
        max_len: Desired maximum length of the returned string. Must be non‑negative.
                 ``0`` yields an empty string, ``1`` yields only the ellipsis.

    Returns:
        A possibly shortened, human‑readable path string.
    """
    s = os.fspath(path)

    # Replace the home directory with "~"
    home_str = str(Path.home())
    if s.startswith(home_str):
        s = "~" + s[len(home_str) :]

    if max_len <= 0:
        return ""
    if len(s) <= max_len:
        return s
    if max_len == 1:
        return "…"

    # Compute how many characters to keep at the start and end.
    keep_start = (max_len - 1) // 2
    keep_end = max_len - 1 - keep_start
    return s[:keep_start] + "…" + s[-keep_end:]


__all__ = ["human_path"]
