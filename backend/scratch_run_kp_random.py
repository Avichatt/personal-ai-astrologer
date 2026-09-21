import sys
from datetime import datetime, UTC

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.astrology.engine import AstrologyEngine
from app.config.constants import AstrologySystem
from app.schemas.analysis import AnalysisFocus
from app.services.ai_interpretation import AstroInterpretationService

engine = AstrologyEngine()
interpreter = AstroInterpretationService()

# Random birth date and time:
# Native: Rohan Mukherjee
# Date of Birth: 27 November 1996, 04:42 AM IST (UTC: 26 Nov 1996 23:12:00)
# Place: Kolkata, West Bengal (22.5726 N, 88.3639 E)
# Target Date: 21 September 2026
birth_utc = datetime(1996, 11, 26, 23, 12, 0, tzinfo=UTC)
lat = 22.5726
lon = 88.3639
name = "Rohan Mukherjee"
target_utc = datetime(2026, 9, 21, 12, 0, 0, tzinfo=UTC)

chart = engine.calculate_natal(
    utc_datetime=birth_utc,
    latitude=lat,
    longitude=lon,
    system=AstrologySystem.KP,
)

# Generate full Life Blueprint in KP system
blueprint = interpreter.generate_analysis(
    chart_dict=chart,
    focus=AnalysisFocus.LIFE_BLUEPRINT,
    target_date=target_utc,
    name=name,
    system=AstrologySystem.KP,
)

print("=== BLUEPRINT OUTPUT START ===")
print(blueprint.formatted_reading)
print("=== BLUEPRINT OUTPUT END ===")

# Also generate Domain Career analysis
career_reading = interpreter.generate_analysis(
    chart_dict=chart,
    focus=AnalysisFocus.CAREER,
    target_date=target_utc,
    name=name,
    system=AstrologySystem.KP,
)

print("=== CAREER OUTPUT START ===")
print(career_reading.formatted_reading)
print("=== CAREER OUTPUT END ===")
