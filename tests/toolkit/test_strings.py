from app.toolkit.strings import slugify


def test_slugify_basic() -> None:
    assert slugify("Hello, World!") == "hello-world"


def test_slugify_strips_accents_and_edges() -> None:
    assert slugify("  Café del Mar  ") == "cafe-del-mar"
    assert slugify("---A___B---") == "a-b"
