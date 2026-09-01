from app.toolkit.strings import title_case


def test_title_case_basic() -> None:
    assert title_case("the lord of the rings") == "The Lord of the Rings"


def test_title_case_first_word_small() -> None:
    assert title_case("of mice and men") == "Of Mice and Men"


def test_title_case_empty_string() -> None:
    assert title_case("") == ""
