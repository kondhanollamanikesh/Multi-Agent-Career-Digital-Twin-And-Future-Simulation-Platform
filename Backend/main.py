from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    Query,
    Depends
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

# ============================================================
# Agent 5 - Learning Roadmap & Course Recommendation
# ============================================================

import requests

from fastapi import HTTPException

from agents.course_service import (
    search_youtube_courses,
    get_ranked_courses
)

from agents.resource_service import (
    gather_resources,
    platform_search_links
)

from agents.learning_roadmap_agent import (
    generate_learning_roadmap
)

from pydantic import BaseModel
from typing import Optional

import learning_progress

# ============================================================
# Auth - full login system (bcrypt + JWT)
# ============================================================

import re

from bson import ObjectId
from bson.errors import InvalidId

from database import auth_users_collection

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
)


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
# AUTH - FULL LOGIN SYSTEM
# ==========================================
#
# bcrypt password hashing + JWT bearer tokens.
#
# Every user-scoped endpoint below now derives user_id
# from the logged-in token, so one person can never read
# or overwrite another person's Career Twin.
#
# Public:  /auth/register, /auth/login
# Private: everything else marked "Authenticated user"
# ==========================================


# -----------------------------------------
# REQUEST / RESPONSE MODELS
# -----------------------------------------

class RegisterRequest(BaseModel):

    email: str

    password: str

    name: str = ""


class LoginRequest(BaseModel):

    email: str

    password: str


class AuthUser(BaseModel):

    user_id: str

    email: str

    name: str


class AuthResponse(BaseModel):

    access_token: str

    token_type: str = "bearer"

    user: AuthUser


# -----------------------------------------
# VALIDATION HELPERS
# -----------------------------------------

EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)

MIN_PASSWORD_LENGTH = 8


def _normalize_email(email: str) -> str:

    return str(email or "").strip().lower()


def _find_auth_user(email: str):

    return auth_users_collection.find_one(
        {
            "email": _normalize_email(email)
        }
    )


def _public_user(document) -> AuthUser:

    return AuthUser(

        user_id=str(document["_id"]),

        email=document.get("email", ""),

        name=document.get("name", "")
    )


# -----------------------------------------
# 1. REGISTER
# -----------------------------------------

@app.post("/auth/register")
def register(request: RegisterRequest):
    """Create an account and return a JWT."""

    email = _normalize_email(request.email)

    password = str(request.password or "")

    name = str(request.name or "").strip()

    # ----------------------------------------------
    # VALIDATE
    # ----------------------------------------------

    if not EMAIL_PATTERN.match(email):

        raise HTTPException(

            status_code=400,

            detail="Please enter a valid email address."
        )

    if len(password) < MIN_PASSWORD_LENGTH:

        raise HTTPException(

            status_code=400,

            detail=(
                f"Password must be at least "
                f"{MIN_PASSWORD_LENGTH} characters."
            )
        )

    # ----------------------------------------------
    # CHECK DUPLICATE
    # ----------------------------------------------

    if _find_auth_user(email):

        raise HTTPException(

            status_code=409,

            detail=(
                "An account with this email already "
                "exists. Please log in instead."
            )
        )

    # ----------------------------------------------
    # CREATE
    # ----------------------------------------------

    document = {

        "email": email,

        "name": name or email.split("@")[0],

        # Plain text is NEVER stored.
        "password_hash": hash_password(password),

        "created_at": learning_progress.utc_now()
    }

    result = auth_users_collection.insert_one(
        document
    )

    document["_id"] = result.inserted_id

    print(
        "[Auth] Registered:",
        email
    )

    return AuthResponse(

        access_token=create_access_token(

            user_id=str(result.inserted_id),

            email=email
        ),

        user=_public_user(document)
    )


# -----------------------------------------
# 2. LOGIN
# -----------------------------------------

@app.post("/auth/login")
def login(request: LoginRequest):
    """Verify credentials and return a JWT."""

    document = _find_auth_user(
        request.email
    )

    if not document or not verify_password(

        str(request.password or ""),

        document.get("password_hash", "")
    ):

        # Same message for wrong email and wrong
        # password, so an attacker cannot tell which
        # emails are registered.

        raise HTTPException(

            status_code=401,

            detail="Incorrect email or password."
        )

    print(
        "[Auth] Login:",
        document.get("email")
    )

    return AuthResponse(

        access_token=create_access_token(

            user_id=str(document["_id"]),

            email=document.get("email", "")
        ),

        user=_public_user(document)
    )


# -----------------------------------------
# 3. CURRENT USER
# -----------------------------------------

@app.get("/auth/me")
def read_current_user(

    current_user: dict = Depends(
        get_current_user
    )
):
    """Return the logged-in user from their token."""

    document = None

    try:

        document = auth_users_collection.find_one(
            {
                "_id": ObjectId(
                    current_user["sub"]
                )
            }
        )

    except (InvalidId, KeyError):

        document = None

    if not document:

        raise HTTPException(

            status_code=401,

            detail="Account no longer exists."
        )

    return _public_user(document)


def _user_id_from_token(
    current_user: dict
) -> str:
    """Single source of truth for whose data this is."""

    return str(
        current_user.get("sub", "")
    ).strip()


# -----------------------------------------
# CAREER TWIN STATUS (IS A TWIN READY?)
# -----------------------------------------
#
# Lets the frontend ask "does this user already have a
# Career Twin?" so it can skip straight to the dashboard
# instead of forcing another upload.
# ==========================================

@app.get("/career-twin/status")
def career_twin_status(

    current_user: dict = Depends(
        get_current_user
    )
):
    """Report whether the logged-in user has a Career Twin."""

    user_id = _user_id_from_token(
        current_user
    )

    twin = career_twins_collection.find_one(

        {"user_id": user_id},

        {

            "_id": 0,

            "profile": 1,

            "skills": 1,

            "career_state": 1,

            "twin_version": 1
        }
    )

    if not twin:

        return {

            "has_twin": False,

            "message": (
                "No Career Twin yet. Upload your resume "
                "to generate one."
            )
        }

    career_state = twin.get(
        "career_state"
    ) or {}

    return {

        "has_twin": True,

        "target_role": (
            (twin.get("profile") or {})
            .get("target_role")
        ),

        "skill_count": len(
            twin.get("skills") or []
        ),

        "readiness_score":
            career_state.get(
                "readiness_score"
            ),

        "market_alignment":
            career_state.get(
                "market_alignment"
            ),

        "message": "Career Twin is ready."
    }


# -----------------------------------------
# FULL CAREER TWIN (FOR FRONTEND RENDERING)
# -----------------------------------------
#
# Returns the complete saved twin so the Career Twin,
# Skill Gap Analysis and Job Opportunities pages can all
# render real data instead of mock values.
# ==========================================

@app.get("/career-twin")
def get_career_twin(

    current_user: dict = Depends(
        get_current_user
    )
):
    """Return the logged-in user's full Career Twin."""

    user_id = _user_id_from_token(
        current_user
    )

    twin = career_twins_collection.find_one(

        {"user_id": user_id},

        {"_id": 0}
    )

    if not twin:

        raise HTTPException(

            status_code=404,

            detail=(
                "No Career Twin yet. Upload your resume "
                "to generate one."
            )
        )

    return {

        "has_twin": True,

        "career_twin": twin
    }


# ==========================================
# SAVE PREFERENCES
# ==========================================
#
# Authenticated. user_id comes from the JWT, so a user can
# only ever write to their own record.
#
# Accepts a JSON body - this also fixes the earlier 422,
# because the frontend sends application/json.
# ==========================================

@app.post("/preferences")
def save_preferences(

    payload: Preferences,

    current_user: dict = Depends(
        get_current_user
    )
):

    user_id = _user_id_from_token(
        current_user
    )

    preferences = payload

    users_collection.update_one(

        {
            "user_id": user_id
        },

        {
            "$set": {
                "user_id": user_id,

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

    resume: UploadFile = File(...),

    current_user: dict = Depends(
        get_current_user
    )
):

    # ==========================================
    # USER (FROM TOKEN)
    # ==========================================

    user_id = _user_id_from_token(
        current_user
    )

    # ==========================================
    # VALIDATE FILE TYPE
    # ==========================================

    filename = os.path.basename(
        resume.filename or ""
    )

    if not filename.lower().endswith(".pdf"):

        raise HTTPException(

            status_code=400,

            detail="Please upload a PDF resume."
        )

    contents = await resume.read()

    # ==========================================
    # VALIDATE PDF SIZE
    # ==========================================
    #
    # 10 MB cap keeps a runaway upload from filling the
    # disk. Also catches an empty file early, before the
    # expensive LLM work starts.
    # ==========================================

    MAX_RESUME_BYTES = 10 * 1024 * 1024

    if len(contents) == 0:

        raise HTTPException(

            status_code=400,

            detail="The uploaded resume is empty."
        )

    if len(contents) > MAX_RESUME_BYTES:

        raise HTTPException(

            status_code=400,

            detail=(
                "Resume is too large. "
                "Maximum size is 10 MB."
            )
        )

    # Basic PDF magic-number check.

    if not contents.startswith(b"%PDF"):

        raise HTTPException(

            status_code=400,

            detail=(
                "That file does not look like a "
                "valid PDF."
            )
        )

    # ==========================================
    # SAVE RESUME (UNIQUE NAME)
    # ==========================================
    #
    # Named after the user and a timestamp so two uploads
    # never overwrite each other, and a crafted filename
    # can never escape the uploads folder.
    # ==========================================

    upload_dir = "uploads"

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    safe_stem = re.sub(

        r"[^A-Za-z0-9._-]+",

        "_",

        os.path.splitext(filename)[0]
    )[:60] or "resume"

    resume_path = os.path.join(

        upload_dir,

        f"{safe_stem}_{user_id[:16]}"
        f"_{int(__import__('time').time())}.pdf"
    )

    with open(
        resume_path,
        "wb"
    ) as file:

        file.write(contents)

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


# ==========================================
# AGENT 5 - LEARNING ROADMAP & COURSES
# ==========================================
#
# These endpoints are ADDITIVE. No existing endpoint was
# changed, so the /preferences and /career-twin workflow
# keeps working exactly as before.
#
# Retrieval is kept separate from the LLM:
#   - The course search service returns REAL resources.
#   - The roadmap structure is built from the REAL skill
#     gaps already stored in the Career Twin.
#   - Nothing is invented when a provider is unavailable.
# ==========================================


# -----------------------------------------
# REQUEST MODELS
# -----------------------------------------

class ProgressRequest(BaseModel):

    skill: str

    resource_url: str = ""

    resource_title: str = ""

    platform: str = ""

    status: str = "not_started"

    level: str = "beginner"


class StatusRequest(BaseModel):

    skill: str

    resource_url: str

    status: str


class SkillLearnedRequest(BaseModel):

    skill: str

    method: str = "confirmation"

    assessment_score: Optional[float] = None


class RoadmapRequest(BaseModel):

    include_resources: bool = True

    max_resources_per_skill: int = 2


# -----------------------------------------
# 1. LEARNING RESOURCES FOR ONE SKILL
# -----------------------------------------

@app.get("/learning-resources")
def get_learning_resources(

    skill: str = Query(
        ...,
        min_length=2
    ),

    level: str = "beginner",

    max_results: int = 2
):
    """Return real learning resources for a skill.

    YouTube results come from the live API. If the API is
    unavailable or blocked, the endpoint still returns the
    platform search links instead of failing.
    """

    try:

        resources = gather_resources(

            skill=skill,

            level=level,

            max_youtube=max_results
        )

    except Exception as exc:

        # ------------------------------------------------
        # Retrieval must never break the endpoint.
        # Platform links below still work.
        # ------------------------------------------------

        print(
            "[Learning Resources] Retrieval failed:",
            exc
        )

        resources = {

            "skill": skill,

            "level": level,

            "youtube_resources": [],

            "documentation": None,

            "platform_links":
                platform_search_links(skill)
        }

    resources["youtube_available"] = bool(
        resources.get("youtube_resources")
    )

    return resources


# -----------------------------------------
# 2. YOUTUBE ONLY (LIVE SEARCH)
# -----------------------------------------

@app.get("/learning-resources/youtube")
def get_youtube_resources(

    skill: str = Query(
        ...,
        min_length=2
    ),

    level: str = "beginner",

    max_results: int = 3
):
    """Return ranked, live YouTube results for a skill."""

    try:

        courses = get_ranked_courses(

            skill=skill,

            level=level,

            max_results=max_results
        )

    except Exception as exc:

        print(
            "[Learning Resources] YouTube failed:",
            exc
        )

        courses = []

    return {

        "skill": skill,

        "level": level,

        "count": len(courses),

        "youtube_resources": courses,

        "youtube_available": bool(courses)
    }


# -----------------------------------------
# 3. GENERATE / REFRESH ROADMAP
# -----------------------------------------

@app.post("/learning-roadmap")
def create_learning_roadmap(

    request: RoadmapRequest,

    current_user: dict = Depends(
        get_current_user
    )
):
    """Generate a phased roadmap from the user's REAL
    skill gaps, with retrieved courses per skill.
    """

    result = generate_learning_roadmap(

        user_id=_user_id_from_token(
            current_user
        ),

        include_resources=(
            request.include_resources
        ),

        max_resources_per_skill=(
            request.max_resources_per_skill
        )
    )

    if not result.get("success"):

        raise HTTPException(

            status_code=404,

            detail=result.get(
                "message",
                "Roadmap could not be generated."
            )
        )

    return result


# -----------------------------------------
# 4. ROADMAP WITHOUT RESOURCES (FAST)
# -----------------------------------------

@app.get("/learning-roadmap")
def get_learning_roadmap(

    include_resources: bool = False,

    current_user: dict = Depends(
        get_current_user
    )
):
    """Fetch the roadmap for the logged-in user.

    Set include_resources=true to also retrieve live
    courses (slower - it calls the course search APIs).
    """

    result = generate_learning_roadmap(

        user_id=_user_id_from_token(
            current_user
        ),

        include_resources=include_resources
    )

    if not result.get("success"):

        raise HTTPException(

            status_code=404,

            detail=result.get(
                "message",
                "Roadmap could not be generated."
            )
        )

    return result


# -----------------------------------------
# 5. SAVE A SELECTED RESOURCE
# -----------------------------------------

@app.post("/learning-progress")
def save_learning_progress(

    request: ProgressRequest,

    current_user: dict = Depends(
        get_current_user
    )
):
    """Save a resource the learner selected."""

    record = learning_progress.save_resource(

        user_id=_user_id_from_token(
            current_user
        ),

        skill=request.skill,

        resource_url=request.resource_url,

        resource_title=request.resource_title,

        platform=request.platform,

        status=request.status,

        level=request.level
    )

    if not record:

        raise HTTPException(

            status_code=400,

            detail=(
                "skill and resource_url "
                "are required."
            )
        )

    return {

        "message": "Progress saved.",

        "record": record
    }


# -----------------------------------------
# 6. GET PROGRESS
# -----------------------------------------

@app.get("/learning-progress")
def get_learning_progress(

    skill: str = None,

    current_user: dict = Depends(
        get_current_user
    )
):
    """Get saved learning progress for the logged-in user."""

    user_id = _user_id_from_token(
        current_user
    )

    if skill:

        records = (
            learning_progress.get_skill_progress(
                user_id,
                skill
            )
        )

    else:

        records = learning_progress.get_progress(
            user_id
        )

    verified = (
        learning_progress.get_verified_skills(
            user_id
        )
    )

    return {

        "user_id": user_id,

        "count": len(records),

        "verified_skills": verified,

        "records": records
    }


# -----------------------------------------
# 7. UPDATE STATUS
# -----------------------------------------

@app.post("/learning-progress/status")
def update_learning_status(

    request: StatusRequest,

    current_user: dict = Depends(
        get_current_user
    )
):
    """Update the status of a saved resource."""

    record = learning_progress.update_status(

        user_id=_user_id_from_token(
            current_user
        ),

        skill=request.skill,

        resource_url=request.resource_url,

        status=request.status
    )

    if not record:

        raise HTTPException(

            status_code=400,

            detail=(
                "Invalid status. Use not_started, "
                "in_progress or completed."
            )
        )

    return {

        "message": "Status updated.",

        "record": record
    }


# -----------------------------------------
# 8. MARK SKILL LEARNED (VERIFIED)
# -----------------------------------------

@app.post("/learning-progress/complete")
def complete_skill(

    request: SkillLearnedRequest,

    current_user: dict = Depends(
        get_current_user
    )
):
    """Mark a skill as learned.

    A skill is only marked as learned after the user
    CONFIRMS it or PASSES a short assessment. Watching a
    video alone is never treated as proficiency.

    Passing recalculates readiness and job matches using
    the existing Skill Gap Agent - the same workflow the
    /career-twin endpoint uses.
    """

    user_id = _user_id_from_token(
        current_user
    )

    outcome = learning_progress.mark_skill_learned(

        user_id=user_id,

        skill=request.skill,

        method=request.method,

        assessment_score=(
            request.assessment_score
        )
    )

    if not outcome.get("success"):

        raise HTTPException(

            status_code=400,

            detail=outcome.get(
                "message",
                "Skill could not be marked as learned."
            )
        )

    # ----------------------------------------------
    # RECALCULATE CAREER TWIN
    #
    # Reuses the existing skill gap workflow so the
    # readiness score, gaps and job matches stay
    # consistent with /career-twin.
    # ----------------------------------------------

    recalculation = None

    try:

        recalculation = recalculate_after_learning(

            user_id=user_id,

            learned_skill=request.skill
        )

    except Exception as exc:

        # Progress is still saved. Recalculation is an
        # enhancement, not a requirement.

        print(
            "[Learning] Recalculation skipped:",
            exc
        )

        recalculation = {

            "recalculated": False,

            "message": (
                "Progress saved. Readiness will refresh "
                "when the Career Twin is regenerated."
            )
        }

    return {

        "message": outcome.get(
            "message",
            "Skill marked as learned."
        ),

        "verified": outcome.get("verified", False),

        "skill": request.skill,

        "recalculation": recalculation
    }


# -----------------------------------------
# RECALCULATION HELPER
# -----------------------------------------

def recalculate_after_learning(

    user_id: str,

    learned_skill: str
):
    """Recompute the Career Twin after a skill is learned.

    Adds the newly learned skill to the twin's skills, then
    reruns the Skill Gap Agent so readiness_score,
    prioritized_gaps and market alignment all refresh.
    """

    career_twin = career_twins_collection.find_one(
        {
            "user_id": str(user_id).strip()
        }
    )

    if not career_twin:

        return {

            "recalculated": False,

            "message": (
                "No Career Twin to recalculate yet."
            )
        }

    career_twin.pop("_id", None)

    # ----------------------------------------------
    # 1. Add the learned skill to the twin's skills.
    #
    # Verified learning becomes part of the profile, so
    # readiness improves only when the user actually
    # demonstrated the skill.
    # ----------------------------------------------

    existing_skills = list(
        career_twin.get("skills") or []
    )

    already_present = any(
        str(skill).strip().lower()
        == learned_skill.strip().lower()
        for skill in existing_skills
    )

    if not already_present:

        existing_skills.append(learned_skill)

    # ----------------------------------------------
    # 2. Rerun the Skill Gap Agent.
    # ----------------------------------------------

    from digital_twin import (
        normalize_skills,
        normalize_roles
    )

    from agents.skill_gap_agent import (
        run_skill_gap_workflow
    )

    from scoring_utils import (
        compute_market_alignment_details
    )

    from models import Preferences as PreferencesModel

    profile = (
        career_twin.get("profile") or {}
    )

    target_role = str(
        profile.get("target_role", "")
    ).strip() or "Software Engineer"

    preference_data = (
        career_twin.get("preferences") or {}
    )

    preferences = PreferencesModel(
        **preference_data
    )

    # Reuse the role knowledge already cached for this
    # twin - never re-research during a recalculation.

    import role_knowledge_manager

    role_knowledge = (
        role_knowledge_manager
        .get_or_create_role_knowledge(

            target_role,

            getattr(
                preferences,
                "experience_level",
                None
            ) or "Entry Level",

            getattr(
                preferences,
                "preferred_industry",
                None
            ) or "Artificial Intelligence"
        )
    )

    normalized_skills = normalize_skills(
        existing_skills
    )

    skill_gap_result = run_skill_gap_workflow(

        current_skills=normalized_skills,

        target_role=target_role,

        required_skills=(
            role_knowledge.required_skills
        ),

        preferred_skills=(
            role_knowledge.preferred_skills
        ),

        tools=role_knowledge.tools,

        cloud=role_knowledge.cloud,

        profile={

            "education":
                career_twin.get("education", []),

            "projects":
                career_twin.get("projects", []),

            "experience":
                career_twin.get("experience", []),

            "experience_level":
                getattr(
                    preferences,
                    "experience_level",
                    None
                ) or "",

            "role_experience_level":
                getattr(
                    role_knowledge,
                    "experience_level",
                    None
                )
        }
    )

    career_state_data = (
        skill_gap_result.get(
            "career_state",
            {}
        )
    )

    jobs = (
        career_twin.get("job_opportunities") or []
    )

    market_alignment_details = (
        compute_market_alignment_details(

            readiness_score=(
                career_state_data.get(
                    "readiness_score",
                    0.0
                )
            ),

            target_role=target_role,

            experience_level=(
                getattr(
                    preferences,
                    "experience_level",
                    None
                ) or ""
            ),

            preferences=(
                dict(
                    preference_data,
                    target_role=target_role
                )
            ),

            jobs=jobs,

            role_experience_level=(
                getattr(
                    role_knowledge,
                    "experience_level",
                    None
                )
            ),

            current_skills=normalized_skills
        )
    )

    # ----------------------------------------------
    # 3. Persist the refreshed twin.
    # ----------------------------------------------

    updated_state = dict(career_state_data)

    updated_state["market_alignment"] = (
        market_alignment_details["score"]
    )

    updated_state["market_alignment_breakdown"] = (
        market_alignment_details["breakdown"]
    )

    updated_state["market_alignment_explanation"] = (
        market_alignment_details["explanation"]
    )

    updated_twin = dict(career_twin)

    updated_twin["skills"] = normalized_skills

    updated_twin["career_state"] = updated_state

    updated_twin["learning_history"] = list(
        dict.fromkeys(
            list(
                career_twin.get(
                    "learning_history"
                ) or []
            )
            + [learned_skill]
        )
    )

    career_twins_collection.update_one(

        {
            "user_id": str(user_id).strip()
        },

        {
            "$set": updated_twin
        },

        upsert=True
    )

    print(
        "[Learning] Career Twin recalculated for",
        user_id
    )

    return {

        "recalculated": True,

        "readiness_score":
            updated_state.get(
                "readiness_score",
                0.0
            ),

        "market_alignment":
            updated_state.get(
                "market_alignment",
                0.0
            ),

        "total_required":
            updated_state.get(
                "total_required",
                0
            ),

        "total_matched":
            updated_state.get(
                "total_matched",
                0
            ),

        "total_missing":
            updated_state.get(
                "total_missing",
                0
            ),

        "remaining_gaps": [
            gap.get("skill")
            for gap in (
                updated_state.get(
                    "prioritized_gaps"
                ) or []
            )
        ],

        "message": (
            "Readiness and job matches recalculated."
        )
    }


# -----------------------------------------
# 9. PLATFORM SEARCH LINKS (STANDALONE)
# -----------------------------------------

@app.get("/learning-platforms")
def get_platform_links(

    skill: str = Query(
        ...,
        min_length=2
    )
):
    """Return search links for Coursera, edX, Udemy and
    official documentation for a skill.
    """

    return {

        "skill": skill,

        "platform_links":
            platform_search_links(skill),

        "documentation":
            (gather_resources(skill).get(
                "documentation"
            ))
    }