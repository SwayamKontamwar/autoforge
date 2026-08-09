import pytest

from app.toolkit.parsing import parse_semver


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
