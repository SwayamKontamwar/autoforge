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
