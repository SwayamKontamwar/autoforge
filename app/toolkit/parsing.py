"""Semantic version parsing utilities.

The :func:`parse_semver` function parses a version string that follows the
`Semantic Versioning 2.0.0 <https://semver.org/>`_ specification into its
components: major, minor, patch, and optional pre‑release identifier.

The function returns a tuple ``(major, minor, patch, prerelease)`` where the
first three items are integers and ``prerelease`` is either ``None`` or a
string containing the pre‑release label (including any dot‑separated
identifiers).

Invalid version strings raise :class:`ValueError`.
"""

from __future__ import annotations

import re
from typing import Optional, Tuple

# Regular expression for a strict semver (no build metadata handling needed)
_SEMVER_RE = re.compile(
    r"""
    ^
    (?P<major>0|[1-9]\d*)               # major version
    \.
    (?P<minor>0|[1-9]\d*)               # minor version
    \.
    (?P<patch>0|[1-9]\d*)               # patch version
    (?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?  # optional pre‑release
    $
    """,
    re.VERBOSE,
)


def parse_semver(version: str) -> Tuple[int, int, int, Optional[str]]:
    """Parse a semantic version string.

    Args:
        version: A version string such as ``\"1.2.3\"`` or ``\"1.2.3-alpha.1\"``.

    Returns:
        A tuple ``(major, minor, patch, prerelease)`` where ``prerelease`` is
        ``None`` if the version does not contain a pre‑release segment.

    Raises:
        ValueError: If *version* does not conform to the semver pattern.
    """
    match = _SEMVER_RE.fullmatch(version.strip())
    if not match:
        raise ValueError(f"Invalid semantic version: {version!r}")

    major = int(match.group("major"))
    minor = int(match.group("minor"))
    patch = int(match.group("patch"))
    prerelease = match.group("prerelease")
    return major, minor, patch, prerelease
