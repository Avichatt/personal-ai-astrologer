"""Tests for KP 4-level significator theory engine."""

from datetime import UTC, datetime
import pytest

from app.astrology.ephemeris import EphemerisService, PlanetPosition
from app.astrology.kp.significators import (
    KpHouseSignificators,
    KpPlanetSignification,
    KpSignificatorEngine,
    KpSignificatorStrength,
)
from app.astrology.vedic.houses import VedicHouseCalculator, VedicHouseInfo
from app.config.constants import AstrologySystem, Ayanamsa, HouseSystem, Planet


class TestKpSignificators:
    """Test suite for KP 4-level significator determination."""

    def test_strength_hierarchy_order(self) -> None:
        """Verify KP Significator hierarchy order (1 is strongest, 4 is weakest)."""
        assert KpSignificatorStrength.LEVEL_1_STAR_OF_OCCUPANT == 1
        assert KpSignificatorStrength.LEVEL_2_OCCUPANT == 2
        assert KpSignificatorStrength.LEVEL_3_STAR_OF_LORD == 3
        assert KpSignificatorStrength.LEVEL_4_LORD == 4

    def test_significator_engine_generation(self) -> None:
        """Calculate significators from a known chart dataset and verify structure."""
        ephem = EphemerisService()
        dt_utc = datetime(1990, 5, 15, 12, 0, 0, tzinfo=UTC)
        lat, lon = 28.6139, 77.2090  # New Delhi
        jd = ephem.datetime_to_julian_day(dt_utc)

        planets_to_calc = [
            Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
            Planet.MARS, Planet.JUPITER, Planet.SATURN, Planet.MEAN_NODE,
        ]
        planets = [
            ephem.calculate_planet(
                jd=jd,
                planet=p,
                system=AstrologySystem.VEDIC,
                ayanamsa=Ayanamsa.KRISHNAMURTI,
            )
            for p in planets_to_calc
        ]
        ayan_val = ephem.get_ayanamsa_value(jd, Ayanamsa.KRISHNAMURTI)
        houses = ephem.calculate_houses(
            jd=jd,
            latitude=lat,
            longitude=lon,
            house_system=HouseSystem.PLACIDUS,
        )
        sid_asc = (houses.ascendant - ayan_val) % 360.0
        bhavas = VedicHouseCalculator.analyze_bhavas(
            lagna_longitude=sid_asc,
            planets=planets,
        )
        lagna_rashi_idx = int(sid_asc // 30) % 12

        significations = KpSignificatorEngine.analyze_significators(
            planets=planets,
            bhavas=bhavas,
            lagna_rashi_idx=lagna_rashi_idx,
        )

        assert len(significations) >= 7
        assert "Sun" in significations
        assert "Moon" in significations

        sun_sig = significations["Sun"]
        assert isinstance(sun_sig, KpPlanetSignification)
        assert isinstance(sun_sig.level_1_houses, list)
        assert isinstance(sun_sig.level_2_houses, list)
        assert isinstance(sun_sig.level_3_houses, list)
        assert isinstance(sun_sig.level_4_houses, list)
        assert len(sun_sig.strong_houses) > 0

    def test_house_significators_inversion(self) -> None:
        """Verify inversion of planet significations into per-house significators."""
        ephem = EphemerisService()
        dt_utc = datetime(1995, 8, 20, 6, 30, 0, tzinfo=UTC)
        lat, lon = 19.0760, 72.8777  # Mumbai
        jd = ephem.datetime_to_julian_day(dt_utc)

        planets_to_calc = [
            Planet.SUN, Planet.MOON, Planet.MERCURY, Planet.VENUS,
            Planet.MARS, Planet.JUPITER, Planet.SATURN, Planet.MEAN_NODE,
        ]
        planets = [
            ephem.calculate_planet(
                jd=jd,
                planet=p,
                system=AstrologySystem.VEDIC,
                ayanamsa=Ayanamsa.KRISHNAMURTI,
            )
            for p in planets_to_calc
        ]
        ayan_val = ephem.get_ayanamsa_value(jd, Ayanamsa.KRISHNAMURTI)
        houses = ephem.calculate_houses(
            jd=jd,
            latitude=lat,
            longitude=lon,
            house_system=HouseSystem.PLACIDUS,
        )
        sid_asc = (houses.ascendant - ayan_val) % 360.0
        bhavas = VedicHouseCalculator.analyze_bhavas(
            lagna_longitude=sid_asc,
            planets=planets,
        )
        lagna_rashi_idx = int(sid_asc // 30) % 12

        significations = KpSignificatorEngine.analyze_significators(
            planets=planets,
            bhavas=bhavas,
            lagna_rashi_idx=lagna_rashi_idx,
        )

        house_sigs = KpSignificatorEngine.get_house_significators(significations)
        assert len(house_sigs) == 12
        for h in range(1, 13):
            hs = house_sigs[h]
            assert isinstance(hs, KpHouseSignificators)
            assert hs.house_number == h
            assert isinstance(hs.all_significators, list)
