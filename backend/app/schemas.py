"""
Pydantic v2 schemas for API validation and serialization.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ScoreBreakdown(BaseModel):
    base_severity: float
    age_hours: float
    age_penalty: float
    duplicate_count: int
    duplicate_bonus: float
    location_risk_bonus: float
    sla_breached: bool
    sla_penalty: float
    total_score: float
    priority_tier: str
    explanation: str


class TimelineItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_status: Optional[str] = None
    to_status: str
    actor: str
    notes: Optional[str] = None
    created_at: datetime


class CommentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author: str
    author_type: str
    comment: str
    created_at: datetime


class ComplaintBase(BaseModel):
    title: Optional[str] = None
    description: str
    raw_input: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    location_address: str
    borough: str = "Central Ward"
    zone: Optional[str] = "Central Ward"
    zip_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    priority: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    citizen_email: Optional[str] = "citizen@civicportal.gov"
    citizen_name: Optional[str] = "Civic Resident"
    citizen_phone: Optional[str] = None
    approval_status: str = "PENDING_REVIEW"
    admin_review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None


class ComplaintCreate(ComplaintBase):
    pass


class ComplaintApprovalUpdate(BaseModel):
    approval_status: str = Field(..., description="APPROVED, REJECTED, or PENDING_REVIEW")
    admin_review_notes: Optional[str] = None
    assigned_department: Optional[str] = None
    reviewed_by: str = "Municipal Operations Administrator"


class BatchApprovalRequest(BaseModel):
    complaint_ids: List[str] = Field(..., min_length=1, description="List of complaint IDs to approve/reject")
    approval_status: str = Field(..., description="APPROVED or REJECTED")
    admin_review_notes: Optional[str] = None
    assigned_department: Optional[str] = None
    reviewed_by: str = "Municipal Operations Administrator"


class UserRegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, description="Citizen Full Name")
    email: str = Field(..., min_length=5, description="Citizen Email Address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")
    phone: Optional[str] = Field(None, description="Contact Phone Number")


class AuthLoginRequest(BaseModel):
    email: str
    password: str
    role: Optional[str] = None  # "CITIZEN" or "ADMIN"
    name: Optional[str] = None


class UserSession(BaseModel):
    id: str
    name: str
    email: str
    role: str  # "CITIZEN" or "ADMIN"
    department: Optional[str] = None
    phone: Optional[str] = None
    token: str


class ComplaintUpdateStatus(BaseModel):
    status: str = Field(..., description="NEW, ASSIGNED, IN_PROGRESS, RESOLVED, CLOSED, DUPLICATE")
    actor: str = "Municipal Staff"
    notes: Optional[str] = None
    resolution_notes: Optional[str] = None


class ComplaintAssign(BaseModel):
    department: str
    officer: Optional[str] = "Field Operations Team"
    actor: str = "Dispatch Admin"
    notes: Optional[str] = None


class CommentCreate(BaseModel):
    author: str
    author_type: str = "Citizen"  # Citizen or Official
    comment: str


class ComplaintSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    category: str
    status: str
    priority: str
    priority_score: float
    location_address: str
    borough: str
    zone: Optional[str] = "Central Ward"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    assigned_department: Optional[str] = None
    similar_complaint_count: int
    created_at: datetime
    sla_due_date: datetime
    is_sla_breached: bool
    age_hours: float
    citizen_email: Optional[str] = "citizen@civicportal.gov"
    citizen_name: Optional[str] = "Civic Resident"
    approval_status: str = "PENDING_REVIEW"
    admin_review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None


class ComplaintDetail(ComplaintSummary):
    description: str
    raw_input: Optional[str] = None
    sub_category: Optional[str] = None
    score_breakdown: Optional[Dict[str, Any]] = None
    assigned_officer: Optional[str] = None
    is_duplicate_of_id: Optional[str] = None
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timeline: List[TimelineItem] = []
    comments: List[CommentItem] = []


class AIAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=5, description="Unstructured citizen complaint text")


class AIAnalyzeResponse(BaseModel):
    category: str
    urgency: str
    issue_summary: str
    extracted_location: Optional[str] = None
    confidence: float
    suggested_department: str
    model_source: Optional[str] = None
    top_candidates: Optional[List[Dict[str, Any]]] = None
    explanation: str


class HotspotLocation(BaseModel):
    latitude: float
    longitude: float
    borough: str
    location_address: str
    count: int
    max_priority_score: float
    highest_priority: str
    categories: List[str]
    complaint_ids: List[str]
