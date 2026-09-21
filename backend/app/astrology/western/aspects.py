"""Western astrology aspect calculations, orb evaluation, and pattern detection."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from app.astrology.ephemeris import PlanetPosition
from app.config.constants import ASPECT_ANGLES, DEFAULT_ORBS, AspectType


@dataclass(frozen=True)
class AspectInfo:
    """Detailed planetary aspect representation."""

    planet_1: str
    planet_2: str
    aspect_type: AspectType
    angle: float  # Exact target angle (e.g. 120.0 for trine)
    actual_angle: float  # Actual shortest angular distance [0, 180]
    orb: float  # Absolute difference from exact angle
    max_orb: float  # Configured max orb threshold
    is_applying: bool  # True if aspect is tightening, False if separating
    is_major: bool  # Conjunction, Sextile, Square, Trine, Opposition


@dataclass(frozen=True)
class AspectPattern:
    """Detected geometric astrological configuration."""

    pattern_type: str  # e.g. "grand_trine", "t_square", "grand_cross", "yod", "stellium"
    planets: list[str]
    element_or_modality: str | None
    description: str


class AspectCalculator:
    """Comprehensive engine for aspect computation, orb evaluation, and pattern detection."""

    MAJOR_ASPECTS = {
        AspectType.CONJUNCTION,
        AspectType.SEXTILE,
        AspectType.SQUARE,
        AspectType.TRINE,
        AspectType.OPPOSITION,
    }

    @staticmethod
    def calculate_angular_distance(lon1: float, lon2: float) -> float:
        """Calculate shortest distance between two points on the 360° circle [0, 180]."""
        diff = abs((lon1 % 360.0) - (lon2 % 360.0))
        if diff > 180.0:
            diff = 360.0 - diff
        return diff

    @classmethod
    def is_aspect_applying(
        cls,
        p1: PlanetPosition,
        p2: PlanetPosition,
        target_angle: float,
    ) -> bool:
        """
        Determine if the aspect between p1 and p2 is applying (tightening) or separating.

        Evaluates the rate of change of distance based on longitudinal speeds.
        """
        curr_dist = cls.calculate_angular_distance(p1.longitude, p2.longitude)
        # Advance positions by 0.1 day using speed_longitude
        next_lon1 = (p1.longitude + p1.speed_longitude * 0.1) % 360.0
        next_lon2 = (p2.longitude + p2.speed_longitude * 0.1) % 360.0
        next_dist = cls.calculate_angular_distance(next_lon1, next_lon2)

        curr_orb = abs(curr_dist - target_angle)
        next_orb = abs(next_dist - target_angle)

        return next_orb < curr_orb

    @classmethod
    def calculate_aspects(
        cls,
        planets: list[PlanetPosition],
        custom_orbs: dict[AspectType, float] | None = None,
        include_minor: bool = True,
    ) -> list[AspectInfo]:
        """
        Compute all active aspects between every pair of celestial bodies.
        """
        orbs = custom_orbs or DEFAULT_ORBS
        aspects: list[AspectInfo] = []

        for p1, p2 in combinations(planets, 2):
            actual_dist = cls.calculate_angular_distance(p1.longitude, p2.longitude)

            for aspect_type, target_angle in ASPECT_ANGLES.items():
                if not include_minor and aspect_type not in cls.MAJOR_ASPECTS:
                    continue

                max_orb = orbs.get(aspect_type, 6.0)

                # Expand orb slightly for luminaries (Sun and Moon)
                if p1.name in ("Sun", "Moon") or p2.name in ("Sun", "Moon"):
                    max_orb += 2.0

                orb = abs(actual_dist - target_angle)
                if orb <= max_orb:
                    is_applying = cls.is_aspect_applying(p1, p2, target_angle)
                    aspects.append(
                        AspectInfo(
                            planet_1=p1.name,
                            planet_2=p2.name,
                            aspect_type=aspect_type,
                            angle=target_angle,
                            actual_angle=round(actual_dist, 4),
                            orb=round(orb, 4),
                            max_orb=round(max_orb, 2),
                            is_applying=is_applying,
                            is_major=aspect_type in cls.MAJOR_ASPECTS,
                        )
                    )

        # Sort aspects by orb (tightest first)
        aspects.sort(key=lambda a: a.orb)
        return aspects

    @classmethod
    def detect_patterns(
        cls,
        planets: list[PlanetPosition],
        aspects: list[AspectInfo],
    ) -> list[AspectPattern]:
        """Detect major geometric aspect configurations in the chart."""
        patterns: list[AspectPattern] = []

        # Build aspect lookup: (p1, p2) -> set of AspectType
        aspect_dict: dict[tuple[str, str], AspectType] = {}
        for a in aspects:
            pair = tuple(sorted([a.planet_1, a.planet_2]))
            aspect_dict[pair] = a.aspect_type

        def has_aspect(p_a: str, p_b: str, a_type: AspectType) -> bool:
            return aspect_dict.get(tuple(sorted([p_a, p_b]))) == a_type

        # 1. Stelliums: 3 or more planets in the same sign or conjunct within ~8°
        sign_groups: dict[str, list[str]] = {}
        for p in planets:
            sign_groups.setdefault(p.sign_name, []).append(p.name)
        for sign_name, group in sign_groups.items():
            if len(group) >= 3:
                patterns.append(
                    AspectPattern(
                        pattern_type="stellium",
                        planets=sorted(group),
                        element_or_modality=sign_name,
                        description=f"Stellium of {len(group)} planets clustered in {sign_name}.",
                    )
                )

        planet_names = [
            p.name for p in planets if p.name not in ("North Node", "True Node", "Ketu")
        ]

        # 2. Grand Trines: 3 planets forming mutually 3 trines (120°)
        for trio in combinations(planet_names, 3):
            p1, p2, p3 = trio
            if (
                has_aspect(p1, p2, AspectType.TRINE)
                and has_aspect(p2, p3, AspectType.TRINE)
                and has_aspect(p1, p3, AspectType.TRINE)
            ):
                patterns.append(
                    AspectPattern(
                        pattern_type="grand_trine",
                        planets=sorted(trio),
                        element_or_modality=None,
                        description=f"Grand Trine harmonizing {p1}, {p2}, and {p3}.",
                    )
                )

        # 3. T-Squares: 2 planets in opposition (180°), both squaring (90°) a 3rd apex planet
        for trio in combinations(planet_names, 3):
            for apex in trio:
                opp_pair = [p for p in trio if p != apex]
                p_a, p_b = opp_pair[0], opp_pair[1]
                if (
                    has_aspect(p_a, p_b, AspectType.OPPOSITION)
                    and has_aspect(apex, p_a, AspectType.SQUARE)
                    and has_aspect(apex, p_b, AspectType.SQUARE)
                ):
                    patterns.append(
                        AspectPattern(
                            pattern_type="t_square",
                            planets=[apex, p_a, p_b],
                            element_or_modality=None,
                            description=f"T-Square with {apex} as the focal apex squaring the {p_a}-{p_b} opposition.",
                        )
                    )

        # 4. Grand Cross: 4 planets forming 4 squares and 2 oppositions
        for quartet in combinations(planet_names, 4):
            # Check for 2 distinct oppositions
            opps = [
                (p1, p2)
                for p1, p2 in combinations(quartet, 2)
                if has_aspect(p1, p2, AspectType.OPPOSITION)
            ]
            if len(opps) == 2:
                # Check that all cross pairs are squares
                p1, p2 = opps[0]
                p3, p4 = opps[1]
                if (
                    has_aspect(p1, p3, AspectType.SQUARE)
                    and has_aspect(p1, p4, AspectType.SQUARE)
                    and has_aspect(p2, p3, AspectType.SQUARE)
                    and has_aspect(p2, p4, AspectType.SQUARE)
                ):
                    patterns.append(
                        AspectPattern(
                            pattern_type="grand_cross",
                            planets=sorted(quartet),
                            element_or_modality=None,
                            description=f"Grand Cross tension pattern between {', '.join(sorted(quartet))}.",
                        )
                    )

        # 5. Yod (Finger of God): 2 planets in sextile (60°), both quincunx (150°) a focal apex planet
        for trio in combinations(planet_names, 3):
            for apex in trio:
                base_pair = [p for p in trio if p != apex]
                p_a, p_b = base_pair[0], base_pair[1]
                if (
                    has_aspect(p_a, p_b, AspectType.SEXTILE)
                    and has_aspect(apex, p_a, AspectType.QUINCUNX)
                    and has_aspect(apex, p_b, AspectType.QUINCUNX)
                ):
                    patterns.append(
                        AspectPattern(
                            pattern_type="yod",
                            planets=[apex, p_a, p_b],
                            element_or_modality=None,
                            description=f"Yod (Finger of Fate) focusing destiny point on {apex} supported by {p_a}-{p_b} sextile.",
                        )
                    )

        return patterns
