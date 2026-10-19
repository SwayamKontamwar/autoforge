import pytest

from app.toolkit.colors import rgb_to_hsv


def test_rgb_to_hsv_basic() -> None:
    # Pure red
    h, s, v = rgb_to_hsv((255, 0, 0))
    assert h == pytest.approx(0.0)
    assert s == pytest.approx(1.0)
    assert v == pytest.approx(1.0)

    # Pure green
    h, s, v = rgb_to_hsv((0, 255, 0))
    assert h == pytest.approx(120.0)
    assert s == pytest.approx(1.0)
    assert v == pytest.approx(1.0)

    # Pure blue
    h, s, v = rgb_to_hsv((0, 0, 255))
    assert h == pytest.approx(240.0)
    assert s == pytest.approx(1.0)
    assert v == pytest.approx(1.0)

    # White
    h, s, v = rgb_to_hsv((255, 255, 255))
    assert h == pytest.approx(0.0)
    assert s == pytest.approx(0.0)
    assert v == pytest.approx(1.0)

    # Gray (128,128,128)
    h, s, v = rgb_to_hsv((128, 128, 128))
    assert h == pytest.approx(0.0)
    assert s == pytest.approx(0.0)
    assert v == pytest.approx(128 / 255.0)


def test_rgb_to_hsv_invalid() -> None:
    with pytest.raises(ValueError):
        rgb_to_hsv((256, 0, 0))  # component too high
    with pytest.raises(ValueError):
        rgb_to_hsv((-1, 0, 0))  # component too low
    with pytest.raises(TypeError):
        rgb_to_hsv((0.5, 0, 0))  # non‑integer component
    with pytest.raises(TypeError):
        rgb_to_hsv([0, 0, 0])  # not a tuple
