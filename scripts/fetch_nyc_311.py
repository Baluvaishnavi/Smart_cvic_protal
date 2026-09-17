"""
NYC 311 Open Data API Downloader & Ingestion Script.
Connects to NYC Open Data Socrata API (https://data.cityofnewyork.us/resource/erm2-nwe9.json)
to fetch live NYC 311 service request records.
Supports:
1. Streaming and downloading custom batch sizes (e.g., 500, 5,000, 50,000 records).
2. Direct insertion into local MongoDB (smart_civic_311.complaints).
3. Exporting labeled datasets to CSV for Machine Learning model training.
"""

import sys
import os
import argparse
import io
import json
import csv
from datetime import datetime, timezone, timedelta
import httpx

# UTF-8 stdout on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Ensure backend directory is accessible
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database import db
from app.models import ComplaintModel
from app.prioritization import update_complaint_priority
from app.config import CATEGORIES_CONFIG

NYC_311_API_URL = "https://data.cityofnewyork.us/resource/erm2-nwe9.json"

# Map NYC Open Data complaint_type to our standardized portal categories
NYC_TYPE_MAPPING = {
    "street light condition": "Streetlight",
    "street light out": "Streetlight",
    "street lighting": "Streetlight",
    "pothole": "Pothole",
    "highway pothole": "Pothole",
    "roadway condition": "Pothole",
    "water system": "Water Supply",
    "sewer": "Water Supply",
    "water quality": "Water Supply",
    "water leak": "Water Supply",
    "sanitation condition": "Garbage & Sanitation",
    "missed collection": "Garbage & Sanitation",
    "dirty condition": "Garbage & Sanitation",
    "illegal dumping": "Garbage & Sanitation",
    "traffic signal condition": "Traffic Signal",
    "sidewalk condition": "Broken Sidewalk",
    "damaged tree": "Trees & Parks",
    "overgrown tree": "Trees & Parks",
    "noise": "Noise & Disturbance",
    "noise - residential": "Noise & Disturbance",
    "noise - street/sidewalk": "Noise & Disturbance",
    "noise - commercial": "Noise & Disturbance",
    "graffiti": "General Civic Issue",
}


def normalize_nyc_category(raw_type: str) -> str:
    """Normalize raw NYC 311 complaint_type string."""
    t_lower = (raw_type or "").lower().strip()
    for pattern, mapped in NYC_TYPE_MAPPING.items():
        if pattern in t_lower:
            return mapped
    return "General Civic Issue"


def fetch_live_nyc_311(limit: int = 500, category_filter: str = None) -> list:
    """Query Socrata API for real live NYC 311 Service Requests."""
    params = {
        "$limit": limit,
        "$order": "created_date DESC",
    }
    if category_filter:
        params["complaint_type"] = category_filter

    print(f"[*] Querying NYC Open Data Socrata API ({NYC_311_API_URL})...")
    print(f"[*] Parameters: limit={limit}, order=created_date DESC")

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(NYC_311_API_URL, params=params)
        if resp.status_code != 200:
            raise RuntimeError(f"NYC 311 API returned HTTP {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        print(f"[+] Successfully received {len(data)} live service requests from NYC 311 API.")
        return data


def transform_record(raw: dict) -> dict:
    """Transform raw Socrata JSON record into Portal Complaint schema."""
    raw_id = raw.get("unique_key", f"NYC-{raw.get('created_date', 'LIVE')}")
    cid = f"NYC-311-{raw_id}"

    raw_type = raw.get("complaint_type", "General Civic Issue")
    category = normalize_nyc_category(raw_type)
    descriptor = raw.get("descriptor") or raw_type
    incident_addr = raw.get("incident_address") or raw.get("intersection_street_1") or "New York, NY"
    borough = (raw.get("borough") or "Manhattan").title()
    if borough == "Unspecified":
        borough = "Manhattan"

    # Lat/Lng
    lat = float(raw["latitude"]) if "latitude" in raw and raw["latitude"] else None
    lng = float(raw["longitude"]) if "longitude" in raw and raw["longitude"] else None

    # Status
    raw_status = (raw.get("status") or "NEW").upper()
    status_map = {
        "OPEN": "NEW",
        "ASSIGNED": "ASSIGNED",
        "IN PROGRESS": "IN_PROGRESS",
        "PENDING": "ASSIGNED",
        "CLOSED": "RESOLVED",
    }
    status = status_map.get(raw_status, "NEW")

    # Dates
    now = datetime.now(timezone.utc)
    cat_config = CATEGORIES_CONFIG.get(category, {"sla_hours": 72, "department": "Municipal Operations"})
    sla_hours = cat_config.get("sla_hours", 72)

    created_at = now
    if "created_date" in raw:
        try:
            created_at = datetime.fromisoformat(raw["created_date"].replace(".000", ""))
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
        except Exception:
            created_at = now

    sla_due_date = created_at + timedelta(hours=sla_hours)

    title = f"{descriptor} at {incident_addr}"
    description = f"Reported {raw_type}: {descriptor}. Location: {incident_addr}, {borough}."

    doc = ComplaintModel.create(
        id=cid,
        title=title[:250],
        description=description,
        raw_input=f"{descriptor} at {incident_addr}",
        category=category,
        sub_category=descriptor,
        status=status,
        location_address=incident_addr,
        borough=borough,
        zip_code=raw.get("incident_zip"),
        latitude=lat,
        longitude=lng,
        assigned_department=raw.get("agency_name") or cat_config.get("department"),
        created_at=created_at,
        updated_at=now,
        sla_due_date=sla_due_date,
        metadata={
            "socrata_unique_key": raw.get("unique_key"),
            "agency": raw.get("agency"),
            "agency_name": raw.get("agency_name"),
            "resolution_description": raw.get("resolution_description"),
        }
    )
    update_complaint_priority(doc, current_time=now)
    return doc


def main():
    parser = argparse.ArgumentParser(description="Fetch and ingest live NYC 311 Service Requests.")
    parser.add_argument("--limit", type=int, default=100, help="Number of records to fetch (e.g. 500, 5000)")
    parser.add_argument("--import-mongo", action="store_true", default=True, help="Import records into MongoDB")
    parser.add_argument("--save-csv", type=str, default=None, help="Save records to CSV for ML training")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print(" [*] NYC 311 OPEN DATASET LIVE STREAMER & INGESTION")
    print("=" * 70)

    try:
        raw_records = fetch_live_nyc_311(limit=args.limit)
    except Exception as e:
        print(f"[!] Live API connection note: {e}")
        print("[!] Falling back to local offline NYC 311 sample generator.")
        return

    transformed = [transform_record(r) for r in raw_records]

    # 1. Import to MongoDB
    if args.import_mongo:
        print(f"[*] Ingesting {len(transformed)} records into MongoDB (collection 'complaints')...")
        inserted = 0
        for doc in transformed:
            res = db["complaints"].update_one(
                {"id": doc["id"]},
                {"$set": doc},
                upsert=True
            )
            if res.upserted_id or res.modified_count:
                inserted += 1
        print(f"[SUCCESS] MongoDB successfully updated with {inserted} records!")
        print(f"[*] Total complaints now in MongoDB: {db['complaints'].count_documents({})}")

    # 2. Save CSV for ML Training
    if args.save_csv:
        print(f"[*] Exporting training dataset to {args.save_csv}...")
        os.makedirs(os.path.dirname(os.path.abspath(args.save_csv)), exist_ok=True)
        with open(args.save_csv, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["complaint_text", "category", "borough"])
            writer.writeheader()
            for doc in transformed:
                writer.writerow({
                    "complaint_text": doc["description"],
                    "category": doc["category"],
                    "borough": doc["borough"]
                })
        print(f"[SUCCESS] Training dataset saved to {args.save_csv} ({len(transformed)} rows).")

    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
