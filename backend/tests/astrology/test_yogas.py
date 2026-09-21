"""Tests for Vedic Yoga and Dosha detection engine."""

from app.astrology.ephemeris import PlanetPosition
from app.astrology.vedic.houses import VedicHouseCalculator
from app.astrology.vedic.rashis import PlanetaryDignity
from app.astrology.vedic.yogas import VedicYogaEngine


def test_gajakesari_and_budhaditya_yoga_detection():
    # Lagna at 0° Aries
    # Moon in 1st house (0° Aries), Jupiter in 4th house (Cancer 95° - Exalted)
    # Sun and Mercury both in 10th house (Capricorn 275°)
    planets = [
        PlanetPosition(0, "Sun", 275.0, 0.0, 1.0, 1.0, False, 9, "Capricorn", 5.0),
        PlanetPosition(1, "Moon", 5.0, 0.0, 0.002, 13.0, False, 0, "Aries", 5.0),
        PlanetPosition(2, "Mercury", 280.0, 0.0, 1.0, 1.2, False, 9, "Capricorn", 10.0),
        PlanetPosition(5, "Jupiter", 95.0, 0.0, 5.0, 0.1, False, 3, "Cancer", 5.0),
    ]

    bhavas = VedicHouseCalculator.analyze_bhavas(0.0, planets)
    dignities = {
        "Sun": PlanetaryDignity.FRIEND,
        "Moon": PlanetaryDignity.OWN_SIGN,
        "Mercury": PlanetaryDignity.NEUTRAL,
        "Jupiter": PlanetaryDignity.EXALTED,
    }

    yogas = VedicYogaEngine.detect_yogas(
        lagna_longitude=0.0,
        planets=planets,
        bhavas=bhavas,
        dignities=dignities,
    )

    yoga_names = [y.name for y in yogas]
    assert "Gajakesari Yoga" in yoga_names
    assert "Budhaditya Yoga" in yoga_names
    assert "Hamsa Yoga" in yoga_names  # Jupiter exalted in 4th (Kendra) = Hamsa Mahapurusha Yoga!
