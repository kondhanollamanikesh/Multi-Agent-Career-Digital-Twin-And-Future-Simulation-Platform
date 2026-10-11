from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form
)

from fastapi.middleware.cors import CORSMiddleware

import os
import sys

# Windows consoles default to cp1252 and crash when the
# LLM returns unicode characters (e.g. non-breaking hyphens).

if hasattr(sys.stdout, "reconfigure"):

    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace"
    )

    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="replace"
    )

from models import Preferences

from database import (
    users_collection,
    career_twins_collection
)

from digital_twin import create_career_twin


# ==========================================
# APP
# ==========================================

app = FastAPI()


# ==========================================
# CORS
# ==========================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=["*"],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ==========================================
# HOME
# ==========================================

@app.get("/")
def home():

    return {
        "message":
            "Career Digital Twin API is running"
    }


# ==========================================
# SAVE PREFERENCES
# ==========================================

@app.post("/preferences")
def save_preferences(

    user_id: str = Form(...),

    target_role: str = Form(None),

    location: str = Form(None),

    work_mode: str = Form(None),

    employment_type: str = Form(None),

    salary_expectation: str = Form(None),

    relocation: bool = Form(None),

    preferred_industry: str = Form(None),

    experience_level: str = Form(None)
):

    preferences = Preferences(

        target_role=target_role,

        location=location,

        work_mode=work_mode,

        employment_type=employment_type,

        salary_expectation=salary_expectation,

        relocation=relocation,

        preferred_industry=preferred_industry,

        experience_level=experience_level
    )

    users_collection.update_one(

        {
            "user_id": user_id
        },

        {
            "$set": {
                "preferences":
                    preferences.model_dump()
            }
        },

        upsert=True
    )

    return {

        "message":
            "Preferences saved successfully",

        "user_id":
            user_id,

        "preferences":
            preferences.model_dump()
    }


# ==========================================
# GENERATE CAREER TWIN
# ==========================================

@app.post("/career-twin")
async def generate_career_twin(

    user_id: str = Form(...),

    resume: UploadFile = File(...)
):

    # ==========================================
    # CREATE UPLOAD DIRECTORY
    # ==========================================

    upload_dir = "uploads"

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    # ==========================================
    # SAVE RESUME
    # ==========================================

    resume_path = os.path.join(

        upload_dir,

        os.path.basename(
            resume.filename
        )
    )

    with open(
        resume_path,
        "wb"
    ) as file:

        file.write(
            await resume.read()
        )

    # ==========================================
    # GET USER PREFERENCES
    # ==========================================

    user = users_collection.find_one(
        {
            "user_id": user_id
        }
    )

    preferences = Preferences()

    if user and "preferences" in user:

        preferences = Preferences(
            **user["preferences"]
        )

    # ==========================================
    # CREATE CAREER TWIN
    # ==========================================

    career_twin = create_career_twin(

        resume_path,

        user_id,

        preferences
    )

    # ==========================================
    # SAVE CAREER TWIN
    # ==========================================

    career_twins_collection.update_one(

        {
            "user_id":
                user_id
        },

        {
            "$set":
                career_twin.model_dump()
        },

        upsert=True
    )

    # ==========================================
    # RESPONSE
    # ==========================================

    return {

        "message":
            "Career Twin created successfully",

        "career_twin":
            career_twin.model_dump()
    }