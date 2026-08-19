import pytest

from app.toolkit.checkdigit import upc_check_digit


def test_upc_check_digit_typical() -> None:
    # Example from UPC‑A specification: payload "03600029145" → check digit 2
    assert upc_check_digit("03600029145") == 2


def test_upc_check_digit_all_zero() -> None:
    # All zeros should yield a check digit of 0
    assert upc_check_digit("00000000000") == 0


def test_upc_check_digit_invalid_length() -> None:
    with pytest.raises(ValueError):
        upc_check_digit("12345")  # too short


def test_upc_check_digit_non_digit() -> None:
    with pytest.raises(ValueError):
        upc_check_digit("ABCDEFGHIJK")
