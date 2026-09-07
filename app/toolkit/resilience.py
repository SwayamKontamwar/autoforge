"""Retry decorator for transient failures.

The :func:`retry` decorator retries the wrapped callable when specified
exceptions are raised, up to a configurable number of attempts.  The first
attempt counts as one, so ``attempts=1`` means the function is called once
without any retries.

Example
-------
>>> @retry(attempts=3, exceptions=(ValueError,))
... def flaky():
...     ...

If the wrapped function raises one of the ``exceptions`` it will be retried
until the attempt limit is reached, after which the last exception is
re‑raised.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Tuple, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def retry(
    attempts: int = 3, exceptions: Tuple[BaseException, ...] = (Exception,)
) -> Callable[[F], F]:
    """Return a decorator that retries a function on given exceptions.

    Args:
        attempts: Total number of attempts (must be >= 1). The original call
            counts as the first attempt.
        exceptions: Tuple of exception classes that trigger a retry.

    Raises:
        ValueError: If *attempts* is less than 1.
    """
    if attempts < 1:
        raise ValueError("attempts must be a positive integer")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exc: BaseException | None = None
            for _ in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # type: ignore[misc]
                    last_exc = exc
            # Exhausted attempts; re‑raise the last exception
            assert last_exc is not None  # for mypy
            raise last_exc

        return wrapper  # type: ignore[return-value]

    return decorator


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a circuit breaker is open and a call is attempted."""


class CircuitBreaker:
    """Simple circuit breaker that opens after a number of consecutive failures.

    The breaker starts in a closed state. Each call to a wrapped function that
    raises an exception increments the failure count. When the count reaches
    ``failure_threshold`` the circuit opens and further calls raise
    :class:`CircuitBreakerOpenError` without invoking the wrapped function.

    The circuit can be manually reset via :meth:`reset`, which closes the
    circuit and clears the failure count.
    """

    def __init__(self, failure_threshold: int = 5):
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        self.failure_threshold = failure_threshold
        self._failure_count = 0
        self._open = False

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if self._open:
                raise CircuitBreakerOpenError("circuit is open")
            try:
                result = func(*args, **kwargs)
                # Reset failure count on success
                self._failure_count = 0
                return result
            except Exception:
                self._failure_count += 1
                if self._failure_count >= self.failure_threshold:
                    self._open = True
                raise

        return wrapper

    def reset(self) -> None:
        """Close the circuit and reset the failure counter."""
        self._failure_count = 0
        self._open = False
