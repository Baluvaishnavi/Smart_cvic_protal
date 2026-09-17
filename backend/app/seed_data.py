"""
Civic Complaint Portal realistic dataset seeder for MongoDB.
Populates the database with municipal complaints across generic civic zones,
including varied statuses, timestamps, SLAs, duplicate clusters, and timeline entries.
Also seeds default citizen account into users collection.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import random
from typing import Union
from pymongo.database import Database

from app.models import ComplaintModel, utcnow
from app.config import CATEGORIES_CONFIG, CIVIC_ZONES
from app.prioritization import update_complaint_priority


# Generic Civic Zones and realistic municipal locations
CIVIC_ZONE_DATA = {
    "Central Ward": {
        "center": (12.9716, 77.5946),
        "locations": [
            ("100 Main Street & Civic Square", 12.9716, 77.5946, "560001"),
            ("Central Plaza & 4th Cross Avenue", 12.9740, 77.5980, "560001"),
            ("Market Street & Metro Station Road", 12.9690, 77.5910, "560002"),
            ("Commercial Road & Civic Center", 12.9760, 77.5955, "560001"),
            ("Grand Avenue & City Library Junction", 12.9725, 77.5890, "560002"),
        ]
    },
    "North District": {
        "center": (13.0358, 77.5970),
        "locations": [
            ("North Avenue & Industrial Parkway", 13.0358, 77.5970, "560024"),
            ("Highland Park Road & 12th St", 13.0420, 77.5910, "560024"),
            ("Valley View Circle near General Hospital", 13.0280, 77.6020, "560032"),
            ("North Sector Ring Road & 8th Main", 13.0450, 77.5880, "560024"),
        ]
    },
    "East Sector": {
        "center": (12.9784, 77.6408),
        "locations": [
            ("East Commercial Boulevard & Ring Road", 12.9784, 77.6408, "560038"),
            ("Greenway Drive & Sector 7", 12.9850, 77.6450, "560038"),
            ("Technology Hub Main Gate & 100ft Road", 12.9720, 77.6350, "560008"),
            ("Parkside Avenue & Community Center", 12.9810, 77.6510, "560038"),
        ]
    },
    "South District": {
        "center": (12.9141, 77.6109),
        "locations": [
            ("South Boulevard & Riverfront Road", 12.9141, 77.6109, "560068"),
            ("Lakeside Avenue & 9th Cross", 12.9190, 77.6150, "560068"),
            ("Residential Layout 4th Block", 12.9080, 77.6050, "560076"),
            ("Crossway Junction & Outer Ring Road", 12.9230, 77.6200, "560068"),
        ]
    },
    "West Sector": {
        "center": (12.9600, 77.5300),
        "locations": [
            ("West Valley Road & Transit Station", 12.9600, 77.5300, "560040"),
            ("Technology Park & West Gate", 12.9650, 77.5350, "560040"),
            ("Hilltop Colony & Water Works Lane", 12.9550, 77.5250, "560079"),
            ("Railway Crossing Road & 2nd Stage", 12.9680, 77.5400, "560040"),
        ]
    }
}

CATEGORY_TEMPLATES = {
    "Water Supply": [
        {
            "title": "Severe water main burst flooding street and sidewalks",
            "description": "A high-pressure underground water pipe burst. Millions of gallons gushing into residential driveways.",
            "raw_input": "Water pipe broken in front of my house gushing clean water everywhere road is flooded",
            "sub_category": "Main Pipe Burst",
            "base_sev": 40,
            "dept": "Water Resources & Drainage Authority",
            "officer": "Eng. Robert Vance (Water Operations)",
        },
        {
            "title": "Contaminated brownish tap water in residential block",
            "description": "Residents reporting rust and sewage smell coming from municipal tap water lines.",
            "raw_input": "Our tap water is brown and smells like sewer since this morning very unsafe",
            "sub_category": "Water Quality",
            "base_sev": 40,
            "dept": "Water Resources & Drainage Authority",
            "officer": "Quality Inspector Morales",
        },
    ],
    "Streetlight": [
        {
            "title": "Series of streetlights completely dark along pedestrian pathway",
            "description": "Three consecutive light poles flickering and out. Major safety concern for pedestrians returning late at night.",
            "raw_input": "Street lights are not working near Gate 3 the path is pitch black and dangerous",
            "sub_category": "Lamp Outage",
            "base_sev": 35,
            "dept": "Electrical & Street Lighting Board",
            "officer": "Lighting Tech Dave Miller",
        },
        {
            "title": "Streetlight pole damaged with exposed wiring after vehicle impact",
            "description": "Metal light pole leaning at 30 degrees with exposed electrical wires near public bus shelter.",
            "raw_input": "Car hit a light pole on Main St, wires are hanging down sparking hazard",
            "sub_category": "Damaged Pole / Wiring",
            "base_sev": 35,
            "dept": "Electrical & Street Lighting Board",
            "officer": "Electrician J. Cooper",
        },
    ],
    "Traffic Signal": [
        {
            "title": "Traffic signal malfunctioning flashing red all directions",
            "description": "Busy multi-lane intersection signal frozen in flashing red mode, causing traffic gridlock.",
            "raw_input": "Traffic lights are all flashing red at intersection total gridlock and near misses",
            "sub_category": "Signal Failure",
            "base_sev": 35,
            "dept": "Traffic & Signals Division",
            "officer": "Traffic Systems Crew A",
        },
    ],
    "Pothole": [
        {
            "title": "Deep asphalt crater causing tire damage and vehicular swerving",
            "description": "14-inch deep pothole in the middle lane causing dangerous evasive driving maneuvers.",
            "raw_input": "Huge pothole right in middle lane already saw two cars blow tires this morning",
            "sub_category": "Roadway Crater",
            "base_sev": 25,
            "dept": "Roadway & Infrastructure Maintenance",
            "officer": "Asphalt Repair Unit 4",
        },
    ],
    "Garbage & Sanitation": [
        {
            "title": "Illegal commercial waste dumping blocking sidewalk",
            "description": "Construction debris, sheetrock, and rotting food waste dumped in public alleyway.",
            "raw_input": "Someone dumped a whole truck of construction trash and smelly garbage blocking the sidewalk",
            "sub_category": "Illegal Dumping",
            "base_sev": 20,
            "dept": "Waste Management & Sanitation Board",
            "officer": "Sanitation Supervisor Green",
        },
    ],
    "Broken Sidewalk": [
        {
            "title": "Heaved concrete sidewalk slab severe pedestrian trip hazard",
            "description": "Tree roots lifted sidewalk slab by 5 inches. Multiple elderly pedestrians have tripped.",
            "raw_input": "Sidewalk is raised 5 inches by tree roots right outside senior living building dangerous",
            "sub_category": "Heaved Concrete",
            "base_sev": 15,
            "dept": "Pedestrian & Sidewalks Division",
            "officer": "Sidewalk Inspector Ortiz",
        }
    ],
    "Trees & Parks": [
        {
            "title": "Large fallen tree branch obstructing road and power lines",
            "description": "Massive oak branch cracked during recent high winds, hanging precariously over utility lines.",
            "raw_input": "Huge tree limb hanging over electric wires ready to fall on passing cars",
            "sub_category": "Hazardous Tree Branch",
            "base_sev": 15,
            "dept": "Urban Parks & Greenery Board",
            "officer": "Arborist Team Lead Ramos",
        }
    ],
    "Noise & Disturbance": [
        {
            "title": "Unpermitted construction noise before authorized municipal hours",
            "description": "Heavy jackhammers and diesel generators operating at 5:00 AM on residential street.",
            "raw_input": "Construction site jackhammering since 5am every single morning waking up whole block",
            "sub_category": "Construction Noise",
            "base_sev": 10,
            "dept": "Civic Health & Noise Control",
            "officer": "Noise Enforcement Unit",
        }
    ],
    "General Civic Issue": [
        {
            "title": "Vandalism and offensive graffiti across public community park bench",
            "description": "Public seating tagged with spray paint and damaged wooden slats.",
            "raw_input": "Park benches covered in graffiti and broken slats need cleaning and repair",
            "sub_category": "Public Property Damage",
            "base_sev": 10,
            "dept": "Municipal Community Affairs",
            "officer": "Facilities Team Baker",
        }
    ]
}


def hash_pw(pw: str) -> str:
    return hashlib.sha256(("civic_portal_secure_salt_2026_" + pw).encode("utf-8")).hexdigest()


def seed_nyc_311_data(db: Database, force: bool = False):
    """Seed database with initial complaints and default citizen account."""
    if not force and db["complaints"].count_documents({}) > 0:
        try:
            db["users"].update_one(
                {"email": "citizen@civicportal.gov"},
                {"$setOnInsert": {
                    "id": "usr_cit_default01",
                    "name": "Sarah Jenkins",
                    "email": "citizen@civicportal.gov",
                    "password_hash": hash_pw("citizen123"),
                    "phone": "(555) 019-2834",
                    "role": "CITIZEN",
                    "department": None,
                    "created_at": utcnow()
                }},
                upsert=True
            )
        except Exception:
            pass
        return db["complaints"].count_documents({})

    # Clear existing collections
    db["complaints"].delete_many({})
    db["complaint_timeline"].delete_many({})
    db["complaint_comments"].delete_many({})
    db["users"].delete_many({})

    now = utcnow()

    # 1. Seed Default Citizen User
    default_citizen = {
        "id": "usr_cit_default01",
        "name": "Sarah Jenkins",
        "email": "citizen@civicportal.gov",
        "password_hash": hash_pw("citizen123"),
        "phone": "(555) 019-2834",
        "role": "CITIZEN",
        "department": None,
        "created_at": now
    }
    db["users"].insert_one(default_citizen)

    # 2. Seed Structured Complaints across zones
    count = 1000
    zones = list(CIVIC_ZONE_DATA.keys())
    statuses = ["NEW", "ASSIGNED", "IN_PROGRESS", "RESOLVED"]

    for zone_idx, zone_name in enumerate(zones):
        zone_info = CIVIC_ZONE_DATA[zone_name]
        locs = zone_info["locations"]

        for cat, templates in CATEGORY_TEMPLATES.items():
            tpl = random.choice(templates)
            loc = random.choice(locs)
            addr, lat, lng, zip_code = loc

            # Status distribution
            status = statuses[(count) % 4]
            age_hours = (count % 80) + 2
            created_at = now - timedelta(hours=age_hours)
            sla_hours = CATEGORIES_CONFIG.get(cat, {}).get("sla_hours", 48)
            sla_due_date = created_at + timedelta(hours=sla_hours)

            resolved_at = created_at + timedelta(hours=min(age_hours - 2, 30)) if status == "RESOLVED" else None
            res_notes = "Issue inspected, verified, and resolved by field technician." if status == "RESOLVED" else None

            count += 1
            cid = f"CIVIC-2026-{count}"
            dept = tpl["dept"]
            similar_count = random.choice([0, 0, 1, 2, 4])

            doc = ComplaintModel.create(
                id=cid,
                title=tpl["title"],
                description=tpl["description"],
                raw_input=tpl["raw_input"],
                category=cat,
                sub_category=tpl["sub_category"],
                status=status,
                location_address=addr,
                borough=zone_name,
                zip_code=zip_code,
                latitude=lat + random.uniform(-0.005, 0.005),
                longitude=lng + random.uniform(-0.005, 0.005),
                assigned_department=dept if status != "NEW" else None,
                assigned_officer=tpl["officer"] if status in ["ASSIGNED", "IN_PROGRESS", "RESOLVED"] else None,
                similar_complaint_count=similar_count,
                created_at=created_at,
                updated_at=now - timedelta(hours=max(0, age_hours - 5)),
                sla_due_date=sla_due_date,
                resolved_at=resolved_at,
                resolution_notes=res_notes,
                citizen_email="citizen@civicportal.gov",
                citizen_name="Sarah Jenkins",
                approval_status="APPROVED" if status != "NEW" else "PENDING_REVIEW",
                metadata={
                    "channel": random.choice(["Civic Mobile App", "Web Portal", "Municipal Helpline", "Field Inspection"]),
                    "duplicate_reports": similar_count
                }
            )

            update_complaint_priority(doc, current_time=now)
            db["complaints"].insert_one(doc)

            # Timeline
            db["complaint_timeline"].insert_one({
                "complaint_id": cid,
                "from_status": None,
                "to_status": "NEW",
                "actor": "Citizen Reporter",
                "notes": f"Complaint registered via {doc['metadata'].get('channel', 'Web Portal')}",
                "created_at": created_at
            })

            if status in ["ASSIGNED", "IN_PROGRESS", "RESOLVED"]:
                db["complaint_timeline"].insert_one({
                    "complaint_id": cid,
                    "from_status": "NEW",
                    "to_status": "ASSIGNED",
                    "actor": "Operations Dispatcher",
                    "notes": f"Dispatched to {dept} for site assessment",
                    "created_at": created_at + timedelta(hours=min(4, age_hours / 3))
                })

            if status in ["IN_PROGRESS", "RESOLVED"]:
                db["complaint_timeline"].insert_one({
                    "complaint_id": cid,
                    "from_status": "ASSIGNED",
                    "to_status": "IN_PROGRESS",
                    "actor": tpl["officer"],
                    "notes": "Field crew deployed with equipment for on-site rectification",
                    "created_at": created_at + timedelta(hours=min(12, age_hours / 2))
                })

            if status == "RESOLVED":
                db["complaint_timeline"].insert_one({
                    "complaint_id": cid,
                    "from_status": "IN_PROGRESS",
                    "to_status": "RESOLVED",
                    "actor": tpl["officer"],
                    "notes": res_notes,
                    "created_at": resolved_at
                })

    # Showcase Case Study issue (Available under both CIVIC-2026-CASE01 and NYC-2026-CASE01 for compatibility)
    cs_created = now - timedelta(days=6)
    cs_sla = cs_created + timedelta(hours=48)
    for cid in ["CIVIC-2026-CASE01", "NYC-2026-CASE01"]:
        cs_doc = ComplaintModel.create(
            id=cid,
            title="Streetlight near Gate 3 non-functional for approximately one week",
            description="There has been no street light near Gate 3 for almost a week and the road gets extremely dark at night.",
            raw_input="There has been no street light near Gate 3 for almost a week and the road gets extremely dark.",
            category="Streetlight",
            sub_category="Street Light Out",
            status="NEW",
            location_address="Gate 3, Central Boulevard near North Crossway",
            borough="Central Ward",
            zip_code="560001",
            latitude=12.9716,
            longitude=77.5946,
            assigned_department="Electrical & Street Lighting Board",
            assigned_officer=None,
            similar_complaint_count=3,
            created_at=cs_created,
            updated_at=now - timedelta(hours=2),
            sla_due_date=cs_sla,
            citizen_email="citizen@civicportal.gov",
            citizen_name="Sarah Jenkins",
            approval_status="PENDING_REVIEW",
            metadata={"channel": "Web Portal", "case_study_example": True}
        )
        update_complaint_priority(cs_doc, current_time=now)
        db["complaints"].insert_one(cs_doc)

        db["complaint_timeline"].insert_one({
            "complaint_id": cid,
            "from_status": None,
            "to_status": "NEW",
            "actor": "Citizen Reporter",
            "notes": "Issue filed using AI Smart Voice/Text assistant",
            "created_at": cs_created
        })

    return db["complaints"].count_documents({})
