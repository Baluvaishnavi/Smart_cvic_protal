"""
Unit test verifying that complaints submission, listing, my-complaints,
upvoting, and analytics work seamlessly even when MongoDB is offline / connection refused.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from app.database import get_db
import pymongo.errors

client = TestClient(app)


def failing_db_dependency():
    """Mock DB where every operation raises ConnectionFailure or ServerSelectionTimeoutError."""
    mock_db = MagicMock()
    mock_coll = MagicMock()
    mock_coll.find.side_effect = pymongo.errors.ServerSelectionTimeoutError("localhost:27017: connection refused")
    mock_coll.find_one.side_effect = pymongo.errors.ServerSelectionTimeoutError("localhost:27017: connection refused")
    mock_coll.insert_one.side_effect = pymongo.errors.ServerSelectionTimeoutError("localhost:27017: connection refused")
    mock_coll.update_one.side_effect = pymongo.errors.ServerSelectionTimeoutError("localhost:27017: connection refused")
    mock_db.__getitem__.return_value = mock_coll
    yield mock_db


def test_complaint_submission_resilience_when_mongodb_is_down():
    """Ensure complaint submission returns 201 Created even when DB connection is refused."""
    app.dependency_overrides[get_db] = failing_db_dependency
    try:
        payload = {
            "title": "Severe water leakage on Central Boulevard",
            "description": "Main water pipeline ruptured, flooding the road.",
            "category": "Water Supply",
            "location_address": "100 Central Boulevard",
            "borough": "Central Ward",
            "citizen_email": "citizen@civicportal.gov",
            "citizen_name": "Sarah Jenkins"
        }
        res = client.post("/api/complaints", json=payload)
        assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.text}"
        data = res.json()
        assert data["id"].startswith("CIVIC-2026-")
        assert data["status"] == "NEW"
        assert data["category"] == "Water Supply"

        # Verify it can be retrieved from my-complaints
        my_res = client.get("/api/complaints/my-complaints?citizen_email=citizen@civicportal.gov")
        assert my_res.status_code == 200
        my_data = my_res.json()
        ids = [c["id"] for c in my_data]
        assert data["id"] in ids

        # Verify upvote works
        up_res = client.post(f"/api/complaints/{data['id']}/upvote")
        assert up_res.status_code == 200
        assert up_res.json()["similar_complaint_count"] >= 1

        # Verify analytics dashboard does not crash
        dash_res = client.get("/api/analytics/dashboard")
        assert dash_res.status_code == 200
        assert dash_res.json()["summary"]["total"] >= 1
    finally:
        app.dependency_overrides.clear()
