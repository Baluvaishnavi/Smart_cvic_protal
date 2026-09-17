"""
Generate a professional, high-impact 16:9 widescreen PowerPoint presentation (.pptx)
for the Smart Civic Complaint & Municipal Issue Management System.
"""

import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

OUTPUT_FILE = r"C:\Users\baluv\OneDrive\Desktop\smart_civic_portal\Smart_Civic_Portal_Presentation.pptx"

# Color Palette Definitions
C_DARK_BG   = RGBColor(15, 23, 42)      # #0F172A (Navy / Slate 900)
C_LIGHT_BG  = RGBColor(248, 250, 252)  # #F8FAFC (Slate 50)
C_CARD_BG   = RGBColor(255, 255, 255)  # Clean white card
C_CARD_DARK = RGBColor(30, 41, 59)      # #1E293B (Slate 800)
C_PRIMARY   = RGBColor(14, 165, 233)   # #0EA5E9 (Sky 500)
C_PRIMARY_D = RGBColor(2, 132, 199)    # #0284C7 (Sky 600)
C_ACCENT    = RGBColor(99, 102, 241)   # #6366F1 (Indigo 500)
C_EMERALD   = RGBColor(16, 185, 129)   # #10B981 (Emerald 500)
C_AMBER     = RGBColor(245, 158, 11)   # #F59E0B (Amber 500)
C_ROSE      = RGBColor(244, 63, 94)    # #F43F5E (Rose 500)
C_TEXT_MAIN = RGBColor(15, 23, 42)     # #0F172A (Slate 900)
C_TEXT_MUTED= RGBColor(100, 116, 139)  # #64748B (Slate 500)
C_TEXT_LIGHT= RGBColor(241, 245, 249)  # #F1F5F9 (Slate 100)
C_BORDER    = RGBColor(226, 232, 240)  # #E2E8F0 (Slate 200)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]


def create_base_slide(is_dark=False):
    """Creates a slide with unified background and standard dimensions."""
    slide = prs.slides.add_slide(blank_layout)
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = C_DARK_BG if is_dark else C_LIGHT_BG
    bg.line.color.rgb = C_DARK_BG if is_dark else C_LIGHT_BG
    return slide


def add_header(slide, title_text, category_text="CIVIC COMPLAINT & OPERATIONS PORTAL", is_dark=False):
    """Adds a modern header with category pill badge and main title."""
    # Category Pill
    badge = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(0.45), Inches(4.2), Inches(0.35))
    badge.fill.solid()
    badge.fill.fore_color.rgb = RGBColor(30, 58, 95) if is_dark else RGBColor(224, 242, 254)
    badge.line.color.rgb = C_PRIMARY if is_dark else C_PRIMARY_D
    tf = badge.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = f"●  {category_text.upper()}"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY if is_dark else C_PRIMARY_D

    # Main Title
    tx_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.75))
    tf2 = tx_box.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = title_text
    p2.font.size = Pt(24)
    p2.font.bold = True
    p2.font.color.rgb = C_TEXT_LIGHT if is_dark else C_TEXT_MAIN


def add_card(slide, left, top, width, height, title, items, badge_text=None, border_color=C_BORDER, is_dark=False):
    """Adds a stylized card container with title, optional badge, and bullet/feature items."""
    card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    card.fill.solid()
    card.fill.fore_color.rgb = C_CARD_DARK if is_dark else C_CARD_BG
    card.line.color.rgb = border_color
    card.line.width = Pt(1.5)

    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = Inches(0.25)
    tf.margin_right = Inches(0.25)
    tf.margin_top = Inches(0.25)
    tf.margin_bottom = Inches(0.2)

    # Title paragraph
    p = tf.paragraphs[0]
    p.text = f"{title}"
    if badge_text:
        p.text += f"  [{badge_text}]"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY if is_dark else C_PRIMARY_D
    p.space_after = Pt(10)

    # Items
    for item in items:
        p_item = tf.add_paragraph()
        p_item.text = f"•  {item}"
        p_item.font.size = Pt(12)
        p_item.font.color.rgb = C_TEXT_LIGHT if is_dark else C_TEXT_MAIN
        p_item.space_after = Pt(6)


# ==============================================================================
# SLIDE 1: Title Slide (Dark Theme)
# ==============================================================================
slide1 = create_base_slide(is_dark=True)

# Gradient / Accent bar
bar = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.3), Inches(7.5))
bar.fill.solid()
bar.fill.fore_color.rgb = C_PRIMARY
bar.line.fill.background()

# Title pill
t_badge = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.2), Inches(4.8), Inches(0.42))
t_badge.fill.solid()
t_badge.fill.fore_color.rgb = RGBColor(30, 58, 95)
t_badge.line.color.rgb = C_PRIMARY
tf_b = t_badge.text_frame
p = tf_b.paragraphs[0]
p.text = "★  FINAL YEAR CAPSTONE & TECHNICAL PRESENTATION"
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = C_PRIMARY

# Main Title Textbox
t_box = slide1.shapes.add_textbox(Inches(1.2), Inches(1.8), Inches(11), Inches(2.2))
tf = t_box.text_frame
tf.word_wrap = True
p1 = tf.paragraphs[0]
p1.text = "Smart Civic Complaint &\nMunicipal Issue Management System"
p1.font.size = Pt(36)
p1.font.bold = True
p1.font.color.rgb = C_TEXT_LIGHT
p1.space_after = Pt(12)

p2 = tf.add_paragraph()
p2.text = "An AI-Powered Full-Stack Platform with Automated Rule-Based Prioritization, SLA Tracking & Real-Time Analytics"
p2.font.size = Pt(16)
p2.font.color.rgb = C_PRIMARY

# Key Feature Pills at bottom
features = [
    ("⚡ FastAPI Backend", "Python 3.14 + Uvicorn Async"),
    ("🍃 MongoDB Database", "Flexible Grievance Schema"),
    ("🤖 Machine Learning", "Scikit-Learn NLP Classification"),
    ("🛡️ RBAC Security", "Dedicated Admin Approvals & Queues")
]

for idx, (f_title, f_sub) in enumerate(features):
    left = Inches(1.2 + idx * 2.8)
    top = Inches(4.8)
    f_card = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(2.6), Inches(1.6))
    f_card.fill.solid()
    f_card.fill.fore_color.rgb = C_CARD_DARK
    f_card.line.color.rgb = RGBColor(51, 65, 85)
    tf_f = f_card.text_frame
    tf_f.margin_left = Inches(0.18)
    tf_f.margin_right = Inches(0.18)
    tf_f.margin_top = Inches(0.2)
    p = tf_f.paragraphs[0]
    p.text = f_title
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = C_PRIMARY
    p.space_after = Pt(4)
    p_sub = tf_f.add_paragraph()
    p_sub.text = f_sub
    p_sub.font.size = Pt(11)
    p_sub.font.color.rgb = C_TEXT_MUTED


# ==============================================================================
# SLIDE 2: Problem Statement & Motivation
# ==============================================================================
slide2 = create_base_slide(is_dark=False)
add_header(slide2, "1. Problem Statement: Modern Challenges in Civic Governance")

cards_s2 = [
    (Inches(0.8), "Citizen Disengagement & Lack of Trust", [
        "Citizens report civic issues through slow, opaque municipal channels.",
        "Zero real-time status visibility leads to duplicate call center complaints.",
        "Citizens have no transparent way to track SLA resolution deadlines."
    ], "CRITICAL ISSUE", C_ROSE),
    (Inches(4.8), "Manual Triage & Operational Delays", [
        "Municipal staff manually read and assign hundreds of daily grievances.",
        "No automated classification or urgency scoring for severe incidents.",
        "Recurring infrastructure bottlenecks remain unnoticed without hotspot tracking."
    ], "BOTTLENECK", C_AMBER),
    (Inches(8.8), "Lack of Unified SLA & Executive Oversight", [
        "Fragmented records across spreadsheets and departmental silos.",
        "Absence of executive analytics on aging complaints and breach rates.",
        "Difficult to prioritize repairs based on public demand and geographic severity."
    ], "GOVERNANCE GAP", C_PRIMARY_D)
]

for left, title, items, badge, col in cards_s2:
    add_card(slide2, left, Inches(1.8), Inches(3.7), Inches(4.8), title, items, badge, col)


# ==============================================================================
# SLIDE 3: Proposed Solution & Objectives
# ==============================================================================
slide3 = create_base_slide(is_dark=False)
add_header(slide3, "2. Proposed Solution: The Smart Civic Operations Platform")

cards_s3 = [
    (Inches(0.8), "Unified Citizen Portal", [
        "Self-service issue submission with photo upload and location selection.",
        "Intelligent category selection with manual 'Other' custom input fallback.",
        "Community Upvoting: Citizens can upvote existing issues to boost priority.",
        "Personal 'My Complaints' dashboard with real-time status progression."
    ], "FRONTEND", C_PRIMARY_D),
    (Inches(4.8), "Smart Operations & Approvals", [
        "Dedicated Approvals Center for municipal supervisors to verify issues.",
        "Strict 4-stage lifecycle pipeline: NEW → ASSIGNED → IN_PROGRESS → RESOLVED.",
        "Departmental routing (Roads, Water, Electricity, Sanitation, Traffic).",
        "Role-Based Access Control ensuring secure single-administrator oversight."
    ], "OPERATIONS", C_EMERALD),
    (Inches(8.8), "Intelligent Automation Engine", [
        "Rule-Based Prioritization scoring (0 to 100) dynamically calculated.",
        "NLP Classification using Scikit-Learn to auto-detect categories and urgency.",
        "Duplicate Grievance Detection using TF-IDF and cosine similarity.",
        "Executive Analytics: Real-time SLA breach rates, aging trends, and hotspots."
    ], "AI & ANALYTICS", C_ACCENT)
]

for left, title, items, badge, col in cards_s3:
    add_card(slide3, left, Inches(1.8), Inches(3.7), Inches(4.8), title, items, badge, col)


# ==============================================================================
# SLIDE 4: System Architecture & Tech Stack
# ==============================================================================
slide4 = create_base_slide(is_dark=False)
add_header(slide4, "3. Full-Stack System Architecture")

layers = [
    ("Presentation Layer (Client SPA)", [
        "Modern Responsive Single Page Application (HTML5, Tailwind CSS, Vanilla JS).",
        "Modular architecture: Citizen Portal, Approvals Center, Operations Queue, Executive Analytics.",
        "Chart.js interactive visualizations for issue distribution and SLA performance.",
        "Custom non-blocking Toast notification system replacing disruptive native alerts."
    ], C_PRIMARY_D),
    ("Application & API Layer (FastAPI)", [
        "Asynchronous Python 3.14 backend powered by Uvicorn.",
        "Modular REST routing: /api/complaints, /api/auth, /api/analytics, /api/ai.",
        "Strict Pydantic v2 data validation schemas with automatic OpenAPI / Swagger documentation.",
        "Single-origin static file serving eliminating CORS latency and configuration issues."
    ], C_EMERALD),
    ("Data & Machine Learning Layer", [
        "MongoDB (PyMongo): Document database handling flexible schemas, timelines, and users.",
        "Machine Learning Pipeline: Scikit-Learn TF-IDF Vectorizer + Multinomial Logistic Regression.",
        "Deterministic Prioritization Engine: Dynamic real-time scoring with aging and SLA multipliers.",
        "Secure Authentication: SHA-256 salted password hashing and role-based session verification."
    ], C_ACCENT)
]

for idx, (title, items, col) in enumerate(layers):
    top = Inches(1.8 + idx * 1.65)
    add_card(slide4, Inches(0.8), top, Inches(11.7), Inches(1.5), title, items, None, col)


# ==============================================================================
# SLIDE 5: Database Schema & MongoDB Architecture
# ==============================================================================
slide5 = create_base_slide(is_dark=False)
add_header(slide5, "4. Database Architecture & Collections (MongoDB)")

cols_data = [
    (Inches(0.8), "Collection: complaints", [
        "id: String (e.g., 'CIVIC-2026-1042')",
        "title, description, category, address",
        "ward_zone: Central, North, East, South, West",
        "priority_score: Float (0.0 to 100.0)",
        "priority_tier: CRITICAL, HIGH, MEDIUM, LOW",
        "status: NEW → ASSIGNED → IN_PROGRESS → RESOLVED",
        "approval_status: PENDING, APPROVED, REJECTED",
        "assigned_department, assigned_officer",
        "upvotes, created_at, sla_target_hours"
    ], "CORE STORE", C_PRIMARY_D),
    (Inches(4.8), "Collection: users & sessions", [
        "email: String (Unique Index)",
        "hashed_password: Salted SHA-256 string",
        "full_name, phone_number, role (CITIZEN / ADMIN)",
        "created_at: ISO Datetime",
        "Strict RBAC: Constant Administrator account (admin@civicportal.gov) for operations.",
        "Self-registration enabled for all citizens.",
        "Session tokens stored with active expiry and verification on all mutating endpoints."
    ], "AUTH & SECURITY", C_EMERALD),
    (Inches(8.8), "Timelines & Comments", [
        "complaint_timeline: Immutable audit trail logging every state change, timestamp, and actor.",
        "Actions tracked: CREATED, APPROVED, REJECTED, ASSIGNED, STATUS_CHANGE, UPVOTED.",
        "complaint_comments: Public and internal notes exchanged between citizens and supervisors.",
        "Ensures total municipal accountability and transparency during public audits."
    ], "AUDIT TRAIL", C_ACCENT)
]

for left, title, items, badge, col in cols_data:
    add_card(slide5, left, Inches(1.8), Inches(3.7), Inches(4.8), title, items, badge, col)


# ==============================================================================
# SLIDE 6: Dynamic Rule-Based Prioritization Engine
# ==============================================================================
slide6 = create_base_slide(is_dark=False)
add_header(slide6, "5. Rule-Based Prioritization Engine (0 - 100 Scoring)")

# Formula Box
f_box = slide6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.1))
f_box.fill.solid()
f_box.fill.fore_color.rgb = RGBColor(238, 242, 255)
f_box.line.color.rgb = C_ACCENT
f_box.line.width = Pt(2)
tf_f = f_box.text_frame
tf_f.margin_top = Inches(0.15)
p = tf_f.paragraphs[0]
p.text = "Mathematical Scoring Formula:"
p.font.size = Pt(12)
p.font.bold = True
p.font.color.rgb = C_ACCENT
p2 = tf_f.add_paragraph()
p2.text = "Priority Score (S) = Base Severity + Aging Penalty + SLA Breach Penalty + Duplicate Multiplier + Hotspot Bonus"
p2.font.size = Pt(14)
p2.font.bold = True
p2.font.color.rgb = C_TEXT_MAIN

factors = [
    (Inches(0.8), "Base Category Severity", [
        "Structural / Gas: 45 pts",
        "Water & Drainage: 35 pts",
        "Roadway Potholes: 30 pts",
        "Streetlight / Power: 25 pts",
        "Waste / Sanitation: 20 pts",
        "Noise / Aesthetics: 15 pts"
    ], C_PRIMARY_D),
    (Inches(3.8), "Aging & SLA Penalties", [
        "Aging: +2.0 pts per elapsed day.",
        "Cap: Up to +20 pts total.",
        "SLA Breach: Immediate +15 pts bonus if resolution target is breached.",
        "Guarantees old complaints never get buried."
    ], C_AMBER),
    (Inches(6.8), "Community Multipliers", [
        "Upvotes: +2.5 pts per citizen upvote.",
        "Similar Reports: +5.0 pts per co-located report.",
        "Community multiplier escalates collective neighborhood problems automatically."
    ], C_EMERALD),
    (Inches(9.8), "Priority Tiers", [
        "CRITICAL: 85 – 100 pts (Immediate 12h SLA)",
        "HIGH: 65 – 84 pts (24h SLA)",
        "MEDIUM: 35 – 64 pts (48h SLA)",
        "LOW: 0 – 34 pts (72h SLA)"
    ], C_ROSE)
]

for left, title, items, col in factors:
    add_card(slide6, left, Inches(3.1), Inches(2.75), Inches(3.5), title, items, None, col)


# ==============================================================================
# SLIDE 7: AI & Machine Learning: NLP Classification
# ==============================================================================
slide7 = create_base_slide(is_dark=False)
add_header(slide7, "6. Machine Learning Pipeline: NLP & Duplicate Detection")

cards_s7 = [
    (Inches(0.8), "Text Preprocessing & NLP Pipeline", [
        "Text Normalization: Lowercase conversion, alphanumeric regex extraction, and stopword removal.",
        "TF-IDF Vectorizer: Extracts unigrams and bigrams (1-2 n-grams) with sublinear term-frequency scaling.",
        "Handles noisy citizen descriptions, colloquial language, and typographical variances.",
        "Fast feature extraction optimized for sub-10ms inference per request."
    ], "FEATURE EXTRACTION", C_PRIMARY_D),
    (Inches(4.8), "Multinomial Logistic Classifier", [
        "Trained on municipal issue corpora with 10+ standard categories.",
        "Balanced class weighting to avoid bias against rare critical infrastructure incidents.",
        "Predicts primary category and outputs calibrated confidence probabilities.",
        "Integrated active learning endpoint (POST /api/ai/retrain) to adapt to new civic trends."
    ], "MODEL ARCHITECTURE", C_ACCENT),
    (Inches(8.8), "Cosine Similarity Duplicate Engine", [
        "Compares new complaints against open issues within the same municipal zone.",
        "Calculates semantic similarity score (0.0 to 1.0) using vector dot products.",
        "Detects duplicate incidents in real-time and increments cluster count instead of creating clutter.",
        "Alerts citizens before form submission if a similar issue was recently reported."
    ], "DUPLICATE DETECTION", C_EMERALD)
]

for left, title, items, badge, col in cards_s7:
    add_card(slide7, left, Inches(1.8), Inches(3.7), Inches(4.8), title, items, badge, col)


# ==============================================================================
# SLIDE 8: Citizen Portal Experience
# ==============================================================================
slide8 = create_base_slide(is_dark=False)
add_header(slide8, "7. Citizen Portal: Intuitive Self-Service Reporting")

cards_s8 = [
    (Inches(0.8), "Streamlined Issue Reporting", [
        "One-click quick category chips (Pothole, Water, Streetlight, Waste, etc.).",
        "Interactive Manual Custom Category Box for non-standard municipal issues.",
        "Zone selection across 5 municipal wards (Central, North, East, South, West).",
        "Live photo preview and client-side format/size validation."
    ], "SUBMISSION", C_PRIMARY_D),
    (Inches(4.8), "Community Upvoting System", [
        "Public feed displaying ongoing complaints in the citizen's neighborhood.",
        "Citizens can upvote existing complaints to highlight collective urgency.",
        "Upvoting directly increments priority score, reducing municipal call center duplication.",
        "Real-time duplicate counter warnings prevent redundant submissions."
    ], "ENGAGEMENT", C_AMBER),
    (Inches(8.8), "Transparent Tracking & SLAs", [
        "Unique tracking reference: CIVIC-2026-XXXX.",
        "'My Complaints' tab displaying all past and active tickets submitted by the logged-in user.",
        "Live lifecycle visual progress bar: NEW → ASSIGNED → IN PROGRESS → RESOLVED.",
        "Clear SLA countdown showing remaining hours before deadline breach."
    ], "TRANSPARENCY", C_EMERALD)
]

for left, title, items, badge, col in cards_s8:
    add_card(slide8, left, Inches(1.8), Inches(3.7), Inches(4.8), title, items, badge, col)


# ==============================================================================
# SLIDE 9: Administrative Portal & Municipal Operations
# ==============================================================================
slide9 = create_base_slide(is_dark=False)
add_header(slide9, "8. Municipal Operations: Dedicated Approvals & Queues")

cards_s9 = [
    (Inches(0.8), "Dedicated Approvals Center", [
        "Supervisor vetting queue to verify authenticity before dispatching field crews.",
        "Summary metric cards: Pending Review, Approved & Dispatched, Rejected.",
        "1-Click Batch Approval: Allows supervisors to clear multiple valid issues simultaneously.",
        "Decision modal with preset remark pills for rapid, standardized dispatch."
    ], "APPROVALS", C_AMBER),
    (Inches(4.8), "Field Operations Queue", [
        "Strict 4-stage lifecycle progression: NEW → ASSIGNED → IN_PROGRESS → RESOLVED.",
        "Departmental dispatch to 9 specialized public boards (Roads, Water, Power, Sanitation).",
        "Officer assignment with contact tracking.",
        "Status Update Modal with resolution notes and direct citizen timeline updates."
    ], "FIELD WORK ORDERS", C_PRIMARY_D),
    (Inches(8.8), "Role-Based Security & Guardrails", [
        "Strict single-administrator credential enforcement (admin@civicportal.gov).",
        "Administrative tabs dynamically hidden from regular citizen accounts.",
        "Backend middleware returns 403 Forbidden for unauthorized mutation attempts.",
        "Audit trail logs supervisor actions for compliance and anti-fraud monitoring."
    ], "GOVERNANCE & RBAC", C_ROSE)
]

for left, title, items, badge, col in cards_s9:
    add_card(slide9, left, Inches(1.8), Inches(3.7), Inches(4.8), title, items, badge, col)


# ==============================================================================
# SLIDE 10: Executive Analytics & Hotspot Intelligence
# ==============================================================================
slide10 = create_base_slide(is_dark=False)
add_header(slide10, "9. Executive Analytics & Hotspot Intelligence")

cards_s10 = [
    (Inches(0.8), "Executive KPI Dashboard", [
        "Total Grievances Registered & Real-Time Resolution Rate (%).",
        "SLA Compliance Percentage & Average Resolution Duration.",
        "Aging Complaints Indicator: Highlights unresolved issues > 48h.",
        "Zone-by-zone performance comparisons across municipal wards."
    ], "KEY METRICS", C_PRIMARY_D),
    (Inches(4.8), "Visual Distribution Analytics", [
        "Interactive Status Breakdown Doughnut Chart (New, Assigned, In Progress, Resolved).",
        "Category Volume Bar Chart illustrating municipal resource demand.",
        "Approval Pipeline Breakdown (Pending vs. Approved vs. Rejected).",
        "Powered by Chart.js with dynamic real-time AJAX data refresh."
    ], "DATA VISUALIZATION", C_ACCENT),
    (Inches(8.8), "High-Priority Hotspots Table", [
        "Clustered spatial analysis identifying recurring problem intersections.",
        "Recurrence Counts: Ranks addresses with repeated infrastructure breakdowns.",
        "Highest Severity Tier tracking to focus municipal capital expenditure.",
        "Clean, high-contrast tabular presentation replacing slow GIS map rendering."
    ], "HOTSPOT DETECTION", C_ROSE)
]

for left, title, items, badge, col in cards_s10:
    add_card(slide10, left, Inches(1.8), Inches(3.7), Inches(4.8), title, items, badge, col)


# ==============================================================================
# SLIDE 11: Testing, Verification & Code Quality
# ==============================================================================
slide11 = create_base_slide(is_dark=False)
add_header(slide11, "10. Comprehensive Testing & Verification Suite")

# Stats Banner
b_box = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(1.1))
b_box.fill.solid()
b_box.fill.fore_color.rgb = RGBColor(236, 253, 245)
b_box.line.color.rgb = C_EMERALD
b_box.line.width = Pt(2)
tf_b = b_box.text_frame
tf_b.margin_top = Inches(0.18)
p = tf_b.paragraphs[0]
p.text = "Automated Test Suite Status: 31 of 31 Tests Passing (100% Pass Rate)"
p.font.size = Pt(16)
p.font.bold = True
p.font.color.rgb = C_EMERALD
p2 = tf_b.add_paragraph()
p2.text = "Verified on Python 3.14 + Pytest with full coverage across authentication, authorization, AI, and APIs."
p2.font.size = Pt(12)
p2.font.color.rgb = C_TEXT_MAIN

test_groups = [
    (Inches(0.8), "Auth & Registration (6 Tests)", [
        "Citizen self-registration validation",
        "Duplicate email rejection",
        "Admin email spoofing prevention",
        "Returning citizen login token",
        "Single-admin credential validation",
        "Strict 403 Forbidden security gate"
    ], C_EMERALD),
    (Inches(3.8), "API & Operations (7 Tests)", [
        "Health checks & config endpoints",
        "Issue submission & validation",
        "Full lifecycle status transitions",
        "Upvoting priority increment",
        "Analytics & metrics computation",
        "Geospatial hotspot aggregation",
        "Custom category handling"
    ], C_PRIMARY_D),
    (Inches(6.8), "AI & Prioritization (11 Tests)", [
        "Case study prompt extraction",
        "NLP categorization accuracy",
        "Duplicate text cosine similarity",
        "Base category severity scoring",
        "Aging penalty calculations",
        "SLA breach escalation logic",
        "Location hotspot bonuses"
    ], C_ACCENT),
    (Inches(9.8), "RBAC & Approvals (7 Tests)", [
        "Citizen complaint isolation",
        "Role-based tab access",
        "Admin approval & rejection workflow",
        "Batch approval execution",
        "Status filter precision",
        "ML dataset training & evaluation",
        "Text normalization benchmarking"
    ], C_AMBER)
]

for left, title, items, col in test_groups:
    add_card(slide11, left, Inches(3.1), Inches(2.75), Inches(3.5), title, items, None, col)


# ==============================================================================
# SLIDE 12: Production Cloud Deployment (Railway)
# ==============================================================================
slide12 = create_base_slide(is_dark=False)
add_header(slide12, "11. Production Cloud Deployment: Railway Architecture")

cards_s12 = [
    (Inches(0.8), "Why Railway Over Serverless (Vercel)?", [
        "Persistent Uvicorn Process: Runs FastAPI continuously without AWS Lambda 10s timeouts.",
        "In-Memory ML Cache: Scikit-Learn model stays in RAM for sub-10ms inference.",
        "Zero Cold Starts: Eliminates 4-8 second serverless spin-up delays for citizens.",
        "Single Origin: Serves static frontend and /api/ on one domain with zero CORS complexity."
    ], "PLATFORM ADVANTAGES", C_PRIMARY_D),
    (Inches(4.8), "Integrated 1-Click MongoDB", [
        "Dedicated cloud database provisioned in 1 click inside the same project canvas.",
        "Automatic environment variable injection: MONGO_URL provided directly to the web app.",
        "Zero manual IP whitelisting or VPC peering headaches required by external database providers.",
        "Persistent volume storage preserving all complaints, users, and audit records."
    ], "DATABASE PROVISIONING", C_EMERALD),
    (Inches(8.8), "Deployment Pipeline & Artifacts", [
        "Procfile: web: python run.py executing Uvicorn with auto-assigned $PORT.",
        "Dynamic Host Binding: Listens on 0.0.0.0 for containerized port forwarding.",
        "Automatic SSL/TLS: Live HTTPS *.up.railway.app domain provisioned instantly.",
        "Continuous Deployment: Auto-builds and deploys directly from GitHub main branch."
    ], "DEPLOYMENT WORKFLOW", C_ACCENT)
]

for left, title, items, badge, col in cards_s12:
    add_card(slide12, left, Inches(1.8), Inches(3.7), Inches(4.8), title, items, badge, col)


# ==============================================================================
# SLIDE 13: Future Scope & Roadmap
# ==============================================================================
slide13 = create_base_slide(is_dark=False)
add_header(slide13, "12. Future Scope & Next Milestones")

milestones = [
    (Inches(0.8), "Mobile App (Flutter / React Native)", [
        "Cross-platform mobile app for iOS and Android.",
        "Instant GPS geotagging and direct camera photo capture.",
        "Push notifications for status transitions and supervisor notes.",
        "Offline complaint drafting with automatic sync when connected."
    ], "MOBILE EXPANSION", C_PRIMARY_D),
    (Inches(4.8), "IoT Sensor Integration", [
        "Automated telemetry from smart water flow meters and streetlights.",
        "Predictive maintenance: Generates tickets before citizens report failures.",
        "Continuous pressure monitoring to detect water pipeline leakages instantly.",
        "Environmental sensors detecting local air and noise pollution surges."
    ], "SMART CITY IOT", C_ACCENT),
    (Inches(8.8), "Multilingual & Citizen Messaging", [
        "Voice-to-text grievance reporting in regional and local languages.",
        "Automated WhatsApp and SMS bot for complaint filing and status inquiry.",
        "Computer Vision for automated pothole depth and trash volume assessment.",
        "Public API access for municipal open data and civic hackathons."
    ], "OMNICHANNEL AI", C_EMERALD)
]

for left, title, items, badge, col in milestones:
    add_card(slide13, left, Inches(1.8), Inches(3.7), Inches(4.8), title, items, badge, col)


# ==============================================================================
# SLIDE 14: Conclusion & Q&A (Dark Theme)
# ==============================================================================
slide14 = create_base_slide(is_dark=True)

# Accent bar
bar = slide14.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0), Inches(0), Inches(0.3), Inches(7.5))
bar.fill.solid()
bar.fill.fore_color.rgb = C_PRIMARY
bar.line.fill.background()

# Badge
badge14 = slide14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.0), Inches(3.2), Inches(0.42))
badge14.fill.solid()
badge14.fill.fore_color.rgb = RGBColor(30, 58, 95)
badge14.line.color.rgb = C_PRIMARY
tf = badge14.text_frame
p = tf.paragraphs[0]
p.text = "✔  PROJECT SUMMARY & IMPACT"
p.font.size = Pt(11)
p.font.bold = True
p.font.color.rgb = C_PRIMARY

# Title
tb = slide14.shapes.add_textbox(Inches(1.2), Inches(1.6), Inches(11), Inches(1.8))
tf2 = tb.text_frame
tf2.word_wrap = True
p = tf2.paragraphs[0]
p.text = "Empowering Citizens, Streamlining Municipal Action"
p.font.size = Pt(32)
p.font.bold = True
p.font.color.rgb = C_TEXT_LIGHT
p.space_after = Pt(10)
p_sub = tf2.add_paragraph()
p_sub.text = "A complete, production-tested civic operations ecosystem built with FastAPI, MongoDB, and Scikit-Learn."
p_sub.font.size = Pt(16)
p_sub.font.color.rgb = C_PRIMARY

# Summary Cards
concl_cards = [
    ("Transparent Citizen Governance", "Eliminates call center black holes through real-time tracking, SLA countdowns, and community upvoting.", C_PRIMARY),
    ("Automated Prioritization", "Rule-based 0-100 scoring ensures life-critical and aging civic problems are routed to field crews first.", C_AMBER),
    ("Battle-Tested Reliability", "100% automated test pass rate across 31 test suites, strict single-admin RBAC, and cloud deployment ready.", C_EMERALD)
]

for idx, (c_title, c_desc, c_col) in enumerate(concl_cards):
    left = Inches(1.2 + idx * 3.7)
    top = Inches(3.6)
    c_shape = slide14.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, Inches(3.4), Inches(2.2))
    c_shape.fill.solid()
    c_shape.fill.fore_color.rgb = C_CARD_DARK
    c_shape.line.color.rgb = c_col
    c_shape.line.width = Pt(1.5)
    tf_c = c_shape.text_frame
    tf_c.margin_left = Inches(0.2)
    tf_c.margin_right = Inches(0.2)
    tf_c.margin_top = Inches(0.2)
    p = tf_c.paragraphs[0]
    p.text = c_title
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = c_col
    p.space_after = Pt(8)
    p_d = tf_c.add_paragraph()
    p_d.text = c_desc
    p_d.font.size = Pt(12)
    p_d.font.color.rgb = C_TEXT_LIGHT

# Footer Q&A Note
qa_box = slide14.shapes.add_textbox(Inches(1.2), Inches(6.1), Inches(11), Inches(0.8))
tf_qa = qa_box.text_frame
p_qa = tf_qa.paragraphs[0]
p_qa.text = "Thank You!  |  Questions & Answers Welcome  |  Live Demo Available"
p_qa.font.size = Pt(16)
p_qa.font.bold = True
p_qa.font.color.rgb = C_PRIMARY
p_qa.alignment = PP_ALIGN.CENTER

# Save presentation
prs.save(OUTPUT_FILE)
print(f"Presentation successfully saved to: {OUTPUT_FILE}")
