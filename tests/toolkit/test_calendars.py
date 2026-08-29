import datetime

import pytest

from app.toolkit.calendars import easter_date, nth_weekday_of_month


def test_easter_date_known_years() -> None:
    """Check a selection of known Easter dates."""
    known = {
        2020: datetime.date(2020, 4, 12),
        2021: datetime.date(2021, 4, 4),
        2022: datetime.date(2022, 4, 17),
        2023: datetime.date(2023, 4, 9),
        2024: datetime.date(2024, 3, 31),
    }
    for year, expected in known.items():
        assert easter_date(year) == expected


def test_easter_date_invalid_year() -> None:
    """Years before the Gregorian reform should raise."""
    with pytest.raises(ValueError):
        easter_date(1500)


def test_nth_weekday_of_month_basic() -> None:
    """Second Monday of May 2023 should be May 8."""
    assert nth_weekday_of_month(2023, 5, 0, 2) == datetime.date(2023, 5, 8)


def test_nth_weekday_of_month_missing_occurrence() -> None:
    """February 2021 has only four Mondays; requesting the fifth should raise."""
    with pytest.raises(ValueError):
        nth_weekday_of_month(2021, 2, 0, 5)
