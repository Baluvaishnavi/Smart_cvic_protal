"""
MongoDB database connection and collection management using PyMongo.
Connects to MongoDB Server on localhost:27017 with database 'smart_civic_311'.
"""

import os
from typing import Generator, Tuple
import pymongo
from pymongo.database import Database

# Comprehensive detection of cloud MongoDB environment variables (Railway, Atlas, Render, Heroku)
MONGODB_URL = (
    os.environ.get("MONGODB_URL")
    or os.environ.get("MONGO_URL")
    or os.environ.get("MONGODB_URI")
    or os.environ.get("MONGO_URI")
    or os.environ.get("MONGO_PRIVATE_URL")
    or os.environ.get("MONGO_PUBLIC_URL")
    or os.environ.get("DATABASE_URL")
    or "mongodb://localhost:27017"
)
DB_NAME = os.environ.get("MONGODB_DB_NAME", "smart_civic_311")

# Configure client connection options (SSL/TLS, timeouts)
is_cloud = not ("localhost" in MONGODB_URL or "127.0.0.1" in MONGODB_URL)
client_kwargs = {
    "serverSelectionTimeoutMS": 4000 if is_cloud else 1500,
    "connectTimeoutMS": 4000 if is_cloud else 1500,
    "socketTimeoutMS": 4000 if is_cloud else 1500,
}

# Attach certifi CA certificates ONLY for cloud SSL/TLS connections (e.g. MongoDB Atlas)
if MONGODB_URL.startswith("mongodb+srv://") or "tls=true" in MONGODB_URL.lower() or "ssl=true" in MONGODB_URL.lower():
    try:
        import certifi
        client_kwargs["tlsCAFile"] = certifi.where()
    except Exception:
        pass

try:
    client = pymongo.MongoClient(MONGODB_URL, **client_kwargs)
except Exception as _e:
    print(f"[MongoDB] Client initialization notice: {_e}")
    client = pymongo.MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)


def _resolve_database() -> Database:
    """Safely select database instance, honoring URI database if specified."""
    try:
        uri_db = client.get_default_database()
        if uri_db is not None:
            return uri_db
    except Exception:
        pass
    return client[DB_NAME]


db: Database = _resolve_database()


def check_db_connection() -> Tuple[bool, str]:
    """Test live MongoDB connection."""
    try:
        client.admin.command("ping")
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e)

# Collections
complaints_col = db["complaints"]
timeline_col = db["complaint_timeline"]
comments_col = db["complaint_comments"]
users_col = db["users"]
sessions_col = db["sessions"]


def get_db() -> Generator[Database, None, None]:
    """FastAPI dependency to yield MongoDB database instance."""
    yield db


def init_db():
    """Verify connection and ensure indexes on MongoDB collections."""
    try:
        # Ping MongoDB server
        client.admin.command("ping")
        print(f"[MongoDB] Successfully connected to database '{db.name}'")

        # Indexes for fast querying & sorting
        complaints_col.create_index([("id", pymongo.ASCENDING)], unique=True)
        complaints_col.create_index([("status", pymongo.ASCENDING)])
        complaints_col.create_index([("category", pymongo.ASCENDING)])
        complaints_col.create_index([("borough", pymongo.ASCENDING)])
        complaints_col.create_index([("priority", pymongo.ASCENDING)])
        complaints_col.create_index([("priority_score", pymongo.DESCENDING)])
        complaints_col.create_index([("created_at", pymongo.DESCENDING)])
        complaints_col.create_index([("sla_due_date", pymongo.ASCENDING)])

        # Compound index for geospatial/borough & category queries
        complaints_col.create_index([("borough", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])
        complaints_col.create_index([("category", pymongo.ASCENDING), ("status", pymongo.ASCENDING)])

        # Timeline and Comments indexes
        timeline_col.create_index([("complaint_id", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)])
        comments_col.create_index([("complaint_id", pymongo.ASCENDING), ("created_at", pymongo.ASCENDING)])

        # Users and Sessions indexes
        users_col.create_index([("email", pymongo.ASCENDING)], unique=True)
        sessions_col.create_index([("token", pymongo.ASCENDING)], unique=True)

    except Exception as e:
        print(f"[MongoDB] Connection warning: {e}")
