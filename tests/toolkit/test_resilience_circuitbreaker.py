import pytest

from app.toolkit.resilience import CircuitBreaker, CircuitBreakerOpenError


def test_circuit_breaker_opens_after_threshold() -> None:
    calls = {"count": 0}

    cb = CircuitBreaker(failure_threshold=2)

    @cb
    def always_fail() -> None:
        calls["count"] += 1
        raise ValueError("failure")

    # First two calls raise the original exception
    with pytest.raises(ValueError):
        always_fail()
    with pytest.raises(ValueError):
        always_fail()
    assert calls["count"] == 2

    # Third call should raise CircuitBreakerOpenError without invoking the function
    with pytest.raises(CircuitBreakerOpenError):
        always_fail()
    # No additional call increment
    assert calls["count"] == 2


def test_circuit_breaker_reset_allows_calls_again() -> None:
    cb = CircuitBreaker(failure_threshold=1)

    @cb
    def flaky() -> None:
        raise RuntimeError("oops")

    # First call fails and opens the circuit
    with pytest.raises(RuntimeError):
        flaky()
    with pytest.raises(CircuitBreakerOpenError):
        flaky()

    # Reset the breaker
    cb.reset()

    # After reset, the next call again raises the original exception (circuit closed)
    with pytest.raises(RuntimeError):
        flaky()
    # Circuit should be open again after this failure
    with pytest.raises(CircuitBreakerOpenError):
        flaky()


def test_circuit_breaker_invalid_threshold_raises() -> None:
    with pytest.raises(ValueError):
        CircuitBreaker(failure_threshold=0)
