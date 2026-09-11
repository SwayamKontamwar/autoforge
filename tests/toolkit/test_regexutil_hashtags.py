from app.toolkit.regexutil import extract_hashtags


def test_extract_hashtags_typical() -> None:
    text = "Learning #Python is fun. #AI #machine_learning"
    assert extract_hashtags(text) == ["Python", "AI", "machine_learning"]


def test_extract_hashtags_edge_cases() -> None:
    text = "#hashtag, with punctuation! Also #123numbers and #mixedCASE."
    assert extract_hashtags(text) == ["hashtag", "123numbers", "mixedCASE"]
    assert extract_hashtags("No tags here.") == []
