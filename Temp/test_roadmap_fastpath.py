# Targeted validation of the uncommitted backend edit:
# the roadmap FAST PATH (include_resources=False) must now
# include free platform_links built from templates.

import sys
import json

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
         + os.sep + "Backend")

sys.path.insert(0, os.getcwd())

from agents.learning_roadmap_agent import (  # noqa: E402
    build_roadmap_structure,
    platform_search_links,
)

FAILURES = []


def check(name, condition, detail=""):

    print(("PASS" if condition else "FAIL") + "  " + name +
          (" -> " + str(detail) if detail and not condition else ""))

    if not condition:
        FAILURES.append(name)


# ---------------------------------------------------------
# 1. platform_search_links works standalone
# ---------------------------------------------------------

links = platform_search_links("Data Structures and Algorithms")

check(
    "platform_search_links non-empty",
    isinstance(links, list) and len(links) >= 3,
    links
)

if links:

    sample = links[0]

    check(
        "links have platform + url",
        "platform" in sample and "url" in sample,
        sample
    )

    print("        sample:", json.dumps(links[:2], indent=None))


# ---------------------------------------------------------
# 2. Fast path on build_roadmap_structure
# ---------------------------------------------------------

TWIN = {
    "user_id": "00000000-0000-0000-0000-000000000000",

    "profile": {
        "target_role": "Software Engineer",
        "experience_level": "Entry Level",
    },

    "skills": ["Python", "SQL"],

    "career_state": {
        "prioritized_gaps": [
            {
                "skill": "Data Structures and Algorithms",
                "priority": "High",
                "importance": "Core requirement",
                "learning_suggestion": "Grind arrays",
            },
            {
                "skill": "Unit Testing",
                "priority": "Medium",
                "importance": "Nice-to-have",
                "learning_suggestion": "pytest",
            },
        ],
    },
}

roadmap = build_roadmap_structure(TWIN, include_resources=False)

phases = roadmap.get("phases") or []

check("fast path produced phases", len(phases) > 0, roadmap.get("phases"))

flat = [s for p in phases for s in p.get("skills", [])]

check("fast path has skills", len(flat) >= 2, len(flat))

missing_links = [
    s["skill"]

    for s in flat

    if not (s.get("resources") or {}).get("platform_links")
]

check(
    "every fast-path skill has platform_links",
    not missing_links,
    missing_links
)

doc_missing = [
    s["skill"]

    for s in flat

    if not (s.get("resources") or {}).get("documentation")
]

check(
    "fast-path documentation present",
    not doc_missing,
    doc_missing
)

yt_empty = all(
    not (s.get("resources") or {}).get("youtube_resources")

    for s in flat
)

check(
    "fast path avoids YouTube API (no live results)",
    yt_empty
)

summary = roadmap.get("summary") or {}

check(
    "summary present",
    summary.get("total_skills") == len(flat)
    and summary.get("total_phases") == len(phases),
    summary
)

if links:

    links_match = all(
        (s.get("resources") or {}).get("platform_links")

        for s in flat
    )


print()

if FAILURES:

    print(str(len(FAILURES)) + " FAILURES: " + ", ".join(FAILURES))

    sys.exit(1)


print("ROADMAP FAST PATH: ALL CHECKS PASS")
