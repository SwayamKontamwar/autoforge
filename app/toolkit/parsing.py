"""Semantic version parsing utilities.

The :func:`parse_semver` function parses a version string that follows the
`Semantic Versioning 2.0.0 <https://semver.org/>`_ specification into its
components: major, minor, patch, and optional pre‑release identifier.

The function returns a tuple ``(major, minor, patch, prerelease)`` where the
first three items are integers and ``prerelease`` is either ``None`` or a
string containing the pre‑release label (including any dot‑separated
identifiers).

Invalid version strings raise :class:`ValueError`.

The :func:`compare_semver` function compares two semantic version strings
according to the SemVer precedence rules, returning ``-1`` if the first
argument is lower, ``0`` if they are equal, and ``1`` if the first argument
is higher.
"""

from __future__ import annotations

import re
from typing import List, Optional, Tuple

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
        version: A version string such as ``"1.2.3"`` or ``"1.2.3-alpha.1"``.

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


def _split_prerelease(pr: str) -> List[str]:
    """Split a prerelease string into dot‑separated identifiers."""
    return pr.split(".")


def _compare_identifiers(a: str, b: str) -> int:
    """Compare two prerelease identifiers according to SemVer rules.

    Returns -1 if a < b, 0 if equal, 1 if a > b.
    """
    a_is_num = a.isdigit()
    b_is_num = b.isdigit()
    if a_is_num and b_is_num:
        a_int = int(a)
        b_int = int(b)
        return (a_int > b_int) - (a_int < b_int)
    if a_is_num:
        return -1  # numeric identifiers have lower precedence
    if b_is_num:
        return 1
    # Both are alphanumeric; compare lexically (ASCII order)
    return (a > b) - (a < b)


def _compare_prerelease(p1: Optional[str], p2: Optional[str]) -> int:
    """Compare two prerelease strings.

    Returns -1 if p1 < p2, 0 if equal, 1 if p1 > p2.
    """
    if p1 is None and p2 is None:
        return 0
    if p1 is None:
        return 1  # a version without prerelease is higher
    if p2 is None:
        return -1

    parts1 = _split_prerelease(p1)
    parts2 = _split_prerelease(p2)

    for a, b in zip(parts1, parts2):
        cmp = _compare_identifiers(a, b)
        if cmp != 0:
            return cmp

    # All compared identifiers are equal; longer list wins
    if len(parts1) == len(parts2):
        return 0
    return 1 if len(parts1) > len(parts2) else -1


def compare_semver(v1: str, v2: str) -> int:
    """Compare two semantic version strings.

    Returns:
        -1 if ``v1`` < ``v2``,
         0 if ``v1`` == ``v2``,
         1 if ``v1`` > ``v2``.
    """
    major1, minor1, patch1, pre1 = parse_semver(v1)
    major2, minor2, patch2, pre2 = parse_semver(v2)

    if major1 != major2:
        return 1 if major1 > major2 else -1
    if minor1 != minor2:
        return 1 if minor1 > minor2 else -1
    if patch1 != patch2:
        return 1 if patch1 > patch2 else -1

    return _compare_prerelease(pre1, pre2)
