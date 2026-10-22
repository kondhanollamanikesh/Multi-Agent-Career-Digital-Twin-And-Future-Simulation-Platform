# ==========================================
# Career Digital Twin - Database
# ==========================================

import os

from pymongo import MongoClient
from dotenv import load_dotenv


# ==========================================
# ENVIRONMENT
# ==========================================

load_dotenv()


# ==========================================
# CONFIGURATION
# ==========================================

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017"
)

DATABASE_NAME = os.getenv(
    "MONGO_DATABASE",
    "career_digital_twin"
)


# ==========================================
# MONGO CLIENT
# ==========================================

client = MongoClient(
    MONGO_URI,
    serverSelectionTimeoutMS=5000
)

db = client[DATABASE_NAME]


# ==========================================
# COLLECTIONS
# ==========================================

users_collection = db["users"]

career_twins_collection = db["career_twins"]

role_knowledge_collection = db["role_knowledge"]

# Agent 5 - Learning Roadmap & Course Recommendation
# Stores selected resources and per-skill learning progress.
learning_progress_collection = db["learning_progress"]

# Auth - user accounts. Stored separately from the
# preference documents in `users` so existing preference
# data is never touched.
auth_users_collection = db["auth_users"]


# ==========================================
# DATABASE CHECK
# ==========================================

def check_database_connection():

    try:

        client.admin.command(
            "ping"
        )

        print(
            "[MongoDB] Connection successful."
        )

        return True

    except Exception as exc:

        print(
            "[MongoDB] Connection failed:",
            exc
        )

        return False