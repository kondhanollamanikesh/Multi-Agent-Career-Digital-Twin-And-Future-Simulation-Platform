# agents/job_opportunities_agent.py

import os
import re
import hashlib
import requests

from typing import TypedDict, List

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

from scoring_utils import (
    category_requirement_match,
    detect_experience_level,
    employment_match_score,
    evaluate_salary,
    experience_score,
    is_experience_mismatch,
    location_match_score,
    parse_salary_range,
    role_similarity,
    weighted_score,
    work_mode_match_score,
)

load_dotenv()


# ============================================================
# 1. STATE
# ============================================================

class JobOpportunitiesState(TypedDict):
    # Career Twin preferences
    target_role: str
    location: str
    work_mode: str
    employment_type: str
    salary_expectation: str
    relocation: bool
    preferred_industry: str
    experience_level: str

    # Career Twin skills
    current_skills: List[str]

    # Workflow state
    search_queries: List[str]
    raw_jobs: List[dict]
    normalized_jobs: List[dict]
    unique_jobs: List[dict]
    filtered_jobs: List[dict]
    matched_jobs: List[dict]
    scored_jobs: List[dict]
    ranked_jobs: List[dict]

    # Final result
    final_results: List[dict]


# ============================================================
# 2. SKILL ALIASES
# ============================================================

SKILL_ALIASES = {
    "ml": "Machine Learning",
    "machine-learning": "Machine Learning",
    "machine learning": "Machine Learning",

    "dl": "Deep Learning",
    "deep-learning": "Deep Learning",
    "deep learning": "Deep Learning",

    "nlp": "Natural Language Processing",

    "llm": "Large Language Models",
    "llms": "Large Language Models",

    "react": "React.js",
    "reactjs": "React.js",

    "node": "Node.js",
    "nodejs": "Node.js",

    "py": "Python",
    "python3": "Python",

    "tf": "TensorFlow",
    "tensorflow": "TensorFlow",

    "pyt": "PyTorch",
    "pytorch": "PyTorch",

    "huggingface": "Hugging Face",
    "hf": "Hugging Face",

    "k8s": "Kubernetes",

    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",

    "docker": "Docker",

    "sql": "SQL",
    "nosql": "NoSQL",

    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",

    "mongodb": "MongoDB",
    "mysql": "MySQL",

    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",

    "typescript": "TypeScript",
    "ts": "TypeScript",

    "javascript": "JavaScript",
    "js": "JavaScript",

    "java": "Java",
    "c++": "C++",

    "spark": "Apache Spark",
    "kafka": "Apache Kafka",
    "airflow": "Apache Airflow",

    "terraform": "Terraform",
    "jenkins": "Jenkins",

    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",

    "linux": "Linux",

    "rest": "REST APIs",
    "rest api": "REST APIs",
    "restful api": "REST APIs",

    "rag": "RAG",

    "vector databases": "Vector Databases",

    "transformers": "Transformers",

    "bert": "BERT",
    "gpt": "GPT",

    "opencv": "OpenCV",

    "numpy": "NumPy",
    "pandas": "Pandas",

    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",

    "matplotlib": "Matplotlib",

    "statistics": "Statistics",

    "feature engineering": "Feature Engineering",

    "prompt engineering": "Prompt Engineering",

    "fine-tuning": "Fine-tuning",

    "computer vision": "Computer Vision",

    "mlflow": "MLflow",

    "databricks": "Databricks",

    "power bi": "Power BI",

    "tableau": "Tableau",

    "excel": "Excel",

    "html": "HTML",
    "css": "CSS",

    "postman": "Postman",
}


def normalize_skill(skill: str) -> str:
    skill = skill.strip()

    if skill.lower() in SKILL_ALIASES:
        return SKILL_ALIASES[skill.lower()]

    return skill


def normalize_skills(skills: List[str]) -> List[str]:

    result = []
    seen = set()

    for skill in skills:

        normalized = normalize_skill(skill)

        key = normalized.lower()

        if key not in seen:
            seen.add(key)
            result.append(normalized)

    return result


# ============================================================
# 3. ROLE ALIASES
# ============================================================

ROLE_ALIASES = {

    "AI Engineer": [
        "Artificial Intelligence Engineer",
        "AI Developer",
        "Machine Learning Engineer"
    ],

    "AI/ML Engineer": [
        "AI Engineer",
        "Machine Learning Engineer",
        "ML Engineer",
        "AI Developer"
    ],

    "Machine Learning Engineer": [
        "ML Engineer",
        "AI Engineer",
        "Machine Learning Developer"
    ],

    "Data Scientist": [
        "Machine Learning Scientist",
        "Data Science Engineer"
    ],

    "Software Engineer": [
        "Software Developer",
        "Software Engineer"
    ],

    "Backend Developer": [
        "Backend Engineer",
        "Python Developer"
    ],

    "Full Stack Developer": [
        "Full Stack Engineer",
        "Software Developer"
    ],

    "Full-Stack Developer": [
        "Full Stack Developer",
        "Full Stack Engineer",
        "Software Developer"
    ],

    "Frontend Developer": [
        "Frontend Engineer",
        "UI Developer"
    ],
}


# ============================================================
# 4. LOAD PREFERENCES
# ============================================================

def load_preferences(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    print("\n[Job Agent] Loading Career Twin preferences")

    return state


# ============================================================
# 5. BUILD SEARCH QUERIES
# ============================================================

def build_search_queries(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    role = state["target_role"]
    location = state["location"]

    queries = []

    # Primary query
    if location:
        queries.append(f"{role} {location}")
    else:
        queries.append(role)

    # Role aliases
    aliases = ROLE_ALIASES.get(role, [])

    for alias in aliases[:3]:

        if location:
            queries.append(f"{alias} {location}")
        else:
            queries.append(alias)

    # Remote search
    if state["work_mode"].lower() == "remote":
        queries.append(f"{role} remote")

    # Industry
    industry = state["preferred_industry"]

    if industry:
        queries.append(f"{role} {industry}")

    # Remove duplicates
    state["search_queries"] = list(dict.fromkeys(queries))

    print("\n[Job Agent] Search queries:")

    for query in state["search_queries"]:
        print("   ", query)

    return state


# ============================================================
# 6. ADZUNA
# ============================================================

def fetch_jobs_from_adzuna(
    query: str,
    api_key: str
) -> List[dict]:

    app_id = os.getenv("ADZUNA_APP_ID")

    if not app_id or not api_key:
        return []

    url = (
        "https://api.adzuna.com/v1/api/jobs/in/search/1"
    )

    params = {
        "app_id": app_id,
        "app_key": api_key,
        "results_per_page": 20,
        "what": query,
        "content-type": "application/json",
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        jobs = []

        for item in data.get("results") or []:

            company = item.get("company") or {}

            location = item.get("location") or {}

            if not isinstance(company, dict):
                company = {}

            if not isinstance(location, dict):
                location = {}

            jobs.append({

                "title": item.get("title") or "",

                "company": company.get(
                    "display_name",
                    ""
                ),

                "location": location.get(
                    "display_name",
                    ""
                ),

                "description": item.get(
                    "description"
                ) or "",

                "salary_min": item.get(
                    "salary_min"
                ),

                "salary_max": item.get(
                    "salary_max"
                ),

                "url": item.get(
                    "redirect_url"
                ) or "",

                "source": "Adzuna",

                "created": item.get(
                    "created"
                ) or "",

            })

        return jobs

    except Exception as e:

        print(
            f"[Adzuna] Error: {e}"
        )

        return []


# ============================================================
# 7. JOBICY
# ============================================================

def fetch_jobs_from_jobicy(
    query: str
) -> List[dict]:

    url = "https://jobicy.com/api/v2/remote-jobs"

    params = {
        "count": 20
    }

    # Jobicy is primarily useful for remote jobs.
    # We therefore don't pretend it is location equivalent
    # to Adzuna.

    try:

        response = requests.get(
            url,
            params=params,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        jobs = []

        for item in data.get("jobs") or []:

            title = item.get(
                "jobTitle"
            ) or ""

            description = item.get(
                "jobDescription"
            ) or ""

            searchable = (
                f"{title} {description}"
            ).lower()

            if query.lower() not in searchable:

                # Keep the job if one of the role
                # keywords appears.
                role_words = query.lower().split()

                if not any(
                    word in searchable
                    for word in role_words
                    if len(word) > 3
                ):
                    continue

            jobs.append({

                "title": title,

                "company": item.get(
                    "companyName"
                ) or "",

                "location": item.get(
                    "jobGeo"
                ) or "",

                "description": description,

                "salary_min": None,

                "salary_max": None,

                "url": item.get(
                    "url"
                ) or "",

                "source": "Jobicy",

                "created": item.get(
                    "pubDate"
                ) or "",

                "work_mode": "Remote",

            })

        return jobs

    except Exception as e:

        print(
            f"[Jobicy] Error: {e}"
        )

        return []


# ============================================================
# 8. JOOBLE
# ============================================================

def fetch_jobs_from_jooble(
    query: str,
    api_key: str
) -> List[dict]:

    if not api_key:
        return []

    url = f"https://jooble.org/api/{api_key}"

    payload = {
        "keywords": query,
        "page": 1,
        "count": 20
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        response.raise_for_status()

        data = response.json()

        jobs = []

        for item in data.get("jobs") or []:

            jobs.append({

                "title": item.get(
                    "title"
                ) or "",

                "company": item.get(
                    "company"
                ) or "",

                "location": item.get(
                    "location"
                ) or "",

                "description": item.get(
                    "snippet"
                ) or "",

                "salary_min": None,

                "salary_max": None,

                "url": item.get(
                    "link"
                ) or "",

                "source": "Jooble",

                "created": item.get(
                    "pubDate"
                ) or "",

            })

        return jobs

    except Exception as e:

        print(
            f"[Jooble] Error: {e}"
        )

        return []


# ============================================================
# 9. FETCH JOBS
# ============================================================

def fetch_jobs(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    all_jobs = []

    adzuna_key = os.getenv(
        "ADZUNA_API_KEY"
    )

    jooble_key = os.getenv(
        "JOOBLE_API_KEY"
    )

    use_jobicy = True

    for query in state["search_queries"]:

        print(
            f"\n[Job Agent] Fetching: {query}"
        )

        # ----------------------------
        # Adzuna
        # ----------------------------

        if adzuna_key:

            jobs = fetch_jobs_from_adzuna(
                query,
                adzuna_key
            )

            print(
                f"Adzuna -> {len(jobs)}"
            )

            all_jobs.extend(jobs)

        # ----------------------------
        # Jobicy
        # ----------------------------

        if use_jobicy:

            jobs = fetch_jobs_from_jobicy(
                query
            )

            print(
                f"Jobicy -> {len(jobs)}"
            )

            all_jobs.extend(jobs)

        # ----------------------------
        # Jooble
        # ----------------------------

        if jooble_key:

            jobs = fetch_jobs_from_jooble(
                query,
                jooble_key
            )

            print(
                f"Jooble -> {len(jobs)}"
            )

            all_jobs.extend(jobs)

    state["raw_jobs"] = all_jobs

    print(
        f"\n[Job Agent] Total jobs: {len(all_jobs)}"
    )

    return state


# ============================================================
# 10. WORK MODE DETECTION
# ============================================================

WORK_MODE_KEYWORDS = {

    "remote": [
        "remote",
        "work from home",
        "wfh",
        "anywhere"
    ],

    "hybrid": [
        "hybrid",
        "flexible"
    ],

    "onsite": [
        "onsite",
        "on-site",
        "office",
        "in-office"
    ]
}


def detect_work_mode(text: str) -> str:

    text = text.lower()

    for mode, keywords in WORK_MODE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in text:
                return mode.capitalize()

    return "Unknown"


# ============================================================
# 11. EMPLOYMENT TYPE
# ============================================================

EMPLOYMENT_TYPES = {

    "full-time": [
        "full-time",
        "full time",
        "permanent"
    ],

    "part-time": [
        "part-time",
        "part time"
    ],

    "contract": [
        "contract",
        "freelance",
        "temporary"
    ],

    "internship": [
        "intern",
        "internship",
        "trainee"
    ]
}


def detect_employment_type(
    text: str
) -> str:

    text = text.lower()

    for employment_type, keywords in EMPLOYMENT_TYPES.items():

        for keyword in keywords:

            if keyword in text:
                return employment_type

    return "Unknown"


# ============================================================
# 12. EXTRACT SKILLS / REQUIREMENTS
# ============================================================

SKILL_KEYWORDS = [

    # ---------------- Languages ----------------
    "Python",
    "Java",
    "JavaScript",
    "TypeScript",
    "C++",
    "C#",
    "Scala",
    "Ruby",
    "PHP",
    "Go",
    "Rust",
    "R programming",
    "Bash",
    "Shell scripting",

    # ---------------- Data stores ----------------
    "SQL",
    "MongoDB",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "Cassandra",
    "Elasticsearch",
    "Snowflake",
    "BigQuery",
    "NoSQL",

    # ---------------- AI / ML ----------------
    "Machine Learning",
    "Deep Learning",
    "NLP",
    "Natural Language Processing",
    "Computer Vision",
    "Generative AI",
    "Large Language Models",
    "LLM",
    "RAG",
    "Prompt Engineering",
    "Fine-tuning",
    "Reinforcement Learning",
    "Feature Engineering",
    "Model Deployment",
    "MLOps",
    "Explainable AI",

    "TensorFlow",
    "PyTorch",
    "Keras",
    "Scikit-learn",
    "Hugging Face",
    "Transformers",
    "OpenCV",
    "spaCy",
    "XGBoost",
    "LightGBM",

    "Pandas",
    "NumPy",
    "SciPy",
    "Matplotlib",
    "Seaborn",

    "Statistics",
    "Probability",
    "Linear Algebra",

    "LangChain",
    "LangGraph",
    "LlamaIndex",
    "Vector Databases",
    "FAISS",
    "Pinecone",
    "ChromaDB",

    # ---------------- Backend / Web ----------------
    "FastAPI",
    "Django",
    "Flask",
    "Node.js",
    "Express.js",
    "React",
    "Angular",
    "Vue",
    "Next.js",

    "REST APIs",
    "GraphQL",
    "Microservices",
    "WebSockets",

    # ---------------- DevOps / Cloud ----------------
    "Docker",
    "Kubernetes",
    "AWS",
    "Azure",
    "GCP",
    "Terraform",
    "Jenkins",
    "CI/CD",
    "GitHub Actions",
    "GitLab CI",
    "Linux",
    "SageMaker",
    "Vertex AI",
    "Azure ML",

    # ---------------- Version control ----------------
    "Git",
    "GitHub",
    "GitLab",

    # ---------------- Data engineering ----------------
    "Apache Spark",
    "Airflow",
    "Kafka",
    "ETL",
    "Data Pipelines",
    "DBT",

    # ---------------- Analytics / BI ----------------
    "Power BI",
    "Tableau",
    "Looker",
    "Excel",
    "Google Analytics",

    # ---------------- Testing / Practices ----------------
    "Unit Testing",
    "Pytest",
    "Selenium",
    "Agile",
    "Scrum",
    "Jira",
    "Confluence",
    "Figma",
    "System Design",
    "Data Structures",
    "Algorithms",
    "Object Oriented Programming",
    "Design Patterns",
    "Code Review",

    # ---------------- Product management ----------------
    "Product Management",
    "Product Strategy",
    "Product Roadmap",
    "User Research",
    "A/B Testing",
    "Stakeholder Management",
    "User Stories",
    "PRD",
    "Roadmap Prioritization",
    "OKRs",
    "KPIs",
    "Engagement and Retention",
    "Product Analytics",
    "Experimentation",

    # ---------------- CRM / Marketing ----------------
    "CRM",
    "Salesforce",
    "HubSpot",
    "Marketing Automation",
    "Email Marketing",
    "Lifecycle Marketing",
    "Iterable",
    "Braze",
    "Segmentation",
    "Campaign Management",
    "Lead Generation",
    "Demand Generation",
    "SEO",
    "Content Marketing",
    "Copywriting",
    "Brand Management",
    "GDPR",
    "Data Privacy",
    "Consent Management",

    # ---------------- Leadership / Soft skills ----------------
    "Team Leadership",
    "People Management",
    "Mentoring",
    "Cross-functional Collaboration",
    "Communication",
    "Problem Solving",
    "Presentation",
    "Negotiation",
    "Hiring",
    "Budget Management",
    "Project Management",

    # ---------------- Sales / Pre-sales ----------------
    "B2B Sales",
    "SaaS",
    "Account Management",
    "Pipeline Management",
    "Quota",
    "Solution Architecture",
    "Pre-Sales",
    "RFP",
    "Proof of Concept",
    "Customer Demos",

    # ---------------- Security ----------------
    "OAuth",
    "JWT",
    "Security Best Practices",
]


def _contains_keyword(
    text_lower: str,
    keyword: str
) -> bool:
    """Word-boundary aware keyword detection.

    Prevents false positives such as RAG inside
    'storage' or REST inside 'interested'.
    """

    keyword_lower = keyword.lower().strip()

    if not keyword_lower:
        return False

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(keyword_lower)
        + r"(?![a-z0-9])"
    )

    return re.search(
        pattern,
        text_lower
    ) is not None


# ---------------------------------------------
# Requirement section headers
# ---------------------------------------------

REQUIREMENT_HEADER_LINE = re.compile(
    r"^\s*(?:[-•*]\s*)?"
    r"(?:requirements?|qualifications?|"
    r"must[- ]haves?|basic qualifications|"
    r"preferred qualifications|"
    r"minimum qualifications|"
    r"desired qualifications|"
    r"what you(?:'|’)?ll need|"
    r"who you(?:'|’)?re|"
    r"what we(?:'|’)?re looking for|"
    r"required skills|key skills|"
    r"job requirements|skills required|"
    r"about you|who you are)"
    r"\s*[:\-]?\s*$",
    re.IGNORECASE,
)

REQUIREMENT_HEADER_INLINE = re.compile(
    r"(?:requirements?|qualifications?|"
    r"must[- ]haves?|required skills|"
    r"key skills|what you(?:'|’)?ll need)"
    r"\s*:",
    re.IGNORECASE,
)

BULLET_LINE = re.compile(
    r"^\s*(?:[•\-\*]|\d+[.)])\s*(.+)$"
)

PATTERN_PHRASE_RULES = [

    # experience with X / proficiency in X / ...
    re.compile(
        r"(?:experience|proficiency|familiarity|"
        r"knowledge|understanding|expertise|background)"
        r"\s+(?:with|in|of|on|using)\s+"
        r"([^.;\n]{3,80})",
        re.IGNORECASE
    ),

    # N years (of) (experience) (in/with/of) X
    re.compile(
        r"\d+\s*(?:\+|to|-|–)?\s*(?:\d+)?\s*"
        r"(?:years?|yrs?)(?:\s+of)?"
        r"(?:\s+experience)?"
        r"(?:\s+(?:in|with|of|on))?\s+"
        r"([^.;,\n]{3,60})",
        re.IGNORECASE
    ),

    # must have X / ability to X / expected to X ...
    re.compile(
        r"(?:must have|must|should|need to|"
        r"required to|expected to|"
        r"ability to|proven track record(?:\s+of)?)"
        r"\s+([^.;\n]{3,90})",
        re.IGNORECASE
    ),

    # strong understanding/knowledge of X
    re.compile(
        r"(?:strong|solid|good|excellent|working)"
        r"\s+(?:understanding|knowledge|grasp|familiarity)"
        r"\s+of\s+([^.;\n]{3,80})",
        re.IGNORECASE
    ),
]


def _clean_phrase(phrase: str) -> str:

    value = re.sub(
        r"\s+",
        " ",
        str(phrase)
    )

    value = value.strip()

    value = value.strip(" \t-•*·:")

    value = value.strip()

    return value


def _dedupe_phrases(phrases: List[str]) -> List[str]:

    result = []
    seen = set()

    for phrase in phrases:

        cleaned = _clean_phrase(phrase)

        if not cleaned:
            continue

        if len(cleaned) < 3:
            continue

        key = cleaned.lower()

        if key in seen:
            continue

        seen.add(key)

        result.append(cleaned)

    return result


def extract_requirement_section_phrases(
    description: str
) -> List[str]:
    """Extract bullet/short lines that appear under
    explicit requirement-style section headers."""

    if not description:
        return []

    phrases: List[str] = []

    in_section = False

    for raw_line in description.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        if (
            REQUIREMENT_HEADER_LINE.match(line)
            or REQUIREMENT_HEADER_INLINE.search(line)
        ):
            in_section = True
            continue

        if not in_section:
            continue

        # A new short header line ends the section.
        if line.endswith(":") and len(line) <= 60:

            in_section = False
            continue

        candidate = None

        bullet = BULLET_LINE.match(line)

        if bullet:

            candidate = bullet.group(1)

        elif (
            len(line) <= 130
            and not line.endswith(".")
            and not line.endswith(",")
        ):

            candidate = line

        if candidate:

            cleaned = _clean_phrase(candidate)

            if 3 <= len(cleaned) <= 160:

                phrases.append(cleaned)

    return _dedupe_phrases(phrases)


def extract_pattern_phrases(
    description: str
) -> List[str]:
    """Extract requirement phrases using regex patterns
    across the whole description."""

    if not description:
        return []

    phrases: List[str] = []

    for pattern in PATTERN_PHRASE_RULES:

        for match in pattern.finditer(description):

            matched_text = match.group(
                match.lastindex or 1
            )

            cleaned = _clean_phrase(matched_text)

            if 3 <= len(cleaned) <= 120:

                phrases.append(cleaned)

    return _dedupe_phrases(phrases)


def extract_required_skills(
    description: str
) -> tuple:
    """Strong requirement extraction.

    Combines:
    1. Requirement-section bullets (explicit core needs)
    2. Pattern-based phrases with no known keyword
    3. Broad word-boundary keyword scan

    Returns (required_skills, requirement_phrases).
    """

    if not description:
        return [], []

    text = description

    text_lower = text.lower()

    # ---------------------------------------------
    # 1. Explicit requirement-section phrases
    # ---------------------------------------------

    section_phrases = (
        extract_requirement_section_phrases(text)
    )

    # ---------------------------------------------
    # 2. Pattern phrases (only when they add no
    #    already-known keyword)
    # ---------------------------------------------

    pattern_phrases = extract_pattern_phrases(text)

    filtered_patterns = []

    for phrase in pattern_phrases:

        phrase_lower = phrase.lower()

        known_hits = any(
            _contains_keyword(phrase_lower, skill)
            for skill in SKILL_KEYWORDS
        )

        if not known_hits:

            filtered_patterns.append(phrase)

    # ---------------------------------------------
    # 3. Broad keyword scan
    # ---------------------------------------------

    keyword_hits = []

    for skill in SKILL_KEYWORDS:

        if _contains_keyword(text_lower, skill):

            keyword_hits.append(skill)

    keyword_hits = normalize_skills(keyword_hits)

    # ---------------------------------------------
    # Combine: explicit requirements first.
    # ---------------------------------------------

    required = []

    required.extend(section_phrases)
    required.extend(filtered_patterns)
    required.extend(keyword_hits)

    required = _dedupe_phrases(required)

    # Cap to avoid drowning in noise.
    required = required[:30]

    return required, section_phrases


def extract_skills(
    description: str
) -> List[str]:
    """Backward-compatible helper: keyword skills only."""

    if not description:
        return []

    description_lower = description.lower()

    found = []

    for skill in SKILL_KEYWORDS:

        if _contains_keyword(
            description_lower,
            skill
        ):
            found.append(skill)

    return normalize_skills(found)


# ============================================================
# 13. NORMALIZE JOBS
# ============================================================

def normalize_jobs(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    normalized = []

    for job in state["raw_jobs"]:

        title = (
            job.get("title") or ""
        ).strip()

        description = (
            job.get("description") or ""
        ).strip()

        combined_text = (
            f"{title} {description}"
        )

        # ---------------------------------------------
        # Requirements are extracted FROM THE
        # DESCRIPTION first - never trusted directly
        # from the API's minimal required_skills field.
        # ---------------------------------------------

        api_skills = [
            str(skill).strip()
            for skill in (
                job.get("required_skills") or []
            )
            if str(skill).strip()
        ]

        requirement_phrases = job.get(
            "requirement_phrases"
        )

        extraction_source = (
            description if description else title
        )

        extracted_skills, extracted_phrases = (
            extract_required_skills(
                extraction_source
            )
        )

        # ---------------------------------------------
        # Thin description -> also scan the title.
        # ---------------------------------------------

        if (
            len(extracted_skills) < 3
            and description
            and title
        ):

            retry_skills, retry_phrases = (
                extract_required_skills(
                    f"{title}\n{description}"
                )
            )

            extracted_skills = _dedupe_phrases(
                list(extracted_skills)
                + list(retry_skills)
            )

            extracted_phrases = _dedupe_phrases(
                list(extracted_phrases)
                + list(retry_phrases)
            )

        # ---------------------------------------------
        # Description findings first, API extras
        # appended (they may add skills the text
        # scanner missed).
        # ---------------------------------------------

        required_skills = _dedupe_phrases(
            list(extracted_skills)
            + api_skills
        )

        # Cap to avoid drowning in noise.
        required_skills = required_skills[:30]

        if requirement_phrases is None:

            requirement_phrases = (
                extracted_phrases
            )

        if requirement_phrases is None:

            requirement_phrases = []

        work_mode = job.get(
            "work_mode"
        )

        if not work_mode:

            work_mode = detect_work_mode(
                combined_text
            )

        employment_type = job.get(
            "employment_type"
        )

        if not employment_type:

            employment_type = detect_employment_type(
                combined_text
            )

        # ------------------------------------------
        # Experience level detection
        # ------------------------------------------

        experience_level = job.get(
            "experience_level"
        ) or "Unknown"

        if experience_level == "Unknown":

            experience_level = detect_experience_level(
                title
            )

        if experience_level == "Unknown":

            experience_level = detect_experience_level(
                description[:2000],
                from_description=True
            )

        normalized.append({

            "title": title,

            "company": (
                job.get("company") or ""
            ).strip(),

            "location": (
                job.get("location") or ""
            ).strip(),

            "work_mode": work_mode,

            "employment_type": employment_type,

            "experience_level": experience_level,

            "salary_min": job.get(
                "salary_min"
            ),

            "salary_max": job.get(
                "salary_max"
            ),

            "description": description,

            "required_skills": required_skills,

            "requirement_phrases":
                requirement_phrases,

            "source": job.get(
                "source"
            ) or "Unknown",

            "url": job.get(
                "url"
            ) or "",

            "created": job.get(
                "created"
            ) or "",

        })

    state["normalized_jobs"] = normalized

    return state


# ============================================================
# 14. DEDUPLICATION
# ============================================================

def job_fingerprint(job: dict) -> str:

    key = "|".join([

        job.get(
            "title", ""
        ).lower().strip(),

        job.get(
            "company", ""
        ).lower().strip(),

        job.get(
            "location", ""
        ).lower().strip(),

    ])

    return hashlib.md5(
        key.encode()
    ).hexdigest()


def deduplicate_jobs(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    seen = set()
    unique = []

    for job in state["normalized_jobs"]:

        fingerprint = job_fingerprint(
            job
        )

        if fingerprint not in seen:

            seen.add(fingerprint)

            unique.append(job)

    state["unique_jobs"] = unique

    return state


# ============================================================
# 15. SALARY PARSING
# ============================================================

# parse_salary_range is imported from scoring_utils.


# ============================================================
# 16. FILTER
# ============================================================

def filter_by_preferences(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    filtered = []

    thin_dropped = 0

    pref_location = (
        state["location"]
        .lower()
        .strip()
    )

    pref_work_mode = (
        state["work_mode"]
        .lower()
        .strip()
    )

    pref_employment = (
        state["employment_type"]
        .lower()
        .strip()
    )

    relocation = state["relocation"]

    for job in state["unique_jobs"]:

        job_location = job[
            "location"
        ].lower()

        job_mode = job[
            "work_mode"
        ].lower()

        job_employment = job[
            "employment_type"
        ].lower()

        # ----------------------------------
        # Location
        # ----------------------------------

        location_match = (
            not pref_location
            or pref_location in job_location
            or job_location in pref_location
        )

        remote_job = (
            job_mode == "remote"
        )

        if not location_match:

            if not remote_job:

                if not relocation:
                    continue

        # ----------------------------------
        # Work mode
        # ----------------------------------

        if pref_work_mode:

            if pref_work_mode != "any":

                if (
                    job_mode != pref_work_mode
                    and job_mode != "unknown"
                ):

                    # Hybrid preference can consider
                    # remote jobs as compatible.
                    if not (
                        pref_work_mode == "hybrid"
                        and job_mode == "remote"
                    ):
                        continue

        # ----------------------------------
        # Employment
        # ----------------------------------

        if pref_employment:

            if pref_employment != "any":

                if (
                    job_employment != pref_employment
                    and job_employment != "unknown"
                ):
                    continue

        # ----------------------------------
        # Experience level (hard filter)
        #
        # Clear mismatches (e.g. Entry Level
        # candidate vs Senior job) are rejected
        # before any scoring happens.
        # ----------------------------------

        if is_experience_mismatch(
            state["experience_level"],
            job.get(
                "experience_level",
                "Unknown"
            )
        ):
            continue

        # ----------------------------------
        # Requirement extraction quality
        # gate
        #
        # Requirements are extracted from the
        # description first. Postings too thin
        # to yield at least 3 requirements
        # (e.g. truncated teasers) cannot be
        # scored honestly - skill fit would be
        # guesswork - so they are not
        # recommended.
        # ----------------------------------

        if len(
            job.get("required_skills") or []
        ) < 3:

            thin_dropped += 1
            continue

        filtered.append(job)

    print(
        "[Job Agent] Filtered:",
        len(filtered),
        "| dropped (thin extraction):",
        thin_dropped,
    )

    state["filtered_jobs"] = filtered

    return state


# ============================================================
# 17. SKILL MATCHING
# ============================================================

def _contains_term(
    haystack: str,
    needle: str
) -> bool:
    """Word-boundary containment check."""

    if not haystack or not needle:
        return False

    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(needle.lower())
        + r"(?![a-z0-9])"
    )

    return re.search(
        pattern,
        haystack.lower()
    ) is not None


def _skill_matches_required(
    required: str,
    user_skills_lower: List[str]
) -> bool:
    """Flexible matching between a required skill /
    requirement phrase and the candidate's skills."""

    requirement = str(required).lower().strip()

    if not requirement:
        return False

    requirement_tokens = set(
        re.findall(
            r"[a-z0-9+#]+",
            requirement
        )
    )

    for user_skill in user_skills_lower:

        if not user_skill:
            continue

        # Exact match
        if user_skill == requirement:
            return True

        # Word-boundary containment in either direction
        # (handles long requirement phrases)
        if _contains_term(requirement, user_skill):
            return True

        if _contains_term(user_skill, requirement):
            return True

        # Token-subset match in either direction
        user_tokens = set(
            re.findall(
                r"[a-z0-9+#]+",
                user_skill
            )
        )

        if not user_tokens:
            continue

        if (
            user_tokens <= requirement_tokens
            or requirement_tokens <= user_tokens
        ):
            return True

    # --------------------------------------------------
    # Alias / category requirement match.
    #
    # e.g. "Proficiency in at least one backend
    #       programming language" satisfied by Python.
    # Deterministic - runs without embeddings.
    # --------------------------------------------------

    if category_requirement_match(
        required,
        user_skills_lower
    ):
        return True

    return False


def match_skills(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    user_skills = normalize_skills(
        state["current_skills"]
    )

    user_skills_lower = [
        skill.lower()
        for skill in user_skills
    ]

    matched_jobs = []

    for job in state["filtered_jobs"]:

        required_skills = normalize_skills(
            job.get(
                "required_skills",
                []
            )
        )

        matched = []
        missing = []

        for required in required_skills:

            if _skill_matches_required(
                required,
                user_skills_lower
            ):

                matched.append(required)

            else:

                missing.append(required)

        total = len(required_skills)

        if total == 0:

            # Unknown is NOT 50% match.
            match_percentage = None

        else:

            match_percentage = round(
                len(matched)
                / total
                * 100,
                1
            )

        job["matched_skills"] = matched

        job["missing_skills"] = missing

        job["skill_match_pct"] = match_percentage

        matched_jobs.append(job)

    state["matched_jobs"] = matched_jobs

    return state


# ============================================================
# 18. JOB SCORE
# ============================================================

# Job Score = how well this candidate matches THIS
# posting (kept separate from readiness and market
# alignment).
#
#   Skill Match       35%
#   Role Similarity   20%
#   Experience Match  20%
#   Location Match    10%
#   Work Mode Match    5%
#   Employment Match   5%
#   Salary Match       5%
#
# Unknown (None) components are excluded and the
# remaining weights renormalized - unknown never
# counts as a match.

JOB_SCORE_WEIGHTS = {
    "skill_match": 0.35,
    "role_similarity": 0.20,
    "experience_match": 0.20,
    "location_match": 0.10,
    "work_mode_match": 0.05,
    "employment_match": 0.05,
    "salary_match": 0.05,
}


def _to_pct(value):
    """0-1 score -> 0-100 percentage (None stays None)."""

    if value is None:
        return None

    return round(float(value) * 100, 1)


def build_scoring_explanation(
    job: dict,
    breakdown: dict,
    state
) -> list:
    """Short human readable reasons behind job_score."""

    lines = []

    # ---------------- Skill ----------------

    skill = breakdown.get("skill_match")

    missing = job.get("missing_skills") or []

    if skill is None:

        lines.append(
            "Requirements could not be extracted, so "
            "skill match is unknown"
        )

    elif skill >= 80:

        lines.append(
            "Strong skill alignment with the listed "
            "requirements"
        )

    elif skill >= 50:

        lines.append(
            "Partial skill alignment - "
            f"{len(missing)} listed requirement(s) "
            "not demonstrated"
        )

    else:

        lines.append(
            "Weak skill alignment with the listed "
            "requirements"
        )

    # ---------------- Role ----------------

    role = breakdown.get("role_similarity") or 0

    if role >= 90:

        lines.append(
            "Role title closely matches your target "
            "role"
        )

    elif role >= 60:

        lines.append(
            "Role is related to your target role"
        )

    else:

        lines.append(
            "Role differs from your target role"
        )

    # ---------------- Experience ----------------

    experience = breakdown.get("experience_match")

    job_level = job.get(
        "experience_level",
        "Unknown"
    )

    if experience is None:

        lines.append(
            "Experience requirement for this posting "
            "is unknown"
        )

    elif experience <= 10:

        lines.append(
            f"Job targets {job_level} experience, far "
            "above your profile"
        )

    elif experience >= 90:

        lines.append(
            "Experience level matches your profile"
        )

    else:

        lines.append(
            "Experience level partially matches "
            f"(job: {job_level})"
        )

    # ---------------- Location ----------------

    location = breakdown.get("location_match")

    preferred_location = (
        state.get("location") or ""
    )

    if location is None:

        lines.append(
            "Location fit could not be determined"
        )

    elif location == 0:

        lines.append(
            "Job location does not match your "
            f"preferred {preferred_location} location"
        )

    elif location >= 100:

        lines.append(
            "Job location matches your preference"
        )

    elif location >= 85:

        lines.append(
            "Job is remote or in the same country as "
            "your preference"
        )

    else:

        lines.append(
            "Location partially matches your preference"
        )

    # ---------------- Work mode ----------------

    work_mode = breakdown.get("work_mode_match")

    if work_mode is None:

        lines.append(
            "Work mode not specified on either side"
        )

    elif work_mode >= 90:

        lines.append(
            "Work mode matches your preference"
        )

    elif work_mode >= 60:

        lines.append(
            "Work mode is compatible with your preference"
        )

    else:

        lines.append(
            "Work mode does not match your preference"
        )

    # ---------------- Employment ----------------

    employment = breakdown.get("employment_match")

    if employment is None:

        lines.append(
            "Employment type not specified on either side"
        )

    elif employment >= 90:

        lines.append(
            "Employment type matches your preference"
        )

    else:

        lines.append(
            "Employment type differs from your preference"
        )

    # ---------------- Salary ----------------

    salary = breakdown.get("salary_match")

    salary_status = job.get("salary_status")

    if salary is None:

        lines.append(
            "Salary not listed for this role"
        )

    elif salary_status == "match":

        lines.append(
            "Salary is within your expected range"
        )

    elif salary_status == "partial":

        lines.append(
            "Salary is slightly below your expectation"
        )

    else:

        lines.append(
            "Salary is below your expectation"
        )

    return lines


def calculate_job_score(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    scored = []

    pref_low, pref_high = parse_salary_range(
        state["salary_expectation"]
    )

    target_role = (
        state.get("target_role") or ""
    )

    # Unknown candidate level stays unknown - it is
    # never defaulted into a generous score.
    candidate_level = (
        state.get("experience_level") or ""
    )

    for job in state["matched_jobs"]:

        # -----------------------------
        # 1. Role relevance
        # -----------------------------

        role_score = role_similarity(
            target_role,
            job.get("title", ""),
            job.get("description", "")
        )

        role_pct = round(
            role_score * 100,
            1
        )

        # -----------------------------
        # 2. Required skill match
        #    (None when unknown)
        # -----------------------------

        skill_pct = job.get(
            "skill_match_pct"
        )

        # -----------------------------
        # 3. Experience (categorical,
        #    None when unknown)
        # -----------------------------

        experience_match = experience_score(
            candidate_level,
            job.get(
                "experience_level",
                "Unknown"
            )
        )

        experience_pct = _to_pct(
            experience_match
        )

        # -----------------------------
        # 4. Location hierarchy
        #    (None when unknown)
        # -----------------------------

        location_match = location_match_score(
            state["location"],
            job.get("location", ""),
            job.get("work_mode", ""),
            state["relocation"]
        )

        location_pct = _to_pct(
            location_match
        )

        # -----------------------------
        # 5. Work mode / employment
        #    (None when unknown)
        # -----------------------------

        work_mode_match = work_mode_match_score(
            state["work_mode"],
            job.get("work_mode", "")
        )

        work_mode_pct = _to_pct(
            work_mode_match
        )

        employment_match = employment_match_score(
            state["employment_type"],
            job.get(
                "employment_type",
                "Unknown"
            )
        )

        employment_pct = _to_pct(
            employment_match
        )

        # -----------------------------
        # 6. Salary: four states,
        #    unknown stays None
        # -----------------------------

        salary_status, salary_score = (
            evaluate_salary(
                job.get("salary_min"),
                job.get("salary_max"),
                pref_low,
                pref_high
            )
        )

        salary_pct = _to_pct(salary_score)

        # -----------------------------
        # Weighted score - unknown
        # components excluded and
        # remaining weights
        # renormalized.
        # -----------------------------

        final_score = weighted_score([

            (
                skill_pct,
                JOB_SCORE_WEIGHTS["skill_match"],
            ),

            (
                role_pct,
                JOB_SCORE_WEIGHTS["role_similarity"],
            ),

            (
                experience_pct,
                JOB_SCORE_WEIGHTS[
                    "experience_match"
                ],
            ),

            (
                location_pct,
                JOB_SCORE_WEIGHTS["location_match"],
            ),

            (
                work_mode_pct,
                JOB_SCORE_WEIGHTS[
                    "work_mode_match"
                ],
            ),

            (
                employment_pct,
                JOB_SCORE_WEIGHTS[
                    "employment_match"
                ],
            ),

            (
                salary_pct,
                JOB_SCORE_WEIGHTS["salary_match"],
            ),
        ])

        if final_score is None:
            final_score = 0.0

        # -----------------------------
        # Large penalty for role
        # mismatch (not a reject:
        # relocation/transfer cases may
        # still be relevant).
        # -----------------------------

        if role_score < 0.35:

            final_score *= 0.4

        # -----------------------------
        # Score breakdown + explanation
        # -----------------------------

        breakdown = {

            "skill_match": skill_pct,

            "role_similarity": role_pct,

            "experience_match": experience_pct,

            "location_match": location_pct,

            "work_mode_match": work_mode_pct,

            "employment_match": employment_pct,

            "salary_match": salary_pct,
        }

        known_preference = [
            value
            for value in (
                work_mode_pct,
                employment_pct,
            )
            if value is not None
        ]

        job["role_similarity"] = round(
            role_score,
            3
        )

        job["experience_match_pct"] = (
            experience_pct
        )

        job["preference_match_pct"] = (
            round(
                sum(known_preference)
                / len(known_preference),
                1
            )
            if known_preference
            else None
        )

        job["location_match_pct"] = (
            location_pct
        )

        job["work_mode_match_pct"] = (
            work_mode_pct
        )

        job["employment_match_pct"] = (
            employment_pct
        )

        job["salary_status"] = salary_status

        job["salary_match_pct"] = salary_pct

        job["score_breakdown"] = breakdown

        job["scoring_explanation"] = (
            build_scoring_explanation(
                job,
                breakdown,
                state
            )
        )

        job["job_score"] = round(
            final_score,
            1
        )

        scored.append(job)

    state["scored_jobs"] = scored

    return state


# ============================================================
# 19. RANK
# ============================================================

def rank_jobs(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    ranked = sorted(
        state["scored_jobs"],
        key=lambda job: job.get(
            "job_score",
            0
        ),
        reverse=True
    )

    state["ranked_jobs"] = ranked

    return state


# ============================================================
# 20. FINAL RESULTS
# ============================================================

def save_jobs(
    state: JobOpportunitiesState
) -> JobOpportunitiesState:

    state["final_results"] = (
        state["ranked_jobs"][:20]
    )

    return state


# ============================================================
# 21. BUILD GRAPH
# ============================================================

workflow = StateGraph(
    JobOpportunitiesState
)

workflow.add_node(
    "load_preferences",
    load_preferences
)

workflow.add_node(
    "build_search_queries",
    build_search_queries
)

workflow.add_node(
    "fetch_jobs",
    fetch_jobs
)

workflow.add_node(
    "normalize_jobs",
    normalize_jobs
)

workflow.add_node(
    "deduplicate_jobs",
    deduplicate_jobs
)

workflow.add_node(
    "filter_by_preferences",
    filter_by_preferences
)

workflow.add_node(
    "match_skills",
    match_skills
)

workflow.add_node(
    "calculate_job_score",
    calculate_job_score
)

workflow.add_node(
    "rank_jobs",
    rank_jobs
)

workflow.add_node(
    "save_jobs",
    save_jobs
)


# ============================================================
# 22. EDGES
# ============================================================

workflow.add_edge(
    START,
    "load_preferences"
)

workflow.add_edge(
    "load_preferences",
    "build_search_queries"
)

workflow.add_edge(
    "build_search_queries",
    "fetch_jobs"
)

workflow.add_edge(
    "fetch_jobs",
    "normalize_jobs"
)

workflow.add_edge(
    "normalize_jobs",
    "deduplicate_jobs"
)

workflow.add_edge(
    "deduplicate_jobs",
    "filter_by_preferences"
)

workflow.add_edge(
    "filter_by_preferences",
    "match_skills"
)

workflow.add_edge(
    "match_skills",
    "calculate_job_score"
)

workflow.add_edge(
    "calculate_job_score",
    "rank_jobs"
)

workflow.add_edge(
    "rank_jobs",
    "save_jobs"
)

workflow.add_edge(
    "save_jobs",
    END
)


job_opportunities_graph = workflow.compile()


# ============================================================
# 23. PUBLIC FUNCTION
# ============================================================

def find_job_opportunities(
    preferences: dict,
    current_skills: List[str]
) -> List[dict]:

    if preferences is None:
        preferences = {}

    if current_skills is None:
        current_skills = []

    initial_state = {

        "target_role": (
            preferences.get("target_role")
            or ""
        ),

        "location": (
            preferences.get("location")
            or ""
        ),

        "work_mode": (
            preferences.get("work_mode")
            or ""
        ),

        "employment_type": (
            preferences.get("employment_type")
            or ""
        ),

        "salary_expectation": (
            preferences.get("salary_expectation")
            or ""
        ),

        "relocation": bool(
            preferences.get("relocation")
            or False
        ),

        "preferred_industry": (
            preferences.get("preferred_industry")
            or ""
        ),

        "experience_level": (
            preferences.get("experience_level")
            or ""
        ),

        "current_skills": current_skills,

        "search_queries": [],
        "raw_jobs": [],
        "normalized_jobs": [],
        "unique_jobs": [],
        "filtered_jobs": [],
        "matched_jobs": [],
        "scored_jobs": [],
        "ranked_jobs": [],
        "final_results": [],
    }

    result = job_opportunities_graph.invoke(
        initial_state
    )

    return result["final_results"]