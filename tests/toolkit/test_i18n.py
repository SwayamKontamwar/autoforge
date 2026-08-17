"""Tests for the internationalization utilities."""

import pytest

from app.toolkit.i18n import plural_rule_en


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
