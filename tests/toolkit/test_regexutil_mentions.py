from app.toolkit.regexutil import extract_mentions


def test_extract_mentions_typical() -> None:
    text = "Hello @alice and @bob123, welcome!"
    assert extract_mentions(text) == ["alice", "bob123"]


def test_extract_mentions_edge_cases() -> None:
    # Mention followed by punctuation and an email address should not be captured as a mention.
    text = "Contact @charlie, or email dave@example.com. Also @eve!"
    assert extract_mentions(text) == ["charlie", "eve"]
