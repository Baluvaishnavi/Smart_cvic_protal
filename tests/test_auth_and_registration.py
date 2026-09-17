"""
Unit and integration tests for User Registration (first-time citizens),
Login (returning citizens & single constant administrator), and role-based access control.
"""

import sys
import os
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from app.database import db, init_db
from app.seed_data import seed_nyc_311_data
from app.config import ADMIN_EMAIL, ADMIN_PASSWORD

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    init_db()
    seed_nyc_311_data(db, force=True)
    yield


def test_first_time_citizen_registration():
    """Verify first-time user registration creates persistent citizen in MongoDB."""
    reg_payload = {
        "name": "Alex Morgan",
        "email": "alex.morgan@mycity.org",
        "password": "SecurePassword123",
        "phone": "(555) 349-1029"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["role"] == "CITIZEN"
    assert data["email"] == "alex.morgan@mycity.org"
    assert "token" in data

    # Verify user exists in MongoDB with hashed password
    user_in_db = db["users"].find_one({"email": "alex.morgan@mycity.org"})
    assert user_in_db is not None
    assert user_in_db["name"] == "Alex Morgan"
    assert user_in_db["password_hash"] != "SecurePassword123"  # Must be hashed!


def test_duplicate_registration_rejected():
    """Attempting to register with an existing email must be rejected with 400."""
    res = client.post("/api/auth/register", json={
        "name": "Imposter Alex",
        "email": "alex.morgan@mycity.org",
        "password": "AnotherPassword"
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"].lower()


def test_registration_with_admin_email_blocked():
    """No public user can register using the reserved admin email."""
    res = client.post("/api/auth/register", json={
        "name": "Fake Admin",
        "email": ADMIN_EMAIL,
        "password": "password123"
    })
    assert res.status_code == 403
    assert "reserved" in res.json()["detail"].lower()


def test_returning_citizen_login():
    """Returning citizen logs in with email and password."""
    # Valid login
    login_res = client.post("/api/auth/login", json={
        "email": "alex.morgan@mycity.org",
        "password": "SecurePassword123"
    })
    assert login_res.status_code == 200
    session = login_res.json()
    assert session["role"] == "CITIZEN"
    assert session["email"] == "alex.morgan@mycity.org"
    assert "token" in session

    # Invalid password
    bad_pw_res = client.post("/api/auth/login", json={
        "email": "alex.morgan@mycity.org",
        "password": "WrongPassword999"
    })
    assert bad_pw_res.status_code == 401

    # Non-existent user
    non_user_res = client.post("/api/auth/login", json={
        "email": "nobody@nowhere.org",
        "password": "AnyPassword"
    })
    assert non_user_res.status_code == 401


def test_single_constant_admin_login():
    """Verify only the single designated constant admin can log in as ADMIN."""
    # Correct admin login
    res = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert res.status_code == 200
    admin_session = res.json()
    assert admin_session["role"] == "ADMIN"
    assert admin_session["email"] == ADMIN_EMAIL

    # Wrong admin password
    bad_admin = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": "wrong_password_attempt"
    })
    assert bad_admin.status_code == 401


def test_strict_admin_endpoint_authorization():
    """Verify citizen tokens cannot perform administrative ticket approvals."""
    # 1. Login citizen
    cit_res = client.post("/api/auth/login", json={
        "email": "alex.morgan@mycity.org",
        "password": "SecurePassword123"
    })
    cit_token = cit_res.json()["token"]

    # 2. Login admin
    adm_res = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    adm_token = adm_res.json()["token"]

    # 3. Create a complaint
    c_res = client.post("/api/complaints", json={
        "title": "Severe pothole on 4th Main",
        "description": "Large road crater causing accidents",
        "category": "Pothole",
        "location_address": "4th Main & Central Ave",
        "borough": "Central Ward",
        "citizen_email": "alex.morgan@mycity.org"
    })
    cid = c_res.json()["id"]

    # 4. Citizen tries to approve ticket -> MUST RETURN 403 FORBIDDEN
    cit_approval = client.patch(
        f"/api/complaints/{cid}/approval",
        json={"approval_status": "APPROVED", "admin_review_notes": "Citizen trying to self-approve"},
        headers={"Authorization": f"Bearer {cit_token}"}
    )
    assert cit_approval.status_code == 403

    # 5. Admin approves ticket -> MUST SUCCEED (200 OK)
    adm_approval = client.patch(
        f"/api/complaints/{cid}/approval",
        json={"approval_status": "APPROVED", "admin_review_notes": "Official municipal approval verified"},
        headers={"Authorization": f"Bearer {adm_token}"}
    )
    assert adm_approval.status_code == 200
    assert adm_approval.json()["approval_status"] == "APPROVED"
