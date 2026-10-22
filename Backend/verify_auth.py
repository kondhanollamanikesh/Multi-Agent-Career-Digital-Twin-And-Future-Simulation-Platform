# Auth + full automation verification.
#
# Verifies the login system and that a user can go from
# "just registered" to a generated Career Twin and a
# learning roadmap with no manual steps in between.
#
# Run:  python verify_auth.py

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


import time

from fastapi.testclient import TestClient

import main

from database import (
    auth_users_collection,
    users_collection,
    career_twins_collection,
    learning_progress_collection,
)

client = TestClient(main.app)

STAMP = str(int(time.time()))

EMAIL = f"authtest_{STAMP}@example.com"

PASSWORD = "S3curePass!"


# ===========================================================
# 1. REGISTRATION
# ===========================================================

print("\n[1] Registration")

response = client.post(

    "/auth/register",

    json={
        "email": EMAIL,
        "password": PASSWORD,
        "name": "Auto Test",
    },
)

check(
    "register 200",
    response.status_code == 200,
    str(response.status_code),
)

data = response.json()

TOKEN = data.get("access_token", "")

USER_ID = data.get("user", {}).get("user_id", "")

check("token issued", bool(TOKEN))

check("user_id returned", bool(USER_ID))

check(
    "email echoed back",
    data["user"]["email"] == EMAIL,
)

# Duplicate registration must be refused.

response = client.post(

    "/auth/register",

    json={
        "email": EMAIL,
        "password": PASSWORD,
        "name": "Dup",
    },
)

check(
    "duplicate email -> 409",
    response.status_code == 409,
    str(response.status_code),
)

# Weak password refused.

response = client.post(

    "/auth/register",

    json={
        "email": f"weak_{STAMP}@example.com",
        "password": "abc",
    },
)

check(
    "short password -> 400",
    response.status_code == 400,
    str(response.status_code),
)

# Invalid email refused.

response = client.post(

    "/auth/register",

    json={
        "email": "not-an-email",
        "password": PASSWORD,
    },
)

check(
    "invalid email -> 400",
    response.status_code == 400,
    str(response.status_code),
)


# ===========================================================
# 2. PASSWORD STORAGE
# ===========================================================

print("\n[2] Password storage")

document = auth_users_collection.find_one(
    {"email": EMAIL}
)

check(
    "plain text password NOT stored",
    document is not None
    and PASSWORD not in str(document.get(
        "password_hash", ""
    )),
)

check(
    "bcrypt hash stored",
    document is not None
    and str(
        document.get("password_hash", "")
    ).startswith("$2b$"),
)


# ===========================================================
# 3. LOGIN
# ===========================================================

print("\n[3] Login")

response = client.post(

    "/auth/login",

    json={
        "email": EMAIL,
        "password": PASSWORD,
    },
)

check(
    "login 200",
    response.status_code == 200,
    str(response.status_code),
)

LOGIN_TOKEN = response.json().get(
    "access_token", ""
)

check("login token issued", bool(LOGIN_TOKEN))

# Wrong password.

response = client.post(

    "/auth/login",

    json={
        "email": EMAIL,
        "password": "WrongPass123",
    },
)

check(
    "wrong password -> 401",
    response.status_code == 401,
    str(response.status_code),
)

# Unknown email - same message, no user enumeration.

response = client.post(

    "/auth/login",

    json={
        "email": f"nobody_{STAMP}@example.com",
        "password": PASSWORD,
    },
)

check(
    "unknown email -> 401",
    response.status_code == 401,
    str(response.status_code),
)

check(
    "no user enumeration (same detail)",
    response.json().get("detail")
    == "Incorrect email or password.",
)


# ===========================================================
# 4. TOKENS / PROTECTION
# ===========================================================

print("\n[4] Route protection")

AUTH = {"Authorization": f"Bearer {LOGIN_TOKEN}"}

protected = [

    ("/auth/me", "get", None),

    ("/preferences", "post", {}),

    ("/career-twin/status", "get", None),

    ("/learning-roadmap", "get", None),

    ("/learning-progress", "get", None),

    ("/learning-progress", "post", {}),

    ("/learning-progress/status", "post", {}),

    ("/learning-progress/complete", "post", {}),
]

for path, method, body in protected:

    if method == "get":

        response = client.get(path)

    else:

        response = client.post(path, json=body or {})

    check(

        f"{path} without token -> 401",

        response.status_code == 401,

        str(response.status_code),
    )

# Garbage token rejected.

response = client.get(

    "/auth/me",

    headers={
        "Authorization": "Bearer not.a.real.token"
    },
)

check(
    "garbage token -> 401",
    response.status_code == 401,
    str(response.status_code),
)

# /auth/me works with a valid token.

response = client.get(
    "/auth/me",
    headers=AUTH,
)

check(
    "/auth/me 200",
    response.status_code == 200,
    str(response.status_code),
)

check(
    "/auth/me returns correct user",
    response.json().get("email") == EMAIL,
)


# ===========================================================
# 5. AUTOMATED PREFERENCES (the old 422 is fixed)
# ===========================================================

print("\n[5] Preferences")

response = client.post(

    "/preferences",

    headers=AUTH,

    json={

        "target_role": "AI Engineer",

        "location": "Hyderabad",

        "work_mode": "Remote",

        "experience_level": "Entry Level",

        "preferred_industry": "Artificial Intelligence",
    },
)

check(
    "/preferences 200 (JSON accepted)",
    response.status_code == 200,
    str(response.status_code),
)

check(
    "preferences returned",
    response.json().get(
        "preferences", {}
    ).get("target_role") == "AI Engineer",
)

# Saved under the TOKEN user, not a client-supplied id.

saved = users_collection.find_one(
    {"user_id": USER_ID}
)

check(
    "saved against token user_id",
    saved is not None
    and saved.get("preferences", {}).get(
        "target_role"
    ) == "AI Engineer",
)


# ===========================================================
# 6. CAREER TWIN STATUS (pre-upload)
# ===========================================================

print("\n[6] Career twin status")

response = client.get(
    "/career-twin/status",
    headers=AUTH,
)

check(
    "status 200",
    response.status_code == 200,
    str(response.status_code),
)

check(
    "reports no twin before upload",
    response.json().get("has_twin") is False,
)


# ===========================================================
# 7. RESUME VALIDATION
# ===========================================================

print("\n[7] Resume upload validation")

# Non-PDF refused.

response = client.post(

    "/career-twin",

    headers=AUTH,

    files={

        "resume": (
            "notes.txt",
            b"hello world",
            "text/plain",
        )
    },
)

check(
    "non-PDF -> 400",
    response.status_code == 400,
    str(response.status_code),
)

# Empty file refused.

response = client.post(

    "/career-twin",

    headers=AUTH,

    files={

        "resume": (
            "resume.pdf",
            b"",
            "application/pdf",
        )
    },
)

check(
    "empty file -> 400",
    response.status_code == 400,
    str(response.status_code),
)

# Fake PDF (wrong magic number) refused.

response = client.post(

    "/career-twin",

    headers=AUTH,

    files={

        "resume": (
            "resume.pdf",
            b"NOTAPDF" + b"x" * 50,
            "application/pdf",
        )
    },
)

check(
    "invalid PDF magic -> 400",
    response.status_code == 400,
    str(response.status_code),
)

# No resume at all.

response = client.post(
    "/career-twin",
    headers=AUTH,
)

check(
    "missing resume -> 422",
    response.status_code == 422,
    str(response.status_code),
)


# ===========================================================
# 8. CROSS-USER ISOLATION
# ===========================================================
#
# The important security property: a second user must not
# be able to read or write the first user's data.
# ===========================================================

print("\n[8] Cross-user isolation")

second_email = f"authtest2_{STAMP}@example.com"

response = client.post(

    "/auth/register",

    json={
        "email": second_email,
        "password": PASSWORD,
        "name": "Second User",
    },
)

SECOND_TOKEN = response.json().get(
    "access_token", ""
)

SECOND_AUTH = {
    "Authorization": f"Bearer {SECOND_TOKEN}"
}

# Second user sees NO progress of the first user.

response = client.get(
    "/learning-progress",
    headers=SECOND_AUTH,
)

check(
    "second user sees no first-user progress",
    response.json().get("count") == 0,
    str(response.json()),
)

# Second user has their own preferences, not the first's.

response = client.get(
    "/career-twin/status",
    headers=SECOND_AUTH,
)

check(
    "second user has no twin",
    response.json().get("has_twin") is False,
)

# First user's preferences are untouched.

response = client.get(
    "/career-twin/status",
    headers=AUTH,
)

check(
    "first user status unaffected",
    response.json().get("has_twin") is False,
)

saved = users_collection.find_one(
    {"user_id": USER_ID}
)

check(
    "first user preferences still theirs",
    saved.get("preferences", {}).get(
        "target_role"
    ) == "AI Engineer",
)


# ===========================================================
# 9. TOKEN EXPIRY / TAMPERING
# ===========================================================

print("\n[9] Token tampering")

tampered = TOKEN[:-4] + "AAAA"

response = client.get(

    "/auth/me",

    headers={
        "Authorization": f"Bearer {tampered}"
    },
)

check(
    "tampered token -> 401",
    response.status_code == 401,
    str(response.status_code),
)


# ===========================================================
# 10. CLEANUP
# ===========================================================

print("\n[10] Cleanup")

for uid in (USER_ID,):

    auth_users_collection.delete_one(
        {"_id": __import__(
            "bson"
        ).ObjectId(uid)}
    )

    users_collection.delete_many(
        {"user_id": uid}
    )

    career_twins_collection.delete_many(
        {"user_id": uid}
    )

    learning_progress_collection.delete_many(
        {"user_id": uid}
    )

auth_users_collection.delete_many(
    {"email": {"$regex": r"^authtest"}}
)

users_collection.delete_many(
    {"user_id": {"$regex": r"^agent5"}}
)

check("test accounts removed", True)


# ===========================================================
# SUMMARY
# ===========================================================

print()

if failures:

    print(
        "AUTH: "
        f"{len(failures)} CHECK(S) FAILED -> {failures}"
    )

    sys.exit(1)

print(
    "=========================================="
)

print("AUTH: ALL CHECKS PASSED")

print(
    "=========================================="
)
