from app.toolkit.regexutil import extract_urls


def test_extract_urls_typical() -> None:
    text = "Check https://example.com and http://test.org/path?query=1."
    result = extract_urls(text)
    assert result == ["https://example.com", "http://test.org/path?query=1"]


def test_extract_urls_edge_cases() -> None:
    # URL followed by punctuation and parentheses should be stripped.
    text = "Visit (https://example.com/path), and also https://example.org."
    result = extract_urls(text)
    assert result == ["https://example.com/path", "https://example.org"]

    # No URLs present
    assert extract_urls("Nothing to see here.") == []
