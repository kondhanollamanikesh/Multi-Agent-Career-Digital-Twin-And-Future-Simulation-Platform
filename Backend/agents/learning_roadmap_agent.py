# ============================================================
# Career Digital Twin - Agent 5
# Learning Roadmap & Course Recommendation Agent
# ============================================================
#
# Reads the REAL skill gaps already computed by the Career
# Twin (career_state.prioritized_gaps) and turns them into
# a phased learning roadmap with projects, milestones and
# retrieved resources.
#
# KEY DESIGN DECISION - Retrieval is separate from the LLM:
#   The course search service retrieves real resources.
#   The roadmap structure is built deterministically from
#   the actual skill gaps.
#   The LLM is used ONLY to write explanations and practice
#   tasks - never to invent course titles, URLs or durations.
#
# IMPORTANT:
# This agent is deliberately written as a NORMAL PYTHON
# SERVICE with no LangGraph dependency. It can be wrapped as
# a LangGraph node later without changing this logic.
# ============================================================

import math
import re
from typing import Any, Dict, List, Optional

from database import career_twins_collection

from learning_progress import get_progress

from agents.resource_service import (
    gather_resources,
    official_documentation_link,
    platform_search_links
)


# ============================================================
# 1. CONFIGURATION
# ============================================================

# How many skills per learning phase. Keeps a phase from
# becoming an unmanageable list of 12 skills.

MAX_SKILLS_PER_PHASE = 4

# Suggested hours per skill, by priority. Used only to give
# the learner an ESTIMATE, clearly labelled as suggested.

HOURS_PER_SKILL = {

    "High": 6,

    "Medium": 4,

    "Low": 2
}

HOURS_PER_WEEK = 8


# ============================================================
# 2. PRACTICAL TASKS BY SKILL PATTERN
# ============================================================
#
# Deterministic practice tasks - no LLM required. Matched
# on skill keywords so a new skill still gets a sensible
# task through the fallback below.
# ============================================================

PRACTICAL_TASKS = [

    (
        ("linux", "bash", "shell"),
        "Set up a Linux environment, create users, manage "
        "permissions and run a service using the command "
        "line. Document every command you used."
    ),

    (
        ("docker", "container"),
        "Containerise an existing project with a Dockerfile, "
        "add a docker-compose file and deploy it locally."
    ),

    (
        ("kubernetes",),
        "Deploy a containerised app to a local Kubernetes "
        "cluster and expose it with a Service."
    ),

    (
        ("sql", "postgres", "mysql", "database", "mongodb", "mongo"),
        "Design a schema for a small application and write "
        "the queries needed to read and report on the data."
    ),

    (
        ("react", "frontend", "next.js", "vue"),
        "Build a small front end that fetches data from an "
        "API and handles loading, error and empty states."
    ),

    (
        ("fastapi", "flask", "django", "backend", "rest", "api"),
        "Build and document a REST API with validation, "
        "error handling and automated tests."
    ),

    (
        ("python",),
        "Write a command line tool that reads a file, "
        "processes it and outputs a summary report."
    ),

    (
        ("machine learning", "ml", "deep learning", "neural"),
        "Train a model on a public dataset, evaluate it "
        "with the right metrics and write up your findings."
    ),

    (
        ("llm", "langchain", "langgraph", "rag", "genai",
         "generative"),
        "Build a small RAG or agent application and compare "
        "the quality of at least two different approaches."
    ),

    (
        ("prompt",),
        "Write and test a set of prompts for a task, then "
        "measure how reliably each version performs."
    ),

    (
        ("git", "github", "version control"),
        "Contribute to a repository using branches and pull "
        "requests, and resolve a merge conflict."
    ),

    (
        ("aws", "azure", "gcp", "cloud"),
        "Deploy a small application to a cloud provider and "
        "set up environment variables and monitoring."
    ),

    (
        ("data structures", "algorithms", "dsa",
         "big o", "time complexity"),
        "Solve 15-20 problems on arrays, hash maps, trees "
        "and graphs, and analyse the time and space "
        "complexity of each solution."
    ),

    (
        ("unit test", "testing framework", "pytest",
         "jest", "test automation"),
        "Add automated tests to an existing project and "
        "wire them into a test runner so they run on every "
        "change."
    ),

    (
        ("http", "rest api", "rest apis", "rest",
         "api design"),
        "Build a REST API and document its status codes, "
        "authentication flow and error responses."
    ),

    (
        ("pandas", "numpy", "data analysis",
         "data science", "data analytics"),
        "Clean and analyse a public dataset, then present "
        "the three most interesting findings."
    ),

    (
        ("javascript", "typescript"),
        "Build an interactive page using modern language "
        "features and add type checking where relevant."
    )
]

DEFAULT_PRACTICAL_TASK = (
    "Build one small end to end project that uses this "
    "skill, then write a short summary of what you learned."
)


def get_practical_task(
    skill: str,
    learning_suggestion: str = ""
) -> str:

    skill_lower = str(skill or "").lower()

    for keywords, task in PRACTICAL_TASKS:

        for keyword in keywords:

            # Word-boundary match so "api" does not fire
            # inside "capabilities" and "ml" does not fire
            # inside "html". The trailing "s?" keeps plural
            # forms like "unit tests" and "testing
            # frameworks" matching their singular keyword.

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(keyword)
                + r"s?(?![a-z0-9])"
            )

            if re.search(pattern, skill_lower):

                return task

    # Fall back to the suggestion the Skill Gap Agent
    # already produced, so we never throw away real input.

    if learning_suggestion:

        return str(learning_suggestion).strip()

    return DEFAULT_PRACTICAL_TASK


# ============================================================
# 3. LOAD CAREER TWIN
# ============================================================

def load_career_twin(
    user_id: Any
) -> Optional[Dict[str, Any]]:
    """Load the saved Career Twin for a user."""

    user_id = str(user_id or "").strip()

    if not user_id:

        print(
            "[Roadmap Agent] No user_id supplied."
        )

        return None

    document = career_twins_collection.find_one(
        {
            "user_id": user_id
        }
    )

    if not document:

        print(
            "[Roadmap Agent] No Career Twin found for",
            user_id
        )

        return None

    document.pop("_id", None)

    return document


# ============================================================
# 4. EXTRACT SKILL GAPS
# ============================================================

def extract_skill_gaps(
    career_twin: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Return real prioritized gaps from the Career Twin.

    Falls back to computing the difference between required
    and current skills when prioritized_gaps is empty, so an
    older twin still produces a roadmap.
    """

    if not career_twin:
        return []

    career_state = (
        career_twin.get("career_state") or {}
    )

    prioritized = (
        career_state.get("prioritized_gaps") or []
    )

    # Keep only gaps that name a real skill.
    gaps = []

    for gap in prioritized:

        if not isinstance(gap, dict):
            continue

        skill = str(
            gap.get("skill", "")
        ).strip()

        if not skill:
            continue

        priority = gap.get("priority", "Medium")

        if priority not in {"High", "Medium", "Low"}:

            priority = "Medium"

        gaps.append({

            "skill": skill,

            "priority": priority,

            "priority_score": gap.get(
                "priority_score"
            ),

            "importance": gap.get(
                "importance",
                "Required for the target role"
            ),

            "learning_suggestion": gap.get(
                "learning_suggestion",
                ""
            )
        })

    if gaps:

        print(
            "[Roadmap Agent] Using",
            len(gaps),
            "prioritized gaps from the Career Twin."
        )

        return gaps

    # --------------------------------------------------------
    # Fallback for twins saved without prioritized_gaps.
    # --------------------------------------------------------

    print(
        "[Roadmap Agent] No prioritized gaps stored - "
        "deriving gaps from required vs current skills."
    )

    return derive_gaps_from_skills(career_twin)


def derive_gaps_from_skills(
    career_twin: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Fallback gap derivation using stored role knowledge."""

    current_skills = [
        str(skill).strip().lower()
        for skill in (
            career_twin.get("skills") or []
        )
        if str(skill).strip()
    ]

    profile = (
        career_twin.get("profile") or {}
    )

    role = str(
        profile.get("target_role", "")
    ).strip()

    required = []

    seen = set()

    # Reuse the cached role knowledge the twin already
    # depended on, so requirements stay consistent.

    try:

        from database import role_knowledge_collection

        documents = role_knowledge_collection.find(
            {
                "role": role
            }
        )

        for document in documents:

            for skill in (
                document.get("required_skills") or []
            ):

                key = str(skill).strip().lower()

                if key and key not in seen:

                    seen.add(key)

                    required.append(str(skill).strip())

    except Exception as exc:

        print(
            "[Roadmap Agent] Role knowledge lookup "
            "failed:",
            exc
        )

    gaps = []

    for skill in required:

        if str(skill).strip().lower() not in current_skills:

            gaps.append({

                "skill": str(skill).strip(),

                "priority": "Medium",

                "priority_score": 2,

                "importance":
                    "Required for the target role",

                "learning_suggestion": (
                    f"Build practical projects using {skill}"
                )
            })

    print(
        "[Roadmap Agent] Derived",
        len(gaps),
        "gaps from role requirements."
    )

    return gaps


# ============================================================
# 5. GROUP GAPS INTO PHASES
# ============================================================
#
# Phases follow the REAL priority order produced by the
# Skill Gap Agent, so the learner closes the most important
# gaps first.
# ============================================================

def group_into_phases(
    gaps: List[Dict[str, Any]]
) -> List[List[Dict[str, Any]]]:
    """Split sorted gaps into phase buckets."""

    if not gaps:
        return []

    priority_order = {"High": 0, "Medium": 1, "Low": 2}

    ordered = sorted(
        gaps,

        key=lambda item: (
            priority_order.get(
                item.get("priority", "Medium"),
                2
            ),

            -(item.get("priority_score") or 0),

            str(item.get("skill", ""))
        )
    )

    phases = []

    current: List[Dict[str, Any]] = []

    for gap in ordered:

        current.append(gap)

        # Start a new phase once a phase is full AND we
        # are about to move into a lower priority band.

        if len(current) >= MAX_SKILLS_PER_PHASE:

            phases.append(current)

            current = []

    if current:

        phases.append(current)

    return phases


# ============================================================
# 6. ESTIMATE DURATION
# ============================================================

def estimate_duration_hours(
    skills: List[Dict[str, Any]]
) -> int:

    total = 0

    for skill in skills:

        priority = skill.get("priority", "Medium")

        total += HOURS_PER_SKILL.get(priority, 4)

    return total


def format_duration(hours: int) -> str:

    if hours <= 0:
        return "Suggested duration: not set"

    weeks = max(
        1,
        math.ceil(hours / HOURS_PER_WEEK)
    )

    return f"Suggested duration: ~{weeks} week" + (
        "s" if weeks != 1 else ""
    )


# ============================================================
# 7. PHASE TITLES
# ============================================================

def phase_title(
    phase_index: int,
    skills: List[Dict[str, Any]]
) -> str:
    """Give each phase a clear, deterministic title.

    The title reflects the REAL priority band of the skills
    in the phase - it never claims "High Priority" when the
    skills are actually Medium or Low.
    """

    number = phase_index + 1

    priority = overall_priority(skills)

    if priority == "High":

        return f"Phase {number} - Priority Foundations"

    if priority == "Medium":

        return f"Phase {number} - Core Skills"

    return f"Phase {number} - Optional Enhancements"


def overall_priority(
    skills: List[Dict[str, Any]]
) -> str:
    """The highest priority present in a phase."""

    priorities = {
        str(skill.get("priority", "Medium"))
        for skill in skills
    }

    for candidate in ("High", "Medium", "Low"):

        if candidate in priorities:
            return candidate

    return "Medium"


# ============================================================
# 8. BUILD ROADMAP (NO LLM, DETERMINISTIC)
# ============================================================

def build_roadmap_structure(
    career_twin: Dict[str, Any],
    include_resources: bool = False,
    max_resources_per_skill: int = 2
) -> Dict[str, Any]:
    """Build the phased roadmap from real skill gaps."""

    profile = (
        career_twin.get("profile") or {}
    )

    target_role = str(
        profile.get("target_role", "")
    ).strip() or "Software Engineer"

    experience_level = str(
        profile.get("experience_level", "")
    ).strip() or "Entry Level"

    gaps = extract_skill_gaps(career_twin)

    # Existing progress so the roadmap shows real status.

    progress_records = get_progress(
        career_twin.get("user_id")
    )

    progress_by_skill: Dict[str, List[Dict]] = {}

    for record in progress_records:

        if not isinstance(record, dict):
            continue

        skill = str(
            record.get("skill", "")
        ).strip()

        if skill:

            progress_by_skill.setdefault(
                skill,
                []
            ).append(record)

    phases_raw = group_into_phases(gaps)

    phases = []

    for index, phase_skills in enumerate(phases_raw):

        hours = estimate_duration_hours(
            phase_skills
        )

        skill_entries = []

        for gap in phase_skills:

            skill = gap["skill"]

            # ------------------------------------------
            # Resources
            # ------------------------------------------

            if include_resources:

                resources = gather_resources(
                    skill=skill,

                    level=(
                        "beginner"
                        if experience_level
                        in ("Entry Level", "")
                        else "intermediate"
                    ),

                    max_youtube=max_resources_per_skill
                )

            else:

                resources = {

                    "skill": skill,

                    "youtube_resources": [],

                    "documentation":
                        official_documentation_link(
                            skill
                        ),

                    # Platform search links are built
                    # locally from templates, so they are
                    # free on the fast path too.

                    "platform_links":
                        platform_search_links(
                            skill
                        )
                }

            skill_records = progress_by_skill.get(
                skill,
                []
            )

            verified = any(
                record.get("skill_verified")
                for record in skill_records
            )

            completed = any(
                record.get("status") == "completed"
                for record in skill_records
            )

            started = any(
                record.get("status") == "in_progress"
                for record in skill_records
            )

            if verified or completed:

                status = "completed"

            elif started:

                status = "in_progress"

            else:

                status = "not_started"

            skill_entries.append({

                "skill": skill,

                "priority": gap.get(
                    "priority",
                    "Medium"
                ),

                "importance": gap.get(
                    "importance",
                    "Required for the target role"
                ),

                "learning_suggestion": gap.get(
                    "learning_suggestion",
                    ""
                ),

                "practical_task": get_practical_task(
                    skill,
                    gap.get(
                        "learning_suggestion",
                        ""
                    )
                ),

                "suggested_hours":
                    HOURS_PER_SKILL.get(
                        gap.get("priority", "Medium"),
                        4
                    ),

                "status": status,

                "skill_verified": verified,

                "resources": resources,

                "progress_records": skill_records
            })

        phases.append({

            "phase_number": index + 1,

            "title": phase_title(
                index,
                phase_skills
            ),

            "priority": overall_priority(
                phase_skills
            ),

            "suggested_duration": format_duration(
                hours
            ),

            "estimated_hours": hours,

            "skills": skill_entries,

            "status": (
                "completed"
                if all(
                    entry["status"] == "completed"
                    for entry in skill_entries
                )
                else "in_progress"
                if any(
                    entry["status"] != "not_started"
                    for entry in skill_entries
                )
                else "not_started"
            )
        })

    roadmap = {

        "target_role": target_role,

        "experience_level": experience_level,

        "total_phases": len(phases),

        "total_skills": len(gaps),

        "phases": phases,

        "summary": build_summary(
            target_role,
            phases,
            gaps
        )
    }

    print(
        "[Roadmap Agent] Roadmap built -",
        len(phases),
        "phases,",
        len(gaps),
        "skills."
    )

    return roadmap


# ============================================================
# 9. SUMMARY
# ============================================================

def build_summary(
    target_role: str,
    phases: List[Dict[str, Any]],
    gaps: List[Dict[str, Any]]
) -> Dict[str, Any]:

    total_hours = sum(
        phase.get("estimated_hours", 0)
        for phase in phases
    )

    high = sum(
        1 for gap in gaps
        if gap.get("priority") == "High"
    )

    medium = sum(
        1 for gap in gaps
        if gap.get("priority") == "Medium"
    )

    low = sum(
        1 for gap in gaps
        if gap.get("priority") == "Low"
    )

    completed = sum(
        1
        for phase in phases
        for skill in phase.get("skills", [])
        if skill.get("status") == "completed"
    )

    return {

        "target_role": target_role,

        "total_phases": len(phases),

        "total_skills": len(gaps),

        "high_priority": high,

        "medium_priority": medium,

        "low_priority": low,

        "completed_skills": completed,

        "total_estimated_hours": total_hours,

        "estimated_weeks": max(
            1,
            math.ceil(total_hours / HOURS_PER_WEEK)
        ) if total_hours else 0,

        "progress_percent": (
            round(
                (completed / len(gaps)) * 100,
                1
            )
            if gaps
            else 0.0
        )
    }


# ============================================================
# 10. PUBLIC API
# ============================================================

def generate_learning_roadmap(
    user_id: Any,
    include_resources: bool = True,
    max_resources_per_skill: int = 2
) -> Dict[str, Any]:
    """Generate (or refresh) the roadmap for a user."""

    print(
        "\n=========================================="
    )

    print(
        "AGENT 5 - LEARNING ROADMAP"
    )

    print(
        "=========================================="
    )

    career_twin = load_career_twin(user_id)

    if not career_twin:

        return {

            "success": False,

            "message": (
                "No Career Twin found for this user. "
                "Generate your Career Twin first."
            ),

            "roadmap": None
        }

    roadmap = build_roadmap_structure(

        career_twin,

        include_resources=include_resources,

        max_resources_per_skill=max_resources_per_skill
    )

    return {

        "success": True,

        "user_id": str(user_id).strip(),

        "message": "Learning roadmap generated.",

        "roadmap": roadmap
    }
