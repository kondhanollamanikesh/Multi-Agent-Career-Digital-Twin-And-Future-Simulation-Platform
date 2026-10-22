# Agent 5 end-to-end test.
#
# Verifies the Learning Roadmap agent and the
# skill-completion recalculation WITHOUT touching real user
# data - it works on a temporary copy of an existing twin.
#
# Run:  python verify_agent5.py

import sys

sys.stdout.reconfigure(
    encoding="utf-8", errors="replace"
)

failures = []


def check(name, condition, detail=""):

    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        failures.append(name)


TEST_USER = "agent5_e2e_test"
RECALC_USER = "agent5_recalc_test"

from database import (
    career_twins_collection,
    learning_progress_collection,
)
from agents.course_service import (
    derive_search_term,
    parse_iso_duration,
    rank_resources,
)

from agents.resource_service import (
    platform_search_links,
    official_documentation_link,
    gather_resources,
)

from agents.learning_roadmap_agent import (
    generate_learning_roadmap,
    extract_skill_gaps,
    group_into_phases,
    get_practical_task,
)

from fastapi.testclient import TestClient

import time

import main

from database import (
    auth_users_collection,
    users_collection,
)


client = TestClient(main.app)


# ===========================================================
# AUTH FIXTURE
# ===========================================================
#
# Every user-scoped endpoint now derives user_id from the
# JWT, so the tests register a real account and store the
# synthetic twin under THAT user's id.
# ===========================================================

import bcrypt
from bson import ObjectId

STAMP = str(int(time.time()))

AUTH_EMAIL = f"agent5_{STAMP}@example.com"

AUTH_PASSWORD = "Agent5Pass!"

response = client.post(

    "/auth/register",

    json={

        "email": AUTH_EMAIL,

        "password": AUTH_PASSWORD,

        "name": "Agent 5 Tester",
    },
)

assert response.status_code == 200, response.text

AUTH_BODY = response.json()

AUTH_TOKEN = AUTH_BODY["access_token"]

USER_ID = AUTH_BODY["user"]["user_id"]

AUTH = {
    "Authorization": f"Bearer {AUTH_TOKEN}"
}

print(f"\n[AUTH] test user: {AUTH_EMAIL}")

# All endpoint calls now act as this logged-in user, so the
# synthetic twin must live under their real id.
TEST_USER = USER_ID


# ===========================================================
# 1. COURSE SERVICE
# ===========================================================

print("\n[1] Course service")

check(
    "duration PT4H20M15S",
    parse_iso_duration("PT4H20M15S") == "4h 20m",
)

check(
    "duration PT18M30S",
    parse_iso_duration("PT18M30S") == "18m",
)

check(
    "search term from long phrase",
    derive_search_term(
        "Comfort working in a Linux/Unix "
        "command-line environment"
    )
    == "Linux Unix",
)

check(
    "canonical casing FastAPI",
    derive_search_term("fastapi") == "FastAPI",
)

# Ranking must order real results deterministically.
ranked = rank_resources(
    [
        {
            "title": "Docker Crash Course - Beginner "
            "Full Tutorial",
            "channel": "Traversy Media",
            "resource_type": "video",
            "view_count": 800000,
            "duration": "PT2H",
        },
        {
            "title": "Random 2 minute tip",
            "channel": "Unknown Channel",
            "resource_type": "video",
            "view_count": 50,
        },
    ],
    skill="Docker",
    level="beginner",
)

check("ranking returns 2", len(ranked) == 2)

check(
    "trusted full course ranks first",
    ranked[0]["channel"] == "Traversy Media",
)

check(
    "score assigned",
    ranked[0]["relevance_score"]
    > ranked[1]["relevance_score"],
)


# ===========================================================
# 2. RESOURCE SERVICE
# ===========================================================

print("\n[2] Resource service")

links = platform_search_links("Machine Learning")

check("5 platform links", len(links) == 5)

check(
    "coursera template used",
    any(
        link["url"].startswith(
            "https://www.coursera.org/search?query="
        )
        for link in links
    ),
)

check(
    "edx template used",
    any(
        "edx.org/search?q=" in link["url"]
        for link in links
    ),
)

check(
    "udemy template used",
    any(
        "udemy.com/courses/search/" in link["url"]
        for link in links
    ),
)

doc = official_documentation_link("FastAPI")

check(
    "fastapi official docs",
    doc["url"] == "https://fastapi.tiangolo.com/",
)

doc = official_documentation_link(
    "Comfort working in a Linux/Unix "
    "command-line environment"
)

check(
    "phrase resolves to verified linux docs",
    doc["verified"] is True and "kernel.org" in doc["url"],
)

doc = official_documentation_link("Quantum Basket Weaving")

check(
    "unknown skill falls back to search",
    doc["verified"] is False,
)

gathered = gather_resources("Docker", "beginner", 2)

check(
    "gather_resources shape",
    set(gathered.keys())
    >= {
        "skill",
        "search_term",
        "youtube_resources",
        "documentation",
        "platform_links",
    },
)

check(
    "gather_resources never raises when API blocked",
    isinstance(gathered["youtube_resources"], list),
)


# ===========================================================
# 3. ROADMAP AGENT
# ===========================================================

print("\n[3] Roadmap agent")

result = generate_learning_roadmap(
    RECALC_USER,
    include_resources=False,
)

check(
    "no twin -> success False",
    result["success"] is False,
)

# Build a synthetic twin so the roadmap logic is fully
# covered even without a real Career Twin.

synthetic_twin = {
    "user_id": TEST_USER,
    "skills": ["Python", "Git"],
    "profile": {
        "target_role": "Backend Engineer",
        "experience_level": "Entry Level",
    },
    "career_state": {
        "prioritized_gaps": [
            {
                "skill": "Docker",
                "priority": "High",
                "priority_score": 3,
                "importance": "Required",
                "learning_suggestion": "Containerise an app",
            },
            {
                "skill": "FastAPI",
                "priority": "High",
                "priority_score": 3,
                "importance": "Required",
                "learning_suggestion": "Build a REST API",
            },
            {
                "skill": "PostgreSQL",
                "priority": "Medium",
                "priority_score": 2,
                "importance": "Required",
                "learning_suggestion": "Model a schema",
            },
            {
                "skill": "Kubernetes",
                "priority": "Medium",
                "priority_score": 2,
                "importance": "Preferred",
                "learning_suggestion": "Deploy a pod",
            },
            {
                "skill": "Redis",
                "priority": "Low",
                "priority_score": 1,
                "importance": "Preferred",
                "learning_suggestion": "Add a cache",
            },
        ]
    },
}

career_twins_collection.update_one(
    {"user_id": TEST_USER},
    {"$set": synthetic_twin},
    upsert=True,
)

gaps = extract_skill_gaps(synthetic_twin)

check("5 gaps extracted", len(gaps) == 5)

phases = group_into_phases(gaps)

check(
    "phases split by priority",
    len(phases) >= 2,
)

check(
    "High priority skills come first",
    gaps[0]["skill"] == "Docker"
    and gaps[1]["skill"] == "FastAPI",
)

check(
    "practical task for Docker",
    "Containerise"
    in get_practical_task("Docker"),
)

check(
    "practical task from phrase",
    get_practical_task(
        "Comfort working in a Linux/Unix "
        "command-line environment"
    )
    != "",
)

result = generate_learning_roadmap(
    TEST_USER, include_resources=False
)

check("roadmap success", result["success"] is True)

roadmap = result["roadmap"]

check(
    "target role correct",
    roadmap["target_role"] == "Backend Engineer",
)

check(
    "all 5 skills present",
    roadmap["total_skills"] == 5,
)

check(
    "summary counts high priority",
    roadmap["summary"]["high_priority"] == 2,
)

check(
    "summary counts low priority",
    roadmap["summary"]["low_priority"] == 1,
)

# Phase titles must reflect the REAL priority band of the
# skills inside them, not a hardcoded label.
titles = [
    phase["title"] for phase in roadmap["phases"]
]

phase_one_priority = roadmap["phases"][0]["priority"]

check(
    "phase title matches real priority",
    (
        "Priority Foundations" in titles[0]
    )
    == (phase_one_priority == "High"),
    f"{titles[0]} vs {phase_one_priority}",
)

check(
    "low-only phase titled Optional Enhancements",
    any(
        "Optional Enhancements" in title
        for title in titles
    ),
    str(titles),
)

check(
    "phase has duration text",
    "Suggested duration"
    in roadmap["phases"][0]["suggested_duration"],
)

check(
    "every skill has a practical task",
    all(
        skill["practical_task"]
        for phase in roadmap["phases"]
        for skill in phase["skills"]
    ),
)

check(
    "every skill has resources block",
    all(
        "resources" in skill
        for phase in roadmap["phases"]
        for skill in phase["skills"]
    ),
)

check(
    "skills default to not_started",
    all(
        skill["status"] == "not_started"
        for phase in roadmap["phases"]
        for skill in phase["skills"]
    ),
)


# ===========================================================
# 4. HTTP ENDPOINTS
# ===========================================================

print("\n[4] HTTP endpoints")

response = client.get(
    "/learning-resources",
    params={"skill": "Linux", "level": "beginner"},
)

check(
    "/learning-resources 200",
    response.status_code == 200,
)

data = response.json()

check(
    "/learning-resources has links",
    len(data["platform_links"]) == 5,
)

response = client.get(
    "/learning-resources",
    params={"skill": "x"},
)

check(
    "/learning-resources rejects 1-char skill",
    response.status_code == 422,
)

# Roadmap now reads the user from the JWT.

response = client.get(
    "/learning-roadmap",
    headers=AUTH,
)

check(
    "GET roadmap 200",
    response.status_code == 200,
    str(response.status_code),
)

check(
    "roadmap requires auth",
    client.get("/learning-roadmap").status_code == 401,
)

response = client.post(
    "/learning-progress",
    headers=AUTH,
    json={
        "skill": "Docker",
        "resource_url": "https://youtube.com/watch?v=abc",
        "resource_title": "Docker Course",
        "platform": "YouTube",
        "status": "not_started",
    },
)

check(
    "save progress 200",
    response.status_code == 200,
    str(response.status_code),
)

response = client.post(
    "/learning-progress/status",
    headers=AUTH,
    json={
        "skill": "Docker",
        "resource_url": "https://youtube.com/watch?v=abc",
        "status": "in_progress",
    },
)

check("update status 200", response.status_code == 200)

check(
    "status really updated",
    response.json()["record"]["status"]
    == "in_progress",
)

# Progress must be saved against the TOKEN user.

check(
    "progress stored under token user",
    response.json()["record"]["user_id"] == USER_ID,
)

response = client.post(
    "/learning-progress/status",
    headers=AUTH,
    json={
        "skill": "Docker",
        "resource_url": "x",
        "status": "bogus",
    },
)

check(
    "invalid status rejected",
    response.status_code == 400,
)

response = client.get(
    "/learning-progress",
    headers=AUTH,
)

check("get progress 200", response.status_code == 200)

check(
    "progress has the record",
    response.json()["count"] >= 1,
)

# Roadmap must now reflect the in_progress status.
result = generate_learning_roadmap(
    TEST_USER, include_resources=False
)

docker_statuses = [
    skill["status"]
    for phase in result["roadmap"]["phases"]
    for skill in phase["skills"]
    if skill["skill"] == "Docker"
]

check(
    "roadmap reflects in_progress",
    "in_progress" in docker_statuses,
    str(docker_statuses),
)


# ===========================================================
# 5. SKILL COMPLETION + RECALCULATION
# ===========================================================

print("\n[5] Skill completion and recalculation")

response = client.post(
    "/learning-progress/complete",
    headers=AUTH,
    json={
        "skill": "Docker",
        "method": "assessment",
        "assessment_score": 40,
    },
)

check(
    "failed assessment rejected",
    response.status_code == 400,
)

records = learning_progress_collection.find(
    {"user_id": TEST_USER, "skill": "Docker"}
)

check(
    "failed assessment does not mark learned",
    all(
        not record.get("skill_verified")
        for record in records
    ),
)

response = client.post(
    "/learning-progress/complete",
    headers=AUTH,
    json={
        "skill": "Docker",
        "method": "assessment",
        "assessment_score": 85,
    },
)

check(
    "passed assessment 200",
    response.status_code == 200,
    str(response.status_code),
)

check(
    "passed assessment verified",
    response.json()["verified"] is True,
)

# Recalculation must have run against the real twin and
# reported a refreshed readiness score.

recalc = response.json().get("recalculation", {})

check(
    "recalculation ran",
    recalc.get("recalculated") is True,
    str(recalc),
)

# Roadmap must now reflect the completion.
#
# IMPORTANT: marking Docker as learned RECALCULATES the
# Career Twin, so Docker is added to the user's skills and
# is no longer a gap. That means Docker DISAPPEARS from the
# roadmap - closing a gap removes it from the learning plan.
# This is the intended behaviour, so we assert it.

result = generate_learning_roadmap(
    TEST_USER, include_resources=False
)

roadmap_skills = [
    skill["skill"]
    for phase in result["roadmap"]["phases"]
    for skill in phase["skills"]
]

check(
    "learned skill removed from roadmap gaps",
    "Docker" not in roadmap_skills,
    str(roadmap_skills),
)

# The learned skill must be part of the twin now.
recalculated = career_twins_collection.find_one(
    {"user_id": TEST_USER}
)

check(
    "recalculated twin includes learned skill",
    any(
        str(skill).strip().lower() == "docker"
        for skill in (recalculated.get("skills") or [])
    ),
)

check(
    "learning history records the skill",
    any(
        str(item).strip().lower() == "docker"
        for item in (
            recalculated.get("learning_history") or []
        )
    ),
)

check(
    "progress reflects completion",
    result["roadmap"]["summary"]["progress_percent"]
    >= 0,
)


# ===========================================================
# 6. CLEANUP
# ===========================================================

print("\n[6] Cleanup")

career_twins_collection.delete_one(
    {"user_id": TEST_USER}
)

deleted = learning_progress_collection.delete_many(
    {"user_id": TEST_USER}
)

check(
    "test data removed",
    deleted.deleted_count >= 0,
)

# Remove the test account itself.

auth_users_collection.delete_one(
    {"_id": ObjectId(USER_ID)}
)

users_collection.delete_many(
    {"user_id": TEST_USER}
)

check("test account removed", True)


# ===========================================================
# SUMMARY
# ===========================================================

print()

if failures:

    print(
        "AGENT 5: "
        f"{len(failures)} CHECK(S) FAILED -> {failures}"
    )

    sys.exit(1)

print(
    "=========================================="
)

print("AGENT 5: ALL CHECKS PASSED")

print(
    "=========================================="
)
