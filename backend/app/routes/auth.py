"""
Authentication & Role-Based Access Control (RBAC) Router.
Handles persistent MongoDB Citizen registration and login, and enforces
strictly single-administrator access for municipal officials.
"""

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Header, Depends, status
from pymongo.database import Database

from app.database import get_db
from app.schemas import AuthLoginRequest, UserRegisterRequest, UserSession
from app.config import (
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    ADMIN_NAME,
    ADMIN_ROLE,
    ADMIN_DEPARTMENT,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# In-memory active session cache
ACTIVE_SESSIONS: Dict[str, Dict[str, Any]] = {}

SALT = "civic_portal_secure_salt_2026_"


def hash_password(password: str) -> str:
    """Generate SHA-256 salted hash of password."""
    return hashlib.sha256((SALT + password).encode("utf-8")).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify raw password against stored salted hash."""
    return hash_password(password) == hashed


def lookup_session(token: str, db: Database) -> Optional[Dict[str, Any]]:
    """Look up active session from memory cache or MongoDB sessions collection."""
    if not token:
        return None
    if token in ACTIVE_SESSIONS:
        return ACTIVE_SESSIONS[token]
    
    session_doc = db["sessions"].find_one({"token": token})
    if session_doc:
        ACTIVE_SESSIONS[token] = session_doc
        return session_doc
    return None


def require_admin(authorization: Optional[str] = Header(None), db: Database = Depends(get_db)) -> Dict[str, Any]:
    """
    Dependency to enforce that ONLY the single authorized municipal administrator
    can access protected administrative endpoints.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative authorization header required."
        )

    token = authorization.replace("Bearer ", "").strip()
    session = lookup_session(token, db)
    if not session or session.get("role") != "ADMIN" or session.get("email", "").lower() != ADMIN_EMAIL.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Only the designated Municipal Administrator can access this section."
        )
    return session


@router.post("/register", response_model=UserSession, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegisterRequest, db: Database = Depends(get_db)):
    """
    First-time citizen registration stored persistently in MongoDB.
    Validates email uniqueness and hashes password.
    """
    clean_email = payload.email.strip().lower()
    clean_name = payload.name.strip()

    # Block registration using the reserved constant Administrator email
    if clean_email == ADMIN_EMAIL.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This email address is reserved for municipal administration. Please use the login tab."
        )

    # Check for existing user in MongoDB
    existing = db["users"].find_one({"email": clean_email})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists. Please log in."
        )

    new_id = f"usr_cit_{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    user_doc = {
        "id": new_id,
        "name": clean_name,
        "email": clean_email,
        "password_hash": hash_password(payload.password),
        "phone": payload.phone.strip() if payload.phone else None,
        "role": "CITIZEN",
        "department": None,
        "created_at": now,
    }
    db["users"].insert_one(user_doc)

    token = f"tok_cit_{uuid.uuid4().hex}"
    session_data = {
        "id": new_id,
        "name": clean_name,
        "email": clean_email,
        "role": "CITIZEN",
        "department": None,
        "phone": user_doc["phone"],
        "token": token,
    }
    ACTIVE_SESSIONS[token] = session_data
    db["sessions"].insert_one({**session_data, "created_at": now})

    return UserSession(**session_data)


@router.post("/login", response_model=UserSession)
def login(payload: AuthLoginRequest, db: Database = Depends(get_db)):
    """
    Authenticate returning citizens or the single designated Municipal Administrator.
    """
    clean_email = payload.email.strip().lower()
    now = datetime.now(timezone.utc)

    # 1. Check if Single Constant Municipal Administrator
    if clean_email == ADMIN_EMAIL.lower():
        if payload.password != ADMIN_PASSWORD:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid administrator credentials."
            )
        token = f"tok_admin_{uuid.uuid4().hex[:16]}"
        admin_session = {
            "id": "usr_admin_001",
            "name": ADMIN_NAME,
            "email": ADMIN_EMAIL,
            "role": ADMIN_ROLE,
            "department": ADMIN_DEPARTMENT,
            "phone": "Official City Operations",
            "token": token,
        }
        ACTIVE_SESSIONS[token] = admin_session
        db["sessions"].insert_one({**admin_session, "created_at": now})
        return UserSession(**admin_session)

    # 2. Citizen Login via MongoDB
    user = db["users"].find_one({"email": clean_email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No account found with this email. Please register first using the Register tab."
        )

    if not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password. Please try again."
        )

    token = f"tok_cit_{uuid.uuid4().hex}"
    user_session = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "role": "CITIZEN",
        "department": None,
        "phone": user.get("phone"),
        "token": token,
    }
    ACTIVE_SESSIONS[token] = user_session
    db["sessions"].insert_one({**user_session, "created_at": now})
    return UserSession(**user_session)


@router.get("/me", response_model=UserSession)
def get_current_user(authorization: Optional[str] = Header(None), db: Database = Depends(get_db)):
    """Retrieve profile of the currently active session token."""
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    token = authorization.replace("Bearer ", "").strip()
    session = lookup_session(token, db)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired or invalid")

    return UserSession(**session)


@router.post("/logout")
def logout(authorization: Optional[str] = Header(None), db: Database = Depends(get_db)):
    """Terminate active session."""
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        ACTIVE_SESSIONS.pop(token, None)
        db["sessions"].delete_many({"token": token})
    return {"status": "success", "message": "Successfully logged out."}


@router.get("/admin-info")
def get_admin_info():
    """Information regarding administrator configuration."""
    return {
        "admin_email": ADMIN_EMAIL,
        "admin_name": ADMIN_NAME,
        "admin_department": ADMIN_DEPARTMENT,
        "note": "Only the designated administrator may access municipal queue triage and operations."
    }
