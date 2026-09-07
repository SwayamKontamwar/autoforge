"""Tests for the progress_bar utility."""

import pytest

from app.toolkit import progress_bar


def test_progress_bar_empty() -> None:
    assert progress_bar(0.0, width=10) == "[----------]"


def test_progress_bar_half() -> None:
    # 0.5 of 10 width should give 5 filled characters
    assert progress_bar(0.5, width=10) == "[#####-----]"


def test_progress_bar_full_and_overflow() -> None:
    assert progress_bar(1.0, width=8) == "[########]"
    # Values greater than 1 are clamped to full
    assert progress_bar(1.2, width=8) == "[########]"


def test_progress_bar_negative_clamped() -> None:
    # Negative values are clamped to empty
    assert progress_bar(-0.3, width=6) == "[------]"


def test_progress_bar_invalid_width() -> None:
    with pytest.raises(ValueError):
        progress_bar(0.5, width=0)
