from math import pi

import pytest

from app.toolkit.geometry import haversine


def test_haversine_typical() -> None:
    # Approximate distance between (0°,0°) and (0°,1°) along the equator
    # Expected: 111.1949 km (Earth radius 6371 km)
    assert haversine((0.0, 0.0), (0.0, 1.0)) == pytest.approx(111.19492664455873, rel=1e-6)


def test_haversine_edge_cases() -> None:
    # Same point yields zero distance
    assert haversine((12.34, 56.78), (12.34, 56.78)) == 0.0

    # Antipodal points: distance should be pi * radius
    earth_radius_km = 6371.0
    expected = pi * earth_radius_km
    assert haversine((0.0, 0.0), (0.0, 180.0)) == pytest.approx(expected, rel=1e-6)
