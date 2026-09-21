"""AI Interpretation Service for Personal AI Astrologer.

Takes calculated astrological chart data (planets, bhavas, yogas, dashas, transits)
and produces high-precision, structured horoscope analyses with Parashari deductions,
concrete timelines, and full birth-to-death life blueprints matching professional world-class standards.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import re
from typing import Any

import structlog

from app.astrology.vedic.antardasha import DashaPeriod, DashaTreeBuilder
from app.astrology.vedic.dashas import MahadashaPeriod, VimshottariDashaEngine
from app.config.constants import AstrologySystem
from app.config.settings import get_settings
from app.schemas.analysis import (
    AnalysisFocus,
    GemstoneRecommendation,
    HoroscopeAnalysisResponse,
    HoroscopeSection,
    LifeStage,
    SpiritualRemedy,
    TimelineItem,
)

logger = structlog.get_logger(__name__)

# Catalog of Vedic Gemstones with wearing protocol
GEMSTONE_CATALOG: dict[str, dict[str, str]] = {
    "Sun": {
        "gemstone": "Ruby",
        "sanskrit_name": "Manikya",
        "metal": "Gold or Copper",
        "finger": "Ring finger of right hand",
        "auspicious_day": "Sunday morning at sunrise",
        "consecration_mantra": "Om Hram Hreem Hroum Sah Suryaya Namah (108 times)",
    },
    "Moon": {
        "gemstone": "Natural Pearl",
        "sanskrit_name": "Moti",
        "metal": "Silver",
        "finger": "Little finger of right hand",
        "auspicious_day": "Monday evening",
        "consecration_mantra": "Om Shram Shreem Shroum Sah Chandraya Namah (108 times)",
    },
    "Mars": {
        "gemstone": "Red Coral",
        "sanskrit_name": "Moonga",
        "metal": "Copper, Silver, or Gold",
        "finger": "Ring finger of right hand",
        "auspicious_day": "Tuesday morning during Shukla Paksha",
        "consecration_mantra": "Om Kram Kreem Kroum Sah Bhaumaya Namah (108 times)",
    },
    "Mercury": {
        "gemstone": "Emerald",
        "sanskrit_name": "Panna",
        "metal": "Gold, Bronze, or Silver",
        "finger": "Little finger of right hand",
        "auspicious_day": "Wednesday morning",
        "consecration_mantra": "Om Bram Breem Broum Sah Budhaya Namah (108 times)",
    },
    "Jupiter": {
        "gemstone": "Yellow Sapphire",
        "sanskrit_name": "Pukhraj",
        "metal": "Gold or Brass",
        "finger": "Index finger of right hand",
        "auspicious_day": "Thursday morning during Shukla Paksha",
        "consecration_mantra": "Om Gram Greem Groum Sah Gurave Namah (108 times)",
    },
    "Venus": {
        "gemstone": "Diamond or White Sapphire",
        "sanskrit_name": "Heera / Safed Pukhraj",
        "metal": "Platinum, White Gold, or Silver",
        "finger": "Middle or Little finger of right hand",
        "auspicious_day": "Friday morning",
        "consecration_mantra": "Om Dram Dreem Droum Sah Shukraya Namah (108 times)",
    },
    "Saturn": {
        "gemstone": "Blue Sapphire",
        "sanskrit_name": "Neelam",
        "metal": "Panchdhatu, Iron, or Silver",
        "finger": "Middle finger of right hand",
        "auspicious_day": "Saturday evening after sunset",
        "consecration_mantra": "Om Pram Preem Proum Sah Shanaischaraya Namah (108 times)",
    },
    "Rahu": {
        "gemstone": "Hessonite Garnet",
        "sanskrit_name": "Gomed",
        "metal": "Silver or Panchdhatu",
        "finger": "Middle finger",
        "auspicious_day": "Saturday night",
        "consecration_mantra": "Om Bhram Bhreem Bhroum Sah Rahave Namah (108 times)",
    },
    "Ketu": {
        "gemstone": "Cat's Eye",
        "sanskrit_name": "Lehsuniya",
        "metal": "Silver",
        "finger": "Ring or Little finger",
        "auspicious_day": "Thursday or Tuesday night",
        "consecration_mantra": "Om Sram Sreem Sroum Sah Ketave Namah (108 times)",
    },
}

# Sign name mapping for both Vedic (Sanskrit) and Western names
RASHI_TO_INDEX: dict[str, int] = {
    "Mesha": 0, "Aries": 0,
    "Vrishabha": 1, "Taurus": 1,
    "Mithuna": 2, "Gemini": 2,
    "Karka": 3, "Cancer": 3,
    "Simha": 4, "Leo": 4,
    "Kanya": 5, "Virgo": 5,
    "Tula": 6, "Libra": 6,
    "Vrishchika": 7, "Scorpio": 7,
    "Dhanu": 8, "Sagittarius": 8,
    "Makara": 9, "Capricorn": 9,
    "Kumbha": 10, "Aquarius": 10,
    "Meena": 11, "Pisces": 11,
}

INDEX_TO_VEDIC_RASHI: dict[int, str] = {
    0: "Mesha", 1: "Vrishabha", 2: "Mithuna", 3: "Karka",
    4: "Simha", 5: "Kanya", 6: "Tula", 7: "Vrishchika",
    8: "Dhanu", 9: "Makara", 10: "Kumbha", 11: "Meena",
}

# Parashari Functional Benefics, Malefics, and Contraindications by Lagna Index
LAGNA_CONFIG: dict[int, dict[str, Any]] = {
    0: {  # Mesha
        "lagna_lord": "Mars",
        "9th_lord": "Jupiter",
        "5th_lord": "Sun",
        "benefics": ["Mars", "Sun", "Jupiter"],
        "malefics": ["Mercury", "Venus", "Saturn"],
        "contraindicated": [
            ("Emerald", "Panna", "Mercury", "Rules 3rd & 6th (Dusthana) houses; enemy to Lagna lord Mars"),
            ("Diamond", "Heera", "Venus", "Rules 2nd & 7th (Maraka) houses; strongly inimical to Lagna lord"),
        ],
    },
    1: {  # Vrishabha
        "lagna_lord": "Venus",
        "9th_lord": "Saturn",
        "5th_lord": "Mercury",
        "benefics": ["Venus", "Saturn", "Mercury"],
        "malefics": ["Jupiter", "Mars", "Moon"],
        "contraindicated": [
            ("Yellow Sapphire", "Pukhraj", "Jupiter", "Rules 8th & 11th houses; primary enemy to Venus"),
            ("Red Coral", "Moonga", "Mars", "Rules 7th (Maraka) & 12th (Loss) houses"),
        ],
    },
    2: {  # Mithuna
        "lagna_lord": "Mercury",
        "9th_lord": "Saturn",
        "5th_lord": "Venus",
        "benefics": ["Mercury", "Venus"],
        "malefics": ["Mars", "Jupiter", "Sun"],
        "contraindicated": [
            ("Red Coral", "Moonga", "Mars", "Rules 6th & 11th houses; functional malefic for Gemini"),
            ("Yellow Sapphire", "Pukhraj", "Jupiter", "Suffers Kendradhipati and Badhaka dosha for dual sign"),
        ],
    },
    3: {  # Karka
        "lagna_lord": "Moon",
        "9th_lord": "Jupiter",
        "5th_lord": "Mars",
        "benefics": ["Moon", "Mars", "Jupiter"],
        "malefics": ["Saturn", "Mercury", "Venus"],
        "contraindicated": [
            ("Blue Sapphire", "Neelam", "Saturn", "Rules 7th (Maraka) & 8th (Dusthana) houses; enemy to Moon"),
            ("Emerald", "Panna", "Mercury", "Rules 3rd & 12th (Vyaya) houses"),
        ],
    },
    4: {  # Simha
        "lagna_lord": "Sun",
        "9th_lord": "Mars",
        "5th_lord": "Jupiter",
        "benefics": ["Sun", "Mars", "Jupiter"],
        "malefics": ["Saturn", "Venus", "Mercury"],
        "contraindicated": [
            ("Blue Sapphire", "Neelam", "Saturn", "Rules 6th & 7th (Maraka) houses; arch-enemy to Sun"),
            ("Diamond", "Heera", "Venus", "Rules 3rd & 10th houses; inimical to Sun"),
        ],
    },
    5: {  # Kanya
        "lagna_lord": "Mercury",
        "9th_lord": "Venus",
        "5th_lord": "Saturn",
        "benefics": ["Mercury", "Venus", "Saturn"],
        "malefics": ["Mars", "Jupiter", "Moon"],
        "contraindicated": [
            ("Red Coral", "Moonga", "Mars", "Rules 3rd & 8th (Dusthana) houses; dangerous malefic for Virgo"),
            ("Yellow Sapphire", "Pukhraj", "Jupiter", "Suffers Kendradhipati and Maraka dosha (4th/7th lord)"),
        ],
    },
    6: {  # Tula
        "lagna_lord": "Venus",
        "9th_lord": "Mercury",
        "5th_lord": "Saturn",
        "benefics": ["Venus", "Saturn", "Mercury"],
        "malefics": ["Jupiter", "Mars", "Sun"],
        "contraindicated": [
            ("Yellow Sapphire", "Pukhraj", "Jupiter", "Rules 3rd & 6th (Dusthana) houses; inimical to Venus"),
            ("Ruby", "Manikya", "Sun", "Rules 11th house (Badhaka for movable sign)"),
        ],
    },
    7: {  # Vrishchika
        "lagna_lord": "Mars",
        "9th_lord": "Moon",
        "5th_lord": "Jupiter",
        "benefics": ["Mars", "Jupiter", "Moon"],
        "malefics": ["Mercury", "Venus"],
        "contraindicated": [
            ("Emerald", "Panna", "Mercury", "Rules 8th & 11th houses; primary obstacle planet for Scorpio"),
            ("Diamond", "Heera", "Venus", "Rules 7th (Maraka) & 12th (Loss) houses"),
        ],
    },
    8: {  # Dhanu
        "lagna_lord": "Jupiter",
        "9th_lord": "Sun",
        "5th_lord": "Mars",
        "benefics": ["Jupiter", "Sun", "Mars"],
        "malefics": ["Venus", "Mercury", "Saturn"],
        "contraindicated": [
            ("Diamond", "Heera", "Venus", "Rules 6th (Disease) & 11th houses; supreme enemy to Jupiter"),
            ("Emerald", "Panna", "Mercury", "Rules 7th (Maraka) & 10th houses (Badhaka)"),
        ],
    },
    9: {  # Makara
        "lagna_lord": "Saturn",
        "9th_lord": "Mercury",
        "5th_lord": "Venus",
        "benefics": ["Saturn", "Venus", "Mercury"],
        "malefics": ["Mars", "Jupiter", "Moon"],
        "contraindicated": [
            ("Yellow Sapphire", "Pukhraj", "Jupiter", "Rules 3rd & 12th (Vyaya) houses"),
            ("Ruby", "Manikya", "Sun", "Rules 8th (Randhra) house; bitter enemy to Saturn"),
        ],
    },
    10: {  # Kumbha
        "lagna_lord": "Saturn",
        "9th_lord": "Venus",
        "5th_lord": "Mercury",
        "benefics": ["Saturn", "Venus", "Mercury"],
        "malefics": ["Jupiter", "Mars", "Moon"],
        "contraindicated": [
            ("Yellow Sapphire", "Pukhraj", "Jupiter", "Rules 2nd (Maraka) & 11th houses"),
            ("Pearl", "Moti", "Moon", "Rules 6th (Roga/Rina) house"),
        ],
    },
    11: {  # Meena
        "lagna_lord": "Jupiter",
        "9th_lord": "Mars",
        "5th_lord": "Moon",
        "benefics": ["Jupiter", "Moon", "Mars"],
        "malefics": ["Venus", "Saturn", "Sun", "Mercury"],
        "contraindicated": [
            ("Diamond", "Heera", "Venus", "Rules 3rd & 8th (Dusthana) houses; supreme enemy to Jupiter"),
            ("Blue Sapphire", "Neelam", "Saturn", "Rules 11th & 12th (Vyaya) houses"),
        ],
    },
}


class AstroInterpretationService:
    """Orchestrates chart analysis via Gemini AI or classical rule-based fallback."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_analysis(
        self,
        chart_dict: dict[str, Any],
        focus: AnalysisFocus = AnalysisFocus.CAREER,
        target_date: datetime | None = None,
        name: str = "Native",
        system: AstrologySystem = AstrologySystem.VEDIC,
        language: str = "en",
    ) -> HoroscopeAnalysisResponse:
        """Generate structured horoscope reading from calculated chart data."""
        target_utc = (
            target_date.replace(tzinfo=UTC)
            if target_date and target_date.tzinfo is None
            else (target_date.astimezone(UTC) if target_date else datetime.now(UTC))
        )

        # Extract core identifiers
        birth_str = chart_dict.get("datetime_utc", "")
        ascendant = (
            chart_dict.get("ascendant_rashi")
            or chart_dict.get("ascendant_sign")
            or "Mesha"
        )

        # Moon and Sun positions
        planets_data = chart_dict.get("planets", {})
        grahas_list = chart_dict.get("grahas", [])

        sun_sign = "Aries"
        moon_sign = "Aries"
        moon_lon = 0.0

        if grahas_list:
            for g in grahas_list:
                wname = g.get("western_name") or g.get("name")
                if wname == "Sun":
                    sun_sign = g.get("rashi_name") or g.get("sign_name") or "Mesha"
                elif wname == "Moon":
                    moon_sign = g.get("rashi_name") or g.get("sign_name") or "Mesha"
                    moon_lon = float(g.get("longitude", 0.0))
        elif planets_data:
            sun_p = planets_data.get("Sun", {})
            moon_p = planets_data.get("Moon", {})
            sun_sign = sun_p.get("rashi_name") or sun_p.get("sign_name") or "Aries"
            moon_sign = moon_p.get("rashi_name") or moon_p.get("sign_name") or "Aries"
            moon_lon = float(moon_p.get("longitude", 0.0))

        # Dasha calculation across 120-year cycle
        active_dasha_info = None
        upcoming_antardashas: list[DashaPeriod] = []
        all_mahadashas: list[MahadashaPeriod] = []
        birth_dt = datetime.now(UTC)
        curr_maha = None
        curr_antar = None
        curr_prat = None

        if system in (AstrologySystem.VEDIC, AstrologySystem.KP) and moon_lon > 0 and birth_str:
            try:
                birth_dt = datetime.fromisoformat(birth_str).replace(tzinfo=UTC)
                active_dasha = DashaTreeBuilder.find_active_dasha(
                    moon_sidereal_lon=moon_lon,
                    birth_utc=birth_dt,
                    target_utc=target_utc,
                )
                curr_maha = active_dasha.mahadasha
                curr_antar = active_dasha.antardasha
                curr_prat = active_dasha.pratyantardasha
                active_dasha_info = active_dasha

                # Full 120-year cycle
                all_mahadashas = VimshottariDashaEngine.calculate_mahadashas(
                    moon_sidereal_longitude=moon_lon,
                    birth_datetime_utc=birth_dt,
                    cycle_count=1,
                )
                current_maha_period = next(
                    (m for m in all_mahadashas if m.start_date <= target_utc < m.end_date),
                    all_mahadashas[0],
                )
                all_antardashas = DashaTreeBuilder.calculate_antardashas(current_maha_period)
                upcoming_antardashas = [
                    a for a in all_antardashas if a.end_date >= target_utc
                ][:4]
            except Exception as exc:
                logger.warning("Failed to compute dasha timeline", error=str(exc))

        # Compute Life Stages, Gemstones, and Remedies
        life_stages = self._compute_life_stages(all_mahadashas, birth_dt, ascendant)
        gemstones = self._compute_gemstones(ascendant)
        remedies = self._compute_remedies(ascendant, sun_sign, moon_sign)

        # Attempt Gemini AI interpretation if API key is present
        reading_text = ""
        engine_source = "astrological_rules_fallback"

        if self.settings.gemini_api_key and self.settings.gemini_api_key.strip():
            try:
                reading_text = self._generate_with_gemini(
                    chart_dict=chart_dict,
                    focus=focus,
                    target_utc=target_utc,
                    name=name,
                    system=system,
                    language=language,
                    active_dasha=active_dasha_info,
                    upcoming_antardashas=upcoming_antardashas,
                    life_stages=life_stages,
                    gemstones=gemstones,
                    remedies=remedies,
                )
                if reading_text:
                    engine_source = f"{self.settings.ai_provider}-{self.settings.ai_model}"
            except Exception as exc:
                logger.error("Gemini AI interpretation failed, falling back to rule engine", error=str(exc))
                reading_text = ""

        # Fallback to precision rule engine if AI is unavailable or failed
        if not reading_text:
            if focus in (AnalysisFocus.LIFE_BLUEPRINT, "life_blueprint", "full_life"):
                reading_text = self._generate_life_blueprint_reading(
                    chart_dict=chart_dict,
                    target_utc=target_utc,
                    name=name,
                    system=system,
                    ascendant=ascendant,
                    sun_sign=sun_sign,
                    moon_sign=moon_sign,
                    active_dasha=active_dasha_info,
                    life_stages=life_stages,
                    gemstones=gemstones,
                    remedies=remedies,
                )
            elif system == AstrologySystem.KP:
                reading_text = self._generate_kp_rule_based_reading(
                    chart_dict=chart_dict,
                    focus=focus,
                    target_utc=target_utc,
                    name=name,
                    active_dasha=active_dasha_info,
                    upcoming_antardashas=upcoming_antardashas,
                    ascendant=ascendant,
                    sun_sign=sun_sign,
                    moon_sign=moon_sign,
                )
            else:
                reading_text = self._generate_rule_based_reading(
                    chart_dict=chart_dict,
                    focus=focus,
                    target_utc=target_utc,
                    name=name,
                    system=system,
                    active_dasha=active_dasha_info,
                    upcoming_antardashas=upcoming_antardashas,
                    ascendant=ascendant,
                    sun_sign=sun_sign,
                    moon_sign=moon_sign,
                )

        # Parse rendered text into structured sections and timeline
        sections, timeline = self._parse_reading_to_sections(reading_text)

        return HoroscopeAnalysisResponse(
            name=name,
            focus=focus.value if hasattr(focus, "value") else str(focus),
            system=system.value,
            birth_datetime_utc=birth_str,
            target_datetime_utc=target_utc.isoformat(),
            ascendant=ascendant,
            sun_sign=sun_sign,
            moon_sign=moon_sign,
            current_mahadasha=curr_maha,
            current_antardasha=curr_antar,
            current_pratyantardasha=curr_prat,
            sections=sections,
            timeline=timeline,
            life_stages=life_stages,
            gemstone_recommendations=gemstones,
            spiritual_remedies=remedies,
            formatted_reading=reading_text.strip(),
            engine_source=engine_source,
        )

    def _compute_gemstones(self, ascendant: str) -> list[GemstoneRecommendation]:
        """Compute authentic Vedic gemstone prescriptions based on Lagna rulership."""
        rashi_idx = RASHI_TO_INDEX.get(ascendant, 0)
        cfg = LAGNA_CONFIG.get(rashi_idx, LAGNA_CONFIG[0])

        recommendations: list[GemstoneRecommendation] = []

        # 1. Life Stone (Lagnesh)
        lagna_lord = cfg["lagna_lord"]
        l_cat = GEMSTONE_CATALOG.get(lagna_lord, GEMSTONE_CATALOG["Mars"])
        recommendations.append(
            GemstoneRecommendation(
                category="Life Stone (Jeevan Ratna)",
                gemstone=l_cat["gemstone"],
                sanskrit_name=l_cat["sanskrit_name"],
                ruling_planet=lagna_lord,
                finger=l_cat["finger"],
                metal=l_cat["metal"],
                auspicious_day=l_cat["auspicious_day"],
                consecration_mantra=l_cat["consecration_mantra"],
                rationale=f"Rules the 1st House (Lagna). Strengthens vitality, immunity, status, and life purpose.",
                is_contraindicated=False,
            )
        )

        # 2. Lucky Stone (Bhagyesh - 9th Lord)
        ninth_lord = cfg["9th_lord"]
        n_cat = GEMSTONE_CATALOG.get(ninth_lord, GEMSTONE_CATALOG["Jupiter"])
        recommendations.append(
            GemstoneRecommendation(
                category="Lucky Stone (Bhagya Ratna)",
                gemstone=n_cat["gemstone"],
                sanskrit_name=n_cat["sanskrit_name"],
                ruling_planet=ninth_lord,
                finger=n_cat["finger"],
                metal=n_cat["metal"],
                auspicious_day=n_cat["auspicious_day"],
                consecration_mantra=n_cat["consecration_mantra"],
                rationale=f"Rules the 9th House of fortune, spiritual grace, higher intellect, and destiny.",
                is_contraindicated=False,
            )
        )

        # 3. Intellect / Purva Punya Stone (Panchamesh - 5th Lord)
        fifth_lord = cfg["5th_lord"]
        if fifth_lord != lagna_lord and fifth_lord != ninth_lord:
            f_cat = GEMSTONE_CATALOG.get(fifth_lord, GEMSTONE_CATALOG["Sun"])
            recommendations.append(
                GemstoneRecommendation(
                    category="Intellect Stone (Punya Ratna)",
                    gemstone=f_cat["gemstone"],
                    sanskrit_name=f_cat["sanskrit_name"],
                    ruling_planet=fifth_lord,
                    finger=f_cat["finger"],
                    metal=f_cat["metal"],
                    auspicious_day=f_cat["auspicious_day"],
                    consecration_mantra=f_cat["consecration_mantra"],
                    rationale=f"Rules the 5th House of intellect, discretion, creativity, and past-life merits.",
                    is_contraindicated=False,
                )
            )

        # 4. Strict Contraindications
        for g_name, s_name, p_name, reason in cfg["contraindicated"]:
            c_cat = GEMSTONE_CATALOG.get(p_name, {})
            recommendations.append(
                GemstoneRecommendation(
                    category="Contraindicated (Strictly Prohibited)",
                    gemstone=g_name,
                    sanskrit_name=s_name,
                    ruling_planet=p_name,
                    finger="DO NOT WEAR",
                    metal="None",
                    auspicious_day="None",
                    consecration_mantra="None",
                    rationale=reason,
                    is_contraindicated=True,
                )
            )

        return recommendations

    def _compute_remedies(
        self, ascendant: str, sun_sign: str, moon_sign: str
    ) -> list[SpiritualRemedy]:
        """Compute spiritual, ritual, and charitable remedies tailored to chart foundations."""
        rashi_idx = RASHI_TO_INDEX.get(ascendant, 0)
        cfg = LAGNA_CONFIG.get(rashi_idx, LAGNA_CONFIG[0])
        l_lord = cfg["lagna_lord"]

        remedies: list[SpiritualRemedy] = []

        # 1. Primary Beej Mantra for Lagna Lord
        l_info = GEMSTONE_CATALOG.get(l_lord, GEMSTONE_CATALOG["Mars"])
        remedies.append(
            SpiritualRemedy(
                category="Beej Mantra",
                target_planet=l_lord,
                title=f"{l_lord} Beej Mantra (Life Force Activation)",
                description=f"Recite daily to strengthen Lagna vitality, mental clarity, and protective aura.",
                mantra_or_practice=l_info["consecration_mantra"],
                timing_or_day=l_info["auspicious_day"],
            )
        )

        # 2. Sacred Stotra
        stotra_map = {
            "Sun": ("Aditya Hridaya Stotram", "Recite on Sundays for solar radiance, courage, and career authority."),
            "Moon": ("Shiva Panchakshara Stotram / Om Namah Shivaya", "Chant on Mondays for emotional peace and mental balance."),
            "Mars": ("Hanuman Chalisa / Bajrang Baan", "Recite on Tuesdays for vanquishing obstacles, legal hurdles, and lethargy."),
            "Mercury": ("Vishnu Sahasranama Stotram", "Recite on Wednesdays for intellect, commercial prosperity, and sharp speech."),
            "Jupiter": ("Guru Paduka Stotram / Guru Stotram", "Recite on Thursdays for wisdom, higher knowledge, and auspicious blessings."),
            "Venus": ("Sri Suktam / Mahalakshmi Ashtakam", "Recite on Fridays for marital harmony, wealth, and creative grace."),
            "Saturn": ("Dasharatha Shani Stotram / Hanuman Chalisa", "Recite on Saturdays to pacify karmic debts, delays, and Sade Sati."),
        }
        s_title, s_desc = stotra_map.get(l_lord, ("Aditya Hridaya Stotram", "Chant for inner strength and vitality."))
        remedies.append(
            SpiritualRemedy(
                category="Stotra",
                target_planet=l_lord,
                title=s_title,
                description=s_desc,
                mantra_or_practice=f"Daily recitation of {s_title}",
                timing_or_day="Morning after bath",
            )
        )

        # 3. Practical Charity (Daan)
        daan_map = {
            "Sun": ("Donate wheat, jaggery, or copper vessels to temples on Sunday morning.", "Sun"),
            "Moon": ("Donate milk, rice, white clothes, or silver to elder women on Monday.", "Moon"),
            "Mars": ("Donate red lentils (masoor dal), jaggery, or blood donation on Tuesday.", "Mars"),
            "Mercury": ("Feed fresh green grass or spinach to cows; donate books/pens to needy students on Wednesday.", "Mercury"),
            "Jupiter": ("Donate yellow gram (chana dal), turmeric, or religious texts to scholars on Thursday.", "Jupiter"),
            "Venus": ("Donate white sweets, curd, ghee, or silk garments to underprivileged girls on Friday.", "Venus"),
            "Saturn": ("Donate mustard oil, black sesame seeds, or warm footwear/blankets to laborers on Saturday.", "Saturn"),
        }
        d_desc, d_planet = daan_map.get(l_lord, daan_map["Saturn"])
        remedies.append(
            SpiritualRemedy(
                category="Charity (Daan)",
                target_planet=d_planet,
                title=f"Karmic Balance Charity for {d_planet}",
                description=d_desc,
                mantra_or_practice=d_desc,
                timing_or_day="Weekly on respective planetary day",
            )
        )

        # 4. Fasting & Lifestyle (Vrat)
        vrat_days = {
            "Sun": "Sunday (Saltless diet)",
            "Moon": "Monday or Purnima",
            "Mars": "Tuesday (Avoid anger and non-vegetarian food)",
            "Mercury": "Wednesday (Practice Maun/Silence for 1 hour)",
            "Jupiter": "Thursday (Eat yellow fruits/gram, respect elders)",
            "Venus": "Friday (Avoid sour foods, maintain neat cleanliness)",
            "Saturn": "Saturday (Light sesame/mustard oil lamp under Peepal tree)",
        }
        remedies.append(
            SpiritualRemedy(
                category="Fasting (Vrat)",
                target_planet=l_lord,
                title=f"Auspicious Planetary Observance ({l_lord})",
                description="Fast or observe a sattvic lifestyle ritual on this day to neutralize planetary friction.",
                mantra_or_practice=f"Observance of {vrat_days.get(l_lord, 'Saturday')}",
                timing_or_day=vrat_days.get(l_lord, "Saturday"),
            )
        )

        return remedies

    def _compute_life_stages(
        self,
        mahadashas: list[MahadashaPeriod],
        birth_dt: datetime,
        ascendant: str,
    ) -> list[LifeStage]:
        """Map the 120-year Vimshottari Mahadashas into 5 lifelong chronological stages."""
        brackets = [
            (1, "0–18 Years", "Childhood, Health & Early Foundations", 0, 18),
            (2, "18–30 Years", "Higher Education, Skill Mastery & Career Launch", 18, 30),
            (3, "30–50 Years", "Professional Zenith, Wealth Accumulation & Family Life", 30, 50),
            (4, "50–65 Years", "Mid-Life Consolidation, Mentorship & Health Vigilance", 50, 65),
            (5, "65+ Years", "Later Years, Longevity (Ayurdaya) & Spiritual Fulfillment", 65, 95),
        ]

        stages: list[LifeStage] = []

        for num, age_str, title, start_age, end_age in brackets:
            t_start = birth_dt + timedelta(days=start_age * 365.2422)
            t_end = birth_dt + timedelta(days=end_age * 365.2422)

            # Identify active Mahadashas overlapping this age window
            overlapping_lords = []
            for m in mahadashas:
                if m.start_date <= t_end and m.end_date >= t_start:
                    overlapping_lords.append(m.lord)

            dasha_ctx = (
                f"Mahadasha cycles: {', '.join(overlapping_lords)}"
                if overlapping_lords
                else "Running planetary sequences"
            )

            if num == 1:
                themes = [
                    "Early physical constitution and immunity development (Lagna)",
                    "Mother's emotional influence and domestic security (4th House)",
                    "Schooling foundations, curiosity, and primary skill formation",
                ]
                milestones = [
                    "Age 0–5: Balarishta immunity stabilization",
                    "Age 14–16: First intellectual awakening and academic direction",
                ]
                guidance = "Nurture emotional grounding and physical stamina. Protect against seasonal respiratory or digestive sensitivities."

            elif num == 2:
                themes = [
                    "Higher academic degrees and professional competitive exams (5th & 9th Houses)",
                    "First independent career steps and initial corporate friction (10th House)",
                    "Formative relationship trials and emotional maturity",
                ]
                milestones = [
                    "Age 22–24: Career entry point / initial professional placement",
                    "Age 27–29: Major job pivot or substantial promotion",
                ]
                guidance = "Embrace disciplined grinding. Initial career delays are structural karmic preparation, not permanent denial."

            elif num == 3:
                themes = [
                    "Peak career authority, leadership status, and societal recognition (10th & 11th Houses)",
                    "Marriage, enduring partnership, and domestic establishment (7th House & D9 Navamsha)",
                    "Major wealth compounding, property acquisition, and child development",
                ]
                milestones = [
                    "Age 32–36: Navamsha maturity activation; definitive professional leap",
                    "Age 42–46: Zenith of material gains and leadership expansion",
                ]
                guidance = "Balance intense professional drive with domestic presence. Maintain ethical integrity in financial dealings."

            elif num == 4:
                themes = [
                    "Transition from executive execution to strategic advisory and mentorship",
                    "Health vigilance: Metabolic, cardiovascular, and joint maintenance (6th & 8th Houses)",
                    "Financial consolidation, wealth preservation, and family legacy planning",
                ]
                milestones = [
                    "Age 52–54: Shift into advisory/consultative roles or independent venture",
                    "Age 60: Shashti Poorthi renewal; spiritual pivot",
                ]
                guidance = "Prioritize preventive health diagnostics. Shift focus from aggressive wealth accumulation to legacy and spiritual grounding."

            else:
                themes = [
                    "Ayurdaya longevity factors and peaceful physical maintenance (8th House grace)",
                    "Spiritual liberation, meditation, and detachment (9th & 12th Houses)",
                    "Revered family elder status, philosophical contribution, and inner peace",
                ]
                milestones = [
                    "Age 70+: Inner serenity and deep spiritual wisdom fruition",
                    "Full life completion with dignity and ancestral grace",
                ]
                guidance = "Engage in daily meditation, sacred recitation, and charitable mentoring. Enjoy the fruits of righteous karmic living."

            stages.append(
                LifeStage(
                    stage_number=num,
                    age_bracket=age_str,
                    title=title,
                    dasha_context=dasha_ctx,
                    key_themes=themes,
                    milestones=milestones,
                    guidance=guidance,
                )
            )

        return stages

    def _generate_life_blueprint_reading(
        self,
        chart_dict: dict[str, Any],
        target_utc: datetime,
        name: str,
        system: AstrologySystem,
        ascendant: str,
        sun_sign: str,
        moon_sign: str,
        active_dasha: Any,
        life_stages: list[LifeStage],
        gemstones: list[GemstoneRecommendation],
        remedies: list[SpiritualRemedy],
    ) -> str:
        """Synthesize the complete 7-section Birth-to-Death Life Blueprint."""
        divider = "--------------------------------------------------"
        lines = [divider]

        # ── Section 1: Foundation ──
        if system == AstrologySystem.KP:
            sub_info = chart_dict.get("ascendant_sublord_info", {})
            sub_str = sub_info.get("sub_lord", "Mercury") if isinstance(sub_info, dict) else getattr(sub_info, "sub_lord", "Mercury")
            star_str = sub_info.get("star_lord", "Ketu") if isinstance(sub_info, dict) else getattr(sub_info, "star_lord", "Ketu")
            lines.append("◆ Birth Chart Foundation & Technical Matrix (KP System)")
            lines.append(f"Primary KP Coordinates for {name}:")
            lines.append(f"• Ascendant (Lagna): {ascendant} | Soul Sign (Sun): {sun_sign} | Mind Sign (Moon): {moon_sign}")
            lines.append(f"• Astrological System: KP Astrology (Krishnamurti Paddhati, Placidus Cusps, Krishnamurti Ayanamsa)")
            lines.append(f"• Ascendant Star Lord: {star_str} | Ascendant Sub-Lord: {sub_str}")
            if active_dasha:
                lines.append(
                    f"• Active Time-Lord: Mahadasha {active_dasha.mahadasha} – Antardasha {active_dasha.antardasha} – Pratyantardasha {active_dasha.pratyantardasha}"
                )
            lines.append("")
            lines.append("Krishnamurti rule:")
            lines.append("Planet is the source, Star Lord indicates the results/houses, and Sub-Lord determines whether the outcome is favorable or unfavorable.")
            lines.append("Placidus cusp sub-lords govern the concrete manifestation of all life events.")
            lines.append("")
            lines.append("✦ Core KP Natal Constitution is POTENT and BALANCED.")
            lines.append("Strong sub-lord foundation for high-precision event manifestation.")
            lines.append("")
            lines.append(divider)
        else:
            lines.append("◆ Birth Chart Foundation & Technical Matrix")
            lines.append(f"Primary Chart Coordinates for {name}:")
            lines.append(f"• Ascendant (Lagna): {ascendant} | Soul Sign (Sun): {sun_sign} | Mind Sign (Moon): {moon_sign}")
            lines.append(f"• Astrological System: Vedic Sidereal (Lahiri Ayanamsa)")
            if active_dasha:
                lines.append(
                    f"• Active Time-Lord: Mahadasha {active_dasha.mahadasha} – Antardasha {active_dasha.antardasha} – Pratyantardasha {active_dasha.pratyantardasha}"
                )
            lines.append("")
            lines.append("Parashari rule:")
            lines.append("Lagna represents the physical body and life trajectory.")
            lines.append("Chandra represents the mind, subconscious perception, and emotional vitality.")
            lines.append("Surya represents the Atman (soul), vitality, and self-realization.")
            lines.append("")
            lines.append("✦ Core Natal Constitution is POTENT and BALANCED.")
            lines.append("Strong foundation for long-term endurance and purposeful fruition.")
            lines.append("")
            lines.append(divider)

        # ── Section 2: Yogas / Cuspal Sub-Lords ──
        if system == AstrologySystem.KP:
            lines.append("◆ KP Cuspal Sub-Lord Matrix & House Promises")
            cuspal_data = chart_dict.get("cuspal_analysis", [])
            if cuspal_data:
                lines.append("Placidus House Cusp Sub-Lords & Significations:")
                for c in cuspal_data[:6]:
                    c_num = c.get("cusp_number") if isinstance(c, dict) else getattr(c, "cusp_number", 1)
                    c_sub = c.get("sub_lord") if isinstance(c, dict) else getattr(c, "sub_lord", "Saturn")
                    c_star = c.get("star_lord") if isinstance(c, dict) else getattr(c, "star_lord", "Mercury")
                    c_rashi = c.get("rashi_name") if isinstance(c, dict) else getattr(c, "rashi_name", "Aries")
                    lines.append(f"• Cusp {c_num} ({c_rashi}): Sub-Lord {c_sub} (Star Lord: {c_star})")
            else:
                lines.append("• 10th Cusp Sub-Lord: Governs professional status and career rise")
                lines.append("• 7th Cusp Sub-Lord: Governs marriage promise and partnership harmony")
                lines.append("• 2nd/11th Cusp Sub-Lords: Govern financial accumulation and fulfillment of desires")

            lines.append("")
            lines.append("Krishnamurti rule:")
            lines.append("The sub-lord of the cusp decides whether the matters of that house are promised or denied.")
            lines.append("A favorable sub-lord connecting to houses 2, 6, 10, 11 ensures victory and worldly fulfillment.")
            lines.append("")
            lines.append("✦ KP Cuspal Sub-Lords confirm realization of core life promises.")
            lines.append("")
            lines.append(divider)
        else:
            lines.append("◆ Classical Yogas & Planetary Strengths")
            yogas = chart_dict.get("yogas", [])
            if yogas:
                lines.append("Key Parashari Yogas Active in Natal Framework:")
                for y in yogas[:4]:
                    y_name = y.get("name", "Auspicious Yoga")
                    y_desc = y.get("description", "Auspicious planetary combination")
                    lines.append(f"• {y_name}: {y_desc}")
            else:
                lines.append("• Raja Yoga Combinations: Kendra and Trikona lord alignments granting status")
                lines.append("• Dhana Yoga Combinations: 2nd and 11th house associations generating wealth")

            lines.append("")
            lines.append("Parashari rule:")
            lines.append("Kendra (1,4,7,10) is Vishnu Sthana (Effort & Status).")
            lines.append("Trikona (1,5,9) is Lakshmi Sthana (Grace & Fortune).")
            lines.append("Their union forms indelible Raja Yoga ensuring victory over adversaries.")
            lines.append("")
            lines.append("✦ Planetary Strengths guarantee resilience during challenging cycles.")
            lines.append("")
            lines.append(divider)

        # ── Section 3: Divisional Charts / KP Significators ──
        if system == AstrologySystem.KP:
            lines.append("◆ KP 4-Level House Significators (Precision Hierarchy)")
            lines.append("KP 4-Tier Hierarchy of Planetary Signification Strength:")
            lines.append("• Level 1 (Strongest): Planets in the constellation (Nakshatra) of house occupants")
            lines.append("• Level 2: Planets directly occupying the Placidus house")
            lines.append("• Level 3: Planets in the constellation of the house lord")
            lines.append("• Level 4 (Weakest): The lord of the house itself")
            lines.append("")
            lines.append("Krishnamurti rule:")
            lines.append("In KP, Level 1 and Level 2 significators prevail decisively over nominal sign rulers.")
            lines.append("Dasha-Bhukti of Level 1 significators triggers instant materialization of events.")
            lines.append("")
            lines.append("✦ 4-Level significator architecture guarantees pinpoint event timing.")
            lines.append("")
            lines.append(divider)
        else:
            lines.append("◆ Divisional Charts (Varga Insights)")
            lines.append("Varga Harmony across Destiny Layers:")
            lines.append("• D1 Rashi Chart: Physical incarnation, primary house dispositions, and worldly events.")
            lines.append("• D9 Navamsha Chart: Inner dharmic strength, marital partnership, and destiny blossoming after age 32.")
            lines.append("• D10 Dasamsha Chart: Career zenith, societal recognition, and professional legacy.")
            lines.append("")
            lines.append("Parashari rule:")
            lines.append("A planet strong in both D1 and D9 achieves Vargottama dignity, giving sovereign results.")
            lines.append("")
            lines.append("✦ Vargas confirm enduring success in middle and later life.")
            lines.append("")
            lines.append(divider)

        # ── Section 4: Whole-Life Journey (5 Stages) ──
        lines.append("◆ Whole-Life Journey: Birth to Death (5 Chronological Stages)")
        for st in life_stages:
            lines.append(f"✦ Stage {st.stage_number} ({st.age_bracket}) – {st.title}")
            lines.append(f"{st.dasha_context} |")
            lines.append("Key themes operating:")
            for th in st.key_themes:
                lines.append(f"• {th}")
            for m in st.milestones:
                lines.append(f"✓ {m}")
            lines.append(f"Guidance: {st.guidance} |")
            lines.append("")

        lines.append(divider)

        # ── Section 5: Strategic Action Plan / KP Ruling Planets ──
        if system == AstrologySystem.KP:
            lines.append("◆ Strategic Life Decisions & Precision Event Timing (Ruling Planets)")
            lines.append("KP Strategic Roadmap & Real-Time Event Triggering:")
            lines.append("• Career Fruition: Act when running Bhukti is a Level 1 or 2 significator of houses 2, 6, 10, 11.")
            lines.append("• Union & Marriage: Triggered during sub-periods of 2nd, 7th, and 11th house significators.")
            lines.append("• Precision Down to Days/Hours: Correlate active Dasha lords with the 5 Ruling Planets (Lagna Sign/Star/Sub + Moon Sign/Star + Day Lord).")
            lines.append("")
            lines.append("Krishnamurti rule:")
            lines.append("Events materialize when the ruling planets at the time of transit or decision coincide with natal significators.")
            lines.append("")
            lines.append("✦ Follow KP Ruling Planets for down-to-the-hour life alignment.")
            lines.append("")
            lines.append(divider)
        else:
            lines.append("◆ Strategic Life Decisions & Action Plan")
            lines.append("Strategic Roadmap based on House Lords:")
            lines.append("• Career Execution: Prioritize leadership and technical mastery. Avoid impulsive mid-career job jumps.")
            lines.append("• Marriage & Union: Exercise mature vetting. Navamsha indicates union based on mutual intellectual respect.")
            lines.append("• Financial Architecture: Build dual income streams. Accumulate physical assets and conservative compounding.")
            lines.append("")
            lines.append("Parashari rule:")
            lines.append("When running dasha aligns with Upachaya houses (3, 6, 10, 11), aggressive worldly enterprise succeeds.")
            lines.append("When dasha activates Moksha houses (4, 8, 12), consolidation and inner mastery are paramount.")
            lines.append("")
            lines.append("✦ Follow karmic timing for peak material and spiritual success.")
            lines.append("")
            lines.append(divider)

        # ── Section 6: Gemstone Prescription ──
        lines.append("◆ Gemstone Prescription (Ratna Chikitsa)")
        lines.append("Vedic Gemstones prescribed based on functional benefics and house lordship:")
        for g in gemstones:
            if not g.is_contraindicated:
                lines.append(f"✦ {g.category}: {g.gemstone} ({g.sanskrit_name})")
                lines.append(f"• Ruling Planet: {g.ruling_planet} | Metal: {g.metal} | Finger: {g.finger}")
                lines.append(f"• Auspicious Day: {g.auspicious_day}")
                lines.append(f"• Consecration Mantra: {g.consecration_mantra}")
                lines.append(f"• Rationale: {g.rationale}")
                lines.append("")

        lines.append("Strict Contraindications (DO NOT WEAR):")
        for g in gemstones:
            if g.is_contraindicated:
                lines.append(f"✓ NEVER WEAR {g.gemstone} ({g.sanskrit_name}): {g.rationale}")

        lines.append("")
        lines.append(divider)

        # ── Section 7: Spiritual Remedies ──
        lines.append("◆ Spiritual & Practical Remedies (Upayas)")
        lines.append("Remedial framework to balance planetary friction and elevate life grace:")
        for r in remedies:
            lines.append(f"✦ {r.category} – {r.title}")
            lines.append(f"• Planet: {r.target_planet}")
            lines.append(f"• Practice: {r.mantra_or_practice}")
            lines.append(f"• Timing: {r.timing_or_day}")
            lines.append(f"• Purpose: {r.description}")
            lines.append("")

        lines.append("✦ Whole-Life Blueprint is sealed with divine balance, wisdom, and protection.")
        lines.append(divider)

        return "\n".join(lines)

    def _generate_with_gemini(
        self,
        chart_dict: dict[str, Any],
        focus: AnalysisFocus,
        target_utc: datetime,
        name: str,
        system: AstrologySystem,
        language: str,
        active_dasha: Any,
        upcoming_antardashas: list[DashaPeriod],
        life_stages: list[LifeStage],
        gemstones: list[GemstoneRecommendation],
        remedies: list[SpiritualRemedy],
    ) -> str:
        """Call Google Gemini to generate precision astrological interpretation."""
        prompt = self._build_gemini_prompt(
            chart_dict=chart_dict,
            focus=focus,
            target_utc=target_utc,
            name=name,
            system=system,
            language=language,
            active_dasha=active_dasha,
            upcoming_antardashas=upcoming_antardashas,
            life_stages=life_stages,
            gemstones=gemstones,
            remedies=remedies,
        )

        api_key = self.settings.gemini_api_key.strip()
        model_name = self.settings.ai_model or "gemini-2.0-flash"

        # Try modern google.genai SDK first
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and hasattr(response, "text") and response.text:
                return response.text
        except Exception as e:
            logger.info("google.genai call attempt failed, trying google.generativeai", error=str(e))

        # Fallback to google.generativeai legacy package
        import google.generativeai as gai
        gai.configure(api_key=api_key)
        model = gai.GenerativeModel(model_name)
        response = model.generate_content(prompt)
        return response.text if response and response.text else ""

    def _build_gemini_prompt(
        self,
        chart_dict: dict[str, Any],
        focus: AnalysisFocus,
        target_utc: datetime,
        name: str,
        system: AstrologySystem,
        language: str,
        active_dasha: Any,
        upcoming_antardashas: list[DashaPeriod],
        life_stages: list[LifeStage],
        gemstones: list[GemstoneRecommendation],
        remedies: list[SpiritualRemedy],
    ) -> str:
        """Construct high-fidelity prompt for Gemini ensuring exact output format."""
        yogas = chart_dict.get("yogas", [])
        yogas_str = ", ".join([y.get("name", "") for y in yogas[:6]]) if yogas else "None detected"

        kp_context_block = ""
        if system == AstrologySystem.KP:
            cuspal_data = chart_dict.get("cuspal_analysis", [])
            cusp_lines = []
            for c in cuspal_data[:12]:
                c_num = c.get("cusp_number") if isinstance(c, dict) else getattr(c, "cusp_number", "")
                c_sub = c.get("sub_lord") if isinstance(c, dict) else getattr(c, "sub_lord", "")
                c_star = c.get("star_lord") if isinstance(c, dict) else getattr(c, "star_lord", "")
                c_sig = c.get("sub_lord_signifies_houses", []) if isinstance(c, dict) else getattr(c, "sub_lord_signifies_houses", [])
                cusp_lines.append(f"Cusp {c_num}: Sub-Lord={c_sub}, Star-Lord={c_star}, Signifies={c_sig}")
            ruling_p = chart_dict.get("ruling_planets_at_birth", {})
            kp_context_block = f"""
KP (KRISHNAMURTI PADDHATI) SYSTEM DATA:
- Ayanamsa: Krishnamurti (Sidereal)
- House System: Placidus Cusps (mandatory for KP)
- Placidus Cuspal Sub-Lords:
  {chr(10).join('  • ' + l for l in cusp_lines)}
- Ruling Planets (for precision down to days/hours): {ruling_p}
- Core KP Rules to Apply:
  1. Planet is the source, its Star Lord indicates results/houses, Sub-Lord decides favorable or adverse.
  2. The Sub-Lord of each house cusp determines the promise of that house.
  3. Timing is governed by Dasha-Bhukti of 4-level significators confirmed by Ruling Planets.
"""

        is_life_blueprint = focus in (AnalysisFocus.LIFE_BLUEPRINT, "life_blueprint", "full_life")

        if is_life_blueprint:
            system_title = "KP (Krishnamurti Paddhati) Sidereal (Krishnamurti Ayanamsa, Placidus Cusps)" if system == AstrologySystem.KP else f"{system.value} (Lahiri Sidereal)"
            astrologer_title = "master KP Astrologer specializing in Krishnamurti Paddhati, Placidus cuspal sub-lords, 4-level significators, and Ruling Planets" if system == AstrologySystem.KP else "master Vedic Astrologer"
            rule_name = "Krishnamurti rule" if system == AstrologySystem.KP else "Parashari rule"

            prompt = f"""You are a world-renowned {astrologer_title} creating a COMPLETE PROFESSIONAL LIFE BLUEPRINT (Birth to Death) for {name}.
Astrological System: {system_title}
Ascendant (Lagna): {chart_dict.get('ascendant_rashi') or chart_dict.get('ascendant_sign')}
Sun: {chart_dict.get('sun_sign')} | Moon: {chart_dict.get('moon_sign')}
Yogas: {yogas_str}
{kp_context_block}

You MUST format the output EXACTLY matching this visual template (use ◆ for section titles, • for connections, ✓ for symptoms/influences, ✦ for conclusions/milestones, and horizontal rules between sections).

REQUIRED 7 SECTIONS:
--------------------------------------------------
◆ Birth Chart Foundation & Technical Matrix
• Ascendant (Lagna): ...
• Sun Sign & Moon Sign: ...
• Technical planetary placements: ...
{rule_name}: ...
✦ Core Natal Constitution is POTENT and BALANCED.

--------------------------------------------------
◆ Classical Yogas & Planetary Strengths (or KP Cuspal Sub-Lord Matrix)
• Details: ...
{rule_name}: ...
✦ Planetary strengths / sub-lords guarantee resilience during challenging cycles.

--------------------------------------------------
◆ Divisional Charts / KP 4-Level Significators
• Details: ...
{rule_name}: ...
✦ Confirms enduring success in middle and later life.

--------------------------------------------------
◆ Whole-Life Journey: Birth to Death (5 Chronological Stages)
✦ Stage 1 (0–18 Years) – Childhood, Health & Early Foundations
• ...
✓ ...
Guidance: ... |

✦ Stage 2 (18–30 Years) – Higher Education, Skill Mastery & Career Launch
• ...
✓ ...
Guidance: ... |

✦ Stage 3 (30–50 Years) – Professional Zenith, Wealth Accumulation & Family Life
• ...
✓ ...
Guidance: ... |

✦ Stage 4 (50–65 Years) – Mid-Life Consolidation, Mentorship & Health Vigilance
• ...
✓ ...
Guidance: ... |

✦ Stage 5 (65+ Years) – Later Years, Longevity (Ayurdaya) & Spiritual Fulfillment
• ...
✓ ...
Guidance: ... |

--------------------------------------------------
◆ Strategic Life Decisions & Action Plan (Timing Down to Days/Hours via Ruling Planets)
• Career Alignment: ...
• Marriage & Domestic Harmony: ...
• Wealth Building: ...
{rule_name}: ...
✦ Follow karmic timing for peak material and spiritual success.

--------------------------------------------------
◆ Gemstone Prescription (Ratna Chikitsa)
✦ Life Stone (Jeevan Ratna): ...
• Metal: ... | Finger: ... | Day: ...
• Mantra: ...
✦ Lucky Stone (Bhagya Ratna): ...
Strict Contraindications (DO NOT WEAR):
✓ NEVER WEAR ...: ...

--------------------------------------------------
◆ Spiritual & Practical Remedies (Upayas)
✦ Beej Mantra: ...
✦ Stotra: ...
✦ Practical Charity (Daan): ...
✦ Fasting (Vrat) & Lifestyle: ...
--------------------------------------------------

Produce the complete reading tailored specifically to the Native. Keep every section authoritative, dignified, and structured without conversational filler.
"""
            return prompt

        # Focus domain prompt (Career, Love, Finance, etc.)
        focus_val = focus.value if hasattr(focus, "value") else str(focus)
        astrologer_title = "master KP Astrologer specializing in Krishnamurti Paddhati event-oriented timing" if system == AstrologySystem.KP else "classical Vedic and Western Astrologer"
        rule_name = "Krishnamurti rule" if system == AstrologySystem.KP else "Parashari rule"

        prompt = f"""You are an elite, {astrologer_title} who provides rigorous, definitive, and crystal-clear astrological analysis.
Target Native: {name}
Focus Domain: {focus_val.upper()}
Target Reference Date: {target_utc.strftime('%B %Y')} (Target year: {target_utc.year})
Astrological System: {system.value}
{kp_context_block}

NATAL CHART DATA:
- Ascendant: {chart_dict.get('ascendant_rashi') or chart_dict.get('ascendant_sign')}
- Sun: {chart_dict.get('sun_sign')}
- Moon: {chart_dict.get('moon_sign')}
- Yogas: {yogas_str}

REQUIRED OUTPUT STYLE AND FORMAT:
You MUST format the output EXACTLY matching this visual template (use ◆ for section titles, • for connections, ✓ for symptoms/influences, ✦ for conclusions/milestones, and horizontal rules between sections). Do NOT write introductory conversational filler.

FORMAT TEMPLATE:
--------------------------------------------------
◆ {focus_val.capitalize()} House Analysis
[House/Cusp] sub-lord and star-lord connection with:
• [House/Planet 1]
• [House/Planet 2]

{rule_name}:
[Specific {rule_name} deduction]

✦ {focus_val.capitalize()} promise is STRONG / CONFIRMED.
No denial. Only delay / testing.

--------------------------------------------------
◆ Why Delay / Challenge Happening?
[8th / 12th / 6th house involvement] + [Saturn / transit / sub-lord testing] |

Influence gives:
✓ Sudden breaks / stalls
✓ Frustration
✓ Direction confusion
✓ Confidence drop

Not destruction, karmic restructuring |

--------------------------------------------------
◆ Current Mahadasha–Antardasha ({target_utc.year} context)
Running dasha activating:
• Themes

In your case: {target_utc.year} mid stagnation | {target_utc.year} end movement |

--------------------------------------------------
◆ Exact {focus_val.capitalize()} Rise Timeline ({rule_name} Based Down to Days/Hours)
✦ [Month Year] – First Opportunity
[Concise description] |

✦ [Month Year] – Strong Activation
[Concise description] |

✦ [Year] – Growth Phase
[Concise description] |
--------------------------------------------------
"""
        return prompt

    def _generate_rule_based_reading(
        self,
        chart_dict: dict[str, Any],
        focus: AnalysisFocus,
        target_utc: datetime,
        name: str,
        system: AstrologySystem,
        active_dasha: Any,
        upcoming_antardashas: list[DashaPeriod],
        ascendant: str,
        sun_sign: str,
        moon_sign: str,
    ) -> str:
        """Synthesize classical Parashari rule deductions algorithmically."""
        target_year = target_utc.year
        bhavas = chart_dict.get("bhavas", [])

        def get_house(num: int) -> dict[str, Any]:
            for b in bhavas:
                if b.get("house_number") == num:
                    return b
            return {}

        h10 = get_house(10)
        h6 = get_house(6)
        h11 = get_house(11)
        h8 = get_house(8)
        h7 = get_house(7)
        h2 = get_house(2)

        lord_10 = h10.get("lord", "Mars")
        lord_6 = h6.get("lord", "Mercury")
        lord_11 = h11.get("lord", "Saturn")
        lord_8 = h8.get("lord", "Mars")
        lord_7 = h7.get("lord", "Venus")
        lord_2 = h2.get("lord", "Venus")

        occupants_10 = h10.get("occupants", [])
        aspects_10 = h10.get("aspecting_grahas", [])

        m_lord = active_dasha.mahadasha if active_dasha else "Saturn"
        a_lord = active_dasha.antardasha if active_dasha else "Mercury"

        if upcoming_antardashas and len(upcoming_antardashas) >= 2:
            d1 = upcoming_antardashas[0]
            d2 = upcoming_antardashas[1]
            date_1_str = d1.start_date.strftime("%B %Y")
            date_2_str = d2.start_date.strftime("%B %Y")
            date_3_str = str(d2.end_date.year)
        else:
            date_1_str = f"August {target_year}"
            date_2_str = f"January {target_year + 1}"
            date_3_str = str(target_year + 2)

        divider = "--------------------------------------------------"

        if focus in (AnalysisFocus.CAREER, AnalysisFocus.GENERAL):
            conn_points = [
                f"• 6th house ({lord_6} - service/job)",
                f"• 11th house ({lord_11} - income & elevation)",
            ]
            if aspects_10:
                conn_points.append(f"• {', '.join(aspects_10)} drishti / aspect influence")
            elif occupants_10:
                conn_points.append(f"• {', '.join(occupants_10)} occupation in 10th house")
            else:
                conn_points.append("• Saturn/Mercury governance influence")

            conn_block = "\n".join(conn_points)

            lines = [
                divider,
                "◆ 10th House (Career House) Analysis",
                f"10th house ({h10.get('rashi_name', 'Capricorn')}) lord ({lord_10}) connected with:",
                conn_block,
                "",
                "Parashari rule:",
                "10th lord + 6th connection = service/job assured.",
                "10th lord + 11th = income confirmed.",
                "",
                "✦ Career promise is STRONG.",
                "No denial. Only delay.",
                "",
                divider,
                "◆ Why Delay Happening?",
                "8th house involvement + Saturn transit effect |",
                "",
                "8th house influence gives:",
                "✓ Sudden breaks",
                "✓ Frustration",
                "✓ Direction confusion",
                "✓ Confidence drop",
                "",
                "Not destruction, karmic restructuring |",
                "",
                divider,
                f"◆ Current Mahadasha–Antardasha ({target_year} context)",
                f"Running {m_lord}–{a_lord} dasha activating:",
                f"• {m_lord} type disciplined energy",
                f"• 8th and Upachaya house themes",
                "• Transformation period",
                "",
                f"{m_lord} dasha first half brings testing obstacles |",
                "Second half grants stability and consolidation |",
                "",
                f"In your case: {target_year} mid = stagnation | {target_year} end = movement",
                "",
                divider,
                "◆ Exact Career Rise Timeline (Parashari Dasha Based)",
                f"✦ {date_1_str} – First Opportunity",
                "Interview / contract / joining probability |",
                "",
                f"✦ {date_2_str} – Strong Activation",
                "Stable job likely |",
                "",
                f"✦ {date_3_str} – Growth Phase",
                "Role clarity + income stabilization |",
                divider,
            ]
            return "\n".join(lines)

        elif focus == AnalysisFocus.LOVE:
            lines = [
                divider,
                "◆ 7th House (Partnership & Marriage) Analysis",
                f"7th house ({h7.get('rashi_name', 'Libra')}) lord ({lord_7}) connected with:",
                f"• Lagna ({ascendant}) & Venusian significations",
                f"• 11th house ({lord_11} - fulfillment of desires)",
                "• Jupiter/Venus benevolence",
                "",
                "Parashari rule:",
                "7th lord well-placed without malefic combustion = marital promise assured.",
                "Jupiter drishti on 7th bhava = enduring partnership.",
                "",
                "✦ Relationship promise is SOLID.",
                "No denial. Maturity-based union.",
                "",
                divider,
                "◆ Why Delay or Emotional Strain Happening?",
                "Saturn transit over natal axis + 8th house introspective transit |",
                "",
                "Karmic influence gives:",
                "✓ Emotional detachment",
                "✓ High standards / filtering out superficial connections",
                "✓ Temporary solitude",
                "",
                "This is emotional purification, preparing for genuine commitment |",
                "",
                divider,
                f"◆ Current Mahadasha–Antardasha ({target_year} context)",
                f"Running {m_lord}–{a_lord} dasha activating:",
                f"• {m_lord} grounding lessons",
                "• Relationship house evaluation",
                "• Realignment of core values",
                "",
                f"In your case: {target_year} mid introspection | {target_year} end emotional opening",
                "",
                divider,
                "◆ Exact Relationship Timeline (Parashari Dasha Based)",
                f"✦ {date_1_str} – Significant Social Introduction",
                "New acquaintance / mutual connection entrance |",
                "",
                f"✦ {date_2_str} – Deepening Commitment",
                "Clarity on partnership and mutual alignment |",
                "",
                f"✦ {date_3_str} – Formalization / Union",
                "Long-term stability and domestic peace |",
                divider,
            ]
            return "\n".join(lines)

        elif focus == AnalysisFocus.FINANCE:
            lines = [
                divider,
                "◆ 2nd & 11th Houses (Wealth & Dhana Yogas) Analysis",
                f"Wealth houses (2nd lord {lord_2}, 11th lord {lord_11}) connected with:",
                "• Dhana Yoga indicators (2nd + 11th lord alignment)",
                "• Kendra & Trikona support",
                "",
                "Parashari rule:",
                "Lords of 2nd and 11th mutual aspect = perpetual wealth accumulation.",
                "11th lord in Upachaya = incremental gains through disciplined effort.",
                "",
                "✦ Wealth promise is EXCELLENT.",
                "Delay in liquidity. Long-term wealth assured.",
                "",
                divider,
                "◆ Why Cash Flow Fluctuations Occur?",
                "8th house transit + Saturn financial prudence test |",
                "",
                "Transit influence gives:",
                "✓ Unexpected expenditure",
                "✓ Blocked funds / pending dues",
                "✓ Restructuring of investments",
                "",
                "Financial tightening before capital expansion |",
                "",
                divider,
                f"◆ Current Mahadasha–Antardasha ({target_year} context)",
                f"Running {m_lord}–{a_lord} dasha activating:",
                f"• {m_lord} frugality and asset building",
                "• New earning channels germination",
                "",
                f"In your case: {target_year} mid consolidation | {target_year} end income surge",
                "",
                divider,
                "◆ Exact Financial Rise Timeline (Parashari Dasha Based)",
                f"✦ {date_1_str} – Debt Relief / New Revenue Stream",
                "First financial stabilization milestone |",
                "",
                f"✦ {date_2_str} – Substantial Inflow",
                "Major deal / bonus / salary revision |",
                "",
                f"✦ {date_3_str} – Wealth Multiplication",
                "Asset acquisition and steady compounding |",
                divider,
            ]
            return "\n".join(lines)

        else:  # HEALTH / SPIRITUAL
            lines = [
                divider,
                "◆ 1st & 6th Houses (Vitality & Resilience) Analysis",
                f"Ascendant ({ascendant}) and 6th lord ({lord_6}) alignment:",
                "• Vitality governance through Lagna lord",
                "• 6th house Upachaya resilience against illnesses",
                "",
                "Parashari rule:",
                "Lagna lord strong in Kendra/Trikona = long life and innate vitality.",
                "Malefics in 6th house = defeat of diseases and opponents.",
                "",
                "✦ Vitality promise is RESILIENT.",
                "Temporary fatigue. No systemic debility.",
                "",
                divider,
                "◆ Why Low Energy / Stress Occurring?",
                "Saturn aspect on vitality axis + nervous system load |",
                "",
                "Influence gives:",
                "✓ Mental fatigue",
                "✓ Sleep irregularity",
                "✓ Digestive sensitivity",
                "",
                "Signal to establish daily rhythm and grounding practices |",
                "",
                divider,
                f"◆ Current Mahadasha–Antardasha ({target_year} context)",
                f"Running {m_lord}–{a_lord} dasha activating:",
                "• Physical discipline requirement",
                "• Detoxification and mental clarity",
                "",
                divider,
                "◆ Exact Vitality Timeline (Parashari Dasha Based)",
                f"✦ {date_1_str} – Energy Recovery",
                "Resolution of underlying fatigue |",
                "",
                f"✦ {date_2_str} – Peak Vitality",
                "Renewed stamina and mental sharpness |",
                "",
                f"✦ {date_3_str} – Sustained Balance",
                "Equilibrium in mind and body |",
                divider,
            ]
            return "\n".join(lines)

    def _generate_kp_rule_based_reading(
        self,
        chart_dict: dict[str, Any],
        focus: AnalysisFocus,
        target_utc: datetime,
        name: str,
        active_dasha: Any,
        upcoming_antardashas: list[DashaPeriod],
        ascendant: str,
        sun_sign: str,
        moon_sign: str,
    ) -> str:
        """Synthesize precision KP Astrology (Krishnamurti Paddhati) rule deductions."""
        target_year = target_utc.year
        cuspal_list = chart_dict.get("cuspal_analysis", [])

        def get_cusp(num: int) -> dict[str, Any]:
            for c in cuspal_list:
                c_num = c.get("cusp_number") if isinstance(c, dict) else getattr(c, "cusp_number", None)
                if c_num == num:
                    return c if isinstance(c, dict) else (c.to_dict() if hasattr(c, "to_dict") else {})
            return {}

        c10 = get_cusp(10)
        c7 = get_cusp(7)
        c2 = get_cusp(2)
        c11 = get_cusp(11)
        c6 = get_cusp(6)
        c1 = get_cusp(1)

        m_lord = active_dasha.mahadasha if active_dasha else "Saturn"
        a_lord = active_dasha.antardasha if active_dasha else "Mercury"

        if upcoming_antardashas and len(upcoming_antardashas) >= 2:
            d1 = upcoming_antardashas[0]
            d2 = upcoming_antardashas[1]
            date_1_str = d1.start_date.strftime("%B %Y")
            date_2_str = d2.start_date.strftime("%B %Y")
            date_3_str = str(d2.end_date.year)
        else:
            date_1_str = f"August {target_year}"
            date_2_str = f"January {target_year + 1}"
            date_3_str = str(target_year + 2)

        divider = "--------------------------------------------------"

        if focus in (AnalysisFocus.CAREER, AnalysisFocus.GENERAL):
            sub_10 = c10.get("sub_lord", "Mercury")
            star_10 = c10.get("star_lord", "Saturn")
            sign_10 = c10.get("sign_lord", "Venus")
            rashi_10 = c10.get("rashi_name", "Capricorn")
            conn_houses = c10.get("sub_lord_signifies_houses", [2, 6, 10, 11])
            conn_str = ", ".join(str(h) for h in conn_houses) if conn_houses else "2, 6, 10, 11"

            lines = [
                divider,
                "◆ 10th House (KP Cuspal & Sub-Lord) Career Analysis",
                f"10th Cusp ({rashi_10}) KP Sub-Lord Dynamics:",
                f"• Cusp Sign Lord: {sign_10} | Star Lord: {star_10}",
                f"• Cusp Sub-Lord: {sub_10} (Signifying Houses: {conn_str})",
                "• Favorable Career Houses: 2nd (Wealth), 6th (Service), 10th (Status), 11th (Gains)",
                "",
                "Krishnamurti rule:",
                "Planet is the source, Star Lord indicates the result, and Sub-Lord qualifies the outcome.",
                "If 10th cusp sub-lord signifies 2, 6, 10, or 11, career fruition is assured without denial.",
                "",
                "✦ Career promise is FIRMLY PROMISED under KP principles.",
                "Sub-lord indicates continuous progress and professional elevation.",
                "",
                divider,
                "◆ Why Obstacles / Delays Occur? (KP Dusthana Connection)",
                f"Sub-lord interaction with 8th/12th cuspal significations during {m_lord} cycle |",
                "",
                "KP adverse connections trigger:",
                "✓ Temporary stagnation in promotions",
                "✓ Professional direction recalibration",
                "✓ Testing by superiors / workload increase",
                "",
                "Not career denial, but necessary karmic preparation for higher authority |",
                "",
                divider,
                f"◆ Current Mahadasha–Antardasha ({target_year} context)",
                f"Running KP Time-Lords: {m_lord} Mahadasha – {a_lord} Antardasha",
                f"• {m_lord} as primary Dasha significator sets structural foundation",
                f"• {a_lord} activates cuspal significator channels",
                "",
                f"In your case: {target_year} mid = consolidation | {target_year} end = breakthrough",
                "",
                divider,
                "◆ Exact Career Rise Timeline (KP Dasha & Ruling Planets Timing)",
                f"✦ {date_1_str} – First Opportunity",
                "Favorable Bhukti transition + Moon transit over ruling planet star |",
                "",
                f"✦ {date_2_str} – Strong Activation",
                "Level 1 significator activation granting permanent role / promotion |",
                "",
                f"✦ {date_3_str} – Peak Elevation",
                "10th & 11th house fruit realization down to the hour |",
                divider,
            ]
            return "\n".join(lines)

        elif focus == AnalysisFocus.LOVE:
            sub_7 = c7.get("sub_lord", "Venus")
            star_7 = c7.get("star_lord", "Jupiter")
            rashi_7 = c7.get("rashi_name", "Libra")
            conn_houses = c7.get("sub_lord_signifies_houses", [2, 7, 11])
            conn_str = ", ".join(str(h) for h in conn_houses) if conn_houses else "2, 7, 11"

            lines = [
                divider,
                "◆ 7th House (KP Cuspal & Sub-Lord) Partnership Analysis",
                f"7th Cusp ({rashi_7}) KP Sub-Lord Dynamics:",
                f"• Cusp Sub-Lord: {sub_7} in Star of {star_7}",
                f"• Signified Houses: {conn_str}",
                "• Favorable Marriage Houses: 2nd (Family Expansion), 7th (Union), 11th (Fulfillment)",
                "",
                "Krishnamurti rule:",
                "If the 7th cusp sub-lord signifies houses 2, 7, or 11, marriage is assured.",
                "Sub-lord not connecting exclusively to 1, 6, 10 confirms no permanent denial.",
                "",
                "✦ Relationship promise is FIRMLY PROMISED under KP principles.",
                "Matrimonial and deep partnership bond is guaranteed.",
                "",
                divider,
                "◆ Why Delays or Filtering Period Occur?",
                "Sub-lord activating 1st or 6th house filtering before 7th/11th fruiting |",
                "",
                "Influence manifests as:",
                "✓ High personal standards and selectivity",
                "✓ Need for intellectual and karmic compatibility",
                "✓ Maturation of mutual expectations",
                "",
                "Karmic maturation ensuring an enduring lifelong bond |",
                "",
                divider,
                f"◆ Current Mahadasha–Antardasha ({target_year} context)",
                f"Running KP Time-Lords: {m_lord} Mahadasha – {a_lord} Antardasha",
                "• Activating relationship significator constellations",
                "",
                f"In your case: {target_year} mid = introspection | {target_year} end = new alignment",
                "",
                divider,
                "◆ Exact Relationship Timeline (KP Dasha & Ruling Planets Timing)",
                f"✦ {date_1_str} – Meaningful Connection",
                "Transit Moon over 7th cusp sub-lord star triggers key introduction |",
                "",
                f"✦ {date_2_str} – Mutual Commitment",
                "Harmonious significator sub-period formalizing alignment |",
                "",
                f"✦ {date_3_str} – Long-Term Union",
                "Enduring stability and domestic joy |",
                divider,
            ]
            return "\n".join(lines)

        elif focus == AnalysisFocus.FINANCE:
            sub_2 = c2.get("sub_lord", "Jupiter")
            sub_11 = c11.get("sub_lord", "Mercury")
            rashi_2 = c2.get("rashi_name", "Taurus")

            lines = [
                divider,
                "◆ 2nd & 11th Houses (KP Cuspal & Sub-Lord) Wealth Analysis",
                f"2nd Cusp ({rashi_2}) Sub-Lord {sub_2} & 11th Cusp Sub-Lord {sub_11}:",
                "• Primary Wealth Houses: 2nd (Assets), 6th (Operating Income), 11th (Net Gains)",
                "• Sub-Lord connections confirm active wealth compounding channels",
                "",
                "Krishnamurti rule:",
                "When 2nd and 11th cusp sub-lords signify 2, 6, 11, tremendous wealth accumulation is promised.",
                "Sub-lord of 11th cusp determines whether all worldly desires are realized.",
                "",
                "✦ Wealth promise is ROBUST under KP principles.",
                "No insolvency. Progressive asset accumulation confirmed.",
                "",
                divider,
                "◆ Why Temporary Cash Flow Fluctuations Occur?",
                "Sub-lord touching 5th (speculation) or 12th (investment outflow) houses |",
                "",
                "Influence gives:",
                "✓ Capital deployment into long-term assets",
                "✓ Delayed invoice or payment realizations",
                "✓ Need for structured budgeting",
                "",
                "Strategic reallocation before explosive expansion |",
                "",
                divider,
                f"◆ Current Mahadasha–Antardasha ({target_year} context)",
                f"Running KP Time-Lords: {m_lord} Mahadasha – {a_lord} Antardasha",
                "• Wealth generation houses activated in dual sequence",
                "",
                f"In your case: {target_year} mid = consolidation | {target_year} end = major inflow",
                "",
                divider,
                "◆ Exact Financial Rise Timeline (KP Dasha & Ruling Planets Timing)",
                f"✦ {date_1_str} – Inflow Initiation",
                "New revenue channel or high-value contract unblocked |",
                "",
                f"✦ {date_2_str} – Significant Gain",
                "Level 1 wealth significators deliver peak liquidity |",
                "",
                f"✦ {date_3_str} – Capital Multiplication",
                "Long-term investments reach compounding maturity |",
                divider,
            ]
            return "\n".join(lines)

        else:  # HEALTH / SPIRITUAL
            sub_1 = c1.get("sub_lord", "Mars")
            sub_6 = c6.get("sub_lord", "Mercury")

            lines = [
                divider,
                "◆ 1st & 6th Houses (KP Cuspal & Sub-Lord) Vitality Analysis",
                f"1st Cusp Sub-Lord {sub_1} & 6th Cusp Sub-Lord {sub_6}:",
                "• 1st Cusp Sub-Lord governs bodily constitution, health, and vitality",
                "• Signification of houses 1, 5, 11 = robust recovery and natural immunity",
                "",
                "Krishnamurti rule:",
                "If 1st cusp sub-lord signifies 1, 5, 11, native overcomes illnesses with ease.",
                "6th cusp sub-lord decides disease manifestation and cure timeframe.",
                "",
                "✦ Vitality promise is RESILIENT under KP principles.",
                "No incurable chronic affliction. High recuperative power.",
                "",
                divider,
                "◆ Why Fatigue or Stress Occurs?",
                "Temporary 6th/8th house sub-lord activation during dasha shifts |",
                "",
                "Influence gives:",
                "✓ Mild mental exhaustion from overwork",
                "✓ Digestive sensitivity requiring clean diet",
                "✓ Irregular circadian rhythm",
                "",
                "Signal to restore bodily balance through disciplined daily routine |",
                "",
                divider,
                f"◆ Current Mahadasha–Antardasha ({target_year} context)",
                f"Running KP Time-Lords: {m_lord} Mahadasha – {a_lord} Antardasha",
                "• Period demands structured sleep and rejuvenation",
                "",
                divider,
                "◆ Exact Vitality Timeline (KP Dasha & Ruling Planets Timing)",
                f"✦ {date_1_str} – Stamina Restoration",
                "Cellular recovery and rejuvenation |",
                "",
                f"✦ {date_2_str} – Peak Vitality",
                "High mental clarity and physical endurance |",
                "",
                f"✦ {date_3_str} – Harmonious Balance",
                "Sustained equilibrium in body and mind |",
                divider,
            ]
            return "\n".join(lines)

    def _parse_reading_to_sections(
        self, text: str
    ) -> tuple[list[HoroscopeSection], list[TimelineItem]]:
        """Parse formatted markdown text into structured sections and timeline items."""
        sections: list[HoroscopeSection] = []
        timeline: list[TimelineItem] = []

        raw_parts = text.split("◆")
        section_idx = 0

        for part in raw_parts:
            part = part.strip()
            if not part:
                continue

            lines = [l.strip() for l in part.split("\n") if l.strip()]
            if not lines:
                continue

            # First non-empty line is title
            title_line = lines[0].replace("--------------------------------------------------", "").strip()
            if not title_line or title_line.startswith("---"):
                if len(lines) > 1:
                    title_line = lines[1].replace("--------------------------------------------------", "").strip()
                    body_lines = lines[2:]
                else:
                    continue
            else:
                body_lines = lines[1:]

            if not title_line:
                continue

            content = "\n".join(body_lines).strip()

            key_points = []
            rules = []
            conclusions = []

            for line in body_lines:
                clean_l = line.strip()
                if clean_l.startswith("•") or clean_l.startswith("✓"):
                    key_points.append(clean_l.lstrip("•✓ ").strip())
                elif clean_l.startswith("✦"):
                    conclusions.append(clean_l.lstrip("✦ ").strip())
                elif "rule:" in clean_l.lower() or "connection =" in clean_l:
                    rules.append(clean_l)

            # Timeline detection
            if "timeline" in title_line.lower():
                current_timeframe = ""
                current_phase = ""
                for line in body_lines:
                    l = line.strip()
                    if l.startswith("✦"):
                        match = re.match(r"✦\s*([^–\-]+)[–\-]\s*(.*)", l)
                        if match:
                            current_timeframe = match.group(1).strip()
                            current_phase = match.group(2).strip()
                    elif l and not l.startswith("---") and current_timeframe:
                        pred_text = l.rstrip(" |").strip()
                        timeline.append(
                            TimelineItem(
                                timeframe=current_timeframe,
                                phase=current_phase,
                                prediction=pred_text,
                            )
                        )
                        current_timeframe = ""
                        current_phase = ""

            sec_id = f"section_{section_idx}_{re.sub(r'[^a-zA-Z0-9]', '_', title_line)[:15].lower()}"
            sections.append(
                HoroscopeSection(
                    id=sec_id,
                    title=title_line,
                    key_points=key_points,
                    rules_applied=rules,
                    conclusions=conclusions,
                    raw_markdown=f"◆ {title_line}\n{content}",
                )
            )
            section_idx += 1

        return sections, timeline


# Module singleton
astro_interpretation_service = AstroInterpretationService()


def get_astro_interpretation_service() -> AstroInterpretationService:
    return astro_interpretation_service
