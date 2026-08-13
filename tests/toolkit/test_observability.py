import time

from app.toolkit.observability import Stopwatch


def test_stopwatch_basic() -> None:
    sw = Stopwatch()
    sw.start()
    time.sleep(0.01)
    elapsed = sw.stop()
    assert isinstance(elapsed, float)
    assert elapsed >= 0.0


def test_stopwatch_edge_cases() -> None:
    sw = Stopwatch()
    # Stopping without a prior start should return 0.0
    assert sw.stop() == 0.0

    # Start and immediately stop
    sw.start()
    elapsed_first = sw.stop()
    assert elapsed_first >= 0.0

    # Subsequent stop without a new start should again return 0.0
    assert sw.stop() == 0.0
