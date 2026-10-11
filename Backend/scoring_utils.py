# ==========================================
# Shared scoring utilities for Career
# Digital Twin (readiness / market /
# job matching).
# ==========================================

import re

from typing import List, Optional, Tuple, Dict, Any


# ==========================================
# 1. EXPERIENCE LEVELS
# ==========================================

EXPERIENCE_ORDER = [
    "No Experience",
    "Internship",
    "Entry Level",
    "Mid Level",
    "Senior",
    "Executive",
]

EXPERIENCE_ALIASES = {
    "no experience": "No Experience",
    "no exp": "No Experience",
    "no professional experience": "No Experience",
    "without experience": "No Experience",
    "no work experience": "No Experience",
    "fresher": "No Experience",

    "intern": "Internship",
    "internship": "Internship",
    "trainee": "Internship",

    "entry": "Entry Level",
    "entry level": "Entry Level",
    "entry-level": "Entry Level",
    "junior": "Entry Level",
    "jr": "Entry Level",
    "associate": "Entry Level",
    "graduate": "Entry Level",
    "new grad": "Entry Level",
    "beginner": "Entry Level",

    "mid": "Mid Level",
    "mid level": "Mid Level",
    "mid-level": "Mid Level",
    "middle": "Mid Level",
    "intermediate": "Mid Level",

    "senior": "Senior",
    "sr": "Senior",
    "sr.": "Senior",
    "lead": "Senior",
    "principal": "Senior",
    "staff": "Senior",
    "manager": "Senior",
    "architect": "Senior",

    "executive": "Executive",
    "director": "Executive",
    "head": "Executive",
    "head of": "Executive",
    "vp": "Executive",
    "vice president": "Executive",
    "chief": "Executive",
}


def normalize_experience_level(
    level: Optional[str]
) -> str:
    """Canonicalize an experience level label."""

    if not level:
        return "Unknown"

    key = str(level).strip().lower()

    if not key:
        return "Unknown"

    if key in EXPERIENCE_ALIASES:
        return EXPERIENCE_ALIASES[key]

    for alias, canonical in EXPERIENCE_ALIASES.items():

        if alias in key:
            return canonical

    for known in EXPERIENCE_ORDER:

        if known.lower() in key:
            return known

    return "Unknown"


def _experience_index(level: str) -> Optional[int]:

    canonical = normalize_experience_level(level)

    if canonical == "Unknown":
        return None

    return EXPERIENCE_ORDER.index(canonical)


def detect_experience_level(
    text: str,
    from_description: bool = False
) -> str:
    """Detect the seniority implied by a job title or
    description snippet.

    from_description=True only trusts strong signals
    (years of experience), because casual words like
    'lead' or 'head' appear in descriptions without
    meaning the role is senior.
    """

    if not text:
        return "Unknown"

    lowered = text.lower()

    if not from_description:

        # ---------------------------------------------
        # 1. Executive signals (titles)
        # ---------------------------------------------

        executive_patterns = [
            r"\bchief\b",
            r"\bvp\b",
            r"\bvice president\b",
            r"\bdirector\b",
            r"\bhead of\b",
            r"^head\b",
        ]

        for pattern in executive_patterns:

            if re.search(pattern, lowered):
                return "Executive"

        # ---------------------------------------------
        # 2. Senior signals (titles)
        # ---------------------------------------------

        senior_patterns = [
            r"\bsenior\b",
            r"\bsr\.?\b",
            r"\blead\b",
            r"\bprincipal\b",
            r"\bstaff\b",
            r"\bmanager\b",
            r"\barchitect\b",
        ]

        for pattern in senior_patterns:

            if re.search(pattern, lowered):
                return "Senior"

        # ---------------------------------------------
        # 3. Entry signals (titles)
        # ---------------------------------------------

        entry_patterns = [
            r"\bjunior\b",
            r"\bjr\.?\b",
            r"\bentry[- ]level\b",
            r"\bentry level\b",
            r"\bassociate\b",
            r"\bgraduate\b",
            r"\bnew grad\b",
            r"\bfresher\b",
            r"\bintern\b",
            r"\binternship\b",
            r"\btrainee\b",
        ]

        for pattern in entry_patterns:

            if re.search(pattern, lowered):
                return "Entry Level"

    # ---------------------------------------------
    # 4. Years of experience signals
    #    (trusted in titles AND descriptions)
    # ---------------------------------------------

    year_matches = re.findall(
        r"(\d+)\s*(?:\+|to|-|–)?\s*(?:\d+)?\s*"
        r"(?:years?|yrs?)\b",
        lowered
    )

    if year_matches:

        max_years = max(
            int(value)
            for value in year_matches
        )

        if max_years >= 5:
            return "Senior"

        if max_years >= 2:
            return "Mid Level"

        return "Entry Level"

    if from_description:
        return "Unknown"

    # ---------------------------------------------
    # 5. Mid-level signals (titles)
    # ---------------------------------------------

    mid_patterns = [
        r"\bmid[- ]level\b",
        r"\bmid level\b",
        r"\bintermediate\b",
    ]

    for pattern in mid_patterns:

        if re.search(pattern, lowered):
            return "Mid Level"

    return "Unknown"


# ---------------------------------------------
# Categorical experience match table.
#
# Unknown is NEVER given a numeric score.
# (candidate, job) -> match in 0.0 - 1.0
# ---------------------------------------------

EXPERIENCE_MATCH_TABLE = {

    # ---------------- No Experience ----------------

    ("No Experience", "No Experience"): 1.0,
    ("No Experience", "Internship"): 1.0,
    ("No Experience", "Entry Level"): 1.0,
    ("No Experience", "Mid Level"): 0.5,
    ("No Experience", "Senior"): 0.0,
    ("No Experience", "Executive"): 0.0,

    # ---------------- Internship ----------------

    ("Internship", "No Experience"): 1.0,
    ("Internship", "Internship"): 1.0,
    ("Internship", "Entry Level"): 1.0,
    ("Internship", "Mid Level"): 0.5,
    ("Internship", "Senior"): 0.0,
    ("Internship", "Executive"): 0.0,

    # ---------------- Entry Level ----------------

    ("Entry Level", "No Experience"): 1.0,
    ("Entry Level", "Internship"): 1.0,
    ("Entry Level", "Entry Level"): 1.0,
    ("Entry Level", "Mid Level"): 0.6,
    ("Entry Level", "Senior"): 0.1,
    ("Entry Level", "Executive"): 0.0,

    # ---------------- Mid Level ----------------

    ("Mid Level", "No Experience"): 0.7,
    ("Mid Level", "Internship"): 0.7,
    ("Mid Level", "Entry Level"): 0.7,
    ("Mid Level", "Mid Level"): 1.0,
    ("Mid Level", "Senior"): 0.6,
    ("Mid Level", "Executive"): 0.4,

    # ---------------- Senior ----------------

    ("Senior", "No Experience"): 0.5,
    ("Senior", "Internship"): 0.5,
    ("Senior", "Entry Level"): 0.5,
    ("Senior", "Mid Level"): 0.7,
    ("Senior", "Senior"): 1.0,
    ("Senior", "Executive"): 0.7,

    # ---------------- Executive ----------------

    ("Executive", "No Experience"): 0.3,
    ("Executive", "Internship"): 0.3,
    ("Executive", "Entry Level"): 0.3,
    ("Executive", "Mid Level"): 0.5,
    ("Executive", "Senior"): 0.7,
    ("Executive", "Executive"): 1.0,
}


def experience_score(
    candidate_level: Optional[str],
    job_level: Optional[str]
) -> Optional[float]:
    """Categorical experience match in 0.0 - 1.0.

    Returns None when either level is unknown so that
    missing data is excluded from weighted scores
    instead of being given a generous 0.7 fallback.
    """

    candidate = normalize_experience_level(
        candidate_level
    )

    job = normalize_experience_level(job_level)

    if candidate == "Unknown" or job == "Unknown":
        return None

    key = (candidate, job)

    if key in EXPERIENCE_MATCH_TABLE:
        return EXPERIENCE_MATCH_TABLE[key]

    # Fallback for unlisted pairs: distance based.

    difference = abs(
        EXPERIENCE_ORDER.index(candidate)
        - EXPERIENCE_ORDER.index(job)
    )

    if difference == 0:
        return 1.0

    if difference == 1:
        return 0.7

    return 0.1


def is_experience_mismatch(
    candidate_level: Optional[str],
    job_level: Optional[str]
) -> bool:
    """Hard-filter helper.

    Reject only truly hopeless gaps (categorical match
    of 0.1 or less). Unknown levels never hard-filter.
    """

    match = experience_score(
        candidate_level,
        job_level
    )

    if match is None:
        return False

    return match <= 0.1


# ==========================================
# 2. ROLE SIMILARITY
# ==========================================

ROLE_SYNONYM_GROUPS = [
    {
        "ai engineer",
        "artificial intelligence engineer",
        "ai developer",
        "machine learning engineer",
        "ml engineer",
        "ai/ml engineer",
        "ai ml engineer",
        "generative ai engineer",
        "genai engineer",
        "llm engineer",
        "nlp engineer",
    },
    {
        "software engineer",
        "software developer",
        "swe",
    },
    {
        "backend engineer",
        "backend developer",
        "backend",
    },
    {
        "frontend engineer",
        "frontend developer",
        "frontend",
    },
    {
        "full stack engineer",
        "full-stack engineer",
        "full stack developer",
        "full-stack developer",
        "fullstack developer",
    },
    {
        "data scientist",
        "data science engineer",
    },
    {
        "product manager",
        "product owner",
        "pm",
    },
    {
        "crm manager",
        "crm marketing manager",
        "lifecycle marketing manager",
    },
]

ROLE_FAMILY_KEYWORDS = {

    "ai_ml": [
        "ai engineer",
        "artificial intelligence",
        "machine learning",
        "ml engineer",
        "deep learning",
        "nlp",
        "natural language",
        "llm",
        "genai",
        "generative ai",
        "data scientist",
        "data science",
        "computer vision",
        "mlops",
        "prompt engineer",
        "ai/ml",
        " ai ",
    ],

    "software": [
        "software engineer",
        "software developer",
        "backend",
        "frontend",
        "full stack",
        "fullstack",
        "web developer",
        "mobile developer",
        "devops",
        "sre",
        "engineer",
        "developer",
        "architect",
    ],

    "data": [
        "data engineer",
        "data analyst",
        "analytics",
        "business intelligence",
        "etl",
        "database",
    ],

    "product": [
        "product manager",
        "product owner",
        "product management",
        "product lead",
        "product ",
        "platform product",
    ],

    "marketing": [
        "marketing",
        "crm",
        "lifecycle",
        "email marketing",
        "growth",
        "brand",
        "demand gen",
        "seo",
        "campaign",
        "content",
    ],

    "sales": [
        "sales",
        "account executive",
        "business development",
        "sdr",
        "bdr",
        "revenue",
        "pre-sales",
        "presales",
        "solutions consultant",
    ],

    "management": [
        "manager",
        "director",
        "head of",
        "vp ",
        "chief",
        "lead",
    ],
}

ROLE_TOKEN_STOPWORDS = {
    "senior",
    "junior",
    "sr",
    "jr",
    "the",
    "of",
    "and",
    "for",
    "with",
    "a",
    "an",
    "in",
    "at",
    "to",
    "role",
    "position",
    "job",
    "experience",
    "specialist",
    "executive",
}


def _normalize_role_text(text: str) -> str:

    value = str(text or "").lower().strip()

    value = re.sub(
        r"[^a-z0-9+#./\-\s]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


def _role_tokens(text: str) -> set:

    tokens = set(
        re.findall(r"[a-z0-9+#./\-]+", text)
    )

    return {
        token
        for token in tokens
        if token not in ROLE_TOKEN_STOPWORDS
        and len(token) > 1
    }


def _detect_role_families(text: str) -> set:

    families = set()

    for family, keywords in ROLE_FAMILY_KEYWORDS.items():

        for keyword in keywords:

            if len(keyword.strip()) <= 3:

                if re.search(
                    r"\b"
                    + re.escape(keyword.strip())
                    + r"\b",
                    text
                ):
                    families.add(family)
                    break

            else:

                if keyword in text:
                    families.add(family)
                    break

    return families


def role_similarity(
    target_role: str,
    job_title: str,
    job_description: str = ""
) -> float:
    """Lexical role relevance between the candidate's
    target role and a job title (with a small description
    signal). Returns 0.0 - 1.0."""

    target = _normalize_role_text(target_role)
    title = _normalize_role_text(job_title)

    if not target or not title:
        return 0.0

    if target == title:
        return 1.0

    # ---------------------------------------------
    # Synonym groups (near-identical roles)
    # ---------------------------------------------

    for group in ROLE_SYNONYM_GROUPS:

        if target in group and title in group:
            return 0.95

    target_tokens = _role_tokens(target)
    title_tokens = _role_tokens(title)

    union = target_tokens | title_tokens

    overlap = (
        len(target_tokens & title_tokens)
        / len(union)
        if union
        else 0.0
    )

    target_families = _detect_role_families(target)
    title_families = _detect_role_families(title)

    shared_families = (
        target_families & title_families
    )

    # ---------------------------------------------
    # Primary score: family overlap + token overlap
    # ---------------------------------------------

    if shared_families:

        score = 0.70 + 0.30 * overlap

    else:

        score = 0.55 * overlap

    # ---------------------------------------------
    # Description signal (small modifier only)
    # ---------------------------------------------

    if job_description and target_families:

        description_snippet = (
            job_description.lower()[:2500]
        )

        primary_families = (
            target_families - {"management"}
            or target_families
        )

        hits = 0

        for family in primary_families:

            for keyword in ROLE_FAMILY_KEYWORDS[family]:

                if len(keyword.strip()) <= 3:

                    if re.search(
                        r"\b"
                        + re.escape(keyword.strip())
                        + r"\b",
                        description_snippet
                    ):
                        hits += 1

                else:

                    if keyword in description_snippet:
                        hits += 1

        if hits >= 4:
            score += 0.10
        elif hits >= 2:
            score += 0.05

    return max(0.0, min(1.0, score))


# ==========================================
# 3. PREFERENCE MATCH SCORES
# ==========================================

# ---------------------------------------------
# Country / city resolution helpers.
#
# Needed so "USA" vs "Hyderabad, Telangana"
# is recognised as a cross-country mismatch
# instead of receiving a soft partial score.
# ---------------------------------------------

COUNTRY_ALIASES = {

    "united states": "usa",
    "united states of america": "usa",
    "usa": "usa",
    "u.s.a": "usa",
    "america": "usa",

    "united kingdom": "uk",
    "great britain": "uk",
    "england": "uk",
    "uk": "uk",

    "india": "india",

    "canada": "canada",
    "australia": "australia",
    "germany": "germany",
    "netherlands": "netherlands",
    "ireland": "ireland",
    "france": "france",
    "spain": "spain",
    "poland": "poland",
    "portugal": "portugal",
    "sweden": "sweden",
    "switzerland": "switzerland",
    "singapore": "singapore",
    "japan": "japan",
    "china": "china",
    "uae": "uae",
    "united arab emirates": "uae",
    "dubai": "uae",
    "saudi arabia": "saudi arabia",
    "brazil": "brazil",
    "mexico": "mexico",

}

CITY_COUNTRY = {

    # India
    "hyderabad": "india",
    "bangalore": "india",
    "bengaluru": "india",
    "chennai": "india",
    "coimbatore": "india",
    "pune": "india",
    "mumbai": "india",
    "bombay": "india",
    "delhi": "india",
    "new delhi": "india",
    "gurgaon": "india",
    "gurugram": "india",
    "noida": "india",
    "kolkata": "india",
    "calcutta": "india",
    "ahmedabad": "india",
    "jaipur": "india",
    "indore": "india",
    "kochi": "india",
    "cochin": "india",
    "trivandrum": "india",
    "vizag": "india",

    # USA
    "new york": "usa",
    "san francisco": "usa",
    "seattle": "usa",
    "austin": "usa",
    "boston": "usa",
    "chicago": "usa",
    "los angeles": "usa",
    "denver": "usa",
    "atlanta": "usa",
    "dallas": "usa",
    "houston": "usa",
    "san jose": "usa",
    "sunnyvale": "usa",
    "mountain view": "usa",
    "palo alto": "usa",
    "remote": None,

    # Others
    "london": "uk",
    "manchester": "uk",
    "edinburgh": "uk",
    "toronto": "canada",
    "vancouver": "canada",
    "montreal": "canada",
    "berlin": "germany",
    "munich": "germany",
    "frankfurt": "germany",
    "amsterdam": "netherlands",
    "dublin": "ireland",
    "paris": "france",
    "madrid": "spain",
    "warsaw": "poland",
    "lisbon": "portugal",
    "stockholm": "sweden",
    "zurich": "switzerland",
    "singapore": "singapore",
    "tokyo": "japan",
    "shanghai": "china",
    "shenzhen": "china",

}

_LOCATION_NOISE = {
    "remote",
    "worldwide",
    "anywhere",
    "global",
    "world wide",
    "hybrid",
    "onsite",
    "on-site",
    "work from home",
    "wfh",
}


def _word_in_text(word: str, text: str) -> bool:
    """Word-boundary containment."""

    if not word or not text:
        return False

    return re.search(
        r"(?<![a-z0-9])"
        + re.escape(word)
        + r"(?![a-z0-9])",
        text
    ) is not None


def resolve_location_country(
    value: Optional[str]
) -> Optional[str]:
    """Best-effort country resolution from a free-form
    location string. Returns None when unknown."""

    text = str(value or "").lower().strip()

    if not text:
        return None

    if text in _LOCATION_NOISE:
        return None

    for alias in sorted(
        COUNTRY_ALIASES,
        key=len,
        reverse=True
    ):

        if _word_in_text(alias, text):
            return COUNTRY_ALIASES[alias]

    for city in sorted(
        CITY_COUNTRY,
        key=len,
        reverse=True
    ):

        if _word_in_text(city, text):
            return CITY_COUNTRY[city]

    return None


def location_match_score(
    pref_location: Optional[str],
    job_location: Optional[str],
    job_work_mode: Optional[str],
    relocation: bool
) -> Optional[float]:
    """Location hierarchy (returns 0.0 - 1.0 or None):

    1. Exact / nested city      -> 1.0
    2. Same country             -> 0.85
    3. Remote eligible          -> 0.85 (0.6 when the
       remote job is in a
       different country and
       relocation is False)
    4. Different country        -> 0.0
    5. Unknown / unresolvable   -> None

    Unknown is never converted into a numeric score.
    """

    preferred = str(
        pref_location or ""
    ).strip()

    location = str(
        job_location or ""
    ).strip()

    mode = str(
        job_work_mode or ""
    ).strip().lower()

    if not preferred:
        return None

    if not location:
        return None

    if location.lower() in _LOCATION_NOISE:
        location = ""

    if not location:
        # e.g. jobGeo = "Worldwide" with no real place.
        if mode == "remote":
            return 0.85

        return None

    preferred_lower = preferred.lower()
    location_lower = location.lower()

    # -------------------------------------------------
    # 1. Exact / nested (city level)
    # -------------------------------------------------

    if (
        preferred_lower in location_lower
        or location_lower in preferred_lower
    ):
        return 1.0

    pref_country = resolve_location_country(preferred)
    job_country = resolve_location_country(location)

    # -------------------------------------------------
    # 2. Same country
    # -------------------------------------------------

    if (
        pref_country
        and job_country
        and pref_country == job_country
    ):
        return 0.85

    # -------------------------------------------------
    # 3. Remote eligible
    # -------------------------------------------------

    if mode == "remote":

        if (
            pref_country
            and job_country
            and pref_country != job_country
        ):
            return 0.85 if relocation else 0.6

        return 0.85

    # -------------------------------------------------
    # 4. Different country
    # -------------------------------------------------

    if (
        pref_country
        and job_country
        and pref_country != job_country
    ):
        return 0.0

    # -------------------------------------------------
    # 5. Unknown - one or both sides unresolvable
    # -------------------------------------------------

    return None


def work_mode_match_score(
    pref_work_mode: Optional[str],
    job_work_mode: Optional[str]
) -> Optional[float]:
    """None when either side is unknown / no preference."""

    preferred = str(
        pref_work_mode or ""
    ).strip().lower()

    mode = str(
        job_work_mode or ""
    ).strip().lower()

    if not preferred or preferred == "any":
        return None

    if not mode or mode == "unknown":
        return None

    if preferred == mode:
        return 1.0

    # A hybrid preference can accept remote roles.
    if preferred == "hybrid" and mode == "remote":
        return 0.8

    return 0.2


def employment_match_score(
    pref_employment: Optional[str],
    job_employment: Optional[str]
) -> Optional[float]:
    """None when either side is unknown / no preference."""

    preferred = str(
        pref_employment or ""
    ).strip().lower()

    employment = str(
        job_employment or ""
    ).strip().lower()

    if not preferred or preferred == "any":
        return None

    if not employment or employment == "unknown":
        return None

    if preferred == employment:
        return 1.0

    return 0.3


# ==========================================
# 3B. WEIGHTED SCORE (UNKNOWN EXCLUDED)
# ==========================================

def weighted_score(
    components: List[
        Tuple[Optional[float], float]
    ]
) -> Optional[float]:
    """Weighted average over 0 - 100 components.

    Components whose value is None (unknown) are
    excluded and the remaining weights are
    renormalized. Unknown is never treated as a
    match or a penalty.

    Returns None when nothing is known.
    """

    available = [
        (value, weight)
        for value, weight in components
        if value is not None and weight > 0
    ]

    if not available:
        return None

    total_weight = sum(
        weight for _, weight in available
    )

    if total_weight <= 0:
        return None

    return sum(
        value * weight
        for value, weight in available
    ) / total_weight


# ==========================================
# 4. SALARY (FOUR STATES)
# ==========================================

def parse_salary_range(salary: str) -> Tuple[float, float]:

    if not salary:
        return 0.0, 0.0

    numbers = re.findall(
        r"\d+(?:\.\d+)?",
        str(salary)
    )

    if not numbers:
        return 0.0, 0.0

    values = [
        float(value) * 100000
        for value in numbers
    ]

    if len(values) == 1:
        return values[0], values[0]

    return values[0], values[1]


def evaluate_salary(
    salary_min: Optional[float],
    salary_max: Optional[float],
    pref_low: float,
    pref_high: float
) -> Tuple[str, Optional[float]]:
    """Returns (salary_status, score).

    salary_status is one of:
    match / partial / mismatch / unknown

    Unknown salary is NEVER converted into a numeric
    reward or penalty.
    """

    if (
        salary_min is None
        or salary_max is None
        or pref_low <= 0
        or pref_high <= 0
    ):
        return "unknown", None

    job_average = (
        float(salary_min) + float(salary_max)
    ) / 2

    if job_average <= 0:
        return "unknown", None

    if pref_low <= job_average <= pref_high:
        return "match", 1.0

    if job_average > pref_high:
        # Earning more than expected is not a problem.
        return "match", 1.0

    # Below the expected range.
    ratio = job_average / pref_low

    if ratio >= 0.8:
        return "partial", round(ratio, 3)

    return "mismatch", round(max(0.1, ratio), 3)


# ==========================================
# 5. MARKET ALIGNMENT
# ==========================================

def _mean(values: List[float]) -> float:

    if not values:
        return 0.0

    return sum(values) / len(values)


def _clamp01(value: float) -> float:

    return max(0.0, min(1.0, value))


MARKET_ALIGNMENT_WEIGHTS = {
    "role_demand": 0.25,
    "skill_demand": 0.30,
    "profile_market_match": 0.30,
    "location_market_fit": 0.15,
}


def _skill_in_job(
    skill: str,
    job_required: List[str]
) -> bool:
    """Loose comparison between a candidate skill and a
    job's required skill list."""

    candidate = str(skill).lower().strip()

    if not candidate:
        return False

    for requirement in job_required:

        requirement = str(
            requirement
        ).lower().strip()

        if not requirement:
            continue

        if candidate == requirement:
            return True

        if candidate in requirement:
            return True

        if requirement in candidate:
            return True

    return False


def compute_market_alignment_details(
    readiness_score: float,
    target_role: str,
    experience_level: str,
    preferences: Dict[str, Any],
    jobs: List[Dict[str, Any]],
    role_experience_level: Optional[str] = None,
    current_skills: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Market Alignment = how well the candidate's skill
    profile aligns with the skills currently demanded
    for the target role / market.

    Deliberately separate from:
      readiness_score  -> preparation for the target role
      job_score        -> fit for one specific posting

    Components:
      role_demand          25%  share of opportunities
                              that are actually for the
                              target role
      skill_demand         30%  how much the market
                              demands the candidate's
                              skills
      profile_market_match 30%  how much of each
                              posting's requirements
                              the candidate satisfies
      location_market_fit  15%  location fit vs the
                              current opportunities

    Unknown components (None) are excluded and the
    remaining weights renormalized.
    """

    preferences = preferences or {}

    current_skills = current_skills or []

    preferred_location = preferences.get(
        "location"
    ) or ""

    relocation = bool(
        preferences.get("relocation")
    )

    role_demand: Optional[float] = None
    skill_demand: Optional[float] = None
    profile_market_match: Optional[float] = None
    location_market_fit: Optional[float] = None

    # -------------------------------------------------
    # With opportunities: measure against the market.
    # -------------------------------------------------

    if jobs:

        top_jobs = jobs[:10]

        # ---------------- Role demand ----------------

        relevant = sum(
            1
            for job in top_jobs
            if role_similarity(
                target_role,
                job.get("title", ""),
                job.get("description", "")
            ) >= 0.6
        )

        role_demand = relevant / len(top_jobs)

        # ---------------- Skill demand ---------------
        # How much the market wants the skills the
        # candidate already has.

        job_skill_lists = [
            [
                str(skill)
                for skill in job.get(
                    "required_skills",
                    []
                ) or []
            ]
            for job in top_jobs
        ]

        if current_skills and any(
            job_skills
            for job_skills in job_skill_lists
        ):

            per_skill = []

            for skill in current_skills:

                hits = sum(
                    1
                    for job_skills in job_skill_lists
                    if job_skills
                    and _skill_in_job(
                        skill,
                        job_skills
                    )
                )

                per_skill.append(
                    hits / len(top_jobs)
                )

            skill_demand = _mean(per_skill)

        # ---------------- Profile vs market ----------
        # How much of each posting the candidate
        # satisfies.

        profile_values = [
            float(job["skill_match_pct"]) / 100
            for job in top_jobs
            if job.get("skill_match_pct")
            is not None
        ]

        if profile_values:
            profile_market_match = _mean(
                profile_values
            )

        # ---------------- Location market fit --------

        location_values = []

        for job in top_jobs:

            score = location_match_score(
                preferred_location,
                job.get("location", ""),
                job.get("work_mode", ""),
                relocation
            )

            if score is not None:
                location_values.append(score)

        if location_values:
            location_market_fit = _mean(
                location_values
            )

    # -------------------------------------------------
    # Without opportunities: profile-based fallback.
    # -------------------------------------------------

    else:

        role_demand = 1.0

        fallback = _clamp01(
            readiness_score / 100
        )

        skill_demand = fallback
        profile_market_match = fallback

    # -------------------------------------------------
    # Weighted combination (unknowns excluded).
    # -------------------------------------------------

    weighted = weighted_score([

        (
            None
            if role_demand is None
            else role_demand * 100,
            MARKET_ALIGNMENT_WEIGHTS["role_demand"],
        ),

        (
            None
            if skill_demand is None
            else skill_demand * 100,
            MARKET_ALIGNMENT_WEIGHTS["skill_demand"],
        ),

        (
            None
            if profile_market_match is None
            else profile_market_match * 100,
            MARKET_ALIGNMENT_WEIGHTS[
                "profile_market_match"
            ],
        ),

        (
            None
            if location_market_fit is None
            else location_market_fit * 100,
            MARKET_ALIGNMENT_WEIGHTS[
                "location_market_fit"
            ],
        ),
    ])

    if weighted is None:
        weighted = 0.0

    # -------------------------------------------------
    # Human readable explanation.
    # -------------------------------------------------

    explanation = []

    if role_demand is not None:

        if role_demand >= 0.7:
            explanation.append(
                "Strong demand for your target role in "
                "the current market"
            )
        elif role_demand >= 0.4:
            explanation.append(
                "Moderate demand for your target role"
            )
        else:
            explanation.append(
                "Few current opportunities match your "
                "target role"
            )

    if skill_demand is not None:

        if skill_demand >= 0.6:
            explanation.append(
                "Your skills are frequently requested "
                "by current postings"
            )
        elif skill_demand >= 0.3:
            explanation.append(
                "Some of your skills are requested by "
                "the market"
            )
        else:
            explanation.append(
                "Your current skills are rarely "
                "requested for this market"
            )

    if profile_market_match is None:
        explanation.append(
            "Posting requirements could not be "
            "compared with your profile"
        )
    elif profile_market_match >= 0.7:
        explanation.append(
            "You satisfy most requirements in the "
            "matched postings"
        )
    elif profile_market_match >= 0.4:
        explanation.append(
            "You satisfy part of the requirements in "
            "the matched postings"
        )
    else:
        explanation.append(
            "Matched postings require many skills you "
            "do not list yet"
        )

    if location_market_fit is None:
        explanation.append(
            "Location fit could not be determined"
            " from the current postings"
        )
    elif location_market_fit >= 0.85:
        explanation.append(
            "Postings are well aligned with your "
            "location preference"
        )
    elif location_market_fit >= 0.5:
        explanation.append(
            "Postings partially align with your "
            "location preference"
        )
    else:
        explanation.append(
            "Few postings match your preferred "
            "location"
        )

    return {

        "score": round(weighted, 2),

        "breakdown": {

            "role_demand": (
                None
                if role_demand is None
                else round(role_demand * 100, 2)
            ),

            "skill_demand": (
                None
                if skill_demand is None
                else round(skill_demand * 100, 2)
            ),

            "profile_market_match": (
                None
                if profile_market_match is None
                else round(
                    profile_market_match * 100,
                    2
                )
            ),

            "location_market_fit": (
                None
                if location_market_fit is None
                else round(
                    location_market_fit * 100,
                    2
                )
            ),

            "weights":
                dict(MARKET_ALIGNMENT_WEIGHTS),
        },

        "explanation": explanation,
    }


def compute_market_alignment(
    readiness_score: float,
    target_role: str,
    experience_level: str,
    preferences: Dict[str, Any],
    jobs: List[Dict[str, Any]],
    role_experience_level: Optional[str] = None,
    current_skills: Optional[List[str]] = None
) -> float:
    """Score-only convenience wrapper around
    compute_market_alignment_details()."""

    details = compute_market_alignment_details(

        readiness_score=readiness_score,

        target_role=target_role,

        experience_level=experience_level,

        preferences=preferences,

        jobs=jobs,

        role_experience_level=(
            role_experience_level
        ),

        current_skills=current_skills,
    )

    return details["score"]


# ==========================================
# 6. REQUIREMENT CATEGORY MATCHING
# ==========================================
#
# Requirement phrases such as
#   "Proficiency in at least one backend
#    programming language (e.g., Python...)"
# are satisfied by concrete candidate skills
# such as Python. Embeddings alone cannot be
# the first authority for this - deterministic
# alias / category matching runs BEFORE any
# semantic similarity.
#
# Match order used by the agents:
#   1. Exact match
#   2. Alias / category match  (this section)
#   3. Semantic embedding match
#   4. LLM validation (borderline only)

SKILL_CATEGORY_MAP = {

    "backend programming": {
        "python",
        "java",
        "javascript",
        "typescript",
        "node.js",
        "go",
        "c#",
        "c++",
        "ruby",
        "php",
        "kotlin",
        "swift",
    },

    "version control": {
        "git",
        "github",
        "gitlab",
        "bitbucket",
        "svn",
    },

    "api development": {
        "rest api",
        "rest apis",
        "restful api",
        "restful apis",
        "fastapi",
        "flask",
        "django",
        "express",
        "express.js",
        "spring boot",
        "graphql",
        "grpc",
        "websocket",
        "websockets",
        "http",
        "json",
        "xml",
    },

    "databases": {
        "sql",
        "mysql",
        "postgresql",
        "mongodb",
        "redis",
        "cassandra",
        "dynamodb",
        "oracle",
        "sqlite",
        "nosql",
    },

    "testing": {
        "pytest",
        "unittest",
        "junit",
        "jest",
        "mocha",
        "junit",
        "testing",
        "unit testing",
        "integration testing",
        "tdd",
        "selenium",
        "playwright",
    },

    "http": {
        "http",
        "https",
        "rest api",
        "rest apis",
        "fastapi",
        "flask",
        "django",
        "oauth",
        "jwt",
        "tls",
        "ssl",
    },

    "linux": {
        "linux",
        "unix",
        "ubuntu",
        "debian",
        "centos",
        "bash",
        "shell scripting",
    },

    # --------------------------------------------------
    # Additional categories (same contract as above).
    # --------------------------------------------------

    "cloud": {
        "aws",
        "azure",
        "gcp",
        "google cloud",
        "heroku",
        "digitalocean",
        "cloud",
    },

    "containers": {
        "docker",
        "kubernetes",
        "containerization",
        "orchestration",
        "helm",
    },

    "ci/cd": {
        "ci/cd",
        "jenkins",
        "github actions",
        "gitlab ci",
        "circleci",
        "azure devops",
        "automation pipelines",
    },

    "frontend": {
        "react",
        "react.js",
        "angular",
        "vue",
        "vue.js",
        "next.js",
        "html",
        "css",
        "javascript",
        "typescript",
    },

    "message queues": {
        "kafka",
        "rabbitmq",
        "apache kafka",
        "redis",
        "pub/sub",
        "message queues",
        "streaming",
    },

    "data structures": {
        "data structures",
        "dsa",
        "algorithms",
        "object oriented programming",
        "oop",
        "system design",
        "design patterns",
    },

    "data analysis": {
        "pandas",
        "numpy",
        "excel",
        "statistics",
        "data analysis",
        "data manipulation",
        "etl",
    },

    "machine learning": {
        "machine learning",
        "deep learning",
        "scikit-learn",
        "tensorflow",
        "pytorch",
        "nlp",
        "computer vision",
        "ml",
    },
}


# Trigger phrases that appear inside a requirement
# sentence and activate a category. A category name is
# always a trigger for itself.

CATEGORY_TRIGGER_KEYS = {

    "backend programming": [
        "backend programming",
        "backend language",
        "backend development",
        "programming language",
        "server-side",
        "server side",
    ],

    "version control": [
        "version control",
        "source control",
    ],

    "api development": [
        "api development",
        "restful api",
        "restful apis",
        "rest api",
        "rest apis",
        "web api",
        "web apis",
        "http api",
        "api design",
        "building api",
        "building apis",
        "apis",
        "api",
    ],

    "databases": [
        "database",
        "databases",
        "relational database",
        "relational databases",
        "nosql",
        "data store",
        "data stores",
        "datastore",
    ],

    "testing": [
        "testing",
        "unit test",
        "unit tests",
        "test framework",
        "test frameworks",
        "test suite",
        "test automation",
    ],

    "http": [
        "http",
        "https",
        "status codes",
    ],

    "linux": [
        "linux",
        "unix",
        "command-line",
        "command line",
        "shell environment",
    ],

    "cloud": [
        "cloud",
        "cloud services",
        "cloud provider",
        "cloud platform",
    ],

    "containers": [
        "containerization",
        "containers",
        "orchestration",
        "kubernetes",
        "docker",
    ],

    "ci/cd": [
        "ci/cd",
        "continuous integration",
        "continuous delivery",
        "continuous deployment",
        "deployment pipelines",
        "automation pipelines",
    ],

    "frontend": [
        "frontend",
        "front-end",
        "front end",
        "ui development",
        "web ui",
    ],

    "message queues": [
        "message queue",
        "message queues",
        "message broker",
        "streaming platform",
        "streaming platforms",
        "pub/sub",
        "event streaming",
    ],

    "data structures": [
        "data structures",
        "algorithms",
        "object-oriented",
        "object oriented",
        "oop",
        "dsa",
        "system design",
        "design patterns",
    ],

    "data analysis": [
        "data manipulation",
        "data analysis",
        "data analytics",
        "data processing",
        "exploratory analysis",
    ],

    "machine learning": [
        "machine-learning",
        "machine learning",
        "ml concepts",
        "ml models",
        "models are served",
    ],
}


def _norm_requirement(value: str) -> str:
    """Normalize a requirement / skill string."""

    text = str(value or "").lower()

    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")

    text = re.sub(
        r"[^a-z0-9+#.\-/ ]+",
        " ",
        text
    )

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def category_requirement_match(
    required_skill: str,
    candidate_skills: List[str]
) -> Optional[str]:
    """Deterministic alias / category match.

    Returns the candidate skill that satisfies the
    requirement phrase, or None.

    Two rules, both checked before any embedding:

    1. Containment - the requirement phrase literally
       contains the candidate skill, e.g.
       "Version control with Git" contains "Git".
    2. Category - the phrase activates a known
       requirement category (e.g. "backend
       programming language") and the candidate owns a
       skill in that category.
    """

    requirement = _norm_requirement(
        required_skill
    )

    if not requirement:
        return None

    if not candidate_skills:
        return None

    # -------------------------------------------------
    # 1. Containment (specific first)
    # -------------------------------------------------

    for candidate in candidate_skills:

        normalized = _norm_requirement(candidate)

        if not normalized:
            continue

        if normalized == requirement:
            return candidate

        if _word_in_text(normalized, requirement):
            return candidate

    # -------------------------------------------------
    # 2. Category match
    # -------------------------------------------------

    for category, skills in (
        SKILL_CATEGORY_MAP.items()
    ):

        triggers = CATEGORY_TRIGGER_KEYS.get(
            category,
            [category],
        )

        activated = any(
            _word_in_text(
                _norm_requirement(trigger),
                requirement,
            )
            for trigger in triggers
        )

        if not activated:
            continue

        category_norm = {
            _norm_requirement(skill)
            for skill in skills
        }

        for candidate in candidate_skills:

            normalized = _norm_requirement(candidate)

            if normalized in category_norm:
                return candidate

    return None
