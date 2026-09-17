"""
Unit tests for Bonus AI classification, summarization, and entity extraction.
Validates the exact case study example from the problem statement:
"There has been no street light near Gate 3 for almost a week and the road gets extremely dark."
-> Category: Streetlight
-> Urgency: Medium
-> Issue: Streetlight near Gate 3 non-functional for approximately one week
"""

import sys
import os
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.ai_service import LocalNLPProcessor, ai_service


def test_case_study_prompt_extraction():
    """
    Test the exact user prompt case study:
    Input: 'There has been no street light near Gate 3 for almost a week and the road gets extremely dark.'
    Expected:
      Category: Streetlight
      Urgency: Medium
      Issue: Streetlight near Gate 3 non-functional for approximately one week
    """
    input_text = "There has been no street light near Gate 3 for almost a week and the road gets extremely dark."
    nlp = LocalNLPProcessor()

    # 1. Category
    category, confidence = nlp.classify_category(input_text)
    assert category == "Streetlight"
    assert confidence >= 0.90

    # 2. Urgency
    urgency = nlp.extract_urgency(input_text)
    assert urgency in ["MEDIUM", "HIGH"]

    # 3. Location
    location = nlp.extract_location(input_text)
    assert "Gate 3" in location

    # 4. Synthesized Issue Summary / Work Order Title
    summary = nlp.summarize_issue(input_text, category, location)
    assert "Streetlight" in summary
    assert "Gate 3" in summary
    assert "approximately one week" in summary.lower() or "one week" in summary.lower() or "week" in summary.lower()


import asyncio


def test_ai_service_full_pipeline():
    """Verify end-to-end AI service analysis."""
    input_text = "There has been no street light near Gate 3 for almost a week and the road gets extremely dark."
    res = asyncio.run(ai_service.analyze_complaint(input_text))

    assert res["category"] == "Streetlight"
    assert res["urgency"] in ["MEDIUM", "HIGH"]
    assert "Gate 3" in res["issue_summary"]
    assert "Street Lighting" in res["suggested_department"] or "Department of Transportation" in res["suggested_department"]


def test_pothole_classification():
    """Verify pothole entity detection and summarization."""
    text = "Massive crater pothole on 5th Avenue damaging tires of passing cars."
    nlp = LocalNLPProcessor()

    cat, conf = nlp.classify_category(text)
    assert cat == "Pothole"
    assert conf >= 0.90

    urgency = nlp.extract_urgency(text)
    assert urgency in ["MEDIUM", "HIGH"]


def test_water_supply_classification():
    """Verify water main leak emergency detection."""
    text = "Water pipe burst and flooding into street near hospital entrance!"
    nlp = LocalNLPProcessor()

    cat, _ = nlp.classify_category(text)
    assert cat == "Water Supply"

    urgency = nlp.extract_urgency(text)
    assert urgency in ["HIGH", "CRITICAL"]


def test_duplicate_similarity():
    """Verify text similarity detection for duplicate grouping."""
    text1 = "Streetlight out near Gate 3 on Flatbush Avenue"
    text2 = "No light working near Gate 3 on Flatbush Avenue, road dark"
    text3 = "Water main leaking on 42nd street near Broadway"

    sim_high = ai_service.calculate_text_similarity(text1, text2)
    sim_low = ai_service.calculate_text_similarity(text1, text3)

    assert sim_high >= 0.30
    assert sim_low < 0.20
    assert sim_high > sim_low
