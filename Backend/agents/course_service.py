# ============================================================
# Career Digital Twin - Agent 5
# Course Retrieval Service (YouTube)
# ============================================================
#
# Design decision:
# Course retrieval is kept SEPARATE from the LLM.
# This service retrieves real resources (real video IDs,
# real titles, real URLs). The LLM only organizes and
# explains them.
#
# This prevents hallucinated course titles, URLs,
# channel names and durations.
#
# IMPORTANT:
# - Results come from the live YouTube Data API v3.
# - If the API key is missing OR the API is blocked for
#   the key, this service does NOT invent results.
#   It returns an empty list and exposes a YouTube
#   search LINK instead (see resource_service.py).
# - Search results are not automatically full courses.
#   rank_resources() scores how course-like each result
#   is so individual videos can be separated from
#   playlists and complete courses.
# ============================================================

import os
import re

from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

import requests


# ============================================================
# 1. ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# 2. CONFIGURATION
# ============================================================

YOUTUBE_API_URL = (
    "https://www.googleapis.com/youtube/v3/search"
)

YOUTUBE_VIDEOS_URL = (
    "https://www.googleapis.com/youtube/v3/videos"
)

REQUEST_TIMEOUT = 15


# ============================================================
# 3. LEVEL KEYWORDS
# ============================================================
#
# Used both to build the search query and to judge how
# suitable a result is for the learner's level.
# ============================================================

LEVEL_KEYWORDS = {

    "beginner": [
        "beginner",
        "introductory",
        "introduction",
        "basics",
        "fundamentals",
        "for beginners",
        "from scratch",
        "101",
        "primer",
        "getting started",
        "zero to hero"
    ],

    "intermediate": [
        "intermediate",
        "beyond basics",
        "in depth",
        "practical",
        "hands on",
        "projects"
    ],

    "advanced": [
        "advanced",
        "expert",
        "production",
        "scalable",
        "architecture",
        "mastery",
        "professional"
    ]
}


# ============================================================
# 4. COURSE-LIKE KEYWORDS
# ============================================================
#
# Used to distinguish a complete course / playlist from a
# single short video.
# ============================================================

COURSE_KEYWORDS = [
    "full course",
    "complete course",
    "complete tutorial",
    "full tutorial",
    "crash course",
    "bootcamp",
    "masterclass",
    "everything you need to know",
    "step by step",
    "series",
    "playlist",
    "roadmap",
    "course"
]


# ============================================================
# 5. TRUSTED CHANNELS
# ============================================================
#
# Channels widely recognised for high quality technical
# teaching. This is a TRUST SIGNAL used only for ranking.
# It never fabricates a result - it only re-orders real
# results returned by the API.
# ============================================================

TRUSTED_CHANNELS = {

    "freeCodeCamp.org",
    "freeCodeCamp",
    "Corey Schafer",
    "TechWorld with Nana",
    "Program With Mosh",
    "Mosh Hamedani",
    "Traversy Media",
    "Fireship",
    "NetworkChuck",
    "CodeWithHarry",
    "Jenny's Lectures CS IT",
    "Telusko",
    "Andrej Karpathy",
    "StatQuest with Josh Starmer",
    "Sentdex",
    "Programming with Mosh",
    "AWS",
    "Google Cloud",
    "Microsoft Developer",
    "IBM Technology",
    "Simplilearn",
    "Intellipaat",
    "Coursera",
    "edX",
    "Udemy",
    "KodeKloud",
    "Docker",
    "MongoDB",
    "TensorFlow",
    "Hugging Face",
    "Patrick Loeber",
    "NeetCode",
    "take U forward"
}


# ============================================================
# 6. NORMALIZE LEVEL
# ============================================================

def normalize_level(level: str) -> str:

    if not level:
        return "beginner"

    value = str(level).strip().lower()

    if "senior" in value or "advanced" in value:
        return "advanced"

    if "mid" in value or "intermediate" in value:
        return "intermediate"

    # Entry Level / Internship / No Experience all map
    # to beginner - they are the same learning need.

    return "beginner"


# ============================================================
# 7. BUILD SEARCH QUERY
# ============================================================

def build_search_query(
    skill: str,
    level: str = "beginner"
) -> str:

    level = normalize_level(level)

    level_hint = "beginner" if level == "beginner" else level

    return f"{skill} {level_hint} full course tutorial"


# ============================================================
# 8. GET API KEY
# ============================================================

def get_api_key() -> Optional[str]:

    key = os.getenv("YOUTUBE_API_KEY")

    if not key:
        return None

    return key.strip()


# ============================================================
# 9. SEARCH YOUTUBE (LIVE API)
# ============================================================
#
# Returns REAL results from the YouTube Data API v3.
# Never invents a title, URL, channel or duration.
#
# Failure modes return an empty list - the caller falls
# back to a search LINK rather than fabricated results.
# ============================================================

def search_youtube_courses(
    skill: str,
    level: str = "beginner",
    max_results: int = 3
) -> List[Dict[str, Any]]:

    if not skill or not str(skill).strip():

        print(
            "[Course Retrieval] Empty skill, skipping."
        )

        return []

    skill = str(skill).strip()

    level = normalize_level(level)

    api_key = get_api_key()

    if not api_key:

        print(
            "[Course Retrieval] YOUTUBE_API_KEY is "
            "missing from .env - returning no results."
        )

        return []

    params = {

        "part": "snippet",

        "q": build_search_query(skill, level),

        "type": "video",

        "videoEmbeddable": "true",

        "maxResults": max(
            1,
            min(int(max_results or 3), 10)
        ),

        "order": "relevance",

        "relevanceLanguage": "en",

        "safeSearch": "moderate",

        "key": api_key
    }

    try:

        response = requests.get(
            YOUTUBE_API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

    except requests.RequestException as exc:

        print(
            "[Course Retrieval] Request failed:",
            exc
        )

        return []

    # --------------------------------------------------------
    # Non-200 response.
    #
    # A 403 usually means the YouTube Data API v3 is not
    # enabled for the key, or the key is restricted.
    # We log a clear message and return nothing rather than
    # fabricating course data.
    # --------------------------------------------------------

    if response.status_code != 200:

        try:
            message = response.json().get(
                "error", {}
            ).get("message", "Unknown error")
        except ValueError:
            message = response.text[:200]

        print(
            "[Course Retrieval] YouTube API returned",
            response.status_code,
            "-", message
        )

        if response.status_code == 403:

            print(
                "[Course Retrieval] Enable 'YouTube Data "
                "API v3' for this key in Google Cloud "
                "Console, or remove the key restriction."
            )

        return []

    try:
        payload = response.json()
    except ValueError:

        print(
            "[Course Retrieval] Invalid JSON response."
        )

        return []

    items = payload.get("items", [])

    if not items:

        print(
            "[Course Retrieval] No results for",
            skill
        )

        return []

    # --------------------------------------------------------
    # Extract real metadata.
    # --------------------------------------------------------

    results = []

    video_ids = []

    for item in items:

        video_id = (item.get("id") or {}).get("videoId")

        if not video_id:
            continue

        video_ids.append(video_id)

        snippet = item.get("snippet") or {}

        title = str(
            snippet.get("title", "")
        ).strip()

        channel = str(
            snippet.get("channelTitle", "")
        ).strip()

        description = str(
            snippet.get("description", "")
        ).strip()

        published_at = str(
            snippet.get("publishedAt", "")
        ).strip()

        thumbnail = ""

        thumbs = snippet.get("thumbnails") or {}

        for quality in ("high", "medium", "default"):

            if quality in thumbs:
                thumbnail = str(
                    thumbs[quality].get("url", "")
                )
                break

        results.append({

            "platform": "YouTube",

            "video_id": video_id,

            # Canonical URL - built from the real ID, so
            # it can never be a hallucinated link.
            "url": (
                "https://www.youtube.com/watch?v="
                + video_id
            ),

            "title": title,

            "channel": channel,

            "description": description[:400],

            "thumbnail": thumbnail,

            "published_at": published_at,

            "resource_type": "video"
        })

    # --------------------------------------------------------
    # Enrich with real durations and view counts.
    #
    # The search endpoint does not return these, so we make
    # a second call to /videos. This keeps durations REAL
    # instead of guessed.
    # --------------------------------------------------------

    durations = fetch_video_details(
        video_ids,
        api_key
    )

    for result in results:

        detail = durations.get(
            result["video_id"],
            {}
        )

        result["duration"] = detail.get("duration")

        result["duration_text"] = detail.get(
            "duration_text"
        )

        result["view_count"] = detail.get("view_count")

    print(
        "[Course Retrieval] YouTube returned",
        len(results),
        "real results for",
        skill
    )

    return results


# ============================================================
# 10. FETCH VIDEO DETAILS (duration + views)
# ============================================================

def fetch_video_details(
    video_ids: List[str],
    api_key: str
) -> Dict[str, Dict[str, Any]]:

    if not video_ids:
        return {}

    try:

        response = requests.get(
            YOUTUBE_VIDEOS_URL,
            params={

                "part": "contentDetails,statistics",

                "id": ",".join(video_ids),

                "key": api_key
            },
            timeout=REQUEST_TIMEOUT
        )

    except requests.RequestException as exc:

        print(
            "[Course Retrieval] Details request failed:",
            exc
        )

        return {}

    if response.status_code != 200:

        # Duration enrichment is OPTIONAL. If it fails the
        # results are still valid - duration just stays
        # unknown rather than being invented.

        print(
            "[Course Retrieval] Details API returned",
            response.status_code,
            "- durations left unknown."
        )

        return {}

    try:
        items = response.json().get("items", [])
    except ValueError:
        return {}

    details = {}

    for item in items:

        video_id = item.get("id")

        if not video_id:
            continue

        duration_iso = (
            (item.get("contentDetails") or {})
            .get("duration", "")
        )

        views = (
            (item.get("statistics") or {})
            .get("viewCount")
        )

        details[video_id] = {

            "duration": duration_iso,

            "duration_text":
                parse_iso_duration(duration_iso),

            "view_count":
                int(views) if views else None
        }

    return details


# ============================================================
# 11. PARSE ISO 8601 DURATION
# ============================================================
#
# PT4H20M15S -> "4h 20m"
# PT18M30S   -> "18m"
# ============================================================

def parse_iso_duration(value: str) -> Optional[str]:

    if not value:
        return None

    match = re.match(
        r"^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?$",
        str(value).strip()
    )

    if not match:
        return None

    hours, minutes, seconds = match.groups()

    parts = []

    if hours:
        parts.append(f"{hours}h")

    if minutes:
        parts.append(f"{minutes}m")

    if not hours and not minutes and seconds:
        parts.append(f"{seconds}s")

    return " ".join(parts) if parts else None


# ============================================================
# 11B. DERIVE A CONCISE SEARCH TERM
# ============================================================
#
# Skill Gaps often describe a requirement as a full phrase,
# e.g.
#   "Comfort working in a Linux/Unix command-line
#    environment"
#   "Basic knowledge of version control systems (Git)..."
#
# Searching YouTube for the whole sentence gives poor
# results. This function extracts the CONCISE skill name so
# the search returns relevant courses.
# ============================================================

# Ordered longest first so "machine learning" wins over
# the single words "machine" / "learning".

KNOWN_SKILL_TERMS = sorted(

    {

        "machine learning", "deep learning",
        "natural language processing", "large language models",
        "data structures", "algorithms",
        "object oriented design", "object oriented programming",
        "unit testing", "testing frameworks", "version control",
        "command line", "rest apis", "rest api", "rest",
        "http", "https", "authentication", "security",
        "object-oriented design", "ci/cd", "cicd",
        "linux", "unix", "bash", "shell", "git", "github",
        "python", "java", "golang", "go", "node.js", "nodejs",
        "javascript", "typescript", "sql", "postgresql",
        "mysql", "mongodb", "redis", "docker", "kubernetes",
        "fastapi", "flask", "django", "react", "graphql",
        "aws", "azure", "gcp", "cloud", "pandas", "numpy",
        "scikit-learn", "tensorflow", "pytorch", "langchain",
        "langgraph", "llm", "rag", "prompt engineering",
        "microservices", "system design", "design patterns",
        "oop", "data analysis", "data structures and algorithms"
    },

    key=len,

    reverse=True
)

# Words that carry no search value on their own.
FILLER_WORDS = {

    "a", "an", "the", "of", "in", "on", "to", "and", "or",
    "for", "with", "at", "by", "from", "is", "are", "be",
    "ability", "able", "comfort", "comfortable", "working",
    "knowledge", "understanding", "familiarity", "proficiency",
    "basic", "solid", "strong", "good", "least", "one",
    "write", "execute", "collaborative", "workflows",
    "environment", "concepts", "e.g", "eg", "such", "systems",
    "commandline", "command", "line", "protocols", "status",
    "codes", "least", "leastone"
}


# Canonical display names so search terms and titles keep
# the correct product casing ("FastAPI", not "Fastapi").

CANONICAL_NAMES = {

    "fastapi": "FastAPI",

    "node.js": "Node.js",

    "nodejs": "Node.js",

    "react": "React",

    "react.js": "React.js",

    "typescript": "TypeScript",

    "javascript": "JavaScript",

    "postgresql": "PostgreSQL",

    "postgres": "PostgreSQL",

    "mysql": "MySQL",

    "mongodb": "MongoDB",

    "kubernetes": "Kubernetes",

    "docker": "Docker",

    "graphql": "GraphQL",

    "rest apis": "REST APIs",

    "rest api": "REST API",

    "ci/cd": "CI/CD",

    "cicd": "CI/CD",

    "llm": "LLM",

    "large language models":
        "Large Language Models",

    "rag": "RAG",

    "langchain": "LangChain",

    "langgraph": "LangGraph",

    "scikit-learn": "Scikit-learn",

    "pandas": "Pandas",

    "numpy": "NumPy",

    "pytorch": "PyTorch",

    "tensorflow": "TensorFlow",

    "golang": "Go",

    "oop": "OOP",

    "http": "HTTP",

    "https": "HTTPS",

    "aws": "AWS",

    "gcp": "GCP",

    "ai": "AI",

    "ml": "ML",

    "nlp": "NLP",

    "bash": "Bash",

    "linux": "Linux",

    "unix": "Unix",

    "git": "Git",

    "github": "GitHub",

    "python": "Python",

    "java": "Java",

    "sql": "SQL",

    "redis": "Redis",

    "flask": "Flask",

    "django": "Django",

    "azure": "Azure"
}


def apply_canonical_names(term: str) -> str:
    """Restore proper product casing in a search term."""

    tokens = term.split()

    fixed = []

    for token in tokens:

        key = token.lower().strip()

        fixed.append(
            CANONICAL_NAMES.get(key, token)
        )

    return " ".join(fixed)


def derive_search_term(skill: str) -> str:
    """Turn a requirement phrase into a concise search term."""

    if not skill:
        return ""

    text = str(skill).strip()

    text = text.replace("\u2011", "-").replace(
        "\u2013", "-"
    )

    lowered = text.lower()

    # Normalised text used only for position matching, so
    # hyphenated forms like "command-line" still match the
    # "command line" term.

    searchable = lowered.replace("-", " ")

    found = []

    # Collect known skill terms that appear in the phrase,
    # remembering WHERE each one appears so the final term
    # keeps the order the requirement used.

    for term in KNOWN_SKILL_TERMS:

        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(term).replace(r"\ ", r"[ \-]+")
            + r"(?![a-z0-9])"
        )

        match = re.search(pattern, searchable)

        if match:

            if term not in [item[1] for item in found]:

                found.append(
                    (match.start(), term)
                )

    if found:

        # Keep the order the requirement used, then take
        # the first two - more dilutes search relevance.

        found.sort(key=lambda item: item[0])

        joined = " ".join(
            term for _, term in found[:2]
        )

        return apply_canonical_names(joined.title())

    # No known skill - strip filler words and keep the
    # first few meaningful words.

    tokens = re.findall(r"[a-zA-Z0-9+#.]+", text)

    meaningful = [
        token for token in tokens
        if token.lower() not in FILLER_WORDS
        and len(token) > 2
    ]

    if meaningful:

        return apply_canonical_names(
            " ".join(meaningful[:3])
        )

    return text[:60]


# ============================================================
# 12. RESOURCE RANKING
# ============================================================
#
# Scores REAL results on:
#   - Topic relevance      (skill named in title)
#   - Level suitability    (matches beginner/advanced)
#   - Course coverage      (full course vs single video)
#   - Provider trust       (known teaching channel)
#   - Accessibility        (free, embeddable, has duration)
#
# Returns the results re-ordered by score, best first.
# ============================================================

def rank_resources(
    resources: List[Dict[str, Any]],
    skill: str,
    level: str = "beginner"
) -> List[Dict[str, Any]]:

    if not resources:
        return []

    skill = (skill or "").strip()

    skill_lower = skill.lower()

    skill_tokens = set(
        re.findall(r"[a-z0-9+#]+", skill_lower)
    )

    level = normalize_level(level)

    level_terms = LEVEL_KEYWORDS.get(
        level,
        LEVEL_KEYWORDS["beginner"]
    )

    # Another level's keywords count as a small penalty,
    # not a hard rejection - a good resource may not name
    # the level at all.

    other_terms = []

    for name, terms in LEVEL_KEYWORDS.items():

        if name != level:
            other_terms.extend(terms)

    ranked = []

    for resource in resources:

        title = str(
            resource.get("title", "")
        ).lower()

        channel = str(
            resource.get("channel", "")
        ).strip()

        resource_type = str(
            resource.get("resource_type", "video")
        )

        title_tokens = set(
            re.findall(r"[a-z0-9+#]+", title)
        )

        score = 0.0

        reasons = []

        # ----------------------------------------------
        # 1. TOPIC RELEVANCE (0-40)
        # ----------------------------------------------

        if skill_lower and skill_lower in title:

            score += 30

            reasons.append("Skill named in title")

        elif skill_tokens and (
            skill_tokens & title_tokens
        ):

            overlap = len(
                skill_tokens & title_tokens
            )

            score += min(overlap * 12, 24)

            reasons.append("Skill keywords in title")

        else:

            score += 5

        # ----------------------------------------------
        # 2. LEVEL SUITABILITY (0-20)
        # ----------------------------------------------

        matched_levels = [
            term for term in level_terms
            if term in title
        ]

        if matched_levels:

            score += 16

            reasons.append(
                f"Marked {level}"
            )

        penalized = [
            term for term in other_terms
            if term in title
        ]

        if penalized and not matched_levels:

            score -= 8

            reasons.append("Level may not match")

        # ----------------------------------------------
        # 3. COURSE COVERAGE (0-25)
        # ----------------------------------------------

        course_hits = [
            term for term in COURSE_KEYWORDS
            if term in title
        ]

        if course_hits:

            score += min(len(course_hits) * 8, 20)

            if "playlist" in course_hits:

                resource_type = "playlist"

                reasons.append("Full playlist")

            else:

                reasons.append("Complete course")

        if resource_type == "playlist":

            score += 5

        # ----------------------------------------------
        # 4. PROVIDER TRUST (0-10)
        # ----------------------------------------------

        if channel in TRUSTED_CHANNELS:

            score += 10

            reasons.append(
                f"Trusted channel ({channel})"
            )

        # ----------------------------------------------
        # 5. ACCESSIBILITY / POPULARITY (0-10)
        # ----------------------------------------------

        views = resource.get("view_count")

        if isinstance(views, int) and views > 0:

            if views >= 500_000:
                score += 8
            elif views >= 100_000:
                score += 6
            elif views >= 20_000:
                score += 4
            elif views >= 1_000:
                score += 2

        if resource.get("duration"):
            score += 2

        resource = dict(resource)

        resource["resource_type"] = resource_type

        resource["relevance_score"] = round(
            max(score, 0.0),
            2
        )

        resource["ranking_reasons"] = reasons

        ranked.append(resource)

    ranked.sort(
        key=lambda item: item.get(
            "relevance_score",
            0
        ),
        reverse=True
    )

    return ranked


# ============================================================
# 13. GET RANKED COURSES
# ============================================================
#
# Convenience wrapper: search AND rank in one call.
# This is what the roadmap agent uses per skill.
# ============================================================

def get_ranked_courses(
    skill: str,
    level: str = "beginner",
    max_results: int = 3
) -> List[Dict[str, Any]]:

    # Retrieve MORE than we return, so ranking has a real
    # choice and the top N are genuinely the best.

    raw = search_youtube_courses(
        skill=skill,
        level=level,
        max_results=10
    )

    ranked = rank_resources(
        raw,
        skill=skill,
        level=level
    )

    return ranked[: max(1, int(max_results or 3))]
