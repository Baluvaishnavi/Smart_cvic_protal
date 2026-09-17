"""
Unit tests for rule-based prioritization engine.
Validates multi-factor scoring based on age, category, duplicate reports, location risk, and SLA breaches.
"""

import sys
import os
from datetime import datetime, timedelta, timezone

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.prioritization import calculate_priority, evaluate_location_risk
from app.config import CATEGORIES_CONFIG


def test_base_category_severities():
    """Verify base severity rankings conform to civic hazard levels."""
    now = datetime.now(timezone.utc)
    sla = now + timedelta(hours=48)

    water_res = calculate_priority("Water Supply", now, sla, similar_count=0, location_address="", current_time=now)
    light_res = calculate_priority("Streetlight", now, sla, similar_count=0, location_address="", current_time=now)
    pothole_res = calculate_priority("Pothole", now, sla, similar_count=0, location_address="", current_time=now)
    sanitation_res = calculate_priority("Garbage & Sanitation", now, sla, similar_count=0, location_address="", current_time=now)

    assert water_res["base_severity"] == 40.0
    assert light_res["base_severity"] == 35.0
    assert pothole_res["base_severity"] == 25.0
    assert sanitation_res["base_severity"] == 20.0
    assert water_res["total_score"] > light_res["total_score"] > pothole_res["total_score"] > sanitation_res["total_score"]


def test_aging_penalty():
    """Verify points accumulate over time as ticket remains open."""
    now = datetime.now(timezone.utc)
    # 24 hours open
    created_24h = now - timedelta(hours=24)
    sla = created_24h + timedelta(hours=96)  # Not yet breached

    res_fresh = calculate_priority("Streetlight", now, sla, similar_count=0, location_address="", current_time=now)
    res_24h = calculate_priority("Streetlight", created_24h, sla, similar_count=0, location_address="", current_time=now)

    assert res_24h["age_hours"] == 24.0
    # 24h / 12h * 2.5 = 5.0
    assert res_24h["age_penalty"] == 5.0
    assert res_24h["total_score"] == res_fresh["total_score"] + 5.0


def test_sla_breach_penalty():
    """Verify overdue tickets receive the +25 SLA breach penalty."""
    now = datetime.now(timezone.utc)
    created = now - timedelta(hours=50)
    sla_breached = now - timedelta(hours=2)  # 2 hours overdue

    res = calculate_priority("Streetlight", created, sla_breached, similar_count=0, location_address="", current_time=now)
    assert res["sla_breached"] is True
    assert res["sla_penalty"] == 25.0
    assert res["total_score"] >= 65.0  # Base 35 + Age ~10 + SLA 25 = 70+


def test_similar_complaints_multiplier():
    """Verify duplicates / 'Me Too' upvotes boost the priority score."""
    now = datetime.now(timezone.utc)
    sla = now + timedelta(hours=48)

    single_report = calculate_priority("Pothole", now, sla, similar_count=0, location_address="", current_time=now)
    two_duplicates = calculate_priority("Pothole", now, sla, similar_count=2, location_address="", current_time=now)

    # 2 duplicates * 12 points = 24 points
    assert two_duplicates["duplicate_bonus"] == 24.0
    assert two_duplicates["total_score"] == single_report["total_score"] + 24.0


def test_location_risk_bonus():
    """Verify school, hospital, and transit zones trigger risk bonuses."""
    has_risk, bonus, reason = evaluate_location_risk("Outside PS 234 Elementary School")
    assert has_risk is True
    assert bonus == 15.0
    assert "School" in reason

    no_risk, bonus_none, _ = evaluate_location_risk("145 Residential Quiet Way")
    assert no_risk is False
    assert bonus_none == 0.0


def test_priority_tier_classification():
    """Verify mapping of scores to CRITICAL, HIGH, MEDIUM, LOW tiers."""
    now = datetime.now(timezone.utc)
    # Critical condition: Water main break (40) + 48h open (10) + SLA breach (25) + 2 duplicates (24) = 99 -> CRITICAL
    created_48h = now - timedelta(hours=48)
    sla_past = now - timedelta(hours=10)

    critical_res = calculate_priority("Water Supply", created_48h, sla_past, similar_count=2, location_address="Main St School", current_time=now)
    assert critical_res["priority_tier"] == "CRITICAL"
    assert critical_res["total_score"] >= 75.0
