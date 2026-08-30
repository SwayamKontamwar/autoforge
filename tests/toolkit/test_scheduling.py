import datetime

from app.toolkit.scheduling import cron_iter, next_cron_time


def test_next_cron_time_every_minute() -> None:
    """A wildcard expression should advance by one minute."""
    base = datetime.datetime(2023, 5, 17, 12, 30, 0)
    result = next_cron_time("* * * * *", base)
    assert result == datetime.datetime(2023, 5, 17, 12, 31, 0)


def test_next_cron_time_yearly_edge() -> None:
    """Expression for midnight Jan 1 should roll over to the next year."""
    # Starting after Jan 1 of the current year.
    base = datetime.datetime(2023, 2, 1, 0, 0, 0)
    result = next_cron_time("0 0 1 1 *", base)
    assert result == datetime.datetime(2024, 1, 1, 0, 0, 0)

    # Starting exactly at the matching moment should give the next year's occurrence.
    exact = datetime.datetime(2023, 1, 1, 0, 0, 0)
    result2 = next_cron_time("0 0 1 1 *", exact)
    assert result2 == datetime.datetime(2024, 1, 1, 0, 0, 0)


def test_cron_iter_multiple_minutes() -> None:
    """cron_iter should yield successive minute matches."""
    start = datetime.datetime(2023, 5, 17, 12, 30, 0)
    gen = cron_iter("* * * * *", start)
    results = [next(gen) for _ in range(3)]
    expected = [
        datetime.datetime(2023, 5, 17, 12, 31, 0),
        datetime.datetime(2023, 5, 17, 12, 32, 0),
        datetime.datetime(2023, 5, 17, 12, 33, 0),
    ]
    assert results == expected


def test_cron_iter_yearly_edge() -> None:
    """cron_iter respects the strict‑after rule for exact matches."""
    start = datetime.datetime(2023, 1, 1, 0, 0, 0)
    gen = cron_iter("0 0 1 1 *", start)
    first = next(gen)
    assert first == datetime.datetime(2024, 1, 1, 0, 0, 0)


def test_cron_iter_preserves_tzinfo() -> None:
    """Timezone information should be retained in yielded datetimes."""
    tz = datetime.timezone.utc
    start = datetime.datetime(2023, 5, 17, 12, 30, 0, tzinfo=tz)
    gen = cron_iter("* * * * *", start)
    first = next(gen)
    assert first.tzinfo is tz
    assert first == datetime.datetime(2023, 5, 17, 12, 31, 0, tzinfo=tz)
