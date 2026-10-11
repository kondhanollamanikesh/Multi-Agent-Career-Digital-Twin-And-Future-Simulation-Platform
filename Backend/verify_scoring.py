# Temporary verification of scoring fixes.

from scoring_utils import (
    compute_market_alignment,
    detect_experience_level,
    evaluate_salary,
    experience_score,
    is_experience_mismatch,
    location_match_score,
    parse_salary_range,
    role_similarity,
)

from agents.job_opportunities_agent import (
    _skill_matches_required,
    calculate_job_score,
    extract_required_skills,
    extract_skills,
    match_skills,
)

failures = []


def check(name, condition, detail=""):

    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        failures.append(name)


# =========================================================
# 1. ROLE SIMILARITY
# =========================================================

print("\n[1] Role similarity")

check(
    "AI vs ML Engineer high",
    role_similarity(
        "AI Engineer", "Machine Learning Engineer"
    ) >= 0.9,
    role_similarity(
        "AI Engineer", "Machine Learning Engineer"
    ),
)

check(
    "AI vs LLM Engineer high",
    role_similarity("AI Engineer", "LLM Engineer") >= 0.9,
)

check(
    "AI vs Senior Product Manager low",
    role_similarity(
        "AI Engineer",
        "Senior Product Manager, Learner Platform Experience",
    ) < 0.35,
    role_similarity(
        "AI Engineer",
        "Senior Product Manager, Learner Platform Experience",
    ),
)

check(
    "AI vs Senior CRM Manager low",
    role_similarity(
        "AI Engineer", "Senior CRM Manager"
    ) < 0.35,
    role_similarity(
        "AI Engineer", "Senior CRM Manager"
    ),
)

check(
    "AI vs Sales Development Rep low",
    role_similarity(
        "AI Engineer",
        "Sales Development Representative",
    ) < 0.35,
    role_similarity(
        "AI Engineer",
        "Sales Development Representative",
    ),
)

check(
    "AI vs AI Engineer exact",
    role_similarity("AI Engineer", "AI Engineer") == 1.0,
)


# =========================================================
# 2. EXPERIENCE LEVEL
# =========================================================

print("\n[2] Experience level")

check(
    "Senior PM detected",
    detect_experience_level("Senior Product Manager")
    == "Senior",
)

check(
    "Senior CRM detected",
    detect_experience_level("Senior CRM Manager")
    == "Senior",
)

check(
    "Cloud Eng Manager detected",
    detect_experience_level(
        "Cloud Engineering Manager"
    )
    == "Senior",
)

check(
    "plain AI Engineer unknown",
    detect_experience_level("AI Engineer") == "Unknown",
)

check(
    "entry score exact",
    experience_score("Entry Level", "Entry Level")
    == 1.0,
)

check(
    "entry vs adjacent",
    experience_score("Entry Level", "Mid Level")
    == 0.6,
)

check(
    "entry vs senior mismatch",
    experience_score("Entry Level", "Senior") == 0.1,
)

check(
    "unknown stays unknown",
    experience_score("Entry Level", "Unknown")
    is None,
)

check(
    "no experience canonical",
    experience_score("No Experience", "No Experience")
    == 1.0,
)

check(
    "no experience vs senior mismatch",
    is_experience_mismatch("No Experience", "Senior")
    and experience_score("No Experience", "Senior")
    == 0.0,
)

check(
    "hard filter senior",
    is_experience_mismatch("Entry Level", "Senior"),
)

check(
    "no hard filter mid",
    not is_experience_mismatch(
        "Entry Level", "Mid Level"
    ),
)


# =========================================================
# 3. SALARY FOUR STATES
# =========================================================

print("\n[3] Salary states")

status, score = evaluate_salary(
    None, None, 1000000, 1500000
)

check(
    "unknown stays unknown",
    status == "unknown" and score is None,
    (status, score),
)

status, score = evaluate_salary(
    1200000, 1400000, 1000000, 1500000
)

check(
    "in range is match",
    status == "match" and score == 1.0,
)

status, score = evaluate_salary(
    500000, 600000, 1000000, 1500000
)

check(
    "below range mismatch/partial",
    status in ("partial", "mismatch"),
    (status, score),
)

low, high = parse_salary_range("10-15 LPA")

check(
    "LPA parse",
    low == 1000000 and high == 1500000,
    (low, high),
)


# =========================================================
# 4. LOCATION EXACT VS COMPATIBLE
# =========================================================

print("\n[4] Location scores")

check(
    "exact",
    location_match_score(
        "Hyderabad", "Hyderabad, India", "Hybrid", True
    )
    == 1.0,
)

check(
    "remote compatible",
    location_match_score(
        "Hyderabad", "USA", "Remote", True
    )
    == 0.85,
)

check(
    "same country compatible",
    location_match_score(
        "Hyderabad", "Bangalore", "On-site", True
    )
    == 0.85,
)

check(
    "same country ignores relocation",
    location_match_score(
        "Hyderabad", "Bangalore", "On-site", False
    )
    == 0.85,
)

check(
    "cross country on-site without relocation",
    location_match_score(
        "Hyderabad", "USA", "On-site", False
    )
    == 0.0,
)

check(
    "cross country remote without relocation",
    location_match_score(
        "Hyderabad", "USA", "Remote", False
    )
    == 0.6,
)

check(
    "unknown location stays unknown",
    location_match_score(
        "", "USA", "Remote", True
    )
    is None,
)


# =========================================================
# 5. MARKET ALIGNMENT != READINESS
# =========================================================

print("\n[5] Market alignment")

prefs = {
    "location": "Hyderabad",
    "work_mode": "Hybrid",
    "employment_type": "Full-time",
    "relocation": True,
}

good_jobs = [
    {
        "title": "AI Engineer",
        "description": "Build ML models",
        "skill_match_pct": 70.0,
        "experience_level": "Entry Level",
        "location": "Hyderabad",
        "work_mode": "Hybrid",
        "employment_type": "Full-time",
    }
]

ma_good = compute_market_alignment(
    36.36,
    "AI Engineer",
    "Entry Level",
    prefs,
    good_jobs,
    "Entry Level",
)

check(
    "aligned market != readiness",
    abs(ma_good - 36.36) > 5,
    ma_good,
)

check(
    "aligned market is high",
    ma_good >= 85,
    ma_good,
)

bad_jobs = [
    {
        "title": "Senior Product Manager",
        "description": "scaled a live product",
        "skill_match_pct": 0.0,
        "experience_level": "Senior",
        "location": "USA",
        "work_mode": "Remote",
        "employment_type": "Full-time",
    }
]

ma_bad = compute_market_alignment(
    50.0,
    "AI Engineer",
    "Entry Level",
    prefs,
    bad_jobs,
    "Entry Level",
)

check(
    "mismatched market is low",
    ma_bad < 40,
    ma_bad,
)

ma_no_jobs = compute_market_alignment(
    36.36,
    "AI Engineer",
    "Entry Level",
    prefs,
    [],
    "Entry Level",
)

check(
    "no-jobs fallback runs",
    0 <= ma_no_jobs <= 100,
    ma_no_jobs,
)


# =========================================================
# 6. REQUIREMENT EXTRACTION
# =========================================================

print("\n[6] Requirement extraction")

codepath_desc = """
Senior Product Manager, Learner Platform Experience

We are looking for a product leader who has scaled a live
product and owned products end-to-end.

Requirements:
- Scaled a live product to millions of users
- Owned products end-to-end
- 5+ years product management experience
- Experience with engagement and retention
- Strong SQL skills and AI-assisted product experience
- Led cross-functional teams

Benefits:
- Great healthcare
"""

skills, phrases = extract_required_skills(codepath_desc)

check(
    "extraction much richer than 2 skills",
    len(skills) >= 6,
    skills,
)

check(
    "captures product requirements",
    any(
        "product" in skill.lower()
        for skill in skills
    ),
    skills,
)

check(
    "section phrases captured",
    len(phrases) >= 3,
    phrases,
)

check(
    "RAG not matched from storage/average",
    "RAG"
    not in extract_skills(
        "We store data in cloud storage and review average costs."
    ),
)

check(
    "REST not matched from interested",
    "REST APIs"
    not in extract_skills(
        "We are interested in talented people."
    ),
)

check(
    "SQL still matched",
    "SQL" in extract_skills("You need SQL knowledge."),
)

crm_desc = """
Senior CRM Manager

Requirements:
- 8+ years CRM/lifecycle marketing experience
- Team leadership
- Email marketing and segmentation
- Iterable or similar marketing automation
- Data privacy and GDPR knowledge
"""

crm_skills, crm_phrases = extract_required_skills(
    crm_desc
)

check(
    "CRM extraction rich",
    len(crm_skills) >= 5,
    crm_skills,
)

check(
    "CRM not just Git+RAG",
    crm_skills != ["Git", "RAG"]
    and any(
        "crm" in skill.lower()
        or "marketing" in skill.lower()
        for skill in crm_skills
    ),
    crm_skills,
)


# =========================================================
# 7. SKILL MATCHING (no false 100%)
# =========================================================

print("\n[7] Skill matching")

user_lower = [
    "python",
    "machine learning",
    "sql",
    "git",
    "rag",
]

check(
    "phrase Python matched",
    _skill_matches_required(
        "Proficiency in Python (data structures, OOP)",
        user_lower,
    ),
)

check(
    "Java not matched by JavaScript",
    not _skill_matches_required(
        "JavaScript", ["java"]
    ),
)

check(
    "senior PM phrase not matched",
    not _skill_matches_required(
        "Scaled a live product to millions of users",
        user_lower,
    ),
)


# =========================================================
# 8. JOB SCORE
# =========================================================

print("\n[8] Job score")

state = {
    "target_role": "AI Engineer",
    "location": "Hyderabad",
    "work_mode": "Hybrid",
    "employment_type": "Full-time",
    "salary_expectation": "10-15 LPA",
    "relocation": True,
    "preferred_industry": "Artificial Intelligence",
    "experience_level": "Entry Level",
    "current_skills": [
        "Python",
        "Machine Learning",
        "SQL",
        "Git",
        "RAG",
    ],
    "filtered_jobs": [
        {
            "title": (
                "Senior Product Manager, "
                "Learner Platform Experience"
            ),
            "company": "CodePath",
            "location": "USA",
            "work_mode": "Remote",
            "employment_type": "Full-time",
            "experience_level": "Senior",
            "salary_min": None,
            "salary_max": None,
            "description": codepath_desc,
            "required_skills": skills,
            "requirement_phrases": phrases,
            "source": "Test",
            "url": "",
            "created": "",
        },
        {
            "title": "AI Engineer",
            "company": "AI Labs",
            "location": "Hyderabad",
            "work_mode": "Hybrid",
            "employment_type": "Full-time",
            "experience_level": "Entry Level",
            "salary_min": None,
            "salary_max": None,
            "description": (
                "Entry level AI Engineer. Python, "
                "SQL, Git, RAG, Machine Learning."
            ),
            "required_skills": [
                "Python",
                "Machine Learning",
                "SQL",
                "Git",
                "RAG",
            ],
            "requirement_phrases": [],
            "source": "Test",
            "url": "",
            "created": "",
        },
    ],
}

state = match_skills(state)
state = calculate_job_score(state)

codepath = state["scored_jobs"][0]
ai_job = state["scored_jobs"][1]

check(
    "CodePath no longer 100% skill match",
    (
        codepath["skill_match_pct"] is None
        or codepath["skill_match_pct"] < 100
    ),
    codepath["skill_match_pct"],
)

check(
    "CodePath role similarity low",
    codepath["role_similarity"] < 0.35,
    codepath["role_similarity"],
)

check(
    "CodePath job_score heavily penalized",
    codepath["job_score"] < 40,
    codepath["job_score"],
)

check(
    "CodePath salary unknown not 50",
    codepath["salary_status"] == "unknown"
    and codepath["salary_match_pct"] is None,
    (
        codepath["salary_status"],
        codepath["salary_match_pct"],
    ),
)

check(
    "CodePath experience mismatch scored low",
    codepath["experience_match_pct"] == 10.0,
    codepath["experience_match_pct"],
)

check(
    "AI job scores higher than CodePath",
    ai_job["job_score"] > codepath["job_score"],
    (ai_job["job_score"], codepath["job_score"]),
)

check(
    "AI job skill match high",
    (
        ai_job["skill_match_pct"] is not None
        and ai_job["skill_match_pct"] >= 90
    ),
    ai_job["skill_match_pct"],
)


# =========================================================
# 9. WEIGHTED SCORE / CATEGORY / BREAKDOWN
# =========================================================

print("\n[9] Weighted score / category / breakdown")

from scoring_utils import (
    category_requirement_match,
    weighted_score,
)

check(
    "weighted excludes unknown",
    weighted_score([(50.0, 0.6), (None, 0.4)])
    == 50.0,
)

check(
    "weighted renormalizes remaining weights",
    weighted_score([(80.0, 0.5), (None, 0.5)])
    == 80.0,
)

check(
    "weighted all unknown -> None",
    weighted_score([(None, 1.0)]) is None,
)

check(
    "category match backend language",
    bool(
        category_requirement_match(
            "Proficiency in at least one backend "
            "programming language",
            ["python", "react"],
        )
    ),
)

check(
    "category match no false hit",
    not category_requirement_match(
        "Proficiency in at least one backend "
        "programming language",
        ["photoshop"],
    ),
)

check(
    "category match containers",
    category_requirement_match(
        "Experience with containerization "
        "(Docker, Kubernetes)",
        ["docker"],
    )
    == "docker",
)

check(
    "job score breakdown has 7 components",
    isinstance(codepath.get("score_breakdown"), dict)
    and set(codepath["score_breakdown"]) == {
        "skill_match",
        "role_similarity",
        "experience_match",
        "location_match",
        "work_mode_match",
        "employment_match",
        "salary_match",
    },
    codepath.get("score_breakdown"),
)

check(
    "job score explanation present",
    isinstance(
        codepath.get("scoring_explanation"), list
    )
    and len(codepath["scoring_explanation"]) >= 5,
    codepath.get("scoring_explanation"),
)

check(
    "work mode component present",
    "work_mode_match_pct" in codepath,
    codepath.get("work_mode_match_pct"),
)


# =========================================================
# SUMMARY
# =========================================================

print("\n==========================================")

if failures:

    print(f"FAILED: {len(failures)} check(s)")

    for failure in failures:
        print("  -", failure)

else:

    print("ALL CHECKS PASSED")

print("==========================================")
