import pytest

from app.toolkit.colors import hex_to_rgb


def test_hex_to_rgb_basic() -> None:
    assert hex_to_rgb("#ff00FF") == (255, 0, 255)
    assert hex_to_rgb("00ff00") == (0, 255, 0)


def test_hex_to_rgb_invalid() -> None:
    with pytest.raises(ValueError):
        hex_to_rgb("#123")  # too short
    with pytest.raises(ValueError):
        hex_to_rgb("gggggg")  # invalid hex digits
