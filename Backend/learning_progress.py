# ============================================================
# Career Digital Twin - Agent 5
# Learning Progress Store
# ============================================================
#
# Stores selected resources and per-skill progress in the
# MongoDB "learning_progress" collection.
#
# Document shape:
# {
#   "user_id": "1999",
#   "skill": "Linux",
#   "resource_url": "verified-resource-url",
#   "resource_title": "...",
#   "platform": "YouTube",
#   "status": "in_progress",   <- not_started |
#                                 in_progress |
#                                 completed
#   "selected_at": "...",
#   "started_at": null,
#   "completed_at": null,
#   "assessment_score": null
# }
#
# IMPORTANT - PROFICIENCY vs COMPLETION:
# Marking a resource as completed does NOT mean the skill
# is proficient. "resource_completed" and "skill_verified"
# are deliberately SEPARATE fields. Watching a video is not
# proof of proficiency.
# ============================================================

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from database import learning_progress_collection


# ============================================================
# 1. STATUSES
# ============================================================

VALID_STATUSES = {
    "not_started",
    "in_progress",
    "completed"
}


# ============================================================
# 2. HELPERS
# ============================================================

def utc_now() -> str:

    return datetime.now(
        timezone.utc
    ).isoformat()


def _clean_user_id(user_id: Any) -> str:

    return str(user_id or "").strip()


def _clean_skill(skill: Any) -> str:

    return str(skill or "").strip()


def _serialize(document: Optional[Dict[str, Any]]):
    """Convert a Mongo document to a JSON-safe dict."""

    if not document:
        return None

    document = dict(document)

    document.pop("_id", None)

    return document


# ============================================================
# 3. SAVE / SELECT A RESOURCE
# ============================================================
#
# Upserts on (user_id, skill, resource_url) so re-selecting
# the same resource never creates a duplicate record.
# ============================================================

def save_resource(
    user_id: Any,
    skill: str,
    resource_url: str,
    resource_title: str = "",
    platform: str = "",
    status: str = "not_started",
    level: str = "beginner"
) -> Optional[Dict[str, Any]]:

    user_id = _clean_user_id(user_id)

    skill = _clean_skill(skill)

    resource_url = str(resource_url or "").strip()

    if not user_id or not skill or not resource_url:

        print(
            "[Learning Progress] Missing user_id, skill "
            "or resource_url - nothing saved."
        )

        return None

    if status not in VALID_STATUSES:
        status = "not_started"

    now = utc_now()

    existing = learning_progress_collection.find_one(
        {

            "user_id": user_id,

            "skill": skill,

            "resource_url": resource_url
        }
    )

    set_data = {

        "resource_title": resource_title,

        "platform": platform,

        "level": level,

        "status": status,

        "updated_at": now,

        # Proficiency stays separate from completion.
        "skill_verified": (
            existing.get("skill_verified", False)
            if existing
            else False
        ),

        "assessment_score": (
            existing.get("assessment_score")
            if existing
            else None
        )
    }

    if existing:

        set_data["status"] = (
            existing.get("status", status)
        )

        set_data["selected_at"] = (
            existing.get("selected_at", now)
        )

        set_data["started_at"] = (
            existing.get("started_at")
        )

        set_data["completed_at"] = (
            existing.get("completed_at")
        )

    else:

        set_data["selected_at"] = now

        set_data["started_at"] = (
            now if status == "in_progress" else None
        )

        set_data["completed_at"] = (
            now if status == "completed" else None
        )

    result = (
        learning_progress_collection.update_one(
            {

                "user_id": user_id,

                "skill": skill,

                "resource_url": resource_url
            },

            {

                "$set": set_data
            },

            upsert=True
        )
    )

    print(
        "[Learning Progress] Saved",
        skill,
        "for user",
        user_id,
        "-",
        set_data["status"]
    )

    return _serialize(
        learning_progress_collection.find_one(
            {

                "user_id": user_id,

                "skill": skill,

                "resource_url": resource_url
            }
        )
    )


# ============================================================
# 4. UPDATE STATUS
# ============================================================

def update_status(
    user_id: Any,
    skill: str,
    resource_url: str,
    status: str
) -> Optional[Dict[str, Any]]:

    user_id = _clean_user_id(user_id)

    skill = _clean_skill(skill)

    resource_url = str(resource_url or "").strip()

    if status not in VALID_STATUSES:

        print(
            "[Learning Progress] Invalid status:",
            status
        )

        return None

    now = utc_now()

    set_data = {

        "status": status,

        "updated_at": now
    }

    if status == "in_progress":

        set_data["started_at"] = now

        set_data["completed_at"] = None

    elif status == "completed":

        set_data["completed_at"] = now

    else:

        set_data["started_at"] = None

        set_data["completed_at"] = None

    learning_progress_collection.update_one(

        {

            "user_id": user_id,

            "skill": skill,

            "resource_url": resource_url
        },

        {

            "$set": set_data
        },

        upsert=True
    )

    return _serialize(
        learning_progress_collection.find_one(
            {

                "user_id": user_id,

                "skill": skill,

                "resource_url": resource_url
            }
        )
    )


# ============================================================
# 5. GET PROGRESS FOR A USER
# ============================================================

def get_progress(
    user_id: Any
) -> List[Dict[str, Any]]:

    user_id = _clean_user_id(user_id)

    if not user_id:
        return []

    cursor = learning_progress_collection.find(
        {
            "user_id": user_id
        }
    )

    return [
        _serialize(document)
        for document in cursor
    ]


# ============================================================
# 6. GET PROGRESS FOR ONE SKILL
# ============================================================

def get_skill_progress(
    user_id: Any,
    skill: str
) -> List[Dict[str, Any]]:

    user_id = _clean_user_id(user_id)

    skill = _clean_skill(skill)

    if not user_id or not skill:
        return []

    cursor = learning_progress_collection.find(
        {

            "user_id": user_id,

            "skill": skill
        }
    )

    return [
        _serialize(document)
        for document in cursor
    ]


# ============================================================
# 7. SKILL LEARNED / VERIFIED
# ============================================================
#
# A skill is only considered LEARNED when the user has
# either:
#   - confirmed it (self attestation), or
#   - passed a short assessment (score >= threshold)
#
# Course completion alone is never treated as proficiency.
# ============================================================

ASSESSMENT_PASS_SCORE = 60


def mark_skill_learned(
    user_id: Any,
    skill: str,
    method: str = "confirmation",
    assessment_score: Optional[float] = None
) -> Dict[str, Any]:
    """Mark a skill as learned for a user.

    Returns a dict describing what happened.
    """

    user_id = _clean_user_id(user_id)

    skill = _clean_skill(skill)

    if not user_id or not skill:

        return {

            "success": False,

            "message": "user_id and skill are required."
        }

    now = utc_now()

    verified = False

    score_to_store = None

    method = str(method or "confirmation").strip().lower()

    # ----------------------------------------------
    # Assessment path
    # ----------------------------------------------

    if method == "assessment":

        if assessment_score is None:

            return {

                "success": False,

                "message": (
                    "assessment_score is required when "
                    "method is 'assessment'."
                )
            }

        try:

            score_to_store = float(
                assessment_score
            )

        except (TypeError, ValueError):

            return {

                "success": False,

                "message": "assessment_score must be a number."
            }

        verified = (
            score_to_store >= ASSESSMENT_PASS_SCORE
        )

        if not verified:

            return {

                "success": False,

                "verified": False,

                "assessment_score": score_to_store,

                "message": (
                    f"Assessment score {score_to_store} "
                    f"is below the pass mark of "
                    f"{ASSESSMENT_PASS_SCORE}. "
                    f"The skill was not marked as learned."
                )
            }

    else:

        # Self confirmation path.
        verified = True

    # ----------------------------------------------
    # Mark every resource for this skill completed and
    # record proficiency on the skill.
    # ----------------------------------------------

    learning_progress_collection.update_many(

        {

            "user_id": user_id,

            "skill": skill
        },

        {

            "$set": {

                "status": "completed",

                "completed_at": now,

                "updated_at": now,

                "skill_verified": verified,

                "assessment_score": score_to_store,

                "verification_method": method
            }
        }
    )

    # If the user never selected a resource, still record
    # the verified skill so the roadmap reflects it.

    existing_count = (
        learning_progress_collection.count_documents(
            {

                "user_id": user_id,

                "skill": skill
            }
        )
    )

    if existing_count == 0:

        learning_progress_collection.insert_one(
            {

                "user_id": user_id,

                "skill": skill,

                "resource_url": "",

                "resource_title": (
                    "Completed outside the platform"
                ),

                "platform": "Other",

                "status": "completed",

                "selected_at": now,

                "started_at": now,

                "completed_at": now,

                "skill_verified": verified,

                "assessment_score": score_to_store,

                "verification_method": method,

                "updated_at": now
            }
        )

    print(
        "[Learning Progress] Skill",
        skill,
        "marked learned for user",
        user_id,
        "- method:",
        method
    )

    return {

        "success": True,

        "verified": verified,

        "skill": skill,

        "method": method,

        "assessment_score": score_to_store,

        "message": (
            f"{skill} marked as learned."
        )
    }


# ============================================================
# 8. GET ALL VERIFIED SKILLS
# ============================================================

def get_verified_skills(
    user_id: Any
) -> List[str]:

    user_id = _clean_user_id(user_id)

    if not user_id:
        return []

    cursor = learning_progress_collection.find(

        {

            "user_id": user_id,

            "skill_verified": True
        },

        {

            "skill": 1,

            "_id": 0
        }
    )

    skills = []

    for document in cursor:

        skill = document.get("skill")

        if skill and skill not in skills:

            skills.append(skill)

    return skills


# ============================================================
# 9. DELETE A SAVED RESOURCE
# ============================================================

def delete_resource(
    user_id: Any,
    skill: str,
    resource_url: str
) -> bool:

    result = (
        learning_progress_collection.delete_one(
            {

                "user_id": _clean_user_id(user_id),

                "skill": _clean_skill(skill),

                "resource_url":
                    str(resource_url or "").strip()
            }
        )
    )

    return result.deleted_count > 0
