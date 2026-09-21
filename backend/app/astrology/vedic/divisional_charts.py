"""Vedic Divisional Charts (Varga) Engine: D1, D2, D3, D7, D9, D10, D12, D60."""

from __future__ import annotations

from dataclasses import asdict, dataclass

from app.astrology.ephemeris import PlanetPosition
from app.config.constants import RASHI_NAMES, Sign


@dataclass(frozen=True)
class VargaPlacement:
    """A planet or point placement inside a specific divisional chart."""

    point_name: str
    sign_index: int  # 0 = Mesha .. 11 = Meena
    sign_name: str
    degree_in_varga: float


@dataclass(frozen=True)
class DivisionalChartResult:
    """Representation of a full divisional chart (e.g. D9 Navamsha)."""

    division_number: int  # 1, 2, 3, 7, 9, 10, 12, 60
    name: str  # e.g. "D9 Navamsha"
    significance: str  # e.g. "Spouse, Dharma, Destiny"
    ascendant: VargaPlacement
    placements: list[VargaPlacement]

    def to_dict(self) -> dict:
        return {
            "division_number": self.division_number,
            "name": self.name,
            "significance": self.significance,
            "ascendant": asdict(self.ascendant),
            "placements": [asdict(p) for p in self.placements],
        }


class DivisionalChartEngine:
    """Calculates classical Parashari Divisional Charts (Vargas)."""

    @staticmethod
    def calculate_d1_rashi(longitude: float) -> tuple[int, float]:
        """D1 Rashi (Division 1: 30° per sign)."""
        sign_idx = int(longitude // 30) % 12
        deg = longitude % 30.0
        return sign_idx, deg

    @staticmethod
    def calculate_d2_hora(longitude: float) -> tuple[int, float]:
        """
        D2 Hora (Division 2: 15° each).
        Odd signs (Aries, Gemini, Leo, etc.): 1st half = Sun (Leo=4), 2nd half = Moon (Cancer=3).
        Even signs: 1st half = Moon (Cancer=3), 2nd half = Sun (Leo=4).
        """
        sign_idx = int(longitude // 30) % 12
        deg_in_sign = longitude % 30.0
        is_odd_sign = sign_idx % 2 == 0  # 0=Aries (odd), 1=Taurus (even)

        if deg_in_sign < 15.0:
            hora_sign = 4 if is_odd_sign else 3
            hora_deg = deg_in_sign * 2.0
        else:
            hora_sign = 3 if is_odd_sign else 4
            hora_deg = (deg_in_sign - 15.0) * 2.0

        return hora_sign, hora_deg

    @staticmethod
    def calculate_d3_drekkana(longitude: float) -> tuple[int, float]:
        """
        D3 Drekkana (Division 3: 10° each).
        1st part (0-10°): Same sign (1st)
        2nd part (10-20°): 5th sign from it
        3rd part (20-30°): 9th sign from it
        """
        sign_idx = int(longitude // 30) % 12
        deg_in_sign = longitude % 30.0
        part = int(deg_in_sign // 10)

        offset = 0 if part == 0 else (4 if part == 1 else 8)
        d3_sign = (sign_idx + offset) % 12
        d3_deg = (deg_in_sign % 10.0) * 3.0
        return d3_sign, d3_deg

    @staticmethod
    def calculate_d7_saptamsha(longitude: float) -> tuple[int, float]:
        """
        D7 Saptamsha (Division 7: 4°17'8.57" = 30/7 degrees each).
        Odd signs count from the sign itself. Even signs count from the 7th sign from it.
        """
        sign_idx = int(longitude // 30) % 12
        deg_in_sign = longitude % 30.0
        span = 30.0 / 7.0
        part = min(int(deg_in_sign // span), 6)

        is_odd_sign = sign_idx % 2 == 0
        start_sign = sign_idx if is_odd_sign else (sign_idx + 6) % 12
        d7_sign = (start_sign + part) % 12
        d7_deg = (deg_in_sign - (part * span)) * 7.0
        return d7_sign, d7_deg

    @staticmethod
    def calculate_d9_navamsha(longitude: float) -> tuple[int, float]:
        """
        D9 Navamsha (Division 9: 3°20' = 3.3333333° each).
        Fire signs (Aries, Leo, Sag) start from Aries (0).
        Earth signs (Taurus, Virgo, Cap) start from Capricorn (9).
        Air signs (Gemini, Libra, Aqua) start from Libra (6).
        Water signs (Cancer, Scorpio, Pisces) start from Cancer (3).
        """
        sign_idx = int(longitude // 30) % 12
        deg_in_sign = longitude % 30.0
        span = 30.0 / 9.0  # 3.33333333°
        part = min(int(deg_in_sign // span), 8)

        element = sign_idx % 4  # 0=Fire, 1=Earth, 2=Air, 3=Water
        start_sign_map = {0: 0, 1: 9, 2: 6, 3: 3}
        start_sign = start_sign_map[element]

        d9_sign = (start_sign + part) % 12
        d9_deg = (deg_in_sign - (part * span)) * 9.0
        return d9_sign, d9_deg

    @staticmethod
    def calculate_d10_dashamsha(longitude: float) -> tuple[int, float]:
        """
        D10 Dashamsha (Division 10: 3° each).
        Odd signs start from the sign itself. Even signs start from the 9th sign from it.
        """
        sign_idx = int(longitude // 30) % 12
        deg_in_sign = longitude % 30.0
        part = min(int(deg_in_sign // 3.0), 9)

        is_odd_sign = sign_idx % 2 == 0
        start_sign = sign_idx if is_odd_sign else (sign_idx + 8) % 12
        d10_sign = (start_sign + part) % 12
        d10_deg = (deg_in_sign % 3.0) * 10.0
        return d10_sign, d10_deg

    @staticmethod
    def calculate_d12_dwadashamsha(longitude: float) -> tuple[int, float]:
        """
        D12 Dwadashamsha (Division 12: 2°30' = 2.5° each).
        Always starts from the sign itself and counts consecutively.
        """
        sign_idx = int(longitude // 30) % 12
        deg_in_sign = longitude % 30.0
        part = min(int(deg_in_sign // 2.5), 11)

        d12_sign = (sign_idx + part) % 12
        d12_deg = (deg_in_sign % 2.5) * 12.0
        return d12_sign, d12_deg

    @staticmethod
    def calculate_d60_shashtiamsha(longitude: float) -> tuple[int, float]:
        """
        D60 Shashtiamsha (Division 60: 0°30' = 0.5° each).
        Starts from the sign itself and cycles continuously.
        """
        sign_idx = int(longitude // 30) % 12
        deg_in_sign = longitude % 30.0
        part = min(int(deg_in_sign // 0.5), 59)

        d60_sign = (sign_idx + part) % 12
        d60_deg = (deg_in_sign % 0.5) * 60.0
        return d60_sign, d60_deg

    @classmethod
    def generate_divisional_chart(
        cls,
        division: int,
        ascendant_lon: float,
        planets: list[PlanetPosition],
    ) -> DivisionalChartResult:
        """
        Construct complete divisional chart for any standard division.
        """
        calc_methods = {
            1: (cls.calculate_d1_rashi, "D1 Rashi", "Physical Body, Vitality, General Life"),
            2: (cls.calculate_d2_hora, "D2 Hora", "Wealth, Financial Prosperity, Family Resources"),
            3: (
                cls.calculate_d3_drekkana,
                "D3 Drekkana",
                "Siblings, Courage, Vitality, Enterprise",
            ),
            7: (cls.calculate_d7_saptamsha, "D7 Saptamsha", "Children, Progeny, Creativity"),
            9: (
                cls.calculate_d9_navamsha,
                "D9 Navamsha",
                "Spouse, Dharma, Inner Strength, Destiny",
            ),
            10: (
                cls.calculate_d10_dashamsha,
                "D10 Dashamsha",
                "Career, Profession, Social Status, Power",
            ),
            12: (
                cls.calculate_d12_dwadashamsha,
                "D12 Dwadashamsha",
                "Parents, Lineage, Ancestral Karma",
            ),
            60: (
                cls.calculate_d60_shashtiamsha,
                "D60 Shashtiamsha",
                "Subtle Karma, Past Life Imprints",
            ),
        }

        func, name, sig = calc_methods.get(
            division, (cls.calculate_d1_rashi, f"D{division} Varga", "Divisional Chart Analysis")
        )

        asc_sign_idx, asc_deg = func(ascendant_lon)
        asc_placement = VargaPlacement(
            point_name="Ascendant (Lagna)",
            sign_index=asc_sign_idx,
            sign_name=RASHI_NAMES[Sign(asc_sign_idx)],
            degree_in_varga=round(asc_deg, 4),
        )

        placements: list[VargaPlacement] = []
        for p in planets:
            p_sign_idx, p_deg = func(p.longitude)
            p_name = "Rahu" if p.name in ("North Node", "True Node") else p.name
            placements.append(
                VargaPlacement(
                    point_name=p_name,
                    sign_index=p_sign_idx,
                    sign_name=RASHI_NAMES[Sign(p_sign_idx)],
                    degree_in_varga=round(p_deg, 4),
                )
            )

        return DivisionalChartResult(
            division_number=division,
            name=name,
            significance=sig,
            ascendant=asc_placement,
            placements=placements,
        )
