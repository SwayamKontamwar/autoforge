"""Tests for the internationalization utilities."""

import pytest

from app.toolkit.i18n import format_list, plural_rule_en


def test_plural_rule_en_basic():
    """Verify correct plural categories for typical counts."""
    assert plural_rule_en(1) == "one"
    assert plural_rule_en(0) == "other"
    assert plural_rule_en(2) == "other"
    assert plural_rule_en(-5) == "other"


def test_plural_rule_en_type_error():
    """The function must reject non‑integer inputs."""
    with pytest.raises(TypeError):
        plural_rule_en(1.5)
    with pytest.raises(TypeError):
        plural_rule_en("1")


def test_format_list_various_cases():
    """Check English list formatting for different lengths and types."""
    # Empty list → empty string
    assert format_list([]) == ""
    # Single element
    assert format_list(["apple"]) == "apple"
    # Two elements
    assert format_list(["apple", "banana"]) == "apple and banana"
    # Three elements
    assert format_list(["apple", "banana", "cherry"]) == "apple, banana, and cherry"
    # Non‑string items are stringified
    assert format_list([1, 2, 3]) == "1, 2, and 3"
