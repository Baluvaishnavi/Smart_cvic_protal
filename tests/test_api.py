"""
Integration tests for FastAPI complaints, lifecycle queues, upvotes, and analytics endpoints.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from app.database import db, init_db
from app.seed_data import seed_nyc_311_data

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    seed_nyc_311_data(db, force=True)
    yield


def test_health_and_config():
    """Verify health check and category config endpoints."""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "online"

    res_cat = client.get("/api/config/categories")
    assert res_cat.status_code == 200
    data = res_cat.json()
    assert "Streetlight" in data["categories"]
    assert "Water Supply" in data["categories"]


def test_complaint_submission_and_priority():
    """Verify citizen complaint creation with dynamic priority calculation."""
    payload = {
        "title": "Streetlight blackout near school crosswalk",
        "description": "Streetlight pole flickering and completely out at night.",
        "category": "Streetlight",
        "location_address": "Corner of 86th St & Lexington Ave near PS 198 School",
        "borough": "Manhattan",
        "priority": "HIGH"
    }
    res = client.post("/api/complaints", json=payload)
    assert res.status_code == 201
    data = res.json()

    assert data["id"].startswith("CIVIC-2026-") or data["id"].startswith("NYC-2026-")
    assert data["status"] == "NEW"
    assert data["category"] == "Streetlight"
    # Base 35 + School risk 15 = >= 50
    assert data["priority_score"] >= 50.0


def test_complaint_lifecycle_transitions():
    """Verify status updates: NEW -> ASSIGNED -> IN_PROGRESS -> RESOLVED."""
    # 1. Create ticket
    payload = {
        "title": "Pothole on Main St",
        "description": "Pothole damaging vehicle tires",
        "category": "Pothole",
        "location_address": "Main St & 39th Ave",
        "borough": "Queens"
    }
    c_res = client.post("/api/complaints", json=payload)
    cid = c_res.json()["id"]

    # 2. Assign to department
    assign_payload = {
        "department": "Department of Transportation (DOT) - Roadway Repair",
        "officer": "Lead Tech J. Miller",
        "notes": "Dispatched for cold patch filling"
    }
    res_assign = client.post(f"/api/complaints/{cid}/assign", json=assign_payload)
    assert res_assign.status_code == 200
    assert res_assign.json()["status"] == "ASSIGNED"

    # 3. Transition to IN_PROGRESS
    res_prog = client.patch(f"/api/complaints/{cid}/status", json={
        "status": "IN_PROGRESS",
        "notes": "Crew arrived on scene with asphalt roller"
    })
    assert res_prog.status_code == 200
    assert res_prog.json()["status"] == "IN_PROGRESS"

    # 4. Transition to RESOLVED
    res_res = client.patch(f"/api/complaints/{cid}/status", json={
        "status": "RESOLVED",
        "notes": "Patch compacted and cured; roadway reopened",
        "resolution_notes": "Filled with high-grade hot mix asphalt."
    })
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"

    # 5. Verify Timeline Audit History
    detail_res = client.get(f"/api/complaints/{cid}")
    detail = detail_res.json()
    statuses = [t["to_status"] for t in detail["timeline"]]
    assert "NEW" in statuses
    assert "ASSIGNED" in statuses
    assert "IN_PROGRESS" in statuses
    assert "RESOLVED" in statuses


def test_upvote_increases_priority():
    """Verify citizen 'I Have This Issue Too' action boosts priority score."""
    payload = {
        "title": "Broken catch basin water backup",
        "description": "Catch basin blocked with leaves causing water pooling",
        "category": "Water Supply",
        "location_address": "Bedford Ave & N 7th St",
        "borough": "Brooklyn"
    }
    c_res = client.post("/api/complaints", json=payload)
    cid = c_res.json()["id"]
    initial_score = c_res.json()["priority_score"]

    # Upvote
    up_res = client.post(f"/api/complaints/{cid}/upvote")
    assert up_res.status_code == 200
    up_data = up_res.json()

    assert up_data["similar_complaint_count"] == 1
    # Should increase by 12 points
    assert up_data["new_priority_score"] == initial_score + 12.0


def test_analytics_dashboard():
    """Verify dashboard metrics contain summary, distributions, aging, and SLA."""
    res = client.get("/api/analytics/dashboard")
    assert res.status_code == 200
    data = res.json()

    assert "summary" in data
    assert data["summary"]["total"] > 0
    assert "unresolved" in data["summary"]
    assert "sla_compliance_rate" in data["summary"]
    assert "category_distribution" in data
    assert "borough_distribution" in data
    assert "aging_breakdown" in data
    assert "department_sla" in data


def test_geospatial_hotspots():
    """Verify geospatial hotspot clustering."""
    res = client.get("/api/analytics/hotspots")
    assert res.status_code == 200
    hotspots = res.json()
    assert isinstance(hotspots, list)
    assert len(hotspots) > 0
    assert "latitude" in hotspots[0]
    assert "count" in hotspots[0]
    assert "max_priority_score" in hotspots[0]


def test_custom_category_submission_and_filtering():
    """Verify citizen submission of a custom manual category and filtering by OTHER."""
    custom_cat = "Stray Animal Rescue"
    payload = {
        "title": "Injured puppy found near Central Ward bus terminal",
        "description": "Puppy needs urgent medical care and animal welfare rescue assistance",
        "category": custom_cat,
        "location_address": "Terminal Way & 5th Ave",
        "borough": "Central Ward",
        "priority": "HIGH",
        "citizen_email": "citizen@civicportal.gov",
        "citizen_name": "Concerned Citizen"
    }

    # 1. Create with custom category
    res = client.post("/api/complaints", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["category"] == custom_cat
    assert data["status"] == "NEW"
    assert data["priority_score"] > 0
    cid = data["id"]

    # 2. Query with category=OTHER
    res_other = client.get("/api/complaints?category=OTHER")
    assert res_other.status_code == 200
    other_list = res_other.json()
    assert any(c["id"] == cid and c["category"] == custom_cat for c in other_list)

    # 3. Query with search matching custom category keyword
    res_search = client.get("/api/complaints?search=Rescue")
    assert res_search.status_code == 200
    search_list = res_search.json()
    assert any(c["id"] == cid for c in search_list)

