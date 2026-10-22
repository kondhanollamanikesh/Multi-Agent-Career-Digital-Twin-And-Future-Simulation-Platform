# ============================================================
# Career Digital Twin - Skill Gap Agent
# ============================================================
#
# Workflow:
#
# Exact Match
#          ↓
# Alias / Category Match
#          ↓
# Embedding Match
#          ↓
# Borderline LLM Validation
#          ↓
# Gap Analysis
#          ↓
# Priority Calculation
#          ↓
# Career State
#
# IMPORTANT:
# - Only required_skills affect skill coverage.
# - preferred_skills are reported separately.
# - tools and cloud are reported separately.
# - Exact matches are checked first.
# - Alias / category matching (deterministic, e.g.
#   "backend programming language" -> Python) runs
#   BEFORE embeddings. Embeddings are never the first
#   authority for known skills.
# - Embeddings are used only when exact and alias
#   matching fail.
# - LLM is used only for borderline cases.
# - readiness_score is component based:
#     Skill Coverage 50% + Project Evidence 20% +
#     Experience 10% + DSA/Fundamentals 10% +
#     Education 10%
# ============================================================

import json
import os
import re

from typing import TypedDict, List, Dict, Any, Optional

import numpy as np

from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END

from langchain_core.messages import HumanMessage, SystemMessage

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from langchain_huggingface import HuggingFaceEmbeddings

from scoring_utils import (
    category_requirement_match,
    experience_score,
)


# ============================================================
# 1. ENVIRONMENT
# ============================================================

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

if not NVIDIA_API_KEY:
    raise RuntimeError(
        "NVIDIA_API_KEY is not configured in the .env file."
    )


# ============================================================
# 2. PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ROLE_SKILLS_PATH = os.path.join(
    BASE_DIR,
    "data",
    "role_skills.json"
)


# ============================================================
# 3. LLM
# ============================================================

LLM_MODEL = os.getenv(
    "NVIDIA_LLM_MODEL",
    "nvidia/nemotron-3.5-super-vl-120b-a12b"
)

llm = ChatNVIDIA(
    model=LLM_MODEL,
    api_key=NVIDIA_API_KEY,
    temperature=0.1,
    top_p=1,
    max_completion_tokens=2048,
    timeout=120
)


# ============================================================
# 4. EMBEDDING MODEL
# ============================================================

HF_TOKEN = os.getenv("HF_TOKEN")

EMBEDDING_MODEL = os.getenv(
    "HF_EMBEDDING_MODEL",
    "Qwen/Qwen3-Embedding-0.6B"
)

print(
    f"[Embedding] Loading model: {EMBEDDING_MODEL}"
)

embedding_model_kwargs = {}

if HF_TOKEN:
    embedding_model_kwargs["token"] = HF_TOKEN

embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL,
    model_kwargs=embedding_model_kwargs
)


# ============================================================
# 5. THRESHOLDS
# ============================================================

# Exact embedding match.
EMBEDDING_MATCH_THRESHOLD = float(
    os.getenv(
        "SKILL_SIMILARITY_THRESHOLD",
        "0.78"
    )
)

# Borderline range.
BORDERLINE_LOWER_THRESHOLD = float(
    os.getenv(
        "SKILL_BORDERLINE_LOWER_THRESHOLD",
        "0.60"
    )
)

BORDERLINE_UPPER_THRESHOLD = float(
    os.getenv(
        "SKILL_BORDERLINE_UPPER_THRESHOLD",
        "0.77"
    )
)


# ============================================================
# 6. ROLE SKILL LOADING
# ============================================================

def load_role_skills() -> dict:

    if not os.path.exists(ROLE_SKILLS_PATH):

        print(
            f"[Role Skills] File not found: "
            f"{ROLE_SKILLS_PATH}"
        )

        return {}

    try:

        with open(
            ROLE_SKILLS_PATH,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):

            print(
                "[Role Skills] JSON root must be an object."
            )

            return {}

        return data

    except json.JSONDecodeError as exc:

        print(
            f"[Role Skills] Invalid JSON: {exc}"
        )

        return {}

    except Exception as exc:

        print(
            f"[Role Skills] Failed to load JSON: {exc}"
        )

        return {}


# ============================================================
# 7. EXTRACT REQUIRED SKILLS
# ============================================================

def _extract_required_skills(
    role_data: Any
) -> List[str]:

    if not isinstance(role_data, dict):
        return []

    required = role_data.get(
        "required_skills"
    )

    if isinstance(required, list) and required:

        return [
            str(skill).strip()
            for skill in required
            if str(skill).strip()
        ]

    # ----------------------------------------------------
    # Legacy schema fallback:
    # core_skills / frameworks / backend / ...
    # (tools and cloud are reported separately, so they
    # are not counted as required.)
    # ----------------------------------------------------

    legacy_keys = [
        "core_skills",
        "frameworks",
        "backend",
        "database",
        "deployment",
        "mlops"
    ]

    collected: List[str] = []

    for key in legacy_keys:

        values = role_data.get(key)

        if isinstance(values, list):

            collected.extend(
                str(skill).strip()
                for skill in values
                if str(skill).strip()
            )

    return [
        skill
        for index, skill in enumerate(collected)
        if skill not in collected[:index]
    ]


# ============================================================
# 8. GET REQUIRED SKILLS
# ============================================================

def get_required_skills(
    target_role: str
) -> List[str]:

    data = load_role_skills()

    if not data:
        return []

    target = target_role.strip().lower()

    for role_name, role_data in data.items():

        if role_name.strip().lower() == target:

            return _extract_required_skills(
                role_data
            )

    print(
        f"[Role Skills] Role not found: {target_role}"
    )

    return []


# ============================================================
# 9. SKILL ALIASES
# ============================================================

SKILL_ALIASES = {

    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "machine-learning": "Machine Learning",

    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "deep-learning": "Deep Learning",

    "nlp": "Natural Language Processing",

    "llm": "Large Language Models",
    "llms": "Large Language Models",
    "large language model": "Large Language Models",
    "large language models": "Large Language Models",

    "genai": "Generative AI",
    "gen ai": "Generative AI",
    "generative ai": "Generative AI",

    "langchain": "LangChain",
    "lang chain": "LangChain",

    "langgraph": "LangGraph",
    "lang graph": "LangGraph",

    "react": "React.js",
    "reactjs": "React.js",
    "react.js": "React.js",

    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",

    "express": "Express.js",
    "expressjs": "Express.js",

    "py": "Python",
    "python3": "Python",

    "tf": "TensorFlow",
    "tensorflow": "TensorFlow",

    "pyt": "PyTorch",
    "pytorch": "PyTorch",

    "huggingface": "Hugging Face",
    "hugging face": "Hugging Face",
    "hf": "Hugging Face",

    "fastapi": "FastAPI",
    "fast api": "FastAPI",

    "flask": "Flask",
    "django": "Django",

    "typescript": "TypeScript",
    "ts": "TypeScript",

    "javascript": "JavaScript",
    "js": "JavaScript",

    "html5": "HTML",
    "html": "HTML",

    "css3": "CSS",
    "css": "CSS",

    "sql": "SQL",

    "nosql": "NoSQL",

    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",

    "mongo": "MongoDB",
    "mongodb": "MongoDB",

    "docker": "Docker",
    "docker desktop": "Docker",

    "aws": "AWS",
    "amazon web services": "AWS",

    "gcp": "GCP",
    "google cloud": "GCP",

    "azure": "Azure",
    "microsoft azure": "Azure",

    "terraform": "Terraform",

    "ansible": "Ansible",

    "jenkins": "Jenkins",

    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",

    "mlflow": "MLflow",

    "airflow": "Apache Airflow",
    "apache airflow": "Apache Airflow",

    "spark": "Apache Spark",
    "apache spark": "Apache Spark",

    "kafka": "Apache Kafka",
    "apache kafka": "Apache Kafka",

    "opencv": "OpenCV",

    "numpy": "NumPy",

    "pandas": "Pandas",

    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "scikit learn": "Scikit-learn",

    "matplotlib": "Matplotlib",

    "seaborn": "Seaborn",

    "jupyter": "Jupyter",

    "git": "Git",

    "github": "GitHub",

    "gitlab": "GitLab",

    "linux": "Linux",

    "redis": "Redis",

    "nginx": "Nginx",

    "microservices": "Microservices",

    "rag": "RAG",

    "vector database": "Vector Databases",
    "vector databases": "Vector Databases",

    "transformers": "Transformers",

    "cnn": "CNN",

    "bert": "BERT",

    "gpt": "GPT",

    "yolo": "YOLO",

    "cuda": "CUDA",

    "prompt engineering": "Prompt Engineering",

    "fine tuning": "Fine-tuning",
    "fine-tuning": "Fine-tuning",

    "transfer learning": "Transfer Learning",

    "feature engineering": "Feature Engineering",

    "model monitoring": "Model Monitoring",

    "data pipelines": "Data Pipelines",

    "data warehousing": "Data Warehousing",

    "etl": "ETL",

    "statistics": "Statistics",

    "mathematics": "Mathematics",

    "linear algebra": "Linear Algebra",

    "testing": "Testing",

    "postman": "Postman",

    "swagger": "Swagger",

    "openapi": "OpenAPI",

    "graphql": "GraphQL",

    "grpc": "gRPC",

    "websocket": "WebSocket",

    "oauth": "OAuth",

    "jwt": "JWT",

    "power bi": "Power BI",

    "tableau": "Tableau",

    "snowflake": "Snowflake",

    "databricks": "Databricks",

    "hadoop": "Hadoop",

    "cassandra": "Cassandra",

    "elasticsearch": "Elasticsearch",

    "prometheus": "Prometheus",

    "grafana": "Grafana",

    "pytest": "pytest",

    "unittest": "unittest",

    "selenium": "Selenium",

    "playwright": "Playwright"
}


# ============================================================
# 10. NORMALIZATION
# ============================================================

def normalize_skill(
    skill: str
) -> str:

    if not skill:
        return ""

    value = str(skill).strip()

    if not value:
        return ""

    key = value.lower()

    return SKILL_ALIASES.get(
        key,
        value
    )


def normalize_skills(
    skills: Optional[List[str]]
) -> List[str]:

    if not skills:
        return []

    result = []
    seen = set()

    for skill in skills:

        normalized = normalize_skill(
            skill
        )

        if not normalized:
            continue

        key = normalized.lower()

        if key not in seen:

            seen.add(key)
            result.append(normalized)

    return result


# ============================================================
# 11. TEXT NORMALIZATION
# ============================================================

def normalize_text(
    text: str
) -> str:

    value = str(text).lower().strip()

    value = value.replace(
        "&",
        " and "
    )

    value = re.sub(
        r"[^a-z0-9+#.\-/ ]+",
        " ",
        value
    )

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return value.strip()


# ============================================================
# 12. LANGGRAPH STATE
# ============================================================

class SkillGapState(TypedDict):

    target_role: str

    current_skills: List[str]

    required_skills: List[str]

    preferred_skills: List[str]

    tools: List[str]

    cloud: List[str]

    profile: Dict[str, Any]

    normalized_current: List[str]

    normalized_required: List[str]

    matched_skills: List[str]

    missing_skills: List[str]

    preferred_matches: List[str]

    semantic_matches: List[Dict[str, Any]]

    borderline_matches: List[Dict[str, Any]]

    partial_matches: List[Dict[str, Any]]

    prioritized_gaps: List[Dict[str, Any]]

    skill_coverage: float

    career_twin_v2: Dict[str, Any]


# ============================================================
# 13. NORMALIZE NODE
# ============================================================

def normalize_all_skills(
    state: SkillGapState
) -> SkillGapState:

    state["normalized_current"] = normalize_skills(
        state["current_skills"]
    )

    state["normalized_required"] = normalize_skills(
        state["required_skills"]
    )

    state["preferred_skills"] = normalize_skills(
        state["preferred_skills"]
    )

    state["tools"] = normalize_skills(
        state["tools"]
    )

    state["cloud"] = normalize_skills(
        state["cloud"]
    )

    return state


# ============================================================
# 14. EMBEDDING CACHE
# ============================================================

_embedding_cache: Dict[str, np.ndarray] = {}


def get_embedding(
    text: str
) -> np.ndarray:

    key = text.lower().strip()

    if key in _embedding_cache:
        return _embedding_cache[key]

    vector = embeddings.embed_query(
        text
    )

    vector = np.asarray(
        vector,
        dtype=np.float32
    )

    _embedding_cache[key] = vector

    return vector


# ============================================================
# 15. COSINE SIMILARITY
# ============================================================

def cosine_similarity(
    a: np.ndarray,
    b: np.ndarray
) -> float:

    denominator = (
        np.linalg.norm(a)
        *
        np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(a, b)
        / denominator
    )


# ============================================================
# 16. EXACT MATCH
# ============================================================

def exact_skill_match(
    required_skill: str,
    current_skills: List[str]
) -> Optional[str]:

    required_normalized = normalize_text(
        normalize_skill(required_skill)
    )

    for current in current_skills:

        current_normalized = normalize_text(
            normalize_skill(current)
        )

        if required_normalized == current_normalized:

            return current

    return None


# ============================================================
# 17. SEMANTIC MATCHING NODE
# ============================================================

def semantic_match(
    state: SkillGapState
) -> SkillGapState:

    current = state["normalized_current"]

    required = state["normalized_required"]

    if not required:

        state["matched_skills"] = []
        state["missing_skills"] = []
        state["semantic_matches"] = []
        state["borderline_matches"] = []
        state["partial_matches"] = []
        state["skill_coverage"] = 0.0

        return state

    if not current:

        state["matched_skills"] = []
        state["missing_skills"] = required
        state["semantic_matches"] = []
        state["borderline_matches"] = []
        state["partial_matches"] = []

        state["skill_coverage"] = 0.0

        return state

    print(
        f"[Skill Matching] "
        f"{len(current)} candidate skills vs "
        f"{len(required)} required skills"
    )

    matched = []
    missing = []

    semantic_matches = []
    borderline_matches = []

    # --------------------------------------------------------
    # Precompute embeddings.
    # --------------------------------------------------------

    current_embeddings = {}

    for skill in current:

        current_embeddings[skill] = get_embedding(
            skill
        )

    # --------------------------------------------------------
    # Process every required skill.
    # --------------------------------------------------------

    for required_skill in required:

        # ====================================================
        # STEP 1 - EXACT / ALIAS MATCH
        # ====================================================

        exact_match = exact_skill_match(
            required_skill,
            current
        )

        if exact_match:

            matched.append(
                required_skill
            )

            semantic_matches.append({

                "required":
                    required_skill,

                "matched_with":
                    exact_match,

                "score":
                    1.0,

                "matched":
                    True,

                "match_type":
                    "exact"
            })

            continue

        # ====================================================
        # STEP 2 - ALIAS / CATEGORY MATCH (deterministic)
        #
        # e.g. "Proficiency in at least one backend
        #       programming language (Python...)" -> Python
        #       "Version control with Git" -> Git
        #       "Understanding of HTTP..." -> REST APIs
        #
        # Runs BEFORE embeddings - known skills must not
        # depend on vector similarity.
        # ====================================================

        alias_match = category_requirement_match(
            required_skill,
            current
        )

        if alias_match:

            matched.append(
                required_skill
            )

            semantic_matches.append({

                "required":
                    required_skill,

                "matched_with":
                    alias_match,

                "score":
                    1.0,

                "matched":
                    True,

                "match_type":
                    "alias"
            })

            continue

        # ====================================================
        # STEP 3 - EMBEDDING MATCH
        # ====================================================

        required_vector = get_embedding(
            required_skill
        )

        best_score = 0.0
        best_match = None

        for current_skill in current:

            score = cosine_similarity(
                required_vector,
                current_embeddings[current_skill]
            )

            if score > best_score:

                best_score = score
                best_match = current_skill

        # ====================================================
        # STEP 4 - DETERMINE MATCH TYPE
        # ====================================================

        if (
            best_match
            and best_score >= EMBEDDING_MATCH_THRESHOLD
        ):

            matched.append(
                required_skill
            )

            semantic_matches.append({

                "required":
                    required_skill,

                "matched_with":
                    best_match,

                "score":
                    round(
                        best_score,
                        3
                    ),

                "matched":
                    True,

                "match_type":
                    "embedding"
            })

        elif (
            best_match
            and
            BORDERLINE_LOWER_THRESHOLD
            <= best_score
            <= BORDERLINE_UPPER_THRESHOLD
        ):

            missing.append(
                required_skill
            )

            candidate = {

                "required":
                    required_skill,

                "matched_with":
                    best_match,

                "score":
                    round(
                        best_score,
                        3
                    )
            }

            borderline_matches.append(
                candidate
            )

            semantic_matches.append({

                "required":
                    required_skill,

                "matched_with":
                    best_match,

                "score":
                    round(
                        best_score,
                        3
                    ),

                "matched":
                    False,

                "match_type":
                    "borderline"
            })

        else:

            missing.append(
                required_skill
            )

            semantic_matches.append({

                "required":
                    required_skill,

                "matched_with":
                    best_match,

                "score":
                    round(
                        best_score,
                        3
                    ),

                "matched":
                    False,

                "match_type":
                    "missing"
            })

    state["matched_skills"] = list(
        dict.fromkeys(matched)
    )

    state["missing_skills"] = list(
        dict.fromkeys(missing)
    )

    state["semantic_matches"] = semantic_matches

    state["borderline_matches"] = borderline_matches

    # Until LLM validation runs, every borderline
    # candidate counts as partial evidence.
    state["partial_matches"] = list(
        borderline_matches
    )

    state["skill_coverage"] = round(
        (
            len(state["matched_skills"])
            /
            len(required)
        )
        * 100,
        2
    )

    print(
        "[Skill Matching] Exact/embedding matched:",
        len(state["matched_skills"])
    )

    print(
        "[Skill Matching] Borderline:",
        len(borderline_matches)
    )

    print(
        "[Skill Matching] Missing:",
        len(state["missing_skills"])
    )

    return state


# ============================================================
# 18. BORDERLINE LLM VALIDATION
# ============================================================

def validate_borderline_matches(
    state: SkillGapState
) -> SkillGapState:

    borderline = state[
        "borderline_matches"
    ]

    if not borderline:

        print(
            "[Borderline] No borderline skills."
        )

        return state

    validated = []

    original_borderline = list(borderline)

    for candidate in borderline:

        required_skill = candidate[
            "required"
        ]

        current_skill = candidate[
            "matched_with"
        ]

        score = candidate[
            "score"
        ]

        prompt = f"""
Determine whether a candidate skill satisfies a required
technical skill.

Required skill:
{required_skill}

Candidate skill:
{current_skill}

Embedding similarity:
{score}

Rules:

- Be strict.
- Related does not mean equivalent.
- Python does not automatically satisfy Pandas.
- Machine Learning does not automatically satisfy Statistics.
- Machine Learning does not automatically satisfy Linear Algebra.
- JavaScript does not automatically satisfy TypeScript.
- Only return MATCH when the candidate skill reasonably
  demonstrates the required skill.

Return ONLY JSON:

{{
    "decision": "MATCH",
    "confidence": 0.90,
    "reason": "short reason"
}}

Decision must be MATCH or NO_MATCH.
"""

        try:

            response = llm.invoke(
                [
                    SystemMessage(
                        content=(
                            "You are a strict technical "
                            "skill equivalence validator."
                        )
                    ),
                    HumanMessage(
                        content=prompt
                    )
                ]
            )

            raw = response.content

            if isinstance(raw, list):

                raw = "".join(
                    str(item)
                    for item in raw
                )

            raw = str(raw).strip()

            start = raw.find("{")
            end = raw.rfind("}")

            if start == -1 or end == -1:
                continue

            data = json.loads(
                raw[start:end + 1]
            )

            decision = str(
                data.get(
                    "decision",
                    "NO_MATCH"
                )
            ).upper().strip()

            confidence = float(
                data.get(
                    "confidence",
                    0
                )
            )

            reason = str(
                data.get(
                    "reason",
                    ""
                )
            )

            if decision == "MATCH":

                validated.append({

                    "required":
                        required_skill,

                    "matched_with":
                        current_skill,

                    "embedding_score":
                        score,

                    "llm_decision":
                        "MATCH",

                    "llm_confidence":
                        round(
                            confidence,
                            3
                        ),

                    "reason":
                        reason
                })

        except Exception as exc:

            print(
                "[Borderline] Validation failed:",
                exc
            )

    matched = list(
        state["matched_skills"]
    )

    missing = list(
        state["missing_skills"]
    )

    for item in validated:

        skill = item["required"]

        if skill not in matched:
            matched.append(skill)

        if skill in missing:
            missing.remove(skill)

        for match in state[
            "semantic_matches"
        ]:

            if match["required"] == skill:

                match["matched"] = True

                match["match_type"] = (
                    "llm_validated"
                )

                match["llm_validation"] = {

                    "decision":
                        item["llm_decision"],

                    "confidence":
                        item["llm_confidence"],

                    "reason":
                        item["reason"]
                }

                break

    state["matched_skills"] = list(
        dict.fromkeys(matched)
    )

    state["missing_skills"] = list(
        dict.fromkeys(missing)
    )

    state["borderline_matches"] = validated

    validated_skills = {
        item["required"]
        for item in validated
    }

    # Borderline skills that were NOT validated as full
    # matches stay missing but earn partial readiness
    # credit (they are still real gaps to close).
    state["partial_matches"] = [
        candidate
        for candidate in original_borderline
        if candidate["required"]
        not in validated_skills
    ]

    required = state[
        "normalized_required"
    ]

    if required:

        state["skill_coverage"] = round(
            (
                len(state["matched_skills"])
                /
                len(required)
            )
            * 100,
            2
        )

    print(
        "[Borderline] Validated matches:",
        len(validated)
    )

    print(
        "[Borderline] Final coverage:",
        state["skill_coverage"]
    )

    return state


# ============================================================
# 19. GAP ANALYSIS
# ============================================================

def analyze_gaps(
    state: SkillGapState
) -> SkillGapState:

    missing = state[
        "missing_skills"
    ]

    if not missing:

        state["prioritized_gaps"] = []

        return state

    role = state[
        "target_role"
    ]

    prompt = f"""
Analyze the missing technical skills for this career role.

Target role:
{role}

Missing skills:
{json.dumps(missing)}

For each skill return:

skill
importance
priority
learning_suggestion

Priority must be:

High
Medium
Low

Return ONLY JSON array.
"""

    try:

        response = llm.invoke(
            [
                SystemMessage(
                    content=(
                        "You are a career skill-gap "
                        "analysis system."
                    )
                ),
                HumanMessage(
                    content=prompt
                )
            ]
        )

        raw = response.content

        if isinstance(raw, list):

            raw = "".join(
                str(item)
                for item in raw
            )

        raw = str(raw).strip()

        start = raw.find("[")
        end = raw.rfind("]")

        if start != -1 and end != -1:

            data = json.loads(
                raw[start:end + 1]
            )

            if isinstance(data, list):

                result = []

                missing_normalized = {
                    normalize_text(skill): skill
                    for skill in missing
                }

                for item in data:

                    if not isinstance(
                        item,
                        dict
                    ):
                        continue

                    skill = str(
                        item.get(
                            "skill",
                            ""
                        )
                    ).strip()

                    if not skill:
                        continue

                    # Make sure the LLM cannot invent
                    # additional missing skills.
                    if normalize_text(skill) not in (
                        missing_normalized
                    ):

                        continue

                    priority = item.get(
                        "priority",
                        "Medium"
                    )

                    if priority not in {
                        "High",
                        "Medium",
                        "Low"
                    }:

                        priority = "Medium"

                    result.append({

                        "skill":
                            missing_normalized[
                                normalize_text(skill)
                            ],

                        "importance":
                            str(
                                item.get(
                                    "importance",
                                    "Required for the target role"
                                )
                            ),

                        "priority":
                            priority,

                        "learning_suggestion":
                            str(
                                item.get(
                                    "learning_suggestion",
                                    f"Build practical projects using {skill}"
                                )
                            )
                    })

                if result:

                    state[
                        "prioritized_gaps"
                    ] = result

                    return state

    except Exception as exc:

        print(
            "[Gap Analysis] LLM failed:",
            exc
        )

    # --------------------------------------------------------
    # Fallback
    # --------------------------------------------------------

    state["prioritized_gaps"] = [

        {
            "skill": skill,

            "importance":
                "Required for the target role",

            "priority":
                "Medium",

            "learning_suggestion":
                f"Build practical projects using {skill}"
        }

        for skill in missing
    ]

    return state


# ============================================================
# 20. PRIORITY CALCULATION
# ============================================================

def calculate_priorities(
    state: SkillGapState
) -> SkillGapState:

    weight = {

        "High": 3,

        "Medium": 2,

        "Low": 1
    }

    gaps = state[
        "prioritized_gaps"
    ]

    for gap in gaps:

        gap["priority_score"] = weight.get(
            gap.get(
                "priority",
                "Medium"
            ),
            2
        )

    gaps.sort(
        key=lambda item:
            item.get(
                "priority_score",
                0
            ),
        reverse=True
    )

    state[
        "prioritized_gaps"
    ] = gaps

    return state


# ============================================================
# 20B. READINESS COMPONENTS
# ============================================================
#
# readiness_score is explicitly component based:
#
#   Skill Coverage   50%
#   Project Evidence 20%
#   Experience       10%
#   DSA/Fundamentals 10%
#   Education        10%
#
# Skill Coverage itself uses exact + alias/category +
# semantic matching (never embeddings alone).

READINESS_WEIGHTS = {

    "skill_coverage": 0.50,
    "project_evidence": 0.20,
    "experience": 0.10,
    "fundamentals": 0.10,
    "education": 0.10,
}


FUNDAMENTAL_REQUIREMENT_KEYS = [
    "data structures",
    "algorithms",
    "object-oriented",
    "object oriented",
    "oop",
    "dsa",
    "system design",
    "design patterns",
    "computer science",
    "problem solving",
    "linear algebra",
    "probability",
    "statistics",
    "mathematics",
    "discrete math",
]


FUNDAMENTAL_TOPICS = [
    "data structures",
    "algorithms",
    "object oriented programming",
    "oop",
    "dsa",
    "system design",
    "design patterns",
    "dbms",
    "sql",
    "operating systems",
    "computer networks",
    "statistics",
    "linear algebra",
    "probability",
    "discrete mathematics",
    "problem solving",
]


def _topic_in_text(topic: str, text: str) -> bool:
    """Word-boundary topic check."""

    if not topic or not text:
        return False

    return re.search(
        r"(?<![a-z0-9])"
        + re.escape(topic)
        + r"(?![a-z0-9])",
        text
    ) is not None


def is_fundamental_requirement(
    required_skill: str
) -> bool:
    """True when a required skill describes
    DSA / CS fundamentals."""

    text = normalize_text(required_skill)

    return any(
        _topic_in_text(key, text)
        for key in FUNDAMENTAL_REQUIREMENT_KEYS
    )


def project_score(
    projects: Optional[List[str]]
) -> float:
    """Project evidence 0 - 100."""

    count = len(projects or [])

    if count <= 0:
        return 0.0

    if count == 1:
        return 50.0

    if count == 2:
        return 75.0

    return 100.0


def education_score(
    education: Optional[List[str]]
) -> float:
    """Education evidence 0 - 100."""

    if not education:
        return 0.0

    text = " ".join(
        str(item) for item in education
    ).lower()

    degree_keys = [
        "phd",
        "doctorate",
        "master",
        "m.tech",
        "mtech",
        "m.s.",
        "mca",
        "mba",
        "bachelor",
        "b.tech",
        "btech",
        "b.e.",
        "b.s.",
        "bca",
        "b.sc",
        "m.sc",
        "graduate degree",
    ]

    if any(key in text for key in degree_keys):
        return 100.0

    return 60.0


def fundamentals_score(
    state: SkillGapState
) -> float:
    """DSA / fundamentals coverage 0 - 100."""

    required = state.get(
        "normalized_required",
        []
    )

    matched = set(
        state.get("matched_skills", [])
    )

    partial = {
        item.get("required")
        for item in state.get(
            "partial_matches",
            []
        )
    }

    fundamental_requirements = [
        skill
        for skill in required
        if is_fundamental_requirement(skill)
    ]

    # --------------------------------------------------
    # Role explicitly requires fundamentals:
    # measure coverage of those requirements.
    # --------------------------------------------------

    if fundamental_requirements:

        credit = 0.0

        for skill in fundamental_requirements:

            if skill in matched:
                credit += 1.0

            elif skill in partial:
                credit += 0.5

        return round(
            credit
            / len(fundamental_requirements)
            * 100,
            2,
        )

    # --------------------------------------------------
    # Role does not list fundamentals explicitly:
    # infer from the candidate's own evidence
    # (3 topics = full evidence).
    # --------------------------------------------------

    current = state.get(
        "normalized_current",
        []
    )

    current_text = [
        normalize_text(skill)
        for skill in current
    ]

    evidenced = sum(
        1
        for topic in FUNDAMENTAL_TOPICS
        if any(
            _topic_in_text(topic, text)
            for text in current_text
        )
    )

    return round(
        min(evidenced / 3, 1.0) * 100,
        2
    )


def experience_component_score(
    profile: Dict[str, Any]
) -> float:
    """Experience evidence 0 - 100.

    Combines the categorical level match between the
    candidate and the role with actual resume
    experience entries.
    """

    level_match = experience_score(
        profile.get("experience_level"),
        profile.get("role_experience_level"),
    )

    # Unknown levels are neutral INSIDE readiness only
    # (job scoring still returns None for unknown).
    if level_match is None:
        level_match = 0.7

    has_experience = bool(
        profile.get("experience")
    )

    evidence = 1.0 if has_experience else 0.4

    return round(
        (level_match + evidence) / 2 * 100,
        2,
    )


# ============================================================
# 21. BUILD CAREER TWIN
# ============================================================

def build_career_twin_v2(
    state: SkillGapState
) -> SkillGapState:

    matched = state[
        "matched_skills"
    ]

    missing = state[
        "missing_skills"
    ]

    required = state[
        "normalized_required"
    ]

    preferred = state[
        "preferred_skills"
    ]

    tools = state[
        "tools"
    ]

    cloud = state[
        "cloud"
    ]

    prioritized = state[
        "prioritized_gaps"
    ]

    partial = state.get(
        "partial_matches",
        []
    )

    high_priority = [

        gap["skill"]

        for gap in prioritized

        if gap.get(
            "priority"
        ) == "High"
    ]

    profile = state.get(
        "profile",
        {}
    ) or {}

    # --------------------------------------------------
    # Component based readiness.
    #
    #   Skill Coverage   50%   (exact + alias/category +
    #                          semantic matching,
    #                          partial credit 0.5)
    #   Project Evidence 20%
    #   Experience       10%
    #   DSA/Fundamentals 10%
    #   Education        10%
    # --------------------------------------------------

    total_required = len(required)

    if total_required > 0:

        skill_component = (
            len(matched) * 1.0
            + len(partial) * 0.5
        ) / total_required * 100

    else:

        skill_component = 0.0

    project_component = project_score(
        profile.get("projects")
    )

    experience_component = (
        experience_component_score(profile)
    )

    fundamentals_component = fundamentals_score(
        state
    )

    education_component = education_score(
        profile.get("education")
    )

    readiness_score = round(

        skill_component
        * READINESS_WEIGHTS["skill_coverage"]

        + project_component
        * READINESS_WEIGHTS["project_evidence"]

        + experience_component
        * READINESS_WEIGHTS["experience"]

        + fundamentals_component
        * READINESS_WEIGHTS["fundamentals"]

        + education_component
        * READINESS_WEIGHTS["education"],

        2
    )

    readiness_breakdown = {

        "skill_coverage":
            round(skill_component, 2),

        "project_evidence":
            round(project_component, 2),

        "experience":
            round(experience_component, 2),

        "fundamentals":
            round(fundamentals_component, 2),

        "education":
            round(education_component, 2),

        "weights":
            dict(READINESS_WEIGHTS),
    }

    # Strict coverage kept for reporting/debugging.
    strict_coverage = round(
        state["skill_coverage"],
        2
    )

    career_twin = {

        "target_role":
            state["target_role"],

        "career_state": {

            "readiness_score":
                readiness_score,

            "readiness_breakdown":
                readiness_breakdown,

            # Placeholder only. Market alignment is
            # computed in digital_twin.py against the
            # actual job market (role demand / skill
            # demand / profile-market fit / location).
            # It must NOT mirror readiness_score.
            "market_alignment":
                0.0,

            "strengths":
                matched,

            "weaknesses":
                high_priority,

            "skill_gaps":
                missing,

            "total_required":
                total_required,

            "total_matched":
                len(matched),

            "total_missing":
                len(missing),

            "total_partial":
                len(partial),

            "strict_coverage":
                strict_coverage
        },

        "skill_analysis": {

            "required_skills":
                required,

            "matched_skills":
                matched,

            "missing_skills":
                missing,

            "preferred_skills":
                preferred,

            "tools":
                tools,

            "cloud":
                cloud
        },

        "semantic_matches":
            state["semantic_matches"],

        "borderline_validation":
            state["borderline_matches"],

        "partial_matches":
            partial,

        "prioritized_gaps":
            prioritized
    }

    state[
        "career_twin_v2"
    ] = career_twin

    return state


# ============================================================
# 22. BUILD GRAPH
# ============================================================

def build_skill_gap_graph():

    workflow = StateGraph(
        SkillGapState
    )

    workflow.add_node(
        "normalize_skills",
        normalize_all_skills
    )

    workflow.add_node(
        "semantic_match",
        semantic_match
    )

    workflow.add_node(
        "validate_borderline",
        validate_borderline_matches
    )

    workflow.add_node(
        "analyze_gaps",
        analyze_gaps
    )

    workflow.add_node(
        "calculate_priorities",
        calculate_priorities
    )

    workflow.add_node(
        "build_career_twin",
        build_career_twin_v2
    )

    workflow.add_edge(
        START,
        "normalize_skills"
    )

    workflow.add_edge(
        "normalize_skills",
        "semantic_match"
    )

    workflow.add_edge(
        "semantic_match",
        "validate_borderline"
    )

    workflow.add_edge(
        "validate_borderline",
        "analyze_gaps"
    )

    workflow.add_edge(
        "analyze_gaps",
        "calculate_priorities"
    )

    workflow.add_edge(
        "calculate_priorities",
        "build_career_twin"
    )

    workflow.add_edge(
        "build_career_twin",
        END
    )

    return workflow.compile()


# ============================================================
# 23. COMPILE ONCE
# ============================================================

skill_gap_graph = build_skill_gap_graph()


# ============================================================
# 24. MAIN WORKFLOW FUNCTION
# ============================================================

def run_skill_gap_workflow(
    current_skills: List[str],
    target_role: str,
    required_skills: Optional[List[str]] = None,
    preferred_skills: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    cloud: Optional[List[str]] = None,
    profile: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:

    current_skills = current_skills or []

    preferred_skills = preferred_skills or []

    tools = tools or []

    cloud = cloud or []

    profile = profile or {}

    if required_skills is None:

        required_skills = get_required_skills(
            target_role
        )

    required_skills = required_skills or []

    print()
    print(
        "=========================================="
    )

    print(
        "[Skill Gap Agent]"
    )

    print(
        "Target role:",
        target_role
    )

    print(
        "Current skills:",
        len(current_skills)
    )

    print(
        "Required skills:",
        len(required_skills)
    )

    print(
        "Preferred skills:",
        len(preferred_skills)
    )

    print(
        "Tools:",
        len(tools)
    )

    print(
        "Cloud:",
        len(cloud)
    )

    print(
        "=========================================="
    )

    initial_state: SkillGapState = {

        "target_role":
            target_role,

        "current_skills":
            current_skills,

        "required_skills":
            required_skills,

        "preferred_skills":
            preferred_skills,

        "tools":
            tools,

        "cloud":
            cloud,

        "profile":
            profile,

        "normalized_current":
            [],

        "normalized_required":
            [],

        "matched_skills":
            [],

        "missing_skills":
            [],

        "preferred_matches":
            [],

        "semantic_matches":
            [],

        "borderline_matches":
            [],

        "partial_matches":
            [],

        "prioritized_gaps":
            [],

        "skill_coverage":
            0.0,

        "career_twin_v2":
            {}
    }

    result = skill_gap_graph.invoke(
        initial_state
    )

    print(
        "[Skill Gap Agent] Workflow completed."
    )

    return result[
        "career_twin_v2"
    ]


# ============================================================
# 25. BACKWARD COMPATIBILITY
# ============================================================

def calculate_skill_gap_with_workflow(
    current_skills: List[str],
    target_role: str
) -> Dict[str, Any]:

    return run_skill_gap_workflow(
        current_skills=current_skills,
        target_role=target_role
    )


# Original name kept for older scripts/tests.

calculate_skill_gap = (
    calculate_skill_gap_with_workflow
)