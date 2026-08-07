from app.toolkit.strings import slugify, truncate


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
