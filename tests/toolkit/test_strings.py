from app.toolkit.strings import slugify, truncate, word_wrap


def test_slugify_basic() -> None:
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_strips_accents_and_edges() -> None:
    assert slugify("  Café del Mar  ") == "cafe-del-mar"
    assert slugify("---A___B---") == "a-b"


def test_truncate_cuts_and_adds_ellipsis() -> None:
    # "Hello world" length is 11, max_length 5 -> "Hell…" (4 chars + ellipsis)
    assert truncate("Hello world", 5) == "Hell…"


def test_truncate_no_cut() -> None:
    assert truncate("Hi", 5) == "Hi"


def test_truncate_edge_cases() -> None:
    assert truncate("abc", 0) == ""
    assert truncate("abc", 1) == "…"


def test_word_wrap_typical() -> None:
    text = "The quick brown fox jumps over the lazy dog"
    expected = "The quick\nbrown fox\njumps over\nthe lazy\ndog"
    assert word_wrap(text, 10) == expected


def test_word_wrap_edge_cases() -> None:
    # Width smaller than any word: each word on its own line
    assert word_wrap("abc def", 2) == "abc\ndef"
    # Zero width returns empty string
    assert word_wrap("anything", 0) == ""
