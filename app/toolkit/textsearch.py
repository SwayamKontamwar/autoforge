"""Utility functions for simple text searching.

Provides a fuzzy similarity ratio based on Levenshtein distance.
"""

from __future__ import annotations

from typing import List, Optional


def _levenshtein(a: str, b: str) -> int:
    """Return the Levenshtein distance between *a* and *b*.

    This implementation uses a classic dynamic‑programming matrix with O(len(a) *
    len(b)) time and O(min(len(a), len(b))) space.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Ensure the shorter string is *a* to minimise space.
    if len(a) > len(b):
        a, b = b, a

    previous_row: List[int] = list(range(len(a) + 1))
    for i, ch_b in enumerate(b, 1):
        current_row: List[int] = [i]
        for j, ch_a in enumerate(a, 1):
            insert_cost = previous_row[j] + 1
            delete_cost = current_row[j - 1] + 1
            replace_cost = previous_row[j - 1] + (ch_a != ch_b)
            current_row.append(min(insert_cost, delete_cost, replace_cost))
        previous_row = current_row
    return previous_row[-1]


def fuzzy_ratio(a: str, b: str) -> int:
    """Return a similarity ratio (0‑100) between *a* and *b*.

    The ratio is based on the Levenshtein distance and the length of the longer
    string:

        ratio = (max_len - distance) / max_len * 100

    If both strings are empty the function returns ``100``.
    """
    max_len = max(len(a), len(b))
    if max_len == 0:
        return 100
    distance = _levenshtein(a, b)
    return int((max_len - distance) * 100 / max_len)


def fuzzy_best_match(query: str, candidates: List[str]) -> Optional[str]:
    """Return the candidate with the highest fuzzy similarity to *query*.

    If *candidates* is empty, returns ``None``.  Ties are resolved by returning
    the first candidate with the maximal ratio.
    """
    if not candidates:
        return None

    best_candidate = candidates[0]
    best_score = fuzzy_ratio(query, best_candidate)

    for cand in candidates[1:]:
        score = fuzzy_ratio(query, cand)
        if score > best_score:
            best_candidate = cand
            best_score = score

    return best_candidate


def ngrams(s: str, n: int) -> List[str]:
    """Return a list of contiguous character *n*-grams from *s*.

    If ``n`` is less than or equal to zero, or greater than the length of *s*,
    an empty list is returned.
    """
    if n <= 0 or n > len(s):
        return []
    return [s[i : i + n] for i in range(len(s) - n + 1)]
