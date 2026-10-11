# Full workflow integration test.
#
# Runs create_career_twin end-to-end:
#   PDF -> resume extraction -> role knowledge ->
#   skill gap graph -> job opportunities graph ->
#   market alignment -> CareerTwin
#
# Only the resume LLM call is stubbed (no API key in
# this environment). Embeddings, Mongo, Jobicy and all
# scoring logic run for real.

import os
import sys

os.environ.setdefault(
    "NVIDIA_API_KEY", "nvapi-workflow-test-dummy"
)
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

sys.stdout.reconfigure(
    encoding="utf-8", errors="replace"
)
sys.stderr.reconfigure(
    encoding="utf-8", errors="replace"
)

failures = []


def check(name, condition, detail=""):

    if condition:
        print(f"  PASS  {name}")
    else:
        print(f"  FAIL  {name} {detail}")
        failures.append(name)


print("\n[STEP 1] Import digital_twin (full dependency tree)")

import digital_twin
from digital_twin import (
    CareerState,
    Preferences,
    ResumeSchema,
    create_career_twin,
)

import agents.skill_gap_agent as skill_gap_agent

check("digital_twin imported", True)


# ---------------------------------------------------------
# Stub ONLY the resume-extraction LLM call.
# ---------------------------------------------------------

class _StubResumeLLM:

    def invoke(self, prompt):

        return ResumeSchema(
            education=[
                "B.Tech Computer Science, 2026"
            ],
            skills=[
                "Python",
                "Machine Learning",
                "Deep Learning",
                "Natural Language Processing",
                "LLMs",
                "LangChain",
                "LangGraph",
                "FastAPI",
                "REST APIs",
                "MongoDB",
                "SQL",
                "Git",
                "RAG",
                "Pandas",
                "NumPy",
                "Docker",
            ],
            projects=[
                "AI-powered Resume Matcher"
            ],
            experience=[
                "Built end-to-end ML pipelines"
            ],
            certifications=[],
            achievements=[],
            target_roles=["AI Engineer"],
            preferences=Preferences(),
        )


digital_twin.structured_model = _StubResumeLLM()


# ---------------------------------------------------------
# Stub skill-gap LLM: fail fast so the workflow uses its
# built-in fallbacks (borderline stays partial, gap
# analysis falls back) exactly as in production on LLM
# errors.
# ---------------------------------------------------------

class _FailingLLM:

    def invoke(self, *args, **kwargs):
        raise RuntimeError(
            "LLM disabled in workflow test"
        )


skill_gap_agent.llm = _FailingLLM()


# =========================================================
print("\n[STEP 2] Run create_career_twin (full pipeline)")

preferences = Preferences(
    target_role="AI Engineer",
    location="Hyderabad",
    work_mode="Hybrid",
    employment_type="Full-time",
    salary_expectation="10-15 LPA",
    relocation=True,
    preferred_industry="Artificial Intelligence",
    experience_level="Entry Level",
)

resume_path = os.path.join(
    os.path.dirname(__file__), "resume.pdf"
)

try:

    career_twin = create_career_twin(
        resume_path,
        user_id="workflow_test_user",
        preferences=preferences,
    )

    check("create_career_twin completed", True)

except Exception as exc:

    check(
        "create_career_twin completed",
        False,
        repr(exc),
    )
    career_twin = None


if career_twin is not None:

    state = career_twin.career_state

    print("\n[STEP 3] Career state checks")

    print("    readiness_score   =", state.readiness_score)
    print("    market_alignment  =", state.market_alignment)
    print("    required/matched/missing/partial =",
          state.total_required, "/",
          state.total_matched, "/",
          state.total_missing, "/",
          state.total_partial)

    check(
        "target role resolved",
        career_twin.profile.get("target_role")
        == "AI Engineer",
        career_twin.profile.get("target_role"),
    )

    check(
        "role knowledge loaded (11 required)",
        state.total_required == 11,
        state.total_required,
    )

    # Readiness is component based:
    #   skill 50% + projects 20% + experience 10%
    #   + fundamentals 10% + education 10%

    if state.total_required > 0:

        expected_skill_component = round(
            (
                state.total_matched * 1.0
                + state.total_partial * 0.5
            )
            / state.total_required
            * 100,
            2,
        )

        breakdown = state.readiness_breakdown

        check(
            "readiness breakdown present",
            isinstance(breakdown, dict)
            and {"skill_coverage",
                 "project_evidence",
                 "experience",
                 "fundamentals",
                 "education",
                 "weights"} <= set(breakdown),
            breakdown,
        )

        check(
            "readiness skill component = coverage",
            abs(
                breakdown.get(
                    "skill_coverage", -1
                )
                - expected_skill_component
            )
            < 0.05,
            (
                breakdown.get("skill_coverage"),
                expected_skill_component,
            ),
        )

        expected_readiness = round(
            sum(
                breakdown[component]
                * breakdown["weights"][component]
                for component in (
                    "skill_coverage",
                    "project_evidence",
                    "experience",
                    "fundamentals",
                    "education",
                )
            ),
            2,
        )

        check(
            "readiness = weighted components",
            abs(
                state.readiness_score
                - expected_readiness
            )
            < 0.05,
            (
                state.readiness_score,
                expected_readiness,
            ),
        )

    check(
        "readiness > strict-only value",
        state.readiness_score
        >= round(
            state.total_matched
            / state.total_required
            * 100,
            2,
        ),
        state.readiness_score,
    )

    check(
        "market_alignment != readiness",
        state.market_alignment
        != state.readiness_score,
        (
            state.market_alignment,
            state.readiness_score,
        ),
    )

    check(
        "market_alignment in [0, 100]",
        0 <= state.market_alignment <= 100,
        state.market_alignment,
    )

    ma_breakdown = state.market_alignment_breakdown

    check(
        "market alignment breakdown present",
        isinstance(ma_breakdown, dict)
        and {"role_demand",
             "skill_demand",
             "profile_market_match",
             "location_market_fit",
             "weights"} <= set(ma_breakdown),
        ma_breakdown,
    )

    check(
        "market alignment explanation present",
        isinstance(
            state.market_alignment_explanation, list
        )
        and len(
            state.market_alignment_explanation
        )
        > 0,
        state.market_alignment_explanation,
    )

    jobs = career_twin.job_opportunities

    print("\n[STEP 4] Job opportunities:",
          len(jobs), "returned")

    check(
        "job pipeline returned list",
        isinstance(jobs, list),
    )

    if jobs:

        from scoring_utils import (
            is_experience_mismatch,
        )

        for index, job in enumerate(jobs):

            prefix = f"job[{index}]"

            check(
                f"{prefix} has job_score",
                isinstance(
                    job.get("job_score"
                ), (int, float)),
                job.get("job_score"),
            )

            check(
                f"{prefix} has role_similarity",
                isinstance(
                    job.get("role_similarity"
                ), (int, float)),
            )

            check(
                f"{prefix} has experience_match_pct",
                "experience_match_pct" in job
                and (
                    job["experience_match_pct"]
                    is None
                    or (
                        isinstance(
                            job[
                                "experience_match_pct"
                            ],
                            (int, float),
                        )
                        and 0
                        <= job[
                            "experience_match_pct"
                        ]
                        <= 100
                    )
                ),
                job.get("experience_match_pct"),
            )

            check(
                f"{prefix} has location_match_pct",
                "location_match_pct" in job
                and (
                    job["location_match_pct"]
                    is None
                    or (
                        isinstance(
                            job[
                                "location_match_pct"
                            ],
                            (int, float),
                        )
                        and 0
                        <= job[
                            "location_match_pct"
                        ]
                        <= 100
                    )
                ),
                job.get("location_match_pct"),
            )

            check(
                f"{prefix} salary states consistent",
                (
                    job.get("salary_status")
                    == "unknown"
                    and job.get(
                        "salary_match_pct"
                    )
                    is None
                )
                or (
                    job.get("salary_status")
                    in (
                        "match",
                        "partial",
                        "mismatch",
                    )
                    and isinstance(
                        job.get(
                            "salary_match_pct"
                        ),
                        (int, float),
                    )
                ),
                (
                    job.get("salary_status"),
                    job.get("salary_match_pct"),
                ),
            )

            check(
                f"{prefix} no experience hard-filter leak",
                not is_experience_mismatch(
                    "Entry Level",
                    job.get(
                        "experience_level",
                        "Unknown",
                    ),
                ),
                job.get("experience_level"),
            )

            if job.get("role_similarity", 1) < 0.35:

                check(
                    f"{prefix} role-mismatch penalized",
                    job.get("job_score", 100) <= 50,
                    job.get("job_score"),
                )

            check(
                f"{prefix} required_skills extracted",
                len(
                    job.get(
                        "required_skills", []
                    )
                )
                >= 3,
                job.get("required_skills"),
            )

        # Ranking must be descending
        scores = [
            job.get("job_score", 0)
            for job in jobs
        ]

        check(
            "jobs ranked by score desc",
            scores == sorted(
                scores, reverse=True
            ),
            scores,
        )

        # An AI-related job (if present) should outrank
        # an unrelated one
        ai_jobs = [
            job
            for job in jobs
            if job.get("role_similarity", 0) >= 0.7
        ]

        other_jobs = [
            job
            for job in jobs
            if job.get("role_similarity", 1) < 0.35
        ]

        if ai_jobs and other_jobs:

            check(
                "AI jobs outrank mismatched jobs",
                min(
                    job["job_score"]
                    for job in ai_jobs
                )
                > max(
                    job["job_score"]
                    for job in other_jobs
                ),
            )

    # Twin structure
    print("\n[STEP 5] CareerTwin structure")

    check(
        "skills extracted from resume",
        len(career_twin.skills) >= 5,
        len(career_twin.skills),
    )

    check(
        "target_roles populated",
        "AI Engineer"
        in career_twin.target_roles,
        career_twin.target_roles,
    )

    check(
        "strengths reported",
        isinstance(
            state.strengths, list
        )
        and len(state.strengths) > 0,
        state.strengths,
    )

    check(
        "skill_gaps reported",
        isinstance(
            state.skill_gaps, list
        ),
        state.skill_gaps,
    )

    # Serialization (what main.py persists to Mongo)
    try:

        dumped = career_twin.model_dump()

        check(
            "model_dump serializes",
            isinstance(dumped, dict),
        )

        import json

        json.dumps(dumped, default=str)

        check(
            "JSON-serializable for Mongo/API",
            True,
        )

    except Exception as exc:

        check(
            "JSON-serializable for Mongo/API",
            False,
            repr(exc),
        )


# =========================================================
print("\n[STEP 6] FastAPI app")

try:

    import main as main_app

    routes = [
        route.path
        for route in main_app.app.routes
    ]

    print("    routes:", routes)

    check(
        "FastAPI app imported",
        True,
    )

    check(
        "home route present",
        "/" in routes,
    )

    check(
        "preferences route present",
        "/preferences" in routes,
    )

    check(
        "career-twin route present",
        "/career-twin" in routes,
    )

except Exception as exc:

    check(
        "FastAPI app imported",
        False,
        repr(exc),
    )


# =========================================================
print("\n==========================================")

if failures:

    print(f"WORKFLOW FAILED: {len(failures)} check(s)")

    for failure in failures:
        print("  -", failure)

    sys.exit(1)

else:

    print("FULL WORKFLOW: ALL CHECKS PASSED")

print("==========================================")
