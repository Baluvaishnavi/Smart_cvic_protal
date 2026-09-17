"""
MongoDB database connection and collection management using PyMongo.
Connects to MongoDB Server on localhost:27017 with database 'smart_civic_311'.
"""

import os
from typing import Generator
import pymongo
from pymongo.database import Database

MONGODB_URL = (
    os.environ.get("MONGODB_URL")
    or os.environ.get("MONGO_URL")
    or os.environ.get("MONGO_PRIVATE_URL")
    or os.environ.get("MONGO_PUBLIC_URL")
    or "mongodb://localhost:27017"
)
DB_NAME = os.environ.get("MONGODB_DB_NAME", "smart_civic_311")

client = pymongo.MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
db: Database = client[DB_NAME]

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
        print(f"[MongoDB] Successfully connected to {MONGODB_URL} (Database: '{DB_NAME}')")

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
