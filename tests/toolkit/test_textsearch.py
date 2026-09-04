from app.toolkit.textsearch import fuzzy_best_match, fuzzy_ratio, ngrams


def test_fuzzy_ratio_typical_case() -> None:
    # Classic Levenshtein example: distance 3, longer length 7 → 57%
    assert fuzzy_ratio("kitten", "sitting") == 57


def test_fuzzy_ratio_edge_cases() -> None:
    # Both empty strings → perfect similarity
    assert fuzzy_ratio("", "") == 100
    # One empty, one non‑empty → no similarity
    assert fuzzy_ratio("abc", "") == 0
    assert fuzzy_ratio("", "xyz") == 0


def test_fuzzy_best_match_typical() -> None:
    query = "apple"
    candidates = ["aple", "apples", "apply", "banana"]
    # "apples" has the highest similarity (distance 1, longer length 6 → 83%)
    assert fuzzy_best_match(query, candidates) == "apples"


def test_fuzzy_best_match_empty_candidates() -> None:
    assert fuzzy_best_match("anything", []) is None


def test_fuzzy_best_match_tie() -> None:
    # All candidates have the same distance to "cat"
    candidates = ["bat", "rat", "mat"]
    assert fuzzy_best_match("cat", candidates) == "bat"


def test_ngrams_typical_and_edge_cases() -> None:
    assert ngrams("hello", 2) == ["he", "el", "ll", "lo"]
    assert ngrams("abc", 1) == ["a", "b", "c"]
    assert ngrams("", 2) == []
    assert ngrams("a", 3) == []
