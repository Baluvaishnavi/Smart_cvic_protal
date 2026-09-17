"""
Unit and integration tests for Role-Based Access Control (RBAC),
Citizen privacy isolation, and Municipal Administrative ticket approval workflows.
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


def test_auth_login_and_roles():
    """Verify login authentication for Citizen and Municipal Admin personas."""
    # Test Admin login
    admin_res = client.post(
        "/api/auth/login",
        json={"email": "admin@civicportal.gov", "password": "admin123"}
    )
    assert admin_res.status_code == 200
    admin_data = admin_res.json()
    assert admin_data["role"] == "ADMIN"
    assert admin_data["email"] == "admin@civicportal.gov"
    assert "token" in admin_data

    # Test Citizen login
    citizen_res = client.post(
        "/api/auth/login",
        json={"email": "citizen@civicportal.gov", "password": "citizen123"}
    )
    assert citizen_res.status_code == 200
    citizen_data = citizen_res.json()
    assert citizen_data["role"] == "CITIZEN"
    assert citizen_data["email"] == "citizen@civicportal.gov"
    assert "token" in citizen_data

    # Test invalid credentials
    bad_res = client.post(
        "/api/auth/login",
        json={"email": "admin@civicportal.gov", "password": "wrongpassword"}
    )
    assert bad_res.status_code == 401


def test_citizen_complaint_submission_and_isolation():
    """Verify citizen submits a complaint and can only see their own tickets."""
    citizen_email = "jane.smith@brooklyn.org"
    other_email = "john.doe@queens.org"

    # 1. Submit ticket for Jane
    jane_ticket_res = client.post(
        "/api/complaints",
        json={
            "title": "Severe water pipe leak flooding sidewalk",
            "description": "Continuous gushing water in front of residential brownstone.",
            "category": "Water Supply",
            "location_address": "452 7th Ave, Brooklyn, NY",
            "borough": "Brooklyn",
            "priority": "HIGH",
            "citizen_name": "Jane Smith",
            "citizen_email": citizen_email,
            "citizen_phone": "(718) 555-0144"
        }
    )
    assert jane_ticket_res.status_code == 201
    jane_ticket = jane_ticket_res.json()
    jane_id = jane_ticket["id"]
    assert jane_ticket["approval_status"] == "PENDING_REVIEW"
    assert jane_ticket["citizen_email"] == citizen_email

    # 2. Query complaints for Jane's email
    jane_feed_res = client.get(f"/api/complaints/my-complaints?citizen_email={citizen_email}")
    assert jane_feed_res.status_code == 200
    jane_feed = jane_feed_res.json()
    assert isinstance(jane_feed, list)
    assert any(c["id"] == jane_id for c in jane_feed)
    for c in jane_feed:
        assert c["citizen_email"].lower() == citizen_email.lower()

    # 3. Query complaints for another citizen - Jane's ticket must NOT appear
    other_feed_res = client.get(f"/api/complaints/my-complaints?citizen_email={other_email}")
    assert other_feed_res.status_code == 200
    other_feed = other_feed_res.json()
    assert isinstance(other_feed, list)
    assert not any(c["id"] == jane_id for c in other_feed)


def test_admin_approval_and_rejection_workflow():
    """Verify administrator approval lifecycle transitions and audit logging."""
    ticket_res = client.post(
        "/api/complaints",
        json={
            "title": "Dangerous pothole damaging tires",
            "description": "Deep 12-inch crater right before intersection.",
            "category": "Pothole",
            "location_address": "125th St & St. Nicholas Ave",
            "borough": "Manhattan",
            "priority": "HIGH",
            "citizen_name": "Marcus Vance",
            "citizen_email": "marcus@harlem.org"
        }
    )
    assert ticket_res.status_code == 201
    ticket_id = ticket_res.json()["id"]

    # 1. Admin Approves Ticket
    approval_res = client.patch(
        f"/api/complaints/{ticket_id}/approval",
        json={
            "approval_status": "APPROVED",
            "admin_review_notes": "Verified by Queens/Manhattan DOT dispatch. Crew scheduled.",
            "reviewed_by": "Ops Manager Davis"
        }
    )
    assert approval_res.status_code == 200
    approved_ticket = approval_res.json()
    assert approved_ticket["approval_status"] == "APPROVED"
    assert approved_ticket["status"] == "ASSIGNED"
    assert approved_ticket["reviewed_by"] == "Ops Manager Davis"

    # Verify audit timeline recorded the approval
    detail_res = client.get(f"/api/complaints/{ticket_id}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert any("APPROVED" in item.get("notes", "") for item in detail["timeline"])

    # 2. Test Rejection Workflow on another ticket
    spam_res = client.post(
        "/api/complaints",
        json={
            "title": "Advertising billboard advertisement",
            "description": "I do not like the shoes advertised on this billboard.",
            "category": "Noise & Disturbance",
            "location_address": "Times Square",
            "borough": "Manhattan",
            "citizen_email": "tester@test.com"
        }
    )
    spam_id = spam_res.json()["id"]

    reject_res = client.patch(
        f"/api/complaints/{spam_id}/approval",
        json={
            "approval_status": "REJECTED",
            "admin_review_notes": "Out of municipal jurisdiction. Private commercial display.",
            "reviewed_by": "Director Vance"
        }
    )
    assert reject_res.status_code == 200
    rejected_ticket = reject_res.json()
    assert rejected_ticket["approval_status"] == "REJECTED"
    assert rejected_ticket["status"] == "RESOLVED"
    assert "jurisdiction" in rejected_ticket["admin_review_notes"]


def test_batch_approval_and_filter():
    """Verify batch approval endpoint and approval_status query filter."""
    # 1. Login as Admin
    admin_login = client.post(
        "/api/auth/login",
        json={"email": "admin@civicportal.gov", "password": "admin123"}
    )
    admin_token = admin_login.json()["token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Login as Citizen
    citizen_login = client.post(
        "/api/auth/login",
        json={"email": "citizen@civicportal.gov", "password": "citizen123"}
    )
    citizen_token = citizen_login.json()["token"]
    citizen_headers = {"Authorization": f"Bearer {citizen_token}"}

    # 3. Create two pending complaints
    c1 = client.post(
        "/api/complaints",
        json={
            "title": "Batch Test 1: Pothole on North Road",
            "description": "Large hole in asphalt",
            "category": "Pothole",
            "location_address": "12 North Road",
            "borough": "North District",
            "priority": "MEDIUM",
            "citizen_name": "Citizen One",
            "citizen_email": "one@test.gov"
        }
    ).json()["id"]

    c2 = client.post(
        "/api/complaints",
        json={
            "title": "Batch Test 2: Streetlight out on East Ave",
            "description": "Dark street pole",
            "category": "Streetlight",
            "location_address": "45 East Ave",
            "borough": "East Sector",
            "priority": "HIGH",
            "citizen_name": "Citizen Two",
            "citizen_email": "two@test.gov"
        }
    ).json()["id"]

    # 4. Filter by approval_status=PENDING_REVIEW
    pending_list = client.get("/api/complaints?approval_status=PENDING_REVIEW").json()
    assert any(c["id"] == c1 for c in pending_list)
    assert any(c["id"] == c2 for c in pending_list)

    # 5. Non-admin cannot batch approve (403 Forbidden)
    forbidden_res = client.post(
        "/api/complaints/batch-approval",
        headers=citizen_headers,
        json={
            "complaint_ids": [c1, c2],
            "approval_status": "APPROVED",
            "admin_review_notes": "Attempt by citizen"
        }
    )
    assert forbidden_res.status_code == 403

    # 6. Admin batch approves both tickets
    batch_res = client.post(
        "/api/complaints/batch-approval",
        headers=admin_headers,
        json={
            "complaint_ids": [c1, c2],
            "approval_status": "APPROVED",
            "admin_review_notes": "Bulk approved by Municipal Admin.",
            "assigned_department": "Municipal Operations Directorate"
        }
    )
    assert batch_res.status_code == 200
    batch_data = batch_res.json()
    assert batch_data["success"] is True
    assert batch_data["processed_count"] == 2
    assert c1 in batch_data["complaint_ids"]
    assert c2 in batch_data["complaint_ids"]

    # 7. Check tickets are now APPROVED
    approved_list = client.get("/api/complaints?approval_status=APPROVED").json()
    assert any(c["id"] == c1 for c in approved_list)
    assert any(c["id"] == c2 for c in approved_list)
