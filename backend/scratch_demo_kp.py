"""Demo script demonstrating KP Astrology (Krishnamurti Paddhati) engine.

Computes a sample birth chart, displays the KP sub-lord table mappings,
cuspal sub-lords, 4-level significators, ruling planets, and generates
the full structured horoscope analysis and life blueprint.
"""

from datetime import UTC, datetime
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from app.astrology.engine import AstrologyEngine
from app.config.constants import AstrologySystem, Ayanamsa, HouseSystem
from app.schemas.analysis import AnalysisFocus
from app.services.ai_interpretation import AstroInterpretationService


def run_kp_demo() -> None:
    engine = AstrologyEngine()
    interpreter = AstroInterpretationService()

    # Sample Birth Data:
    # Native: Ananya Sharma
    # Date: October 14, 1993, 08:45 AM IST (03:15 UTC)
    # Place: Jaipur, Rajasthan (26.9124° N, 75.7873° E)
    # Query Date: September 21, 2026
    birth_dt = datetime(1993, 10, 14, 3, 15, 0, tzinfo=UTC)
    query_dt = datetime(2026, 9, 21, 10, 30, 0, tzinfo=UTC)
    lat = 26.9124
    lon = 75.7873
    name = "Ananya Sharma"

    print("================================================================================")
    print(f"  KP ASTROLOGY (KRISHNAMURTI PADDHATI) SYSTEM DEMO")
    print(f"  Native: {name}")
    print(f"  Birth Time (UTC): {birth_dt.isoformat()} | Jaipur (Lat: {lat}, Lon: {lon})")
    print("================================================================================\n")

    # 1. Calculate KP Natal Chart
    chart = engine.calculate_kp_chart(
        utc_datetime=birth_dt,
        latitude=lat,
        longitude=lon,
        query_datetime=query_dt,
    )

    print("─── 1. ASCENDANT & CORE KP IDENTIFIERS ───")
    print(f"  Ascendant Degree   : {chart.ascendant_longitude:.4f}° ({chart.ascendant_rashi})")
    print(f"  Nakshatra          : {chart.ascendant_nakshatra.name} (Pada {chart.ascendant_nakshatra.pada})")
    print(f"  Star Lord          : {chart.ascendant_sublord_info.star_lord}")
    print(f"  KP Sub-Lord        : {chart.ascendant_sublord_info.sub_lord}")
    print(f"  KP Sub-Sub-Lord    : {chart.ascendant_sublord_info.sub_sub_lord}")
    print(f"  KP Number (1-249)  : #{chart.ascendant_sublord_info.kp_number}")
    print(f"  Ayanamsa           : {chart.ayanamsa} ({chart.ayanamsa_value:.4f}°)\n")

    print("─── 2. PLACIDUS HOUSE CUSPS & KP SUB-LORDS ───")
    for cusp in chart.cuspal_analysis:
        signifies = ", ".join(str(h) for h in cusp.sub_lord_signifies_houses) or "None"
        pos_str = "Favorable" if cusp.is_promise_positive else "Mixed"
        print(
            f"  Cusp {cusp.cusp_number:2d} | {cusp.longitude:7.2f}° ({cusp.rashi_name:<11}) | "
            f"Sign Lord: {cusp.sign_lord:<7} | Star Lord: {cusp.star_lord:<7} | "
            f"Sub-Lord: {cusp.sub_lord:<7} | KP #{cusp.kp_number:3d} | "
            f"Signifies: [{signifies}] -> {pos_str}"
        )
    print()

    print("─── 3. PLANETS IN KP SUB-LORD POSITIONS ───")
    for g in chart.grahas:
        print(
            f"  {g.name:<10} ({g.western_name:<11}) | Longitude: {g.longitude:7.2f}° ({g.rashi_name:<11}) | "
            f"House: {g.house_number:2d} | Star: {g.star_lord:<7} | Sub: {g.sub_lord:<7} | Sub-Sub: {g.sub_sub_lord:<7} | "
            f"KP #{g.kp_number:3d}"
        )
    print()

    print("─── 4. KP 4-LEVEL SIGNIFICATORS HIERARCHY ───")
    for p_name, sig in chart.significators.items():
        l1 = ", ".join(str(h) for h in sig.level_1_houses) or "—"
        l2 = ", ".join(str(h) for h in sig.level_2_houses) or "—"
        l3 = ", ".join(str(h) for h in sig.level_3_houses) or "—"
        l4 = ", ".join(str(h) for h in sig.level_4_houses) or "—"
        print(
            f"  {p_name:<10} | L1 (Star of Occ): [{l1:<5}] | L2 (Occ): [{l2:<5}] | "
            f"L3 (Star of Lord): [{l3:<5}] | L4 (Lord): [{l4:<5}] | "
            f"Strong: {sig.strong_houses}"
        )
    print()

    print("─── 5. KP RULING PLANETS (PRECISION EVENT TIMING DOWN TO DAYS/HOURS) ───")
    rp = chart.ruling_planets_at_birth
    print(f"  At Birth Moment ({rp.moment_utc}):")
    print(f"    • Ascendant Sign Lord : {rp.ascendant_sign_lord}")
    print(f"    • Ascendant Star Lord : {rp.ascendant_star_lord}")
    print(f"    • Ascendant Sub-Lord  : {rp.ascendant_sub_lord}")
    print(f"    • Moon Sign Lord      : {rp.moon_sign_lord}")
    print(f"    • Moon Star Lord      : {rp.moon_star_lord}")
    print(f"    • Moon Sub-Lord       : {rp.moon_sub_lord}")
    print(f"    • Day Lord (Weekday)  : {rp.day_lord}")

    if chart.ruling_planets_at_query:
        rp_q = chart.ruling_planets_at_query
        print(f"\n  At Query Moment ({rp_q.moment_utc}):")
        print(f"    • Ascendant Sign Lord : {rp_q.ascendant_sign_lord}")
        print(f"    • Ascendant Star Lord : {rp_q.ascendant_star_lord}")
        print(f"    • Moon Sign Lord      : {rp_q.moon_sign_lord}")
        print(f"    • Moon Star Lord      : {rp_q.moon_star_lord}")
        print(f"    • Day Lord (Weekday)  : {rp_q.day_lord}")
    print()

    # 6. Generate Career Reading via KP Rules
    chart_dict = chart.to_dict()
    analysis_res = interpreter.generate_analysis(
        chart_dict=chart_dict,
        focus=AnalysisFocus.CAREER,
        target_date=query_dt,
        name=name,
        system=AstrologySystem.KP,
    )

    print("================================================================================")
    print("  KP STRUCTURED CAREER INTERPRETATION (EVENT-ORIENTED TIMING)")
    print("================================================================================\n")
    print(analysis_res.formatted_reading)
    print()

    # 7. Generate Full KP Life Blueprint (Birth to Death)
    blueprint_res = interpreter.generate_analysis(
        chart_dict=chart_dict,
        focus=AnalysisFocus.LIFE_BLUEPRINT,
        target_date=query_dt,
        name=name,
        system=AstrologySystem.KP,
    )

    print("================================================================================")
    print("  KP COMPLETE LIFE BLUEPRINT (BIRTH TO DEATH - 7 SECTIONS)")
    print("================================================================================\n")
    print(blueprint_res.formatted_reading)
    print()
    print("DEMO COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    run_kp_demo()
