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


__all__ = ["extract_emails"]
