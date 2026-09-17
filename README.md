# 🏛️ Smart Civic Complaint & Municipal Operations Portal
> **An AI-Powered, Data-Driven Governance Platform with Automated Prioritization, SLA Tracking, and Real-Time Operational Queues.**

[![Python 3.14](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-009688.svg)](https://fastapi.tiangolo.com/)
[![MongoDB](https://img.shields.io/badge/MongoDB-PyMongo_4.6-47A248.svg)](https://www.mongodb.com/)
[![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.4.0-F7931E.svg)](https://scikit-learn.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-31%2F31%20Passing%20(100%25)-success.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 Table of Contents
1. [Project Overview](#-project-overview)
2. [What the Project Does: End-to-End Workflow (Scratch to End)](#-what-the-project-does-end-to-end-workflow-scratch-to-end)
3. [Technology Stack Used at Each Stage](#-technology-stack-used-at-each-stage)
4. [Dynamic Rule-Based Prioritization Engine](#-dynamic-rule-based-prioritization-engine)
5. [Machine Learning & NLP Pipeline](#-machine-learning--nlp-pipeline)
6. [Database Schema & Collections (MongoDB)](#-database-schema--collections-mongodb)
7. [Role-Based Access Control (RBAC) & Default Credentials](#-role-based-access-control-rbac--default-credentials)
8. [Installation & Local Setup Guide](#-installation--local-setup-guide)

---

## 🌟 Project Overview

Municipal administrations face overwhelming challenges managing civic grievances—from hazardous roadway potholes and burst water mains to dark streetlights and waste accumulation. Traditional grievance systems act as administrative "black holes" where complaints lack transparency, duplicate reports overwhelm staff, and life-critical hazards wait behind minor cosmetic issues.

The **Smart Civic Complaint & Municipal Operations Portal** provides a transparent, automated, and intelligent solution. It connects citizens and municipal departments through a responsive web application that automatically classifies grievances, detects duplicates in real time, prioritizes repairs using an algorithmic 0–100 scoring model, and tracks strict Service Level Agreement (SLA) deadlines until final resolution.

---

## 🔄 What the Project Does: End-to-End Workflow (Scratch to End)

The platform governs the entire lifecycle of a municipal issue through 8 continuous stages:

```
[Citizen Registration & Login]
              │
              ▼
[Grievance Submission + Custom Category] ──▶ [NLP Auto-Classification & Duplicate Check]
              │
              ▼
[Dynamic 0-100 Prioritization Engine]
              │
              ▼
[Supervisor Approvals Center] (Vetting & 1-Click Batch Approval)
              │
              ▼
[Operations Queue] (Department Dispatch & Field Officer Assignment)
              │
              ▼
[Lifecycle Progression: NEW ──▶ ASSIGNED ──▶ IN_PROGRESS ──▶ RESOLVED]
              │
              ▼
[Citizen Tracking Portal + Real-Time Executive Analytics & Hotspot Tables]
```

### Stage 1: Citizen Onboarding & Identity Management
* Citizens self-register using their Full Name, Email, Password, and Phone Number.
* Passwords are encrypted using **salted SHA-256 hashing** (`civic_portal_secure_salt_2026_`) before being stored in the MongoDB `users` collection.
* System enforces unique email constraints and strictly blocks unauthorized users from claiming the reserved administrator identity.
* Returning citizens receive a secure bearer session token persisted in `localStorage`.

### Stage 2: Grievance Submission & Manual Category Input
* Citizens report an issue by entering a title, detailed description, municipal ward zone (Central, North, East, South, West), and optional photo.
* **Interactive Category Selection**: Citizens can click preset category chips (Pothole, Water Supply, Streetlight, Garbage, etc.) or click **"✏️ Other (Custom)"** to reveal an interactive manual input box for specialized issues (e.g., stray animal rescue, playground damage).
* Citizens can browse ongoing issues in their neighborhood and **Upvote** existing tickets rather than submitting duplicate complaints.

### Stage 3: AI NLP Triage & Duplicate Detection
* Upon text entry, an in-memory **Scikit-Learn Machine Learning pipeline** analyzes the unstructured text:
  * Automatically extracts unigram/bigram and sub-word character features.
  * Predicts the primary municipal category and department.
* A **Cosine Similarity engine** compares the new complaint vector against active tickets in the same ward. If a similar issue is detected, the citizen is warned immediately, preventing database clutter.

### Stage 4: Dynamic 0–100 Rule-Based Prioritization
* Every complaint is assigned an algorithmic urgency score ($S \in [0, 100]$):
  $$S = S_{\text{base}} + P_{\text{aging}} + P_{\text{breach}} + M_{\text{duplicates}} + B_{\text{location}}$$
* Severity is weighted by category risk, age penalties (+2 pts/day), immediate SLA breach penalties (+15 pts), community upvotes (+2.5 pts each), and co-located incident multipliers.
* Issues are categorized into 4 tiers: **CRITICAL** (12h SLA), **HIGH** (24h SLA), **MEDIUM** (48h SLA), or **LOW** (72h SLA).

### Stage 5: Supervisor Vetting (Dedicated Approvals Center)
* Municipal supervisors review submissions in the **Approvals Center** before field crews are mobilized.
* Features summary KPI cards (Pending Review, Approved & Dispatched, Rejected).
* Supervisors can execute **1-Click Batch Approvals** or reject false alarms with standardized remark pills.

### Stage 6: Field Operations Queue & Departmental Dispatch
* Approved complaints move directly to the **Operations Queue** and are routed to one of 9 municipal boards (Roadway Maintenance, Water Drainage, Electrical Board, Sanitation, etc.).
* Supervisors assign field officers and update statuses through the operational pipeline:
  $$\text{NEW} \longrightarrow \text{ASSIGNED} \longrightarrow \text{IN\_PROGRESS} \longrightarrow \text{RESOLVED}$$

### Stage 7: Citizen Tracking & Immutable Audit Log
* Citizens track ticket resolution in real time inside **"My Complaints"**.
* Features a live 4-stage visual progress bar, remaining SLA countdown hours, and officer remarks.
* An immutable audit log (`complaint_timeline`) records every action, timestamp, and actor for complete municipal accountability.

### Stage 8: Executive Analytics & Hotspot Intelligence
* Municipal commissioners access the **Executive Analytics** portal.
* Summarizes city-wide metrics: Total Grievances, Resolution Rate (%), SLA Compliance (%), and Aging Complaints (> 48h).
* High-contrast **Hotspot Table** highlights recurring problem intersections by recurrence frequency and severity tier, guiding municipal budget allocation.

---

## 🛠️ Technology Stack Used at Each Stage

| Stage / Component | Technologies Used | Exact Purpose |
| :--- | :--- | :--- |
| **Presentation Layer (Frontend)** | **HTML5, Tailwind CSS, Vanilla JavaScript (ES6+), Chart.js** | Single Page Application (SPA) providing responsive citizen reporting, dynamic category selection chips, supervisor approval modals, real-time SLA countdown timers, non-blocking toast notifications, and interactive analytics charts. |
| **Application Layer (Backend API)** | **FastAPI, Uvicorn, Python 3.14** | High-performance asynchronous REST API. Handles request routing, Pydantic v2 data validation, automated lifecycle status transitions, and serves static frontend assets from a single origin with zero CORS latency. |
| **Database & Persistence** | **MongoDB, PyMongo 4.6** | Flexible document store accommodating semi-structured complaint attributes, citizen profiles, session tokens, and immutable timeline audit trails. |
| **AI / NLP & Duplicate Engine** | **Scikit-Learn 1.4, Joblib** | Preprocesses raw text with TF-IDF unigram + bigram and character n-grams. Uses a Soft Voting Ensemble (LinearSVC, Logistic Regression, ComplementNB) for sub-10ms classification and cosine similarity duplicate matching. |
| **Security & RBAC** | **Salted SHA-256, Bearer Session Auth** | Citizen registration and strict single-administrator authorization. Protected mutation endpoints verify the token and return `403 Forbidden` for unauthorized accounts. |
| **Automated Verification** | **Pytest 9.1, HTTPX** | Automated test suite comprising 31 tests covering authorization gates, lifecycle transitions, prioritization math, and ML classification accuracy. |
| **Cloud Deployment** | **Railway PaaS, Procfile, Docker** | Containerized cloud deployment running persistent Uvicorn processes with in-memory ML model caching and 1-click cloud MongoDB provisioning. |

---

## ⚖️ Dynamic Rule-Based Prioritization Engine

Rather than sorting complaints by static submission time, the platform computes a deterministic **Priority Score (0 to 100)**:

$$\text{Priority Score } (S) = S_{\text{base}} + P_{\text{aging}} + P_{\text{breach}} + M_{\text{duplicates}} + B_{\text{location}}$$

### Scoring Parameters:
* **Base Category Severity ($S_{\text{base}}$)**:
  * Gas Leak / Structural Collapse: **45 pts**
  * Water Main Burst / Drainage Overflow: **35 pts**
  * Hazardous Roadway Pothole: **30 pts**
  * Streetlight Outage / Exposed Wiring: **25 pts**
  * Garbage & Sanitation Accumulation: **20 pts**
  * Noise & Disturbance / Minor Civic: **15 pts**
* **Aging Penalty ($P_{\text{aging}}$)**: $+2.0\text{ pts}$ per elapsed day (capped at $+20\text{ pts}$). Ensures long-neglected complaints are not buried.
* **SLA Breach Penalty ($P_{\text{breach}}$)**: Immediate $+15\text{ pts}$ penalty once the target resolution deadline expires.
* **Community Multipliers ($M_{\text{duplicates}}$)**: $+2.5\text{ pts}$ per citizen upvote; $+5.0\text{ pts}$ per co-located report.
* **Location Hotspot Bonus ($B_{\text{location}}$)**: $+10\text{ pts}$ for intersections with $\ge 3$ active reports.

### Priority Tiers & SLA Targets:
| Tier | Score Range | SLA Resolution Target | Escalation Level |
| :--- | :--- | :--- | :--- |
| **CRITICAL** | **85 – 100** | **12 Hours** | Emergency field crew dispatch |
| **HIGH** | **65 – 84** | **24 Hours** | High-priority departmental work order |
| **MEDIUM** | **35 – 64** | **48 Hours** | Standard operational schedule |
| **LOW** | **0 – 34** | **72 Hours** | Routine maintenance sweep |

---

## 🤖 Machine Learning & NLP Pipeline

### 1. Training Dataset (`nyc_311_training_data.csv`)
* **Size**: 360 curated, balanced real-world municipal grievance records (40 samples per category).
* **Fields**: `complaint_text` (unstructured free text), `category` (target label), `borough` (ward zone).
* **9 Target Classes**:
  1. `Pothole`
  2. `Water Supply`
  3. `Streetlight`
  4. `Garbage & Sanitation`
  5. `Broken Sidewalk`
  6. `Traffic Signal`
  7. `Trees & Parks`
  8. `Noise & Disturbance`
  9. `General Civic Issue`

### 2. Model Architecture: Soft Voting Multi-Model Ensemble
* **Hybrid Feature Union**:
  * **Word N-Grams (1–2)**: Captures civic phrase context (e.g., *"water leak"*, *"street light"*, *"power outage"*).
  * **Character N-Grams (3–5)**: Uses sub-word word-boundary features (`char_wb`) to recognize typos, misspellings, and colloquial municipal terms.
* **Ensemble Classifiers**:
  * **Calibrated Linear Support Vector Machine (`LinearSVC`)** (Weight: 4)
  * **Multinomial Logistic Regression (`LogisticRegression`)** (Weight: 3)
  * **Complement Naive Bayes (`ComplementNB`)** (Weight: 2)

### 3. Performance Metrics (Holdout Evaluation & 5-Fold Cross-Validation)
* **Holdout Test Accuracy**: **91.7%**
* **5-Fold Cross-Validation Accuracy**: **91.4% (±1.8%)**
* **Weighted F1-Score**: **91.5%**
* **Precision on Critical Classes (Pothole & Water Supply)**: **100.0%**
* **Inference Speed**: **< 10ms** per prediction in RAM.

---

## 🗄️ Database Schema & Collections (MongoDB)

The MongoDB database (`smart_civic_311`) utilizes 5 indexed collections:

1. **`complaints`**: Core document store.
   * `id`: Unique municipal ticket string (e.g., `"CIVIC-2026-1042"`).
   * `title`, `description`, `category`, `ward_zone`, `address`.
   * `priority_score` (Float 0–100), `priority_tier` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`).
   * `status` (`NEW`, `ASSIGNED`, `IN_PROGRESS`, `RESOLVED`).
   * `approval_status` (`PENDING`, `APPROVED`, `REJECTED`).
   * `assigned_department`, `assigned_officer`, `upvotes`, `sla_target_hours`, `created_at`.
2. **`users`**: Citizen and admin accounts.
   * `email` (Unique Index), `hashed_password` (Salted SHA-256), `full_name`, `phone_number`, `role` (`CITIZEN` or `ADMIN`).
3. **`sessions`**: Active authentication tokens.
   * `token`, `email`, `role`, `created_at`, `expires_at`.
4. **`complaint_timeline`**: Immutable audit logs.
   * `complaint_id`, `action` (`CREATED`, `APPROVED`, `REJECTED`, `ASSIGNED`, `STATUS_CHANGE`), `performed_by`, `notes`, `timestamp`.
5. **`complaint_comments`**: Public and internal correspondence between citizens and municipal supervisors.

---

## 🔐 Role-Based Access Control (RBAC) & Default Credentials

| Persona | Default Email | Default Password | Role | Access Permissions |
| :--- | :--- | :--- | :--- | :--- |
| **Municipal Administrator** | `admin@civicportal.gov` | `admin123` | `ADMIN` | Full access: Approvals Center, 1-click batch approvals, Operations Queue, department dispatch, status updates, and Executive Analytics. |
| **Pre-Seeded Citizen** | `citizen@civicportal.gov` | `citizen123` | `CITIZEN` | Submit issues, custom category input, community upvoting, and personal "My Complaints" tracking. Admin tabs are locked. |
| **Self-Registered Citizen** | *(Any valid email)* | *(User defined)* | `CITIZEN` | Immediate self-registration via `POST /api/auth/register`. |

---

## 💻 Installation & Local Setup Guide

### Step 1: Clone or Open Project
```powershell
cd C:\Users\baluv\OneDrive\Desktop\smart_civic_portal
```

### Step 2: Ensure MongoDB is Running
MongoDB runs locally on port `27017` (`mongodb://localhost:27017`):
```powershell
mongod --version
```

### Step 3: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Run the Application Server
```powershell
python run.py
```
* 🌐 **Web Portal**: [http://localhost:8000/](http://localhost:8000/)
* 📑 **Interactive OpenAPI Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* 📊 **Interactive Web Slide Deck**: [http://localhost:8000/presentation.html](http://localhost:8000/presentation.html)

---

