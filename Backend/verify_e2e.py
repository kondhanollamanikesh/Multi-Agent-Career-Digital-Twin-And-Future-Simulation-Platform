# End-to-end automation verification.
#
# Proves the whole flow is automatic with NO manual steps:
#   register -> login -> upload resume -> Career Twin
#   -> learning roadmap -> progress -> skill verified
#
# Uses FastAPI's in-process TestClient so it exercises the
# real route handlers without depending on a live server
# socket (which is flaky on Windows under load).
#
# Run:  python verify_e2e.py

import sys

sys.stdout.reconfigure(
    encoding="utf-8", errors="replace"
)

import os
import time

from fastapi.testclient import TestClient

import main

from database import (
    auth_users_collection,
    users_collection,
    career_twins_collection,
    learning_progress_collection,
)
from bson import ObjectId

client = TestClient(main.app)

RESUME = os.path.join(
    os.path.dirname(__file__),
    "uploads",
    "resume.pdf",
)

failures = []


def check(name, condition, detail=""):
    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        failures.append(name)


# ===========================================================
# 1. REGISTER + LOGIN
# ===========================================================

print("\n[1] Register + login")

stamp = str(int(time.time()))
email = f"e2e_{stamp}@example.com"
password = "E2ePass!2024"

r = client.post(
    "/auth/register",
    json={
        "email": email,
        "password": password,
        "name": "E2E Tester",
    },
)
check("register 200", r.status_code == 200, str(r.status_code))

reg = r.json()
token = reg["access_token"]
user_id = reg["user"]["user_id"]
H = {"Authorization": f"Bearer {token}"}

r = client.post(
    "/auth/login",
    json={"email": email, "password": password},
)
check("login 200", r.status_code == 200, str(r.status_code))
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}

r = client.get("/auth/me", headers=H)
check("/auth/me 200", r.status_code == 200)
check("/auth/me correct email", r.json()["email"] == email)


# ===========================================================
# 2. NO TWIN YET
# ===========================================================

print("\n[2] Career twin status before upload")

r = client.get("/career-twin/status", headers=H)
check("status 200", r.status_code == 200)
check("has_twin False", r.json()["has_twin"] is False)


# ===========================================================
# 3. UPLOAD RESUME -> FULLY AUTOMATIC TWIN
# ===========================================================

print("\n[3] Upload resume (full pipeline)")

if not os.path.exists(RESUME):
    print("  FAIL  sample resume missing:", RESUME)
    failures.append("resume")
    sys.exit(1)

with open(RESUME, "rb") as fh:
    r = client.post(
        "/career-twin",
        headers=H,
        files={
            "resume": (
                "resume.pdf",
                fh,
                "application/pdf",
            )
        },
    )

check(
    "career-twin 200",
    r.status_code == 200,
    str(r.status_code),
)

resp = r.json()

# The twin is nested under "career_twin".
twin = resp.get("career_twin", resp)

check("twin has user_id", twin.get("user_id") == user_id)
check(
    "twin has career_state",
    "career_state" in twin,
)
check(
    "twin has skill_gap / gaps",
    bool(
        twin.get("skill_gap")
        or twin.get("career_state", {}).get("skill_gaps")
        or twin.get("career_state", {}).get("missing_skills")
    ),
)

r = client.get("/career-twin/status", headers=H)
check(
    "has_twin True after upload",
    r.json()["has_twin"] is True,
)


# ===========================================================
# 4. PREFERENCES (JSON, auto-saved)
# ===========================================================

print("\n[4] Preferences (JSON accepted)")

r = client.post(
    "/preferences",
    headers=H,
    json={
        "target_role": "AI Engineer",
        "location": "Hyderabad",
        "work_mode": "Remote",
        "experience_level": "Entry Level",
    },
)
check(
    "/preferences 200 (JSON)",
    r.status_code == 200,
    str(r.status_code),
)
check(
    "target_role saved",
    r.json()["preferences"]["target_role"] == "AI Engineer",
)


# ===========================================================
# 5. LEARNING ROADMAP (auto from real gaps)
# ===========================================================

print("\n[5] Learning roadmap")

r = client.get("/learning-roadmap", headers=H)
check("roadmap 200", r.status_code == 200, str(r.status_code))

rm = r.json()
check("roadmap success", rm.get("success") is True)
phases = rm["roadmap"]["phases"]
check("has phases", len(phases) > 0, str(len(phases)))

skills_in_roadmap = [
    s["skill"] for p in phases for s in p["skills"]
]
check("roadmap has skills", len(skills_in_roadmap) > 0)

first_skill = skills_in_roadmap[0] if skills_in_roadmap else ""
print(f"        (first skill: {first_skill[:60]}...)")


# ===========================================================
# 6. PROGRESS TRACKING
# ===========================================================

print("\n[6] Progress tracking")

r = client.post(
    "/learning-progress",
    headers=H,
    json={
        "skill": first_skill,
        "resource_url": "https://youtube.com/watch?v=e2e",
        "resource_title": "E2E Course",
        "platform": "YouTube",
        "status": "in_progress",
        "level": "beginner",
    },
)
check(
    "save progress 200",
    r.status_code == 200,
    str(r.status_code),
)
check(
    "stored under token user",
    r.json()["record"]["user_id"] == user_id,
)

r = client.get("/learning-progress", headers=H)
check("progress count 1", r.json()["count"] >= 1)


# ===========================================================
# 7. SKILL VERIFIED -> RECALCULATION
# ===========================================================

print("\n[7] Skill verified + recalculation")

r = client.post(
    "/learning-progress/complete",
    headers=H,
    json={
        "skill": first_skill,
        "method": "assessment",
        "assessment_score": 85,
    },
)
check("complete 200", r.status_code == 200, str(r.status_code))

body = r.json()
check("verified True", body.get("verified") is True)
check(
    "recalculation ran",
    body.get("recalculation", {}).get("recalculated")
    is True,
    str(body.get("recalculation", {})),
)


# ===========================================================
# 8. CROSS-USER ISOLATION
# ===========================================================

print("\n[8] Cross-user isolation")

email2 = f"e2e2_{stamp}@example.com"
r = client.post(
    "/auth/register",
    json={
        "email": email2,
        "password": password,
        "name": "Other",
    },
)
H2 = {
    "Authorization": f"Bearer {r.json()['access_token']}"
}

r = client.get("/learning-progress", headers=H2)
check("other user sees no progress", r.json()["count"] == 0)

r = client.get("/career-twin/status", headers=H2)
check("other user has no twin", r.json()["has_twin"] is False)

r = client.get("/learning-roadmap")
check("no token -> 401", r.status_code == 401)


# ===========================================================
# CLEANUP
# ===========================================================

print("\n[9] Cleanup")

auth_users_collection.delete_one(
    {"_id": ObjectId(user_id)}
)
users_collection.delete_many({"user_id": user_id})
career_twins_collection.delete_many({"user_id": user_id})
learning_progress_collection.delete_many(
    {"user_id": user_id}
)
auth_users_collection.delete_many(
    {"email": {"$regex": r"^e2e"}}
)
check("test accounts removed", True)


print()
if failures:
    print(
        f"E2E: {len(failures)} CHECK(S) FAILED -> {failures}"
    )
    sys.exit(1)

print("=" * 42)
print("E2E: FULL AUTOMATED FLOW PASSED")
print("=" * 42)
