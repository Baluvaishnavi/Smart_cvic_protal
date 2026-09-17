"""
Analytics and SLA reporting routes powered by MongoDB.
Calculates issue distributions, aging metrics, SLA compliance, and geospatial hotspots.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
from fastapi import APIRouter, Depends
from pymongo.database import Database

from app.database import get_db
from app.models import utcnow
from app.config import CATEGORIES_CONFIG, NYC_BOROUGHS
from app.seed_data import seed_nyc_311_data
from app.routes.complaints import IN_MEMORY_COMPLAINTS

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/dashboard")
def get_dashboard_metrics(db: Database = Depends(get_db)) -> Dict[str, Any]:
    """
    Return comprehensive executive analytics from MongoDB and resilient in-memory store:
    Issue distribution, unresolved complaints, aging complaints, and SLA performance.
    """
    now = utcnow()
    try:
        db_complaints = list(db["complaints"].find({}))
    except Exception as e:
        print(f"[Analytics DB Find Notice] {e}")
        db_complaints = []

    seen_ids = {c.get("id") for c in db_complaints}
    all_complaints = list(db_complaints)
    for c in IN_MEMORY_COMPLAINTS:
        if c.get("id") not in seen_ids:
            all_complaints.append(c)
            seen_ids.add(c.get("id"))

    total = len(all_complaints)
    if total == 0:
        return {
            "summary": {
                "total": 0, "unresolved": 0, "resolved": 0,
                "aging_count": 0, "sla_breached": 0,
                "sla_compliance_rate": 100.0, "avg_resolution_hours": 0.0
            },
            "category_distribution": {},
            "borough_distribution": {},
            "status_distribution": {},
            "priority_distribution": {},
            "aging_breakdown": {},
            "department_sla": {}
        }

    unresolved = [c for c in all_complaints if c.get("status") != "RESOLVED"]
    resolved = [c for c in all_complaints if c.get("status") == "RESOLVED"]

    # SLA and Aging evaluations
    sla_breached = 0
    aging_48h_plus = 0
    aging_buckets = {
        "0_24h": 0,
        "24_48h": 0,
        "48_72h": 0,
        "over_72h": 0
    }

    for c in unresolved:
        c_created = c.get("created_at", now)
        if isinstance(c_created, str):
            try:
                c_created = datetime.fromisoformat(c_created)
            except Exception:
                c_created = now
        if c_created.tzinfo is None:
            c_created = c_created.replace(tzinfo=timezone.utc)

        c_sla = c.get("sla_due_date", now)
        if isinstance(c_sla, str):
            try:
                c_sla = datetime.fromisoformat(c_sla)
            except Exception:
                c_sla = now
        if c_sla.tzinfo is None:
            c_sla = c_sla.replace(tzinfo=timezone.utc)

        age_hours = (now - c_created).total_seconds() / 3600.0
        if age_hours >= 48:
            aging_48h_plus += 1

        if now > c_sla:
            sla_breached += 1

        if age_hours < 24:
            aging_buckets["0_24h"] += 1
        elif age_hours < 48:
            aging_buckets["24_48h"] += 1
        elif age_hours < 72:
            aging_buckets["48_72h"] += 1
        else:
            aging_buckets["over_72h"] += 1

    # MTTR (Mean Time to Resolution)
    resolution_durations = []
    for c in resolved:
        c_res = c.get("resolved_at")
        c_created = c.get("created_at")
        if c_res and c_created:
            if isinstance(c_res, str):
                try:
                    c_res = datetime.fromisoformat(c_res)
                except Exception:
                    continue
            if isinstance(c_created, str):
                try:
                    c_created = datetime.fromisoformat(c_created)
                except Exception:
                    continue
            if c_res.tzinfo is None:
                c_res = c_res.replace(tzinfo=timezone.utc)
            if c_created.tzinfo is None:
                c_created = c_created.replace(tzinfo=timezone.utc)

            dur = max(0.0, (c_res - c_created).total_seconds() / 3600.0)
            resolution_durations.append(dur)

    avg_resolution_hours = round(sum(resolution_durations) / len(resolution_durations), 1) if resolution_durations else 0.0
    compliant_count = len(all_complaints) - sla_breached
    sla_compliance_rate = round((compliant_count / total) * 100.0, 1) if total > 0 else 100.0

    # Category Distribution via aggregation
    cat_counts = {}
    for c in all_complaints:
        cat = c.get("category", "General Civic Issue")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1

    # Borough Distribution
    borough_counts = {}
    for c in all_complaints:
        b = c.get("borough", "Manhattan")
        borough_counts[b] = borough_counts.get(b, 0) + 1

    # Status Distribution
    status_counts = {"NEW": 0, "ASSIGNED": 0, "IN_PROGRESS": 0, "RESOLVED": 0}
    for c in all_complaints:
        s = c.get("status", "NEW")
        status_counts[s] = status_counts.get(s, 0) + 1

    # Priority Distribution
    priority_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for c in all_complaints:
        p = c.get("priority", "MEDIUM")
        priority_counts[p] = priority_counts.get(p, 0) + 1

    # Department SLA Performance
    dept_stats: Dict[str, Dict[str, Any]] = {}
    for c in all_complaints:
        dept = c.get("assigned_department") or "Unassigned Triage"
        if dept not in dept_stats:
            dept_stats[dept] = {"total": 0, "resolved": 0, "open": 0, "breached": 0}

        dept_stats[dept]["total"] += 1
        if c.get("status") == "RESOLVED":
            dept_stats[dept]["resolved"] += 1
        else:
            dept_stats[dept]["open"] += 1
            c_sla = c.get("sla_due_date", now)
            if isinstance(c_sla, str):
                try:
                    c_sla = datetime.fromisoformat(c_sla)
                except Exception:
                    c_sla = now
            if c_sla.tzinfo is None:
                c_sla = c_sla.replace(tzinfo=timezone.utc)
            if now > c_sla:
                dept_stats[dept]["breached"] += 1

    for dept, s in dept_stats.items():
        comp = ((s["total"] - s["breached"]) / s["total"] * 100.0) if s["total"] > 0 else 100.0
        s["compliance_rate"] = round(comp, 1)

    return {
        "summary": {
            "total": total,
            "unresolved": len(unresolved),
            "resolved": len(resolved),
            "aging_count": aging_48h_plus,
            "sla_breached": sla_breached,
            "sla_compliance_rate": sla_compliance_rate,
            "avg_resolution_hours": avg_resolution_hours,
        },
        "category_distribution": cat_counts,
        "borough_distribution": borough_counts,
        "status_distribution": status_counts,
        "priority_distribution": priority_counts,
        "aging_breakdown": aging_buckets,
        "department_sla": dept_stats,
    }


@router.get("/hotspots")
def get_hotspots(db: Database = Depends(get_db)) -> List[Dict[str, Any]]:
    """Geospatial clustering of complaints from MongoDB and resilient in-memory store."""
    try:
        db_complaints = list(db["complaints"].find({
            "latitude": {"$ne": None},
            "longitude": {"$ne": None}
        }))
    except Exception as e:
        print(f"[Hotspots DB Find Notice] {e}")
        db_complaints = []

    seen_ids = {c.get("id") for c in db_complaints}
    complaints = list(db_complaints)
    for c in IN_MEMORY_COMPLAINTS:
        if c.get("id") not in seen_ids and c.get("latitude") is not None and c.get("longitude") is not None:
            complaints.append(c)
            seen_ids.add(c.get("id"))

    clusters: List[Dict[str, Any]] = []

    for c in complaints:
        lat = c.get("latitude")
        lng = c.get("longitude")
        if lat is None or lng is None:
            continue

        placed = False
        for cl in clusters:
            dist = ((cl["latitude"] - lat)**2 + (cl["longitude"] - lng)**2) ** 0.5
            if dist < 0.008:
                cl["count"] += 1
                cl["complaint_ids"].append(c.get("id"))
                cat = c.get("category")
                if cat and cat not in cl["categories"]:
                    cl["categories"].append(cat)
                score = float(c.get("priority_score", 25.0))
                if score > cl["max_priority_score"]:
                    cl["max_priority_score"] = score
                    cl["highest_priority"] = c.get("priority", "MEDIUM")
                placed = True
                break

        if not placed:
            clusters.append({
                "latitude": lat,
                "longitude": lng,
                "borough": c.get("borough", "Manhattan"),
                "location_address": c.get("location_address", ""),
                "count": 1,
                "max_priority_score": float(c.get("priority_score", 25.0)),
                "highest_priority": c.get("priority", "MEDIUM"),
                "categories": [c.get("category", "General Civic Issue")],
                "complaint_ids": [c.get("id")],
            })

    clusters.sort(key=lambda x: (x["max_priority_score"], x["count"]), reverse=True)
    return clusters


@router.post("/seed")
def seed_database(force: bool = False, db: Database = Depends(get_db)):
    """Seed or reset realistic NYC 311 service request dataset directly in MongoDB."""
    total_count = seed_nyc_311_data(db, force=force)
    return {
        "status": "success",
        "message": f"MongoDB database seeded with {total_count} NYC 311 Service Requests.",
        "total_records": total_count
    }
