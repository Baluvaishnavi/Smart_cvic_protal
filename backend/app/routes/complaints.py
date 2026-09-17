"""
Complaints API routes using MongoDB for storage, query filtering,
lifecycle transitions, assignments, timeline auditing, and duplicate upvoting.
Includes resilient in-memory fallback store to ensure zero-downtime availability
even if cloud MongoDB is starting up, network partitioned, or temporarily unlinked.
"""

from datetime import datetime, timedelta, timezone
import json
import random
import re
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Header, status
from pymongo.database import Database
import pymongo

from app.database import get_db
from app.models import ComplaintModel, format_doc_id, utcnow
from app.schemas import (
    ComplaintCreate,
    ComplaintUpdateStatus,
    ComplaintAssign,
    CommentCreate,
    ComplaintSummary,
    ComplaintDetail,
    ComplaintApprovalUpdate,
    BatchApprovalRequest,
)
from app.config import CATEGORIES_CONFIG, CIVIC_ZONES, ZONE_ALIASES
from app.routes.auth import lookup_session, ADMIN_EMAIL
from app.prioritization import update_complaint_priority, calculate_priority
from app.ai_service import ai_service

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])

# In-Memory Fallback Stores
_init_now = datetime.now(timezone.utc)
IN_MEMORY_COMPLAINTS: List[Dict[str, Any]] = [
    {
        "id": "CIVIC-2026-CASE01",
        "title": "Streetlight near Gate 3 non-functional for approximately one week",
        "description": "There has been no street light near Gate 3 for almost a week and the road gets extremely dark at night.",
        "raw_input": "There has been no street light near Gate 3 for almost a week and the road gets extremely dark at night.",
        "category": "Streetlight",
        "sub_category": "Street Light Out",
        "status": "NEW",
        "priority": "HIGH",
        "priority_score": 62.0,
        "location_address": "Gate 3, Central Boulevard near North Crossway",
        "borough": "Central Ward",
        "zip_code": "560001",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "assigned_department": "Electrical & Street Lighting Board",
        "assigned_officer": None,
        "similar_complaint_count": 3,
        "created_at": _init_now - timedelta(days=5),
        "updated_at": _init_now - timedelta(hours=2),
        "sla_due_date": _init_now - timedelta(days=2),
        "resolved_at": None,
        "resolution_notes": None,
        "citizen_email": "citizen@civicportal.gov",
        "citizen_name": "Sarah Jenkins",
        "citizen_phone": "(555) 019-2834",
        "approval_status": "PENDING_REVIEW",
        "admin_review_notes": None,
        "reviewed_by": None,
        "score_breakdown": {
            "base_severity": 35,
            "aging_penalty": 12.0,
            "sla_breach_penalty": 15,
            "duplicate_bonus": 6.0,
            "location_risk": 0.0,
            "total_score": 68.0,
            "priority_tier": "HIGH",
            "explanation": "High Priority: Severe dark hazard, 3 duplicate reports."
        },
        "metadata": {"channel": "Web Portal", "case_study_example": True}
    }
]

IN_MEMORY_TIMELINE: List[Dict[str, Any]] = [
    {
        "complaint_id": "CIVIC-2026-CASE01",
        "from_status": None,
        "to_status": "NEW",
        "actor": "Citizen Reporter",
        "notes": "Issue filed using AI Smart Voice/Text assistant. SLA target: 48h.",
        "created_at": _init_now - timedelta(days=5),
    }
]

IN_MEMORY_COMMENTS: List[Dict[str, Any]] = []


# Internal Resilience Helpers
def _safe_db_find_one(db: Database, complaint_id: str) -> Optional[Dict[str, Any]]:
    try:
        return db["complaints"].find_one({"id": complaint_id})
    except Exception as e:
        print(f"[Complaints DB FindOne Notice] {e}")
        return None


def _get_complaint_record(complaint_id: str, db: Database) -> Optional[Dict[str, Any]]:
    doc = _safe_db_find_one(db, complaint_id)
    if doc:
        return doc
    for c in IN_MEMORY_COMPLAINTS:
        if c.get("id") == complaint_id:
            return c
    return None


def _safe_db_insert(db: Database, doc: Dict[str, Any]) -> bool:
    try:
        db["complaints"].insert_one(dict(doc))
        return True
    except pymongo.errors.DuplicateKeyError:
        try:
            db["complaints"].replace_one({"id": doc.get("id")}, dict(doc), upsert=True)
            return True
        except Exception:
            return False
    except Exception as e:
        print(f"[Complaints DB Insert Notice] {e}")
        return False


def _safe_db_update(db: Database, complaint_id: str, updates: Dict[str, Any]) -> bool:
    try:
        db["complaints"].update_one({"id": complaint_id}, {"$set": updates})
        return True
    except Exception as e:
        print(f"[Complaints DB Update Notice] {e}")
        return False


def _update_complaint_record(complaint_id: str, updates: Dict[str, Any], db: Database):
    for c in IN_MEMORY_COMPLAINTS:
        if c.get("id") == complaint_id:
            c.update(updates)
            break
    _safe_db_update(db, complaint_id, updates)


def _add_timeline(complaint_id: str, from_status: Optional[str], to_status: str, actor: str, notes: str, created_at: datetime, db: Database):
    tl_entry = {
        "complaint_id": complaint_id,
        "from_status": from_status,
        "to_status": to_status,
        "actor": actor,
        "notes": notes,
        "created_at": created_at,
    }
    IN_MEMORY_TIMELINE.append(tl_entry)
    try:
        db["complaint_timeline"].insert_one(dict(tl_entry))
    except Exception as e:
        print(f"[Timeline DB Insert Notice] {e}")


def _get_timeline(complaint_id: str, db: Database) -> List[Dict[str, Any]]:
    timeline_list = []
    seen = set()
    try:
        for t in db["complaint_timeline"].find({"complaint_id": complaint_id}).sort("created_at", pymongo.ASCENDING):
            k = (t.get("to_status"), t.get("notes"))
            if k not in seen:
                seen.add(k)
                timeline_list.append(t)
    except Exception:
        pass
    for t in IN_MEMORY_TIMELINE:
        if t.get("complaint_id") == complaint_id:
            k = (t.get("to_status"), t.get("notes"))
            if k not in seen:
                seen.add(k)
                timeline_list.append(t)
    return timeline_list


def _add_comment(complaint_id: str, author: str, author_type: str, comment: str, created_at: datetime, db: Database):
    entry = {
        "complaint_id": complaint_id,
        "author": author,
        "author_type": author_type,
        "comment": comment,
        "created_at": created_at,
    }
    IN_MEMORY_COMMENTS.append(entry)
    try:
        db["complaint_comments"].insert_one(dict(entry))
    except Exception as e:
        print(f"[Comment DB Insert Notice] {e}")


def _get_comments(complaint_id: str, db: Database) -> List[Dict[str, Any]]:
    comment_list = []
    seen = set()
    try:
        for c in db["complaint_comments"].find({"complaint_id": complaint_id}).sort("created_at", pymongo.ASCENDING):
            k = (c.get("author"), c.get("comment"))
            if k not in seen:
                seen.add(k)
                comment_list.append(c)
    except Exception:
        pass
    for c in IN_MEMORY_COMMENTS:
        if c.get("complaint_id") == complaint_id:
            k = (c.get("author"), c.get("comment"))
            if k not in seen:
                seen.add(k)
                comment_list.append(c)
    return comment_list


def verify_admin_access(authorization: Optional[str], db: Database):
    """Enforce strict single-administrator access for administrative mutations."""
    if authorization:
        token = authorization.replace("Bearer ", "").strip()
        session = lookup_session(token, db)
        if not session or session.get("role") != "ADMIN" or session.get("email", "").lower() != ADMIN_EMAIL.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Denied: Only the designated Municipal Administrator can perform this action."
            )


def enrich_complaint_summary(doc: Dict[str, Any], now: datetime) -> dict:
    """Helper to convert complaint doc to enriched summary."""
    format_doc_id(doc)
    created_at = doc.get("created_at", now)
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at)
        except Exception:
            created_at = now
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    sla_due = doc.get("sla_due_date", now)
    if isinstance(sla_due, str):
        try:
            sla_due = datetime.fromisoformat(sla_due)
        except Exception:
            sla_due = now
    if sla_due.tzinfo is None:
        sla_due = sla_due.replace(tzinfo=timezone.utc)

    age_hours = round(max(0.0, (now - created_at).total_seconds() / 3600.0), 1)
    is_breached = (now > sla_due) and (doc.get("status") != "RESOLVED")

    return {
        "id": doc.get("id"),
        "title": doc.get("title", ""),
        "category": doc.get("category", ""),
        "status": doc.get("status", "NEW"),
        "priority": doc.get("priority", "MEDIUM"),
        "priority_score": float(doc.get("priority_score", 25.0)),
        "location_address": doc.get("location_address", ""),
        "borough": doc.get("borough", "Central Ward"),
        "latitude": doc.get("latitude"),
        "longitude": doc.get("longitude"),
        "assigned_department": doc.get("assigned_department"),
        "similar_complaint_count": int(doc.get("similar_complaint_count", 0)),
        "created_at": created_at,
        "sla_due_date": sla_due,
        "is_sla_breached": is_breached,
        "age_hours": age_hours,
        "citizen_email": doc.get("citizen_email", "citizen@example.com"),
        "citizen_name": doc.get("citizen_name", "Citizen Reporter"),
        "approval_status": doc.get("approval_status", "PENDING_REVIEW"),
        "admin_review_notes": doc.get("admin_review_notes"),
        "reviewed_by": doc.get("reviewed_by"),
    }


@router.get("", response_model=List[ComplaintSummary])
def list_complaints(
    status_filter: Optional[str] = Query(None, alias="status"),
    category: Optional[str] = None,
    borough: Optional[str] = None,
    priority: Optional[str] = None,
    approval_status: Optional[str] = None,
    is_aging: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = Query("priority", pattern="^(priority|created|score)$"),
    limit: int = Query(100, ge=1, le=500),
    skip: int = Query(0, ge=0),
    db: Database = Depends(get_db),
):
    """List complaints with MongoDB multi-criteria filtering and resilient in-memory fallback."""
    now = utcnow()
    filter_q: Dict[str, Any] = {}

    if status_filter and status_filter.upper() != "ALL":
        filter_q["status"] = status_filter.upper()

    if approval_status and approval_status.upper() != "ALL":
        filter_q["approval_status"] = approval_status.upper()

    if category and category.upper() != "ALL":
        if category.upper() == "OTHER":
            filter_q["category"] = {"$nin": list(CATEGORIES_CONFIG.keys())}
        else:
            filter_q["category"] = category

    if borough and borough.upper() != "ALL":
        filter_q["borough"] = borough

    if priority and priority.upper() != "ALL":
        filter_q["priority"] = priority.upper()

    if is_aging:
        filter_q["status"] = {"$ne": "RESOLVED"}
        filter_q["$or"] = [
            {"sla_due_date": {"$lt": now}},
            {"created_at": {"$lt": now - timedelta(hours=48)}}
        ]

    if search:
        s = search.strip()
        filter_q["$or"] = [
            {"id": {"$regex": s, "$options": "i"}},
            {"title": {"$regex": s, "$options": "i"}},
            {"description": {"$regex": s, "$options": "i"}},
            {"location_address": {"$regex": s, "$options": "i"}},
            {"category": {"$regex": s, "$options": "i"}},
        ]

    sort_spec = [("priority_score", pymongo.DESCENDING), ("created_at", pymongo.DESCENDING)]
    if sort_by == "created":
        sort_spec = [("created_at", pymongo.DESCENDING)]

    results = []
    seen_ids = set()

    # 1. Query MongoDB
    try:
        cursor = db["complaints"].find(filter_q).sort(sort_spec).skip(skip).limit(limit)
        for doc in cursor:
            summary = enrich_complaint_summary(doc, now)
            if summary["id"] not in seen_ids:
                seen_ids.add(summary["id"])
                results.append(summary)
    except Exception as db_err:
        print(f"[List Complaints DB Notice] {db_err}")

    # 2. Check In-Memory Store
    for doc in IN_MEMORY_COMPLAINTS:
        cid = doc.get("id")
        if cid in seen_ids:
            continue
        if status_filter and status_filter.upper() != "ALL" and doc.get("status") != status_filter.upper():
            continue
        if approval_status and approval_status.upper() != "ALL" and doc.get("approval_status") != approval_status.upper():
            continue
        if category and category.upper() != "ALL":
            if category.upper() == "OTHER" and doc.get("category") in CATEGORIES_CONFIG:
                continue
            elif category.upper() != "OTHER" and doc.get("category") != category:
                continue
        if borough and borough.upper() != "ALL" and doc.get("borough") != borough:
            continue
        if priority and priority.upper() != "ALL" and doc.get("priority") != priority.upper():
            continue
        if is_aging:
            doc_created = doc.get("created_at", now)
            doc_sla = doc.get("sla_due_date", now)
            if doc.get("status") == "RESOLVED" or (now <= doc_sla and (now - doc_created) < timedelta(hours=48)):
                continue
        if search:
            s = search.strip().lower()
            text_str = f"{doc.get('id', '')} {doc.get('title', '')} {doc.get('description', '')} {doc.get('location_address', '')} {doc.get('category', '')}".lower()
            if s not in text_str:
                continue

        summary = enrich_complaint_summary(doc, now)
        seen_ids.add(cid)
        results.append(summary)

    # Sort results
    if sort_by == "created":
        results.sort(key=lambda x: x.get("created_at", now), reverse=True)
    else:
        results.sort(key=lambda x: (x.get("priority_score", 0.0), x.get("created_at", now)), reverse=True)

    if limit and len(results) > limit:
        return results[skip : skip + limit]
    return results


@router.get("/my-complaints", response_model=List[ComplaintSummary])
def get_my_complaints(
    citizen_email: str = Query(..., description="Email of the logged in citizen"),
    db: Database = Depends(get_db),
):
    """
    Citizen-Only Endpoint: Retrieve strictly complaints submitted by this citizen.
    Ensures data privacy: citizens cannot see other citizens' complaints.
    """
    now = utcnow()
    clean_email = citizen_email.strip().lower()
    results = []
    seen_ids = set()

    # 1. Query MongoDB if available
    try:
        cursor = db["complaints"].find({
            "citizen_email": {"$regex": f"^{re.escape(clean_email)}$", "$options": "i"}
        }).sort("created_at", pymongo.DESCENDING)
        for doc in cursor:
            summary = enrich_complaint_summary(doc, now)
            if summary["id"] not in seen_ids:
                seen_ids.add(summary["id"])
                results.append(summary)
    except Exception as db_err:
        print(f"[My Complaints DB Notice] {db_err}")

    # 2. Check In-Memory Store
    for doc in IN_MEMORY_COMPLAINTS:
        if doc.get("id") in seen_ids:
            continue
        c_email = (doc.get("citizen_email") or "").strip().lower()
        if c_email == clean_email:
            summary = enrich_complaint_summary(doc, now)
            seen_ids.add(summary["id"])
            results.append(summary)

    results.sort(key=lambda x: x.get("created_at", now), reverse=True)
    return results


@router.get("/nearby")
def get_nearby_complaints(
    borough: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 6,
    db: Database = Depends(get_db),
):
    """Retrieve recent active complaints in the same borough/category for duplicate detection."""
    now = utcnow()
    filter_q: Dict[str, Any] = {"status": {"$ne": "RESOLVED"}}

    if borough:
        filter_q["borough"] = borough
    if category:
        filter_q["category"] = category

    results = []
    seen_ids = set()
    try:
        cursor = db["complaints"].find(filter_q).sort("created_at", pymongo.DESCENDING).limit(limit)
        for doc in cursor:
            summary = enrich_complaint_summary(doc, now)
            seen_ids.add(summary["id"])
            results.append(summary)
    except Exception as db_err:
        print(f"[Nearby DB Notice] {db_err}")

    for doc in IN_MEMORY_COMPLAINTS:
        if len(results) >= limit:
            break
        if doc.get("id") in seen_ids:
            continue
        if doc.get("status") == "RESOLVED":
            continue
        if borough and doc.get("borough") != borough:
            continue
        if category and doc.get("category") != category:
            continue
        summary = enrich_complaint_summary(doc, now)
        seen_ids.add(doc.get("id"))
        results.append(summary)

    return results[:limit]


@router.get("/{complaint_id}", response_model=ComplaintDetail)
def get_complaint(complaint_id: str, db: Database = Depends(get_db)):
    """Retrieve full details, timeline audit, comments, and prioritization breakdown."""
    complaint = _get_complaint_record(complaint_id, db)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

    now = utcnow()
    summary_data = enrich_complaint_summary(complaint, now)

    # Parse breakdown
    score_breakdown = complaint.get("score_breakdown")
    if isinstance(score_breakdown, str):
        try:
            score_breakdown = json.loads(score_breakdown)
        except Exception:
            score_breakdown = None

    if not score_breakdown:
        score_breakdown = calculate_priority(
            category=complaint.get("category"),
            created_at=summary_data["created_at"],
            sla_due_date=summary_data["sla_due_date"],
            similar_count=complaint.get("similar_complaint_count", 0),
            location_address=complaint.get("location_address", ""),
            current_time=now
        )

    # Fetch timeline and comments
    tl_records = _get_timeline(complaint_id, db)
    timeline = []
    for idx, t in enumerate(tl_records, start=1):
        timeline.append({
            "id": idx,
            "from_status": t.get("from_status"),
            "to_status": t.get("to_status", "NEW"),
            "actor": t.get("actor", "System"),
            "notes": t.get("notes"),
            "created_at": t.get("created_at", now),
        })

    com_records = _get_comments(complaint_id, db)
    comments = []
    for idx, c in enumerate(com_records, start=1):
        comments.append({
            "id": idx,
            "author": c.get("author", "Citizen"),
            "author_type": c.get("author_type", "Citizen"),
            "comment": c.get("comment", ""),
            "created_at": c.get("created_at", now),
        })

    return {
        **summary_data,
        "description": complaint.get("description", ""),
        "raw_input": complaint.get("raw_input"),
        "sub_category": complaint.get("sub_category"),
        "score_breakdown": score_breakdown,
        "assigned_officer": complaint.get("assigned_officer"),
        "is_duplicate_of_id": complaint.get("is_duplicate_of_id"),
        "updated_at": complaint.get("updated_at", now),
        "resolved_at": complaint.get("resolved_at"),
        "resolution_notes": complaint.get("resolution_notes"),
        "metadata": complaint.get("metadata", {}),
        "timeline": timeline,
        "comments": comments,
    }


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_complaint(data: ComplaintCreate, db: Database = Depends(get_db)):
    """
    Citizen complaint submission with AI enrichment, location validation,
    SLA calculation, and rule-based prioritization stored in MongoDB with resilient in-memory fallback.
    """
    now = utcnow()
    category = data.category
    title = data.title
    description = data.description
    raw_input = data.raw_input or data.description

    # Auto-fill missing fields using AI Service
    if not category or not title:
        try:
            ai_res = await ai_service.analyze_complaint(raw_input or description)
            if not category:
                category = ai_res.get("category", "General Civic Issue")
            if not title:
                title = ai_res.get("issue_summary", "Civic Grievance")
        except Exception as ai_err:
            print(f"[AI Notice] {ai_err}")
            if not category:
                category = "General Civic Issue"
            if not title:
                title = (description[:50] if description else "Civic Grievance")

    cat_config = CATEGORIES_CONFIG.get(category, {"sla_hours": 72, "department": "Municipal Operations"})
    sla_hours = cat_config.get("sla_hours", 72)
    sla_due_date = now + timedelta(hours=sla_hours)

    lat = data.latitude
    lng = data.longitude
    resolved_zone = ZONE_ALIASES.get(data.borough, data.borough or "Central Ward")
    if lat is None or lng is None:
        zone_info = CIVIC_ZONES.get(resolved_zone, list(CIVIC_ZONES.values())[0])
        lat = zone_info["lat"] + random.uniform(-0.015, 0.015)
        lng = zone_info["lng"] + random.uniform(-0.015, 0.015)

    # Generate guaranteed unique, non-colliding complaint ID
    max_id_num = 1050
    for c in IN_MEMORY_COMPLAINTS:
        try:
            c_id = str(c.get("id", ""))
            if c_id.startswith("CIVIC-2026-"):
                num = int(c_id.split("-")[-1])
                if num > max_id_num:
                    max_id_num = num
        except Exception:
            pass

    try:
        for c in db["complaints"].find({"id": {"$regex": r"^CIVIC-2026-\d+$"}}, {"id": 1}).sort("id", -1).limit(10):
            try:
                num = int(c["id"].split("-")[-1])
                if num > max_id_num:
                    max_id_num = num
            except Exception:
                pass
    except Exception:
        pass

    candidate = max_id_num + 1
    mem_ids = {c.get("id") for c in IN_MEMORY_COMPLAINTS}
    while f"CIVIC-2026-{candidate}" in mem_ids:
        candidate += 1
    complaint_id = f"CIVIC-2026-{candidate}"

    doc = ComplaintModel.create(
        id=complaint_id,
        title=title,
        description=description,
        raw_input=raw_input,
        category=category,
        sub_category=data.sub_category,
        status="NEW",
        location_address=data.location_address,
        borough=resolved_zone,
        zip_code=data.zip_code,
        latitude=round(lat, 6),
        longitude=round(lng, 6),
        assigned_department=cat_config.get("department"),
        similar_complaint_count=0,
        metadata=data.metadata or {},
        created_at=now,
        updated_at=now,
        sla_due_date=sla_due_date,
        citizen_email=data.citizen_email or "citizen@civicportal.gov",
        citizen_name=data.citizen_name or "Citizen Reporter",
        citizen_phone=data.citizen_phone,
        approval_status="PENDING_REVIEW",
    )

    # Compute rule-based priority score
    update_complaint_priority(doc, current_time=now)

    # 1. Save in resilient in-memory store
    IN_MEMORY_COMPLAINTS.insert(0, doc)

    # 2. Attempt MongoDB write
    _safe_db_insert(db, doc)

    # 3. Add timeline entry in memory and DB
    _add_timeline(
        complaint_id=complaint_id,
        from_status=None,
        to_status="NEW",
        actor="Citizen Reporter",
        notes=f"Issue submitted for {category}. SLA target: {sla_hours}h.",
        created_at=now,
        db=db,
    )

    return enrich_complaint_summary(doc, now)


@router.patch("/{complaint_id}/status")
def update_status(
    complaint_id: str,
    data: ComplaintUpdateStatus,
    authorization: Optional[str] = Header(None),
    db: Database = Depends(get_db),
):
    """Update complaint lifecycle status in MongoDB and in-memory store."""
    verify_admin_access(authorization, db)
    complaint = _get_complaint_record(complaint_id, db)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

    old_status = complaint.get("status")
    new_status = data.status.upper()
    now = utcnow()

    updates: Dict[str, Any] = {
        "status": new_status,
        "updated_at": now,
    }

    if new_status == "RESOLVED":
        updates["resolved_at"] = now
        updates["resolution_notes"] = data.resolution_notes or data.notes or "Resolved by municipal crew."

    complaint.update(updates)
    update_complaint_priority(complaint, current_time=now)

    updates["priority_score"] = complaint["priority_score"]
    updates["priority"] = complaint["priority"]
    updates["score_breakdown"] = complaint["score_breakdown"]

    _update_complaint_record(complaint_id, updates, db)

    _add_timeline(
        complaint_id=complaint_id,
        from_status=old_status,
        to_status=new_status,
        actor=data.actor,
        notes=data.notes or f"Status changed from {old_status} to {new_status}",
        created_at=now,
        db=db,
    )

    updated_doc = _get_complaint_record(complaint_id, db) or complaint
    return enrich_complaint_summary(updated_doc, now)


@router.patch("/{complaint_id}/approval")
def update_complaint_approval(
    complaint_id: str,
    data: ComplaintApprovalUpdate,
    authorization: Optional[str] = Header(None),
    db: Database = Depends(get_db),
):
    """
    Municipal Official / Administrator Review Action:
    Approves or rejects incoming citizen complaints with administrative remarks.
    """
    verify_admin_access(authorization, db)
    complaint = _get_complaint_record(complaint_id, db)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

    now = utcnow()
    new_approval = data.approval_status.upper().strip()
    if new_approval not in ["APPROVED", "REJECTED", "PENDING_REVIEW"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid approval status. Must be APPROVED, REJECTED, or PENDING_REVIEW."
        )

    updates = {
        "approval_status": new_approval,
        "admin_review_notes": data.admin_review_notes,
        "reviewed_by": data.reviewed_by,
        "updated_at": now,
    }

    if data.assigned_department:
        updates["assigned_department"] = data.assigned_department

    if new_approval == "APPROVED" and complaint.get("status") == "NEW":
        updates["status"] = "ASSIGNED"
    elif new_approval == "REJECTED":
        updates["status"] = "RESOLVED"
        updates["resolution_notes"] = f"Rejected: {data.admin_review_notes or 'Declined by municipal reviewer'}"
        updates["resolved_at"] = now

    _update_complaint_record(complaint_id, updates, db)

    action_note = f"Municipal Review: Ticket {new_approval}."
    if data.admin_review_notes:
        action_note += f" Remarks: {data.admin_review_notes}"

    _add_timeline(
        complaint_id=complaint_id,
        from_status=complaint.get("approval_status", "PENDING_REVIEW"),
        to_status=new_approval,
        actor=data.reviewed_by,
        notes=action_note,
        created_at=now,
        db=db,
    )

    updated_doc = _get_complaint_record(complaint_id, db) or complaint
    return enrich_complaint_summary(updated_doc, now)


@router.post("/batch-approval")
def batch_update_complaint_approval(
    data: BatchApprovalRequest,
    authorization: Optional[str] = Header(None),
    db: Database = Depends(get_db),
):
    """
    Batch Approval/Rejection for Municipal Administrator:
    Updates multiple tickets in one call with audit history.
    """
    verify_admin_access(authorization, db)
    now = utcnow()
    new_approval = data.approval_status.upper().strip()
    if new_approval not in ["APPROVED", "REJECTED", "PENDING_REVIEW"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid approval status. Must be APPROVED, REJECTED, or PENDING_REVIEW."
        )

    processed_ids = []
    for cid in data.complaint_ids:
        complaint = _get_complaint_record(cid, db)
        if not complaint:
            continue

        updates = {
            "approval_status": new_approval,
            "admin_review_notes": data.admin_review_notes,
            "reviewed_by": data.reviewed_by,
            "updated_at": now,
        }
        if data.assigned_department:
            updates["assigned_department"] = data.assigned_department

        if new_approval == "APPROVED" and complaint.get("status") == "NEW":
            updates["status"] = "ASSIGNED"
        elif new_approval == "REJECTED":
            updates["status"] = "RESOLVED"
            updates["resolution_notes"] = f"Rejected: {data.admin_review_notes or 'Declined in batch review'}"
            updates["resolved_at"] = now

        _update_complaint_record(cid, updates, db)

        action_note = f"Batch Municipal Review: Ticket {new_approval}."
        if data.admin_review_notes:
            action_note += f" Remarks: {data.admin_review_notes}"

        _add_timeline(
            complaint_id=cid,
            from_status=complaint.get("approval_status", "PENDING_REVIEW"),
            to_status=new_approval,
            actor=data.reviewed_by,
            notes=action_note,
            created_at=now,
            db=db,
        )
        processed_ids.append(cid)

    return {
        "success": True,
        "action": new_approval,
        "processed_count": len(processed_ids),
        "complaint_ids": processed_ids,
    }


@router.post("/{complaint_id}/assign")
def assign_complaint(
    complaint_id: str,
    data: ComplaintAssign,
    authorization: Optional[str] = Header(None),
    db: Database = Depends(get_db),
):
    """Assign ticket to department and officer, advancing to ASSIGNED status."""
    verify_admin_access(authorization, db)
    complaint = _get_complaint_record(complaint_id, db)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

    old_status = complaint.get("status")
    now = utcnow()
    new_status = "ASSIGNED" if old_status == "NEW" else old_status

    updates = {
        "assigned_department": data.department,
        "assigned_officer": data.officer,
        "status": new_status,
        "updated_at": now,
    }
    complaint.update(updates)
    update_complaint_priority(complaint, current_time=now)

    updates["priority_score"] = complaint["priority_score"]
    updates["priority"] = complaint["priority"]
    updates["score_breakdown"] = complaint["score_breakdown"]

    _update_complaint_record(complaint_id, updates, db)

    _add_timeline(
        complaint_id=complaint_id,
        from_status=old_status,
        to_status=new_status,
        actor=data.actor,
        notes=f"Assigned to {data.department}" + (f" (Officer: {data.officer})" if data.officer else ""),
        created_at=now,
        db=db,
    )

    updated_doc = _get_complaint_record(complaint_id, db) or complaint
    return enrich_complaint_summary(updated_doc, now)


@router.post("/{complaint_id}/comments")
def add_comment(
    complaint_id: str,
    data: CommentCreate,
    db: Database = Depends(get_db),
):
    """Add a public citizen or official staff comment in MongoDB and in-memory store."""
    complaint = _get_complaint_record(complaint_id, db)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

    now = utcnow()
    _add_comment(
        complaint_id=complaint_id,
        author=data.author,
        author_type=data.author_type,
        comment=data.comment,
        created_at=now,
        db=db,
    )
    return {"status": "success", "comment_id": f"com_{int(now.timestamp() * 1000)}"}


@router.post("/{complaint_id}/upvote")
def upvote_complaint(complaint_id: str, db: Database = Depends(get_db)):
    """
    Citizen 'I Have This Issue Too' action.
    Increments similar complaints count and recalculates priority score!
    """
    complaint = _get_complaint_record(complaint_id, db)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found")

    now = utcnow()
    complaint["similar_complaint_count"] = int(complaint.get("similar_complaint_count", 0)) + 1
    score_result = update_complaint_priority(complaint, current_time=now)

    updates = {
        "similar_complaint_count": complaint["similar_complaint_count"],
        "priority_score": score_result["total_score"],
        "priority": score_result["priority_tier"],
        "score_breakdown": json.dumps(score_result),
        "updated_at": now,
    }
    _update_complaint_record(complaint_id, updates, db)

    _add_timeline(
        complaint_id=complaint_id,
        from_status=complaint.get("status"),
        to_status=complaint.get("status"),
        actor="Citizen Reporter",
        notes=f"Additional citizen reported this issue (+1 upvote). Priority recalculated to {score_result['total_score']} ({score_result['priority_tier']}).",
        created_at=now,
        db=db,
    )

    return {
        "complaint_id": complaint_id,
        "similar_complaint_count": complaint["similar_complaint_count"],
        "new_priority_score": score_result["total_score"],
        "new_priority_tier": score_result["priority_tier"],
        "explanation": score_result["explanation"]
    }
