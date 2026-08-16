import datetime

import pytest

from app.toolkit.calendars import easter_date


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
