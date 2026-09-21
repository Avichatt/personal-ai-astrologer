"""Randomized birth date & time tests for the astrology calculation engines.

Tests across the full valid date range (1800-2100), random geographic coordinates,
and multiple astrology systems — ensuring the engines never raise exceptions and
always produce structurally sound output regardless of input.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pytest

from app.astrology.engine import AstrologyEngine
from app.astrology.ephemeris import EphemerisService
from app.astrology.vedic.natal import VedicNatalChartEngine
from app.astrology.western.natal import WesternNatalChartEngine
from app.config.constants import Ayanamsa, HouseSystem

# ── Deterministic seed for reproducible CI runs ──────────────────────────────
RANDOM_SEED = 42
_rng = random.Random(RANDOM_SEED)

# ── Date range the Swiss Ephemeris / fallback support reliably ────────────────
EPOCH_START = datetime(1800, 1, 1, tzinfo=UTC)
EPOCH_END = datetime(2100, 12, 31, tzinfo=UTC)
EPOCH_SPAN_DAYS = (EPOCH_END - EPOCH_START).days

WESTERN_ZODIAC_SIGNS = {
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
}

VEDIC_RASHI_NAMES = {
    "Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
    "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def random_utc_datetime() -> datetime:
    """Return a uniformly random UTC datetime within the supported epoch."""
    offset_days = _rng.randint(0, EPOCH_SPAN_DAYS)
    offset_seconds = _rng.randint(0, 86399)
    return EPOCH_START + timedelta(days=offset_days, seconds=offset_seconds)


def random_lat_lon() -> tuple[float, float]:
    """Return a random (latitude, longitude) pair in valid geographic ranges."""
    lat = round(_rng.uniform(-89.9, 89.9), 4)
    lon = round(_rng.uniform(-179.9, 179.9), 4)
    return lat, lon


def random_ayanamsa() -> Ayanamsa:
    return _rng.choice(list(Ayanamsa))


def random_house_system() -> HouseSystem:
    return _rng.choice(list(HouseSystem))


# ── Pre-generated stable fixture set (avoids test variability) ────────────────

N_RANDOM_CASES = 10  # Keep suite fast — 10 diverse datetimes

RANDOM_BIRTH_CASES: list[dict] = [
    {
        "dt": random_utc_datetime(),
        "lat": lat,
        "lon": lon,
        "label": f"random_{i}",
    }
    for i, (lat, lon) in enumerate(random_lat_lon() for _ in range(N_RANDOM_CASES))
]


# ── Western Natal ─────────────────────────────────────────────────────────────

class TestWesternNatalRandomBirths:
    """Western natal chart must succeed for any valid birth datetime in the epoch."""

    @pytest.mark.parametrize("case", RANDOM_BIRTH_CASES, ids=[c["label"] for c in RANDOM_BIRTH_CASES])
    def test_western_chart_never_raises(self, case: dict):
        engine = WesternNatalChartEngine(EphemerisService())
        chart = engine.calculate_chart(
            dt_utc=case["dt"],
            latitude=case["lat"],
            longitude=case["lon"],
            house_system=HouseSystem.PLACIDUS,
        )

        # Structural invariants
        assert chart.system == "western"
        assert len(chart.planets) == 11, f"Expected 11 planets, got {len(chart.planets)}"
        assert len(chart.houses) == 12, f"Expected 12 houses, got {len(chart.houses)}"
        assert chart.sun_sign in WESTERN_ZODIAC_SIGNS, f"Unexpected sun sign: {chart.sun_sign}"
        assert chart.moon_sign in WESTERN_ZODIAC_SIGNS, f"Unexpected moon sign: {chart.moon_sign}"
        assert chart.ascendant_sign in WESTERN_ZODIAC_SIGNS, f"Unexpected ASC sign: {chart.ascendant_sign}"
        assert chart.chart_signature != ""
        assert 0.0 <= chart.angles["ascendant"] < 360.0
        assert 0.0 <= chart.angles["midheaven"] < 360.0

        # All planet longitudes must be in [0, 360)
        for p in chart.planets:
            assert 0.0 <= p.longitude < 360.0, (
                f"Planet {p.name} longitude {p.longitude} out of range for {case['dt']}"
            )

        # Elemental balance counts must be non-negative
        b = chart.balance
        assert b.fire >= 0 and b.earth >= 0 and b.air >= 0 and b.water >= 0
        assert b.dominant_element in ("Fire", "Earth", "Air", "Water")

    @pytest.mark.parametrize("house_sys", list(HouseSystem))
    def test_house_systems_all_produce_12_houses(self, house_sys: HouseSystem):
        """Each house system must produce exactly 12 valid house cusps."""
        engine = WesternNatalChartEngine(EphemerisService())
        # Use a mid-latitude birth so Placidus-like systems are well-behaved
        dt = datetime(1985, 3, 21, 6, 0, 0, tzinfo=UTC)
        chart = engine.calculate_chart(
            dt_utc=dt,
            latitude=51.5,   # London-ish
            longitude=-0.12,
            house_system=house_sys,
        )
        assert len(chart.houses) == 12
        for h in chart.houses:
            assert 1 <= h.house_number <= 12
            assert 0.0 <= h.cusp_longitude < 360.0


# ── Vedic Natal ───────────────────────────────────────────────────────────────

class TestVedicNatalRandomBirths:
    """Vedic natal chart (Kundli) must be complete for any valid birth datetime."""

    @pytest.mark.parametrize("case", RANDOM_BIRTH_CASES, ids=[c["label"] for c in RANDOM_BIRTH_CASES])
    def test_vedic_chart_never_raises(self, case: dict):
        engine = VedicNatalChartEngine(EphemerisService())
        chart = engine.calculate_chart(
            dt_utc=case["dt"],
            latitude=case["lat"],
            longitude=case["lon"],
            ayanamsa=Ayanamsa.LAHIRI,
        )

        # Structural invariants
        assert chart.system == "vedic"
        assert len(chart.grahas) == 9, f"Expected 9 Grahas, got {len(chart.grahas)}"  # 7 + Rahu + Ketu
        assert len(chart.bhavas) == 12
        assert chart.ascendant_rashi in VEDIC_RASHI_NAMES, (
            f"Unexpected ascendant rashi: {chart.ascendant_rashi}"
        )
        assert 0.0 <= chart.ascendant_longitude < 360.0
        assert chart.ayanamsa_value > 0.0

        # All graha longitudes must be in [0, 360)
        for g in chart.grahas:
            assert 0.0 <= g.longitude < 360.0, (
                f"Graha {g.name} longitude {g.longitude} out of range for {case['dt']}"
            )
            assert 0 <= g.rashi_index <= 11
            assert 1 <= g.house_number <= 12
            assert g.rashi_name in VEDIC_RASHI_NAMES

        # Jaimini Karakas
        assert len(chart.karakas) >= 7, "Expected at least 7 Jaimini Karakas"
        ak = next((k for k in chart.karakas if k.code == "AK"), None)
        assert ak is not None, "Atmakaraka (AK) must always be present"

        # Mahadashas
        assert len(chart.mahadashas) >= 9, "Vimshottari must produce at least 9 Mahadasha periods"
        # Dasha periods must be chronologically ordered
        for i in range(1, len(chart.mahadashas)):
            assert chart.mahadashas[i - 1].end_date <= chart.mahadashas[i].start_date, (
                "Mahadasha periods must not overlap"
            )

    @pytest.mark.parametrize("ayanamsa", list(Ayanamsa))
    def test_ayanamsa_variance_stays_within_bounds(self, ayanamsa: Ayanamsa):
        """Different ayanamsas should differ by at most ~2° for the same birth time."""
        engine = VedicNatalChartEngine(EphemerisService())
        dt = datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)
        chart = engine.calculate_chart(
            dt_utc=dt,
            latitude=28.6,  # Delhi
            longitude=77.2,
            ayanamsa=ayanamsa,
        )
        lahiri_chart = engine.calculate_chart(
            dt_utc=dt,
            latitude=28.6,
            longitude=77.2,
            ayanamsa=Ayanamsa.LAHIRI,
        )
        # Ayanamsa values should all be in a reasonable range for J2000
        assert 22.0 < chart.ayanamsa_value < 25.5, (
            f"{ayanamsa} ayanamsa value {chart.ayanamsa_value} is out of the expected 22-25.5° range"
        )
        # Max deviation of ayanamsa values between any system should be < 2.5°
        diff = abs(chart.ayanamsa_value - lahiri_chart.ayanamsa_value)
        assert diff < 2.5, f"{ayanamsa} vs Lahiri diff {diff:.3f}° exceeds 2.5°"


# ── Unified Engine ────────────────────────────────────────────────────────────

class TestUnifiedEngineRandomBirths:
    """AstrologyEngine facade should produce valid dict output for any random input."""

    @pytest.mark.parametrize("case", RANDOM_BIRTH_CASES, ids=[c["label"] for c in RANDOM_BIRTH_CASES])
    def test_western_dict_output_has_required_keys(self, case: dict):
        engine = AstrologyEngine()
        result = engine.calculate_natal(
            utc_datetime=case["dt"],
            latitude=case["lat"],
            longitude=case["lon"],
            system=__import__("app.config.constants", fromlist=["AstrologySystem"]).AstrologySystem.WESTERN,
        )
        required_keys = {"system", "sun_sign", "moon_sign", "ascendant_sign", "planets", "houses", "aspects"}
        missing = required_keys - result.keys()
        assert not missing, f"Missing keys in Western output: {missing} for {case['dt']}"

    @pytest.mark.parametrize("case", RANDOM_BIRTH_CASES, ids=[c["label"] for c in RANDOM_BIRTH_CASES])
    def test_vedic_dict_output_has_required_keys(self, case: dict):
        from app.config.constants import AstrologySystem
        engine = AstrologyEngine()
        result = engine.calculate_natal(
            utc_datetime=case["dt"],
            latitude=case["lat"],
            longitude=case["lon"],
            system=AstrologySystem.VEDIC,
        )
        required_keys = {
            "system", "ayanamsa", "ayanamsa_value", "ascendant_rashi",
            "grahas", "bhavas", "karakas", "yogas", "mahadashas",
        }
        missing = required_keys - result.keys()
        assert not missing, f"Missing keys in Vedic output: {missing} for {case['dt']}"


# ── Edge Cases ────────────────────────────────────────────────────────────────

class TestBirthEdgeCases:
    """Specific edge-case datetimes that historically stress-test astrology engines."""

    @pytest.mark.parametrize("dt,label", [
        (datetime(1800, 1, 1, 0, 0, 0, tzinfo=UTC), "epoch_start_1800"),
        (datetime(2099, 12, 31, 23, 59, 59, tzinfo=UTC), "epoch_end_2099"),
        (datetime(2000, 1, 1, 0, 0, 0, tzinfo=UTC), "j2000_epoch"),
        (datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC), "unix_epoch"),
        (datetime(2024, 2, 29, 12, 0, 0, tzinfo=UTC), "leap_day"),
        (datetime(1582, 10, 15, 0, 0, 0, tzinfo=UTC), "gregorian_reform_day"),
        (datetime(2000, 6, 21, 11, 48, 0, tzinfo=UTC), "summer_solstice_2000"),
        (datetime(2000, 12, 22, 13, 37, 0, tzinfo=UTC), "winter_solstice_2000"),
    ])
    def test_edge_case_datetime_western(self, dt: datetime, label: str):
        """Western chart calculation must not raise for historical/astronomical edge dates."""
        try:
            engine = WesternNatalChartEngine(EphemerisService())
            chart = engine.calculate_chart(dt_utc=dt, latitude=0.0, longitude=0.0)
            assert chart.system == "western"
            assert len(chart.planets) == 11
        except Exception as exc:
            pytest.fail(f"Western chart raised for {label} ({dt}): {exc!r}")

    @pytest.mark.parametrize("dt,label", [
        (datetime(1800, 1, 1, 0, 0, 0, tzinfo=UTC), "epoch_start_1800"),
        (datetime(2099, 12, 31, 23, 59, 59, tzinfo=UTC), "epoch_end_2099"),
        (datetime(2000, 1, 1, 0, 0, 0, tzinfo=UTC), "j2000_epoch"),
        (datetime(1970, 1, 1, 0, 0, 0, tzinfo=UTC), "unix_epoch"),
        (datetime(2024, 2, 29, 12, 0, 0, tzinfo=UTC), "leap_day"),
        (datetime(2000, 6, 21, 11, 48, 0, tzinfo=UTC), "summer_solstice_2000"),
    ])
    def test_edge_case_datetime_vedic(self, dt: datetime, label: str):
        """Vedic chart calculation must not raise for historical/astronomical edge dates."""
        try:
            engine = VedicNatalChartEngine(EphemerisService())
            chart = engine.calculate_chart(dt_utc=dt, latitude=0.0, longitude=0.0)
            assert chart.system == "vedic"
            assert len(chart.grahas) == 9
        except Exception as exc:
            pytest.fail(f"Vedic chart raised for {label} ({dt}): {exc!r}")

    @pytest.mark.parametrize("lat,lon,label", [
        (89.9, 0.0, "north_pole"),
        (-89.9, 0.0, "south_pole"),
        (0.0, 0.0, "null_island"),
        (51.5, -0.1, "london"),
        (-33.9, 151.2, "sydney"),
        (35.7, 139.7, "tokyo"),
        (1.3, 103.8, "singapore_near_equator"),
        (60.2, 24.9, "helsinki_high_lat"),
    ])
    def test_geographic_extremes_western(self, lat: float, lon: float, label: str):
        """Western chart must work for geographically extreme coordinates."""
        engine = WesternNatalChartEngine(EphemerisService())
        dt = datetime(2000, 6, 21, 12, 0, 0, tzinfo=UTC)
        chart = engine.calculate_chart(dt_utc=dt, latitude=lat, longitude=lon)
        assert chart.system == "western"
        assert len(chart.planets) == 11


# ── Quick summary print for manual dev runs ───────────────────────────────────

def _print_random_chart_summary(idx: int, case: dict) -> None:
    """Print a human-readable chart summary — useful for manual exploratory runs."""
    from app.astrology.engine import AstrologyEngine
    from app.config.constants import AstrologySystem

    engine = AstrologyEngine()
    w = engine.calculate_natal(
        utc_datetime=case["dt"],
        latitude=case["lat"],
        longitude=case["lon"],
        system=AstrologySystem.WESTERN,
    )
    v = engine.calculate_natal(
        utc_datetime=case["dt"],
        latitude=case["lat"],
        longitude=case["lon"],
        system=AstrologySystem.VEDIC,
    )
    print(
        f"\n[{idx}] {case['dt'].strftime('%Y-%m-%d %H:%M UTC')}  "
        f"lat={case['lat']:.2f} lon={case['lon']:.2f}\n"
        f"  Western: Sun={w['sun_sign']:<12} Moon={w['moon_sign']:<12} ASC={w['ascendant_sign']}\n"
        f"  Vedic  : Sun={next(g['rashi_name'] for g in v['grahas'] if g['western_name']=='Sun'):<12} "
        f"Moon={next(g['rashi_name'] for g in v['grahas'] if g['western_name']=='Moon'):<12} "
        f"Lagna={v['ascendant_rashi']}"
    )


if __name__ == "__main__":
    print("=" * 70)
    print("RANDOM BIRTH DATE/TIME CHART QUICK OUTPUT")
    print("=" * 70)
    for i, case in enumerate(RANDOM_BIRTH_CASES):
        _print_random_chart_summary(i, case)
    print("\n" + "=" * 70)
