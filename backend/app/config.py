"""
Configuration settings for Smart Civic Complaint & Issue Management System.
Defines category SLAs, severity weights, borough centers, and prioritization parameters.
"""

from typing import Dict, Any

CATEGORIES_CONFIG: Dict[str, Dict[str, Any]] = {
    "Water Supply": {
        "sla_hours": 24,
        "base_severity": 40,
        "department": "Water Resources & Drainage Authority",
        "keywords": ["water", "leak", "pipe", "flooding", "contamination", "sewer", "drain", "hydrant", "sewage"],
        "icon": "droplet",
        "color": "blue",
    },
    "Streetlight": {
        "sla_hours": 48,
        "base_severity": 35,
        "department": "Electrical & Street Lighting Board",
        "keywords": ["streetlight", "street light", "lamp", "dark", "pole", "light out", "fixture", "lighting"],
        "icon": "lightbulb",
        "color": "amber",
    },
    "Traffic Signal": {
        "sla_hours": 24,
        "base_severity": 35,
        "department": "Traffic & Signals Division",
        "keywords": ["traffic light", "traffic signal", "signal out", "red light", "pedestrian signal", "stop sign"],
        "icon": "alert-triangle",
        "color": "red",
    },
    "Pothole": {
        "sla_hours": 72,
        "base_severity": 25,
        "department": "Roadway & Infrastructure Maintenance",
        "keywords": ["pothole", "crater", "asphalt", "cracked road", "depression", "sinkhole", "road damage"],
        "icon": "circle-alert",
        "color": "orange",
    },
    "Garbage & Sanitation": {
        "sla_hours": 48,
        "base_severity": 20,
        "department": "Waste Management & Sanitation Board",
        "keywords": ["garbage", "trash", "waste", "dumping", "recycling", "debris", "overflow", "litter", "refuse"],
        "icon": "trash-2",
        "color": "emerald",
    },
    "Broken Sidewalk": {
        "sla_hours": 96,
        "base_severity": 15,
        "department": "Pedestrian & Sidewalks Division",
        "keywords": ["sidewalk", "pavement", "curb", "trip hazard", "concrete", "cracked sidewalk"],
        "icon": "footprints",
        "color": "stone",
    },
    "Trees & Parks": {
        "sla_hours": 96,
        "base_severity": 15,
        "department": "Urban Parks & Greenery Board",
        "keywords": ["tree", "branch", "park", "fallen tree", "overgrown", "limb", "stump"],
        "icon": "trees",
        "color": "green",
    },
    "Noise & Disturbance": {
        "sla_hours": 72,
        "base_severity": 10,
        "department": "Civic Health & Noise Control",
        "keywords": ["noise", "loud music", "construction noise", "barking", "generator", "party"],
        "icon": "volume-2",
        "color": "purple",
    },
    "General Civic Issue": {
        "sla_hours": 96,
        "base_severity": 10,
        "department": "Municipal Community Affairs",
        "keywords": ["graffiti", "bench", "signage", "public property"],
        "icon": "help-circle",
        "color": "slate",
    }
}

# Generic Municipal Zones (Replaces country/city specific boroughs)
CIVIC_ZONES = {
    "Central Ward": {"lat": 12.9716, "lng": 77.5946, "code": "CW"},
    "North District": {"lat": 13.0358, "lng": 77.5970, "code": "ND"},
    "East Sector": {"lat": 12.9784, "lng": 77.6408, "code": "ES"},
    "South District": {"lat": 12.9141, "lng": 77.6109, "code": "SD"},
    "West Sector": {"lat": 12.9600, "lng": 77.5300, "code": "WS"},
}

# Backward compatibility alias map
ZONE_ALIASES = {
    "Manhattan": "Central Ward",
    "Brooklyn": "South District",
    "Queens": "East Sector",
    "Bronx": "North District",
    "Staten Island": "West Sector",
}

# Also expose NYC_BOROUGHS as an alias to avoid breaking any legacy code
NYC_BOROUGHS = CIVIC_ZONES

# Constant Administrator Configuration (Single Admin Person Allowed)
ADMIN_EMAIL = "admin@civicportal.gov"
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "Municipal Operations Administrator"
ADMIN_ROLE = "ADMIN"
ADMIN_DEPARTMENT = "Directorate of Municipal Operations"

# Rule-Based Prioritization Engine Weights
PRIORITY_WEIGHTS = {
    "points_per_12h_aging": 2.5,
    "sla_breach_penalty": 25.0,
    "points_per_duplicate": 12.0,
    "max_duplicate_points": 60.0,
    "high_risk_location_bonus": 15.0,  # schools, hospitals, arterial avenues
}

PRIORITY_TIERS = [
    {"tier": "CRITICAL", "min_score": 75, "color": "red", "badge": "bg-red-100 text-red-800 border-red-300"},
    {"tier": "HIGH", "min_score": 50, "color": "orange", "badge": "bg-orange-100 text-orange-800 border-orange-300"},
    {"tier": "MEDIUM", "min_score": 25, "color": "yellow", "badge": "bg-yellow-100 text-yellow-800 border-yellow-300"},
    {"tier": "LOW", "min_score": 0, "color": "green", "badge": "bg-green-100 text-green-800 border-green-300"},
]
