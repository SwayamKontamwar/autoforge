"""Utility functions for regular‑expression based text processing."""

from __future__ import annotations

import re
from typing import List


def extract_emails(text: str) -> List[str]:
    """Return a list of all email addresses found in *text*.

    The regular expression is deliberately permissive yet avoids trailing
    punctuation. It matches typical email forms such as ``user@example.com`` or
    ``user.name+tag@sub.domain.co.uk``.
    """
    # Pattern:
    #   local part: alphanumerics and ._%+- characters
    #   @ symbol
    #   domain: alphanumerics, hyphens and dots, ending with a TLD of at least two letters.
    #   Allows multiple dot‑separated TLD components (e.g. .co.uk).
    email_pattern = re.compile(
        r"[A-Za-z0-9._%+-]+@"  # local part
        r"[A-Za-z0-9.-]+\."  # domain and first dot
        r"[A-Za-z]{2,}"  # first TLD component
        r"(?:\.[A-Za-z]{2,})*"  # optional additional TLD components
    )
    return email_pattern.findall(text)


def extract_urls(text: str) -> List[str]:
    """Return a list of all HTTP/HTTPS URLs found in *text*.

    The function looks for substrings that start with ``http://`` or
    ``https://`` and continues until whitespace or a character that cannot be
    part of a URL. Trailing punctuation such as ``. , ; : ! ? )]}`` is stripped
    from each match.
    """
    # Rough match: start with http(s) and consume any non‑whitespace characters
    raw_urls = re.findall(r"https?://[^\s'\"<>]+", text)

    cleaned: List[str] = []
    for url in raw_urls:
        # Strip trailing punctuation that is unlikely to be part of the URL.
        while url and url[-1] in ".,;:!?)]}":
            url = url[:-1]
        cleaned.append(url)
    return cleaned


def extract_hashtags(text: str) -> List[str]:
    """Return a list of hashtag strings (without the leading ``#``) found in *text*.

    Hashtags consist of letters, digits, or underscores and are terminated by
    any character that is not part of that set.
    """
    hashtag_pattern = re.compile(r"#([A-Za-z0-9_]+)")
    return hashtag_pattern.findall(text)


def extract_mentions(text: str) -> List[str]:
    """Return a list of @mention usernames (without the leading ``@``) found in *text*.

    Mentions consist of letters, digits, or underscores. The ``@`` must not be
    part of an email address, so a negative look‑behind ensures the preceding
    character is not typical of an email local‑part.
    """
    # Negative look‑behind prevents matching the @ in email addresses.
    mention_pattern = re.compile(r"(?<![A-Za-z0-9._%+-])@([A-Za-z0-9_]+)")
    return mention_pattern.findall(text)
