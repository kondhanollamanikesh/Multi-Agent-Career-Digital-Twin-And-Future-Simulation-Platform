# ============================================================
# Career Digital Twin - Agent 5
# Resource Service (Platform Search Links)
# ============================================================
#
# Providers without an authorized catalog API are handled
# with their public SEARCH pages.
#
# These links are FALLBACKS - they let the learner browse
# what exists right now. They are NOT proof that a specific
# course exists, and no course title, URL or duration is
# invented for them.
#
# For providers you later integrate through an authorized
# catalog, return individual course titles and DIRECT course
# URLs instead of a search link.
#
# IMPORTANT:
# - Official documentation links are curated and verified,
#   not LLM generated.
# - Search links are built from a real URL template with the
#   skill name URL-encoded, so they always resolve to a real
#   search page on the provider's site.
# ============================================================

import os
import re

from typing import List, Dict, Any, Optional

from urllib.parse import quote_plus


# ============================================================
# 1. PLATFORM SEARCH URL TEMPLATES
# ============================================================

PLATFORM_SEARCH_TEMPLATES = {

    "Coursera":
        "https://www.coursera.org/search?query={skill}",

    "edX":
        "https://www.edx.org/search?q={skill}",

    "Udemy":
        (
            "https://www.udemy.com/courses/search/"
            "?q={skill}"
        ),

    "YouTube":
        (
            "https://www.youtube.com/results?"
            "search_query={skill}+full+course"
        ),

    "Google Documentation":
        (
            "https://www.google.com/search?q="
            "{skill}+official+documentation"
        )
}


# ============================================================
# 2. PLATFORM DESCRIPTIONS
# ============================================================

PLATFORM_DESCRIPTIONS = {

    "Coursera":
        "Structured university courses and certificates",

    "edX":
        "University and professional courses",

    "Udemy":
        "Practical paid and free project based courses",

    "YouTube":
        "Free video tutorials and playlists",

    "Google Documentation":
        "Verified official documentation"
}


# ============================================================
# 3. OFFICIAL DOCUMENTATION (CURATED)
# ============================================================
#
# Verified official docs for skills this platform is most
# likely to recommend. Skills outside this map fall back to
# a documentation search link.
# ============================================================

OFFICIAL_DOCUMENTATION = {

    "python":
        "https://docs.python.org/3/",

    "fastapi":
        "https://fastapi.tiangolo.com/",

    "django":
        "https://docs.djangoproject.com/",

    "flask":
        "https://flask.palletsprojects.com/",

    "docker":
        "https://docs.docker.com/",

    "kubernetes":
        "https://kubernetes.io/docs/home/",

    "git":
        "https://git-scm.com/doc",

    "github":
        "https://docs.github.com/",

    "postgresql":
        "https://www.postgresql.org/docs/",

    "mysql":
        "https://dev.mysql.com/doc/",

    "mongodb":
        "https://www.mongodb.com/docs/",

    "redis":
        "https://redis.io/docs/latest/",

    "sql":
        "https://www.w3schools.com/sql/",

    "javascript":
        "https://developer.mozilla.org/en-US/docs/Web/JavaScript",

    "typescript":
        "https://www.typescriptlang.org/docs/",

    "react":
        "https://react.dev/learn",

    "react.js":
        "https://react.dev/learn",

    "node.js":
        "https://nodejs.org/en/learn",

    "express.js":
        "https://expressjs.com/",

    "aws":
        "https://docs.aws.amazon.com/",

    "azure":
        "https://learn.microsoft.com/azure/",

    "gcp":
        "https://cloud.google.com/docs",

    "google cloud":
        "https://cloud.google.com/docs",

    "linux":
        "https://www.kernel.org/doc/html/latest/",

    "bash":
        "https://www.gnu.org/software/bash/manual/",

    "html":
        "https://developer.mozilla.org/en-US/docs/Web/HTML",

    "css":
        "https://developer.mozilla.org/en-US/docs/Web/CSS",

    "pandas":
        "https://pandas.pydata.org/docs/",

    "numpy":
        "https://numpy.org/doc/",

    "scikit-learn":
        "https://scikit-learn.org/stable/",

    "tensorflow":
        "https://www.tensorflow.org/",

    "pytorch":
        "https://pytorch.org/docs/stable/",

    "langchain":
        "https://python.langchain.com/",

    "langgraph":
        "https://langchain-ai.github.io/langgraph/",

    "pydantic":
        "https://docs.pydantic.dev/",

    "graphql":
        "https://graphql.org/learn/",

    "nginx":
        "https://nginx.org/en/docs/",

    "terraform":
        "https://developer.hashicorp.com/terraform/docs",

    "jenkins":
        "https://www.jenkins.io/doc/",

    "prometheus":
        "https://prometheus.io/docs/introduction/overview/"
}


# ============================================================
# 4. SEARCH LINKS FOR A SKILL
# ============================================================

def platform_search_links(
    skill: str
) -> List[Dict[str, str]]:

    if not skill or not str(skill).strip():

        return []

    skill = str(skill).strip()

    query = quote_plus(skill)

    links = []

    for platform, template in (
        PLATFORM_SEARCH_TEMPLATES.items()
    ):

        links.append({

            "platform": platform,

            # Built from a real, current URL template.
            "url": template.format(skill=query),

            "type": "search_link",

            "description":
                PLATFORM_DESCRIPTIONS.get(
                    platform,
                    ""
                )
        })

    return links


# ============================================================
# 5. OFFICIAL DOCUMENTATION LINK
# ============================================================

def official_documentation_link(
    skill: str
) -> Optional[Dict[str, str]]:

    if not skill or not str(skill).strip():

        return None

    skill = str(skill).strip()

    key = skill.lower().strip()

    # 1. Exact match.
    url = OFFICIAL_DOCUMENTATION.get(key)

    # 2. Requirement phrases often contain the real skill
    #    name, e.g. "Comfort working in a Linux/Unix
    #    command-line environment". Scan for the skill
    #    mentioned FIRST in the text so verified docs still
    #    surface. Word boundaries stop "sql" matching inside
    #    "sqlite" style false positives.

    if not url:

        best_key = None

        best_position = None

        for candidate in OFFICIAL_DOCUMENTATION:

            pattern = (
                r"(?<![a-z0-9])"
                + re.escape(candidate)
                + r"(?![a-z0-9])"
            )

            match = re.search(pattern, key)

            if match:

                position = match.start()

                # Earliest mention wins. On a tie the
                # longer, more specific term wins.

                if (
                    best_position is None
                    or position < best_position
                    or (
                        position == best_position
                        and len(candidate)
                        > len(best_key)
                    )
                ):

                    best_position = position

                    best_key = candidate

        if best_key:

            url = OFFICIAL_DOCUMENTATION[best_key]

            key = best_key

    if url:

        return {

            "platform": "Official documentation",

            "url": url,

            "type": "official_documentation",

            "description": (
                f"Official {skill} documentation"
            ),

            "verified": True
        }

    # Unknown skill - fall back to a documentation search
    # rather than guessing a documentation URL.

    query = quote_plus(skill)

    return {

        "platform": "Documentation search",

        "url": (
            "https://www.google.com/search?q="
            + query
            + "+official+documentation"
        ),

        "type": "documentation_search",

        "description": (
            f"Find the official {skill} documentation"
        ),

        "verified": False
    }


# ============================================================
# 6. ALL RESOURCES FOR A SKILL
# ============================================================
#
# Combines live YouTube results (already ranked) with the
# platform search links and verified documentation.
#
# This is the single function the roadmap agent and the
# /learning-resources endpoint call.
# ============================================================

def gather_resources(
    skill: str,
    level: str = "beginner",
    max_youtube: int = 2
) -> Dict[str, Any]:

    # Imported here so this module works even if the
    # YouTube service is unavailable.

    from agents.course_service import (
        get_ranked_courses,
        derive_search_term
    )

    skill = (skill or "").strip()

    # Requirement phrases are turned into a concise search
    # term so provider search returns relevant courses
    # instead of nothing.

    search_term = derive_search_term(skill) or skill

    try:

        youtube_resources = get_ranked_courses(
            skill=search_term,
            level=level,
            max_results=max_youtube
        )

    except Exception as exc:

        # Never let a retrieval failure break the roadmap.
        # The platform links below still work.

        print(
            "[Resource Service] YouTube retrieval "
            "failed:",
            exc
        )

        youtube_resources = []

    # Only mark results as "retrieved live" when they
    # really came from the API.

    for resource in youtube_resources:

        resource["source"] = "live_search"

    return {

        "skill": skill,

        "search_term": search_term,

        "level": level,

        "youtube_resources": youtube_resources,

        "documentation":
            official_documentation_link(skill),

        "platform_links":
            platform_search_links(search_term)
    }
