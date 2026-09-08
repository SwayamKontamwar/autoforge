"""Observability utilities for the toolkit.

Provides a simple ``Stopwatch`` class for measuring elapsed time in seconds.
"""

from __future__ import annotations

import time
from typing import Optional


class Stopwatch:
    """A lightweight stopwatch.

    Typical usage::

        sw = Stopwatch()
        sw.start()
        # … do work …
        elapsed = sw.stop()   # seconds as ``float``

    ``stop`` returns ``0.0`` if the stopwatch has not been started or has already
    been stopped. After ``stop`` the stopwatch can be started again.
    """

    __slots__ = ("_start",)

    def __init__(self) -> None:
        self._start: Optional[float] = None

    def start(self) -> None:
        """Start or restart the timer."""
        self._start = time.perf_counter()

    def stop(self) -> float:
        """Stop the timer and return the elapsed seconds.

        Returns ``0.0`` if the stopwatch was not running.
        """
        if self._start is None:
            return 0.0
        now = time.perf_counter()
        elapsed = now - self._start
        self._start = None
        return elapsed


class Timer:
    """Context manager that measures the duration of a code block.

    Example
    -------
    >>> with Timer() as t:
    ...     # do some work
    ...     pass
    >>> elapsed = t.elapsed  # seconds as ``float``

    The elapsed time is stored in the ``elapsed`` attribute after exiting the
    context, regardless of whether the block raised an exception.
    """

    __slots__ = ("_stopwatch", "elapsed")

    def __init__(self) -> None:
        self._stopwatch = Stopwatch()
        self.elapsed: float = 0.0

    def __enter__(self) -> "Timer":
        self._stopwatch.start()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        self.elapsed = self._stopwatch.stop()
        # Do not suppress exceptions.
        return False


class RateCounter:
    """Count events and report a per‑second rate.

    Typical usage::

        rc = RateCounter()
        rc.tick()          # record an event
        rc.tick(3)         # record three more events
        current_rate = rc.rate()   # events per second since first tick

    The counter starts timing on the first ``tick``. ``rate`` returns ``0.0`` if
    no events have been recorded or if the elapsed time is effectively zero.
    The counter can be cleared with :meth:`reset`.
    """

    __slots__ = ("_start", "_count")

    def __init__(self) -> None:
        self._start: Optional[float] = None
        self._count: int = 0

    def tick(self, n: int = 1) -> None:
        """Record ``n`` events (default ``1``). Starts the timer on first call."""
        if self._start is None:
            self._start = time.perf_counter()
        self._count += max(n, 0)

    def rate(self) -> float:
        """Return the current event rate (events per second).

        Returns ``0.0`` when no events have been recorded or when the elapsed
        time is zero or negative.
        """
        if self._count == 0 or self._start is None:
            return 0.0
        elapsed = time.perf_counter() - self._start
        if elapsed <= 0.0:
            return 0.0
        return self._count / elapsed

    def reset(self) -> None:
        """Clear the counter and timer."""
        self._start = None
        self._count = 0
