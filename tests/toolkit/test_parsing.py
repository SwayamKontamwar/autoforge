import pytest

from app.toolkit.parsing import compare_semver, parse_semver


def test_parse_semver_basic() -> None:
    assert parse_semver("1.2.3") == (1, 2, 3, None)
    assert parse_semver("0.0.1-alpha") == (0, 0, 1, "alpha")
    assert parse_semver("10.20.30-beta.2") == (10, 20, 30, "beta.2")
    # Leading/trailing whitespace should be ignored
    assert parse_semver("  2.4.6-rc1  ") == (2, 4, 6, "rc1")


def test_parse_semver_invalid() -> None:
    with pytest.raises(ValueError):
        parse_semver("1.2")  # missing patch
    with pytest.raises(ValueError):
        parse_semver("1.2.3-")  # empty prerelease
    with pytest.raises(ValueError):
        parse_semver("v1.2.3")  # unexpected leading character
    with pytest.raises(ValueError):
        parse_semver("1.2.3+build")  # build metadata not supported


def test_compare_semver_basic_and_edge_cases() -> None:
    # Equality
    assert compare_semver("1.2.3", "1.2.3") == 0
    # Simple ordering
    assert compare_semver("1.2.3", "1.2.4") == -1
    assert compare_semver("2.0.0", "1.9.9") == 1
    # Pre‑release vs release
    assert compare_semver("1.0.0-alpha", "1.0.0") == -1
    # Pre‑release ordering
    assert compare_semver("1.0.0-alpha.1", "1.0.0-alpha") == 1
    # Numeric identifier vs alphanumeric identifier
    assert compare_semver("1.0.0-1", "1.0.0-alpha") == -1
    # Longer pre‑release with higher precedence
    assert compare_semver("1.0.0-alpha.beta", "1.0.0-alpha.1") == 1
    # Identical pre‑release strings
    assert compare_semver("1.0.0-rc.1", "1.0.0-rc.1") == 0
