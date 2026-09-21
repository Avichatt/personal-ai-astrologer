"""Tests for aspect calculations, applying/separating detection, and geometric patterns."""

from app.astrology.ephemeris import PlanetPosition
from app.astrology.western.aspects import AspectCalculator
from app.config.constants import AspectType


def test_angular_distance_calculation():
    assert AspectCalculator.calculate_angular_distance(10.0, 20.0) == 10.0
    assert AspectCalculator.calculate_angular_distance(350.0, 10.0) == 20.0
    assert AspectCalculator.calculate_angular_distance(10.0, 350.0) == 20.0
    assert AspectCalculator.calculate_angular_distance(0.0, 180.0) == 180.0
    assert AspectCalculator.calculate_angular_distance(0.0, 270.0) == 90.0


def test_aspect_detection_trine_and_opposition():
    # Sun at 0° Aries, Moon at 120° Leo (exact trine), Mars at 180° Libra (exact opp)
    p1 = PlanetPosition(0, "Sun", 0.0, 0.0, 1.0, 0.98, False, 0, "Aries", 0.0)
    p2 = PlanetPosition(1, "Moon", 120.0, 0.0, 0.002, 13.2, False, 4, "Leo", 0.0)
    p3 = PlanetPosition(4, "Mars", 180.0, 0.0, 1.5, 0.5, False, 6, "Libra", 0.0)

    aspects = AspectCalculator.calculate_aspects([p1, p2, p3])
    aspect_types = [a.aspect_type for a in aspects]

    assert AspectType.TRINE in aspect_types
    assert AspectType.OPPOSITION in aspect_types
    assert AspectType.SEXTILE in aspect_types  # Moon 120° vs Mars 180° = 60°


def test_stellium_pattern_detection():
    # 3 planets in Capricorn (Sign index 9)
    p1 = PlanetPosition(0, "Sun", 280.0, 0.0, 1.0, 1.0, False, 9, "Capricorn", 10.0)
    p2 = PlanetPosition(2, "Mercury", 285.0, 0.0, 1.0, 1.2, False, 9, "Capricorn", 15.0)
    p3 = PlanetPosition(3, "Venus", 290.0, 0.0, 1.0, 1.1, False, 9, "Capricorn", 20.0)

    aspects = AspectCalculator.calculate_aspects([p1, p2, p3])
    patterns = AspectCalculator.detect_patterns([p1, p2, p3], aspects)

    stelliums = [pt for pt in patterns if pt.pattern_type == "stellium"]
    assert len(stelliums) >= 1
    assert stelliums[0].element_or_modality == "Capricorn"
