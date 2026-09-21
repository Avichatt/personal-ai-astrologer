"""Pydantic schemas for AI Horoscope Analysis and interpretation layer."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
import uuid

from pydantic import BaseModel, Field

from app.config.constants import AstrologySystem, Ayanamsa, HouseSystem


class AnalysisFocus(StrEnum):
    CAREER = "career"
    LOVE = "love"
    HEALTH = "health"
    FINANCE = "finance"
    SPIRITUAL = "spiritual"
    GENERAL = "general"
    LIFE_BLUEPRINT = "life_blueprint"



class DirectAnalysisRequest(BaseModel):
    """Analyze horoscope from explicit birth data."""

    name: str = Field("Native", description="Name of the person")
    utc_datetime: datetime = Field(..., description="UTC birth timestamp")
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    target_date: datetime | None = Field(
        None,
        description="Target date for current dasha and transit context (defaults to now)",
    )
    focus: AnalysisFocus = Field(
        AnalysisFocus.CAREER,
        description="Domain focus for precision interpretation",
    )
    system: AstrologySystem = Field(
        AstrologySystem.VEDIC,
        description="Vedic or Western astrology engine",
    )
    ayanamsa: Ayanamsa = Field(
        Ayanamsa.LAHIRI,
        description="Ayanamsa used for Vedic calculations",
    )
    house_system: HouseSystem = Field(
        HouseSystem.PLACIDUS,
        description="House system used for Western calculations",
    )
    language: str = Field(
        "en",
        description="Output language or style (e.g. 'en', 'bengali-english', 'hindi-english')",
    )


class ProfileAnalysisRequest(BaseModel):
    """Analyze horoscope from a saved birth profile."""

    birth_profile_id: uuid.UUID
    target_date: datetime | None = None
    focus: AnalysisFocus = AnalysisFocus.CAREER
    system: AstrologySystem = AstrologySystem.VEDIC
    ayanamsa: Ayanamsa = Ayanamsa.LAHIRI
    house_system: HouseSystem = HouseSystem.PLACIDUS
    language: str = "en"


class HoroscopeSection(BaseModel):
    """A structured astrological reading section."""

    id: str = Field(..., description="Section identifier (e.g., house_10, delay_diagnosis)")
    title: str = Field(..., description="Section header, e.g., '10th House (Career House) Analysis'")
    key_points: list[str] = Field(default_factory=list, description="Core connections and planetary factors")
    rules_applied: list[str] = Field(default_factory=list, description="Parashari or classical astrological rules")
    conclusions: list[str] = Field(default_factory=list, description="Takeaways, assurances, or warnings")
    raw_markdown: str = Field(..., description="Rendered section text")


class TimelineItem(BaseModel):
    """A specific timeline prediction milestone."""

    timeframe: str = Field(..., description="e.g. 'August 2026' or 'Q3 2026'")
    phase: str = Field(..., description="e.g. 'First Opportunity' or 'Strong Activation'")
    prediction: str = Field(..., description="e.g. 'Interview / contract / joining probability'")


class LifeStage(BaseModel):
    """A distinct life phase from birth to death mapped to dasha cycles."""

    stage_number: int
    age_bracket: str = Field(..., description="e.g. '0–18 Years' or '18–30 Years'")
    title: str = Field(..., description="e.g. 'Childhood, Health & Foundations'")
    dasha_context: str = Field(..., description="Active Mahadasha periods operating during this phase")
    key_themes: list[str] = Field(default_factory=list)
    milestones: list[str] = Field(default_factory=list)
    guidance: str = Field(..., description="Key life guidance and cautions for this stage")


class GemstoneRecommendation(BaseModel):
    """Vedic gemstone prescription based on functional benefics and house lordship."""

    category: str = Field(..., description="'Life Stone (Jeevan Ratna)', 'Lucky Stone (Bhagya Ratna)', or 'Contraindicated'")
    gemstone: str = Field(..., description="e.g. 'Emerald', 'Yellow Sapphire', 'Blue Sapphire', 'Ruby'")
    sanskrit_name: str = Field(..., description="e.g. 'Panna', 'Pukhraj', 'Neelam', 'Manikya'")
    ruling_planet: str
    finger: str
    metal: str
    auspicious_day: str
    consecration_mantra: str
    rationale: str
    is_contraindicated: bool = False


class SpiritualRemedy(BaseModel):
    """Vedic spiritual, ritual, and charitable remedy."""

    category: str = Field(..., description="'Beej Mantra', 'Stotra', 'Charity (Daan)', 'Fasting (Vrat)', or 'Lifestyle'")
    target_planet: str
    title: str
    description: str
    mantra_or_practice: str
    timing_or_day: str


class HoroscopeAnalysisResponse(BaseModel):
    """Full structured horoscope analysis output matching precision astrological format."""

    name: str
    focus: str
    system: str
    birth_datetime_utc: str
    target_datetime_utc: str
    ascendant: str
    sun_sign: str
    moon_sign: str
    current_mahadasha: str | None = None
    current_antardasha: str | None = None
    current_pratyantardasha: str | None = None
    sections: list[HoroscopeSection]
    timeline: list[TimelineItem]
    life_stages: list[LifeStage] = Field(default_factory=list)
    gemstone_recommendations: list[GemstoneRecommendation] = Field(default_factory=list)
    spiritual_remedies: list[SpiritualRemedy] = Field(default_factory=list)
    formatted_reading: str = Field(
        ...,
        description="Cleanly formatted full text with ◆ sections, • and ✓ bullets, and dividers",
    )
    engine_source: str = Field(
        ...,
        description="Indicates whether generated via Gemini AI or Astrological Rule-Based Engine",
    )

