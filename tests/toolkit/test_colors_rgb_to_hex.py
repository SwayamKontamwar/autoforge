import pytest

from app.toolkit.colors import rgb_to_hex


def test_rgb_to_hex_basic() -> None:
    assert rgb_to_hex((255, 0, 255)) == "#ff00ff"
    assert rgb_to_hex((0, 255, 0)) == "#00ff00"
    assert rgb_to_hex((0, 0, 0)) == "#000000"
    assert rgb_to_hex((255, 255, 255)) == "#ffffff"


def test_rgb_to_hex_invalid() -> None:
    with pytest.raises(ValueError):
        rgb_to_hex((256, 0, 0))  # component too high
    with pytest.raises(ValueError):
        rgb_to_hex((-1, 0, 0))  # component too low
    with pytest.raises(TypeError):
        rgb_to_hex((0.5, 0, 0))  # non‑int component
    with pytest.raises(TypeError):
        rgb_to_hex([0, 0, 0])  # not a tuple
