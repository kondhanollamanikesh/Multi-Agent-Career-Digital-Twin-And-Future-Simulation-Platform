# Role knowledge caching verification.
#
# Verifies data/role_skills.json caching:
#   role missing -> LLM research -> stored back to
#   JSON (+ MongoDB) -> subsequent calls are cache
#   hits with no further research.
#
# Also verifies:
#   - JSON-only path (Mongo purged -> still a hit)
#   - legacy JSON entries (empty required_skills)
#     are treated as a miss and rebuilt
#   - test roles are cleaned up afterwards

import json
import os
import sys

sys.stdout.reconfigure(
    encoding="utf-8", errors="replace"
)
sys.stderr.reconfigure(
    encoding="utf-8", errors="replace"
)

sys.path.insert(
    0,
    os.path.dirname(os.path.abspath(__file__)),
)

import role_knowledge_manager as rkm

from role_knowledge_manager import (
    ROLE_KNOWLEDGE_FILE,
    get_or_create_role_knowledge,
    load_json_cache,
)

from models import RoleKnowledge


failures = []


def check(name, condition, detail=""):

    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        failures.append(name)


def write_json_cache(data):

    with open(
        ROLE_KNOWLEDGE_FILE,
        "w",
        encoding="utf-8",
    ) as fh:

        json.dump(
            data,
            fh,
            indent=4,
            ensure_ascii=False,
        )


def purge(role):

    data = load_json_cache()

    if role in data:

        del data[role]

        write_json_cache(data)

    rkm.role_knowledge_collection.delete_many(
        {"role": role}
    )


TEST_ROLE = "MLOps Engineer"
LEGACY_ROLE = "Legacy Cache Probe Role"

EXPERIENCE = "Entry Level"
INDUSTRY = "Artificial Intelligence"

real_research = rkm.research_role


def forbidden_research(*args, **kwargs):

    raise AssertionError(
        "research_role called despite cache"
    )


try:

    # --------------------------------------------------
    # 1. Clean slate
    # --------------------------------------------------

    print("\n[1] Clean slate")

    purge(TEST_ROLE)
    purge(LEGACY_ROLE)

    check(
        "test role absent before test",
        TEST_ROLE not in load_json_cache(),
    )

    # --------------------------------------------------
    # 2. Missing role -> research -> stored back
    # --------------------------------------------------

    print("\n[2] Missing role -> research -> stored")

    knowledge = get_or_create_role_knowledge(
        TEST_ROLE,
        EXPERIENCE,
        INDUSTRY,
    )

    check(
        "research returned knowledge",
        knowledge is not None,
    )

    check(
        "required_skills populated (>=3)",
        knowledge is not None
        and len(knowledge.required_skills) >= 3,
        (
            knowledge.required_skills
            if knowledge
            else None
        ),
    )

    stored = load_json_cache().get(TEST_ROLE)

    check(
        "stored in data/role_skills.json",
        isinstance(stored, dict),
        type(stored).__name__,
    )

    check(
        "json entry required_skills (>=3)",
        len(
            (stored or {}).get("required_skills")
            or []
        )
        >= 3,
        (stored or {}).get("required_skills"),
    )

    document = rkm.role_knowledge_collection.find_one(
        {
            "role": TEST_ROLE,
            "experience_level": EXPERIENCE,
            "industry": INDUSTRY,
        }
    )

    check(
        "stored in MongoDB",
        document is not None,
    )

    # --------------------------------------------------
    # 3. Second call -> cache hit, no research
    # --------------------------------------------------

    print(
        "\n[3] Second call served from cache"
    )

    rkm.research_role = forbidden_research

    try:

        cached = get_or_create_role_knowledge(
            TEST_ROLE,
            EXPERIENCE,
            INDUSTRY,
        )

        check(
            "cache hit returns knowledge",
            cached is not None,
        )

        check(
            "same required_skills from cache",
            cached is not None
            and cached.required_skills
            == knowledge.required_skills,
            (
                cached.required_skills
                if cached
                else None
            ),
        )

    finally:

        rkm.research_role = real_research

    # --------------------------------------------------
    # 4. JSON-only path: Mongo purged, still a hit
    # --------------------------------------------------

    print(
        "\n[4] JSON cache path (Mongo purged)"
    )

    rkm.role_knowledge_collection.delete_many(
        {"role": TEST_ROLE}
    )

    rkm.research_role = forbidden_research

    try:

        from_json = get_or_create_role_knowledge(
            TEST_ROLE,
            EXPERIENCE,
            INDUSTRY,
        )

        check(
            "json cache hit after mongo purge",
            from_json is not None
            and from_json.required_skills
            == knowledge.required_skills,
            (
                from_json.required_skills
                if from_json
                else None
            ),
        )

    finally:

        rkm.research_role = real_research

    check(
        "json hit re-saved to MongoDB",
        rkm.role_knowledge_collection.find_one(
            {"role": TEST_ROLE}
        )
        is not None,
    )

    # --------------------------------------------------
    # 5. Existing production role -> cache hit
    # --------------------------------------------------

    print(
        "\n[5] Existing role hits cache"
    )

    rkm.research_role = forbidden_research

    try:

        existing = get_or_create_role_knowledge(
            "AI Engineer",
            EXPERIENCE,
            INDUSTRY,
        )

        check(
            "existing role from cache (>=3)",
            existing is not None
            and len(existing.required_skills) >= 3,
            (
                existing.required_skills
                if existing
                else None
            ),
        )

    finally:

        rkm.research_role = real_research

    # --------------------------------------------------
    # 6. Legacy entry (empty required_skills)
    #    is a miss and gets rebuilt
    # --------------------------------------------------

    print(
        "\n[6] Legacy entry treated as miss"
    )

    data = load_json_cache()

    data[LEGACY_ROLE] = {
        "role": LEGACY_ROLE,
        "required_skills": [],
        "core_skills": ["legacy skill"],
    }

    write_json_cache(data)

    rkm.role_knowledge_collection.delete_many(
        {"role": LEGACY_ROLE}
    )

    research_calls = []

    def counting_research(
        role, experience_level, industry
    ):

        research_calls.append(role)

        return RoleKnowledge(
            role=role,
            experience_level=experience_level,
            industry=industry,
            required_skills=[
                "Rebuilt skill A",
                "Rebuilt skill B",
                "Rebuilt skill C",
            ],
        )

    rkm.research_role = counting_research

    try:

        rebuilt = get_or_create_role_knowledge(
            LEGACY_ROLE,
            EXPERIENCE,
            INDUSTRY,
        )

        check(
            "legacy entry triggers re-research",
            research_calls == [LEGACY_ROLE],
            research_calls,
        )

        check(
            "legacy entry rebuilt (>=3)",
            len(rebuilt.required_skills) >= 3,
            rebuilt.required_skills,
        )

    finally:

        rkm.research_role = real_research

    check(
        "rebuilt entry stored in json",
        (
            load_json_cache().get(LEGACY_ROLE)
            or {}
        ).get("required_skills")
        == [
            "Rebuilt skill A",
            "Rebuilt skill B",
            "Rebuilt skill C",
        ],
    )

except Exception as exc:

    check(
        "caching workflow completed",
        False,
        repr(exc),
    )

finally:

    # --------------------------------------------------
    # 7. Cleanup - never leave test roles behind
    # --------------------------------------------------

    rkm.research_role = real_research

    print("\n[7] Cleanup")

    purge(TEST_ROLE)
    purge(LEGACY_ROLE)

    remaining = load_json_cache()

    check(
        "test roles removed from json",
        TEST_ROLE not in remaining
        and LEGACY_ROLE not in remaining,
    )

    check(
        "test roles removed from mongo",
        rkm.role_knowledge_collection.find_one(
            {"role": TEST_ROLE}
        )
        is None
        and rkm.role_knowledge_collection.find_one(
            {"role": LEGACY_ROLE}
        )
        is None,
    )


# =========================================================
print("\n==========================================")

if failures:

    print(f"FAILED: {len(failures)} check(s)")

    for failure in failures:

        print("  -", failure)

    sys.exit(1)

else:

    print("CACHE: ALL CHECKS PASSED")

print("==========================================")
