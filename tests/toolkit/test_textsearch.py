from app.toolkit.textsearch import fuzzy_ratio


def test_fuzzy_ratio_typical_case() -> None:
    # Classic Levenshtein example: distance 3, longer length 7 → 57%
    assert fuzzy_ratio("kitten", "sitting") == 57


def test_fuzzy_ratio_edge_cases() -> None:
    # Both empty strings → perfect similarity
    assert fuzzy_ratio("", "") == 100
    # One empty, one non‑empty → no similarity
    assert fuzzy_ratio("abc", "") == 0
    assert fuzzy_ratio("", "xyz") == 0
