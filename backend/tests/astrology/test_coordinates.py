"""Tests for GeographicCoordinates."""

import pytest

from app.astrology.coordinates import GeographicCoordinates


def test_coordinates_validation_valid():
    coords = GeographicCoordinates(latitude=22.5726, longitude=88.3639)
    assert coords.latitude == 22.5726
    assert coords.longitude == 88.3639
    assert "N" in coords.lat_dms
    assert "E" in coords.lng_dms


def test_coordinates_validation_invalid_latitude():
    with pytest.raises(ValueError):
        GeographicCoordinates(latitude=95.0, longitude=0.0)


def test_coordinates_validation_invalid_longitude():
    with pytest.raises(ValueError):
        GeographicCoordinates(latitude=0.0, longitude=185.0)


def test_coordinates_distance_calculation():
    ny = GeographicCoordinates(latitude=40.7128, longitude=-74.0060)
    london = GeographicCoordinates(latitude=51.5074, longitude=-0.1278)
    distance = ny.distance_to(london)
    # Great circle distance between NY and London is ~5570 km
    assert 5500 < distance < 5700
