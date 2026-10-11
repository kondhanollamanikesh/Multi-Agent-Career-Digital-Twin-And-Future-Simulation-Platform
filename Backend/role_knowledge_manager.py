import json
import os

from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from models import RoleKnowledge
from database import role_knowledge_collection
from agents.role_research_agent import (
    research_role as research_role_agent
)


load_dotenv()


# ============================================================
# CONFIGURATION
# ============================================================

ROLE_KNOWLEDGE_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "role_skills.json"
)


# ============================================================
# LLM
# ============================================================

client = ChatNVIDIA(

    model=os.getenv(
        "NVIDIA_LLM_MODEL",
        "nvidia/nemotron-3-super-120b-a12b"
    ),

    api_key=os.getenv(
        "NVIDIA_API_KEY"
    ),

    temperature=0,

    top_p=1,

    max_completion_tokens=2048,

    timeout=300
)


# ============================================================
# EXTRACTION SCHEMA
# ============================================================

class RoleKnowledgeExtraction(BaseModel):

    required_skills: list[str] = Field(
        default_factory=list
    )

    preferred_skills: list[str] = Field(
        default_factory=list
    )

    tools: list[str] = Field(
        default_factory=list
    )

    cloud: list[str] = Field(
        default_factory=list
    )

    responsibilities: list[str] = Field(
        default_factory=list
    )


structured_role_model = client.with_structured_output(
    RoleKnowledgeExtraction
)


# ============================================================
# NORMALIZATION
# ============================================================

ROLE_SKILL_ALIASES = {

    "ml": "Machine Learning",

    "machine learning":
        "Machine Learning",

    "dl": "Deep Learning",

    "deep learning":
        "Deep Learning",

    "nlp":
        "Natural Language Processing",

    "llm":
        "Large Language Models",

    "llms":
        "Large Language Models",

    "langchain":
        "LangChain",

    "langgraph":
        "LangGraph",

    "fast api":
        "FastAPI",

    "fastapi":
        "FastAPI",

    "react":
        "React.js",

    "reactjs":
        "React.js",

    "mongodb":
        "MongoDB",

    "mongo":
        "MongoDB",

    "postgres":
        "PostgreSQL",

    "postgresql":
        "PostgreSQL",

    "mysql":
        "MySQL",

    "rest":
        "REST APIs",

    "rest api":
        "REST APIs",

    "python":
        "Python",

    "java":
        "Java",

    "javascript":
        "JavaScript",

    "typescript":
        "TypeScript",

    "docker":
        "Docker",

    "kubernetes":
        "Kubernetes",

    "aws":
        "AWS",

    "azure":
        "Azure",

    "gcp":
        "GCP",

    "git":
        "Git",

    "github":
        "GitHub",

    "rag":
        "RAG",

    "prompt engineering":
        "Prompt Engineering"
}


def normalize_list(
    values: list[str]
) -> list[str]:

    result = []
    seen = set()

    for value in values:

        if not value:
            continue

        clean = str(value).strip()

        key = clean.lower()

        normalized = ROLE_SKILL_ALIASES.get(
            key,
            clean
        )

        normalized_key = normalized.lower()

        if normalized_key not in seen:

            seen.add(normalized_key)

            result.append(
                normalized
            )

    return result


# ============================================================
# JSON CACHE
# ============================================================

def load_json_cache() -> dict:

    if not os.path.exists(
        ROLE_KNOWLEDGE_FILE
    ):

        return {}

    try:

        with open(
            ROLE_KNOWLEDGE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):

            return data

    except Exception as exc:

        print(
            "[Role Knowledge] JSON error:",
            exc
        )

    return {}


def save_json_cache(
    knowledge: RoleKnowledge
):

    data = load_json_cache()

    data[knowledge.role] = (
        knowledge.model_dump()
    )

    os.makedirs(
        os.path.dirname(
            ROLE_KNOWLEDGE_FILE
        ),
        exist_ok=True
    )

    with open(
        ROLE_KNOWLEDGE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# MONGODB CACHE
# ============================================================

def get_from_mongodb(
    role: str,
    experience_level: str,
    industry: str
) -> Optional[RoleKnowledge]:

    document = (
        role_knowledge_collection.find_one(
            {
                "role": role,
                "experience_level":
                    experience_level,
                "industry":
                    industry
            }
        )
    )

    if not document:

        return None

    document.pop(
        "_id",
        None
    )

    return RoleKnowledge(
        **document
    )


def save_to_mongodb(
    knowledge: RoleKnowledge
):

    role_knowledge_collection.update_one(

        {
            "role":
                knowledge.role,

            "experience_level":
                knowledge.experience_level,

            "industry":
                knowledge.industry
        },

        {
            "$set":
                knowledge.model_dump()
        },

        upsert=True
    )


# ============================================================
# RESEARCH ROLE
# ============================================================

def research_role(
    role: str,
    experience_level: str,
    industry: str
) -> RoleKnowledge:

    print(
        f"[Role Research] Researching {role}"
    )

    knowledge = None

    # ----------------------------------------------------
    # The structured LLM occasionally returns an empty
    # skill list. Retry before accepting - an empty entry
    # would be saved to the cache and then treated as a
    # legacy miss forever (re-researched on every call).
    # ----------------------------------------------------

    for attempt in range(3):

        knowledge = research_role_agent(
            target_role=role,
            experience_level=experience_level,
            industry=industry
        )

        knowledge.required_skills = normalize_list(
            knowledge.required_skills
        )

        knowledge.preferred_skills = normalize_list(
            knowledge.preferred_skills
        )

        knowledge.tools = normalize_list(
            knowledge.tools
        )

        knowledge.cloud = normalize_list(
            knowledge.cloud
        )

        if knowledge.required_skills:

            break

        print(
            "[Role Research] Empty result, "
            f"retrying ({attempt + 1}/3)..."
        )

    if not knowledge or not knowledge.required_skills:

        raise ValueError(
            f"Role research returned no required "
            f"skills for {role!r} after retries."
        )

    return knowledge


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def get_or_create_role_knowledge(
    role: str,
    experience_level: str = "Entry Level",
    industry: str = "Artificial Intelligence"
) -> RoleKnowledge:

    role = role.strip()

    experience_level = (
        experience_level
        or "Entry Level"
    ).strip()

    industry = (
        industry
        or "Artificial Intelligence"
    ).strip()

    # --------------------------------------------------------
    # 1. MongoDB
    # --------------------------------------------------------

    cached = get_from_mongodb(
        role,
        experience_level,
        industry
    )

    if cached:

        print(
            "[Role Knowledge] MongoDB CACHE HIT"
        )

        return cached

    # --------------------------------------------------------
    # 2. JSON
    # --------------------------------------------------------

    json_data = load_json_cache()

    for role_name, data in json_data.items():

        if (
            role_name.lower().strip()
            == role.lower().strip()
        ):

            required_skills = data.get(
                "required_skills",
                []
            )

            # Legacy entries (core_skills / frameworks /
            # backend ...) are treated as a cache miss so
            # the research agent can rebuild them.

            if not required_skills:

                continue

            knowledge = RoleKnowledge(

                role=role,

                experience_level=
                    data.get(
                        "experience_level",
                        experience_level
                    ),

                category=
                    data.get(
                        "category"
                    ),

                industry=
                    data.get(
                        "industry",
                        industry
                    ),

                required_skills=
                    required_skills,

                preferred_skills=
                    data.get(
                        "preferred_skills",
                        []
                    ),

                tools=
                    data.get(
                        "tools",
                        []
                    ),

                cloud=
                    data.get(
                        "cloud",
                        []
                    ),

                responsibilities=
                    data.get(
                        "responsibilities",
                        []
                    ),

                sources=
                    data.get(
                        "sources",
                        []
                    )
            )

            print(
                "[Role Knowledge] JSON CACHE HIT"
            )

            save_to_mongodb(
                knowledge
            )

            return knowledge

    # --------------------------------------------------------
    # 3. LLM research
    # --------------------------------------------------------

    print(
        "[Role Knowledge] CACHE MISS"
    )

    knowledge = research_role(
        role,
        experience_level,
        industry
    )

    # --------------------------------------------------------
    # 4. Save both caches
    # --------------------------------------------------------

    save_json_cache(
        knowledge
    )

    save_to_mongodb(
        knowledge
    )

    print(
        "[Role Knowledge] Knowledge saved."
    )

    return knowledge