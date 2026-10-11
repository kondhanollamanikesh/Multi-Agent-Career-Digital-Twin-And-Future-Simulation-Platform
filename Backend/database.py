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