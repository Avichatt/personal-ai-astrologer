"""Tests for the HistoricalTimezoneEngine."""

from datetime import UTC, date, time

import pytest

from app.astrology.timezone import HistoricalTimezoneEngine


@pytest.fixture
def tz_engine():
    return HistoricalTimezoneEngine()


def test_find_timezone_kolkata(tz_engine):
    # Kolkata: 22.5726° N, 88.3639° E
    tz_name = tz_engine.find_timezone(22.5726, 88.3639)
    assert tz_name == "Asia/Kolkata"


def test_find_timezone_new_york(tz_engine):
    # New York: 40.7128° N, -74.0060° W
    tz_name = tz_engine.find_timezone(40.7128, -74.0060)
    assert tz_name == "America/New_York"


def test_find_timezone_london(tz_engine):
    # London: 51.5074° N, -0.1278° W
    tz_name = tz_engine.find_timezone(51.5074, -0.1278)
    assert tz_name == "Europe/London"


def test_convert_to_utc_kolkata_ist(tz_engine):
    # IST is UTC+05:30 (no DST)
    d = date(1995, 5, 10)
    t = time(14, 35, 0)
    local_aware, utc_dt = tz_engine.convert_to_utc(d, t, "Asia/Kolkata")

    # 14:35 - 5h30m = 09:05 UTC
    assert utc_dt.year == 1995
    assert utc_dt.month == 5
    assert utc_dt.day == 10
    assert utc_dt.hour == 9
    assert utc_dt.minute == 5
    assert utc_dt.second == 0
    assert utc_dt.tzinfo == UTC


def test_convert_to_utc_london_summer_dst(tz_engine):
    # London in July is BST (UTC+1)
    d = date(1985, 7, 20)
    t = time(22, 15, 0)
    local_aware, utc_dt = tz_engine.convert_to_utc(d, t, "Europe/London")

    # 22:15 - 1h = 21:15 UTC
    assert utc_dt.hour == 21
    assert utc_dt.minute == 15
    assert utc_dt.tzinfo == UTC


def test_convert_to_utc_new_york_winter(tz_engine):
    # New York in January is EST (UTC-5)
    d = date(1990, 1, 15)
    t = time(8, 30, 0)
    local_aware, utc_dt = tz_engine.convert_to_utc(d, t, "America/New_York")

    # 08:30 + 5h = 13:30 UTC
    assert utc_dt.hour == 13
    assert utc_dt.minute == 30
    assert utc_dt.tzinfo == UTC
