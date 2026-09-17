"""
MongoDB Document Schemas and Helpers for Complaint, Timeline, and Comments.
"""

from datetime import datetime, timezone
import json
from typing import Dict, Any, Optional


def utcnow():
    return datetime.now(timezone.utc)


def format_doc_id(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Helper to ensure MongoDB document has string id and no raw ObjectId serialization issues."""
    if not doc:
        return None
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    # Parse score_breakdown if string
    if "score_breakdown" in doc and isinstance(doc["score_breakdown"], str):
        try:
            doc["score_breakdown"] = json.loads(doc["score_breakdown"])
        except Exception:
            pass
    return doc


class ComplaintModel:
    """Helper class to construct standardized Complaint document dictionaries for MongoDB."""

    @staticmethod
    def create(
        id: str,
        title: str,
        description: str,
        category: str,
        location_address: str,
        borough: str,
        sla_due_date: datetime,
        raw_input: Optional[str] = None,
        sub_category: Optional[str] = None,
        status: str = "NEW",
        priority: str = "MEDIUM",
        priority_score: float = 25.0,
        zip_code: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        assigned_department: Optional[str] = None,
        assigned_officer: Optional[str] = None,
        similar_complaint_count: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        resolved_at: Optional[datetime] = None,
        resolution_notes: Optional[str] = None,
        citizen_email: Optional[str] = "citizen@example.com",
        citizen_name: Optional[str] = "NYC Resident",
        citizen_phone: Optional[str] = None,
        approval_status: str = "PENDING_REVIEW",
        admin_review_notes: Optional[str] = None,
        reviewed_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        now = created_at or utcnow()
        return {
            "id": id,
            "title": title,
            "description": description,
            "raw_input": raw_input or description,
            "category": category,
            "sub_category": sub_category,
            "status": status,
            "priority": priority,
            "priority_score": float(priority_score),
            "score_breakdown": None,
            "location_address": location_address,
            "borough": borough,
            "zip_code": zip_code,
            "latitude": latitude,
            "longitude": longitude,
            "assigned_department": assigned_department,
            "assigned_officer": assigned_officer,
            "similar_complaint_count": similar_complaint_count,
            "is_duplicate_of_id": None,
            "created_at": now,
            "updated_at": updated_at or now,
            "sla_due_date": sla_due_date,
            "resolved_at": resolved_at,
            "resolution_notes": resolution_notes,
            "citizen_email": citizen_email or "citizen@example.com",
            "citizen_name": citizen_name or "NYC Resident",
            "citizen_phone": citizen_phone,
            "approval_status": approval_status,
            "admin_review_notes": admin_review_notes,
            "reviewed_by": reviewed_by,
            "metadata": metadata or {},
        }
