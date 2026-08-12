import pytest

from app.toolkit.resilience import retry


def test_retry_successful_after_failures() -> None:
    calls = {"count": 0}

    @retry(attempts=3, exceptions=(ValueError,))
    def flaky() -> str:
        calls["count"] += 1
        if calls["count"] < 3:
            raise ValueError("temporary failure")
        return "ok"

    result = flaky()
    assert result == "ok"
    assert calls["count"] == 3


def test_retry_exhausts_and_raises() -> None:
    calls = {"count": 0}

    @retry(attempts=2, exceptions=(KeyError,))
    def always_fails() -> None:
        calls["count"] += 1
        raise KeyError("always fails")

    with pytest.raises(KeyError):
        always_fails()
    assert calls["count"] == 2


def test_retry_invalid_attempts_raises_at_declaration() -> None:
    with pytest.raises(ValueError):

        @retry(attempts=0)
        def func() -> None:
            pass
