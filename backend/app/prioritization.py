"""
Rule-Based Prioritization Engine for Civic Complaints.
Calculates multi-factor dynamic priority scores based on:
1. Issue Category Base Severity (e.g., Water leaks > Streetlights > Potholes > Sanitation)
2. Aging Penalty (accumulates points as issue remains unresolved, with steep SLA breach penalty)
3. Duplicate / Similar Complaint Frequency (higher citizen frequency indicates broad civic impact)
4. Location Risk Bonus (schools, hospitals, arterial avenues, high-traffic intersections)
"""

from datetime import datetime, timezone
import json
import re
from typing import Dict, Any, Tuple
from app.config import CATEGORIES_CONFIG, PRIORITY_WEIGHTS, PRIORITY_TIERS


HIGH_RISK_KEYWORDS = [
    "school", "hospital", "clinic", "subway", "station", "highway",
    "expressway", "crosswalk", "intersection", "kindergarten", "elderly",
    "transit", "playground", "pedestrian", "avenue", "broadway"
]


def evaluate_location_risk(address: str) -> Tuple[bool, float, str]:
    """Check if location contains vulnerable or high-density risk keywords."""
    if not address:
        return False, 0.0, "Standard civic zone"
    
    addr_lower = address.lower()
    for kw in HIGH_RISK_KEYWORDS:
        if re.search(r'\b' + re.escape(kw) + r'\b', addr_lower):
            return True, PRIORITY_WEIGHTS["high_risk_location_bonus"], f"High-risk zone detected ({kw.title()})"
            
    return False, 0.0, "Standard civic zone"


def calculate_priority(
    category: str,
    created_at: datetime,
    sla_due_date: datetime,
    similar_count: int = 0,
    location_address: str = "",
    current_time: datetime = None
) -> Dict[str, Any]:
    """
    Calculate dynamic multi-factor priority score and tier.
    
    Formula:
    Score = Base_Category_Severity + Aging_Points + Duplicate_Bonus + Location_Risk + SLA_Breach_Penalty
    """
    if current_time is None:
        current_time = datetime.now(timezone.utc)

    # Normalize timezones if naive
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    if sla_due_date.tzinfo is None:
        sla_due_date = sla_due_date.replace(tzinfo=timezone.utc)
    if current_time.tzinfo is None:
        current_time = current_time.replace(tzinfo=timezone.utc)

    # 1. Base Severity by Category
    cat_config = CATEGORIES_CONFIG.get(category, {"base_severity": 15, "sla_hours": 72})
    base_severity = float(cat_config.get("base_severity", 15))

    # 2. Aging Penalty
    age_seconds = max(0.0, (current_time - created_at).total_seconds())
    age_hours = round(age_seconds / 3600.0, 1)
    age_penalty = round((age_hours / 12.0) * PRIORITY_WEIGHTS["points_per_12h_aging"], 1)

    # 3. SLA Breach Penalty
    sla_breached = current_time > sla_due_date
    sla_penalty = PRIORITY_WEIGHTS["sla_breach_penalty"] if sla_breached else 0.0

    # 4. Duplicate / Similar Issues Impact
    duplicate_bonus = min(
        float(similar_count) * PRIORITY_WEIGHTS["points_per_duplicate"],
        PRIORITY_WEIGHTS["max_duplicate_points"]
    )

    # 5. Location Risk Factor
    has_risk, location_risk_bonus, risk_reason = evaluate_location_risk(location_address)

    # Total Score
    total_score = round(base_severity + age_penalty + sla_penalty + duplicate_bonus + location_risk_bonus, 1)

    # Map to Tier
    priority_tier = "LOW"
    for tier_info in PRIORITY_TIERS:
        if total_score >= tier_info["min_score"]:
            priority_tier = tier_info["tier"]
            break

    # Build human-readable audit explanation
    parts = [f"Base: {base_severity} ({category})"]
    if age_penalty > 0:
        parts.append(f"Aging: +{age_penalty} ({age_hours}h open)")
    if sla_breached:
        parts.append(f"SLA Overdue: +{sla_penalty}")
    if duplicate_bonus > 0:
        parts.append(f"Similar Reports: +{duplicate_bonus} ({similar_count} duplicates)")
    if location_risk_bonus > 0:
        parts.append(f"Location Risk: +{location_risk_bonus} ({risk_reason})")

    explanation = " | ".join(parts) + f" => Score: {total_score} ({priority_tier})"

    return {
        "base_severity": base_severity,
        "age_hours": age_hours,
        "age_penalty": age_penalty,
        "duplicate_count": similar_count,
        "duplicate_bonus": duplicate_bonus,
        "location_risk_bonus": location_risk_bonus,
        "sla_breached": sla_breached,
        "sla_penalty": sla_penalty,
        "total_score": total_score,
        "priority_tier": priority_tier,
        "explanation": explanation
    }


def update_complaint_priority(complaint, current_time: datetime = None):
    """Utility to recompute and apply priority on a complaint instance or dict."""
    if isinstance(complaint, dict):
        cat = complaint.get("category", "General Civic Issue")
        created = complaint.get("created_at")
        sla = complaint.get("sla_due_date")
        similar = complaint.get("similar_complaint_count", 0)
        addr = complaint.get("location_address", "")
        result = calculate_priority(cat, created, sla, similar, addr, current_time)
        complaint["priority_score"] = result["total_score"]
        complaint["priority"] = result["priority_tier"]
        complaint["score_breakdown"] = json.dumps(result)
        return result

    result = calculate_priority(
        category=complaint.category,
        created_at=complaint.created_at,
        sla_due_date=complaint.sla_due_date,
        similar_count=complaint.similar_complaint_count or 0,
        location_address=complaint.location_address or "",
        current_time=current_time
    )
    complaint.priority_score = result["total_score"]
    complaint.priority = result["priority_tier"]
    complaint.score_breakdown = json.dumps(result)
    return result
