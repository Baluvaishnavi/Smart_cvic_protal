"""
Main FastAPI Application Entrypoint.
Initializes database, seeds initial NYC 311 service requests,
registers API routers, and mounts frontend static files.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response

from app.database import init_db, db
from app.routes import complaints, analytics, ai, auth
from app.seed_data import seed_nyc_311_data
from app.config import CATEGORIES_CONFIG, NYC_BOROUGHS


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize MongoDB connection & indexes
    init_db()
    # Seed initial NYC 311 dataset if MongoDB collection is fresh
    try:
        count = seed_nyc_311_data(db, force=False)
        print(f"[Civic Portal] MongoDB initialized with {count} records.")
    except Exception as e:
        print(f"[Civic Portal] MongoDB seed note: {e}")
    yield


app = FastAPI(
    title="Smart Civic Complaint & Issue Management System",
    description="Municipal authority civic portal handling citizen issue submission, rule-based prioritization, AI classification, and executive SLA analytics.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for flexible development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(analytics.router)
app.include_router(ai.router)


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)


@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "system": "Smart Civic Complaint & Issue Management System",
        "version": "1.0.0"
    }


@app.get("/api/config/categories")
def get_categories():
    """Return available civic categories and their SLA definitions."""
    return {
        "categories": CATEGORIES_CONFIG,
        "boroughs": NYC_BOROUGHS
    }


# Frontend static files mounting
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

    @app.get("/")
    def serve_frontend_index():
        return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))
