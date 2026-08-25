from app.toolkit.webframework import path_to_regex


def test_path_to_regex_basic() -> None:
    """A simple pattern with two parameters should match and capture correctly."""
    pattern = "/users/{id}/posts/{post_id}"
    regex = path_to_regex(pattern)

    match = regex.match("/users/42/posts/99")
    assert match is not None
    assert match.groupdict() == {"id": "42", "post_id": "99"}

    # Non‑matching path (missing segment) should yield no match.
    assert regex.match("/users/42/posts") is None


def test_path_to_regex_static_only() -> None:
    """A pattern without parameters should behave like a literal matcher."""
    pattern = "/about"
    regex = path_to_regex(pattern)

    assert regex.match("/about") is not None
    assert regex.match("/about/extra") is None
