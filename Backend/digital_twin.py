# ==========================================
# Career Digital Twin - Digital Twin Builder
# ==========================================

from langchain_community.document_loaders import PyPDFLoader

from pydantic import BaseModel, Field

from typing import List, Dict, Any

from langchain_nvidia_ai_endpoints import ChatNVIDIA

import os
import json
import sys

# Windows consoles default to cp1252 and crash when the
# LLM returns unicode characters (e.g. non-breaking hyphens).

if hasattr(sys.stdout, "reconfigure"):

    sys.stdout.reconfigure(
        encoding="utf-8",
        errors="replace"
    )

    sys.stderr.reconfigure(
        encoding="utf-8",
        errors="replace"
    )

from dotenv import load_dotenv

from models import Preferences

import role_knowledge_manager

from agents.skill_gap_agent import (
    run_skill_gap_workflow
)

from agents.job_opportunities_agent import (
    find_job_opportunities
)

from scoring_utils import (
    compute_market_alignment_details
)

from structured_llm import StructuredLLM


# ==========================================
# 1. ENVIRONMENT
# ==========================================

load_dotenv()


# ==========================================
# 2. CONFIGURATION
# ==========================================

ROLE_KNOWLEDGE_FILE = os.path.join(
    os.path.dirname(__file__),
    "data",
    "role_skills.json"
)


# ==========================================
# 3. RESUME EXTRACTION SCHEMA
# ==========================================

class ResumeSchema(BaseModel):

    education: List[str] = Field(
        default_factory=list
    )

    skills: List[str] = Field(
        default_factory=list
    )

    projects: List[str] = Field(
        default_factory=list
    )

    experience: List[str] = Field(
        default_factory=list
    )

    certifications: List[str] = Field(
        default_factory=list
    )

    achievements: List[str] = Field(
        default_factory=list
    )

    target_roles: List[str] = Field(
        default_factory=list
    )

    preferences: Preferences = Field(
        default_factory=Preferences
    )


# ==========================================
# 4. LLM
# ==========================================

client = ChatNVIDIA(

    model=os.getenv(
        "NVIDIA_LLM_MODEL",
        "nvidia/nemotron-3-super-120b-a12b"
    ),

    api_key=os.getenv(
        "NVIDIA_API_KEY"
    ),

    temperature=1,

    top_p=1,

    max_completion_tokens=4096,

    timeout=300
)


# ==========================================
# 5. STRUCTURED RESUME MODEL
# ==========================================

# with_structured_output() ends on a format the NVIDIA API
# always rejects with HTTP 400 (nvext.guided_json), which
# masks the real failure. StructuredLLM sends only the
# accepted formats and retries.

structured_model = StructuredLLM(
    client,
    ResumeSchema
)


# ==========================================
# 6. ROLE KNOWLEDGE SCHEMA
# ==========================================

class RoleKnowledge(BaseModel):

    required_skills: List[str] = Field(
        default_factory=list
    )

    preferred_skills: List[str] = Field(
        default_factory=list
    )

    tools: List[str] = Field(
        default_factory=list
    )

    cloud: List[str] = Field(
        default_factory=list
    )


class RoleKnowledgeExtraction(BaseModel):

    required_skills: List[str] = Field(
        default_factory=list
    )

    preferred_skills: List[str] = Field(
        default_factory=list
    )

    tools: List[str] = Field(
        default_factory=list
    )

    cloud: List[str] = Field(
        default_factory=list
    )


# ==========================================
# 7. STRUCTURED ROLE MODEL
# ==========================================

structured_role_model = client.with_structured_output(
    RoleKnowledgeExtraction
)


# ==========================================
# 8. CAREER STATE
# ==========================================

class CareerState(BaseModel):

    readiness_score: float = 0.0

    readiness_breakdown: Dict[str, Any] = Field(
        default_factory=dict
    )

    market_alignment: float = 0.0

    market_alignment_breakdown: Dict[str, Any] = Field(
        default_factory=dict
    )

    market_alignment_explanation: List[str] = Field(
        default_factory=list
    )

    strengths: List[str] = Field(
        default_factory=list
    )

    weaknesses: List[str] = Field(
        default_factory=list
    )

    skill_gaps: List[str] = Field(
        default_factory=list
    )

    total_required: int = 0

    total_matched: int = 0

    total_missing: int = 0

    total_partial: int = 0

    prioritized_gaps: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    semantic_matches: List[Dict[str, Any]] = Field(
        default_factory=list
    )


# ==========================================
# 9. CAREER TWIN
# ==========================================

class CareerTwin(BaseModel):

    user_id: str

    profile: Dict[str, str] = Field(
        default_factory=dict
    )

    education: List[str] = Field(
        default_factory=list
    )

    skills: List[str] = Field(
        default_factory=list
    )

    projects: List[str] = Field(
        default_factory=list
    )

    experience: List[str] = Field(
        default_factory=list
    )

    certifications: List[str] = Field(
        default_factory=list
    )

    achievements: List[str] = Field(
        default_factory=list
    )

    target_roles: List[str] = Field(
        default_factory=list
    )

    preferences: Preferences = Field(
        default_factory=Preferences
    )

    career_state: CareerState = Field(
        default_factory=CareerState
    )

    job_opportunities: List[Dict[str, Any]] = Field(
        default_factory=list
    )

    learning_history: List[str] = Field(
        default_factory=list
    )

    twin_version: int = 2


# ==========================================
# 10. LOAD ROLE KNOWLEDGE
# ==========================================

def load_role_knowledge():

    if not os.path.exists(
        ROLE_KNOWLEDGE_FILE
    ):

        print(
            "[Role Cache] JSON file does not exist."
        )

        return {}

    try:

        with open(
            ROLE_KNOWLEDGE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if not isinstance(data, dict):

            print(
                "[Role Cache] JSON root must be an object."
            )

            return {}

        print(
            "[Role Cache] Loaded role knowledge."
        )

        return data

    except json.JSONDecodeError:

        print(
            "[Role Cache] JSON file is invalid."
        )

        return {}

    except Exception as exc:

        print(
            "[Role Cache] Error loading JSON:",
            exc
        )

        return {}


# ==========================================
# 11. SAVE ROLE KNOWLEDGE
# ==========================================

def save_role_knowledge(
    role_name: str,
    role_knowledge: RoleKnowledge
):

    data = load_role_knowledge()

    data[role_name] = (
        role_knowledge.model_dump()
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

    print(
        f"[Role Cache] Saved '{role_name}' to JSON."
    )


# ==========================================
# 12. RESEARCH ROLE KNOWLEDGE
# ==========================================

def research_role_knowledge(
    target_role: str,
    experience_level: str,
    industry: str
):

    print(
        f"[Role Research] Researching: {target_role}"
    )

    role_knowledge = (
        role_knowledge_manager.research_role(
            role=target_role,
            experience_level=experience_level,
            industry=industry
        )
    )

    print(
        "[Role Research] Role knowledge generated."
    )

    return role_knowledge


# ==========================================
# 13. GET OR CREATE ROLE KNOWLEDGE
# ==========================================

def get_or_create_role_knowledge(
    target_role: str,
    experience_level: str,
    industry: str
):

    print(
        f"[Role Knowledge] Checking cache for: "
        f"{target_role}"
    )

    role_knowledge = (
        role_knowledge_manager.get_or_create_role_knowledge(
            role=target_role,
            experience_level=experience_level,
            industry=industry
        )
    )

    print(
        "[Role Knowledge] Role knowledge ready."
    )

    return role_knowledge


# ==========================================
# 14. CREATE CAREER TWIN
# ==========================================

def create_career_twin(
    resume_path,
    user_id,
    preferences
):

    print(
        "\n=========================================="
    )

    print(
        "CAREER DIGITAL TWIN"
    )

    print(
        "=========================================="
    )

    # ==========================================
    # STEP 1: LOAD PDF
    # ==========================================

    print("[1] Loading PDF...")

    loader = PyPDFLoader(
        resume_path
    )

    docs = loader.load()

    print("[2] PDF loaded.")

    # ==========================================
    # STEP 2: EXTRACT TEXT
    # ==========================================

    resume_text = "\n".join(

        document.page_content

        for document in docs
    )

    print(
        "[3] Resume text extracted."
    )

    print(
        "[INFO] Resume characters:",
        len(resume_text)
    )

    # ==========================================
    # STEP 3: RESUME EXTRACTION
    # ==========================================

    prompt = f"""
You are a resume information extraction system.

Extract structured information from the resume text below.

IMPORTANT RULES:

1. Extract ONLY information actually present.
2. Do NOT invent information.
3. Return empty lists when information is absent.
4. Preserve actual wording where useful.
5. Do not explain anything.

FIELDS:

education:
Extract degrees, colleges, universities, programs,
percentages, CGPA, years and education status.

skills:
Extract ALL technical and professional skills explicitly mentioned.

projects:
Extract ALL projects mentioned.

experience:
Extract internships, jobs and professional experience.
Do NOT put projects here.

certifications:
Extract certificates and certifications.

achievements:
Extract awards, accomplishments, coding achievements,
competitions, hackathons and other accomplishments.

target_roles:
Extract explicitly stated target roles.

preferences:
Extract ONLY explicitly mentioned preferences.

Resume:

{resume_text}
"""

    # ==========================================
    # STEP 4: CALL LLM
    # ==========================================

    print(
        "[4] Calling NVIDIA LLM..."
    )

    result = structured_model.invoke(
        prompt
    )

    print(
        "[5] Resume structured successfully."
    )

    # ==========================================
    # STEP 5: NORMALIZE DATA
    # ==========================================

    normalized_skills = normalize_skills(
        result.skills
    )

    normalized_roles = normalize_roles(
        result.target_roles
    )

    print(
        "[INFO] Extracted skills:",
        len(normalized_skills)
    )

    print(
        "[INFO] Extracted roles:",
        normalized_roles
    )

    # ==========================================
    # STEP 6: TARGET ROLE
    # ==========================================

    target_role = (
        getattr(
            preferences,
            "target_role",
            None
        )
        or ""
    ).strip()

    # Preference has priority.

    if not target_role:

        if normalized_roles:

            target_role = normalized_roles[0]

        else:

            target_role = "Software Engineer"

    target_role = normalize_roles(
        [target_role]
    )[0]

    # ==========================================
    # ADD TARGET ROLE
    # ==========================================

    if target_role not in normalized_roles:

        normalized_roles.insert(
            0,
            target_role
        )

    print(
        f"[Career Twin] Target Role: {target_role}"
    )

    # ==========================================
    # STEP 7: ROLE KNOWLEDGE
    # ==========================================

    print(
        "[Career Twin] Getting role knowledge..."
    )

    role_knowledge = get_or_create_role_knowledge(

        target_role=target_role,

        experience_level=(
            getattr(
                preferences,
                "experience_level",
                None
            )
            or "Entry Level"
        ),

        industry=(
            getattr(
                preferences,
                "preferred_industry",
                None
            )
            or "Artificial Intelligence"
        )
    )

    print(
        "[Career Twin] Role knowledge ready."
    )

    print(
        "[Role Knowledge] Required:",
        role_knowledge.required_skills
    )

    print(
        "[Role Knowledge] Preferred:",
        role_knowledge.preferred_skills
    )

    print(
        "[Role Knowledge] Tools:",
        role_knowledge.tools
    )

    print(
        "[Role Knowledge] Cloud:",
        role_knowledge.cloud
    )

    # ==========================================
    # STEP 8: SKILL GAP AGENT
    # ==========================================

    print(
        "[Career Twin] Starting Skill Gap Agent..."
    )

    skill_gap_result = run_skill_gap_workflow(

        current_skills=normalized_skills,

        target_role=target_role,

        required_skills=
            role_knowledge.required_skills,

        preferred_skills=
            role_knowledge.preferred_skills,

        tools=
            role_knowledge.tools,

        cloud=
            role_knowledge.cloud,

        # Resume evidence for the component based
        # readiness score (projects / experience /
        # education) plus categorical levels.
        profile={

            "education":
                result.education,

            "projects":
                result.projects,

            "experience":
                result.experience,

            # Unknown candidate level stays unknown -
            # never defaulted into a match.
            "experience_level":
                (
                    getattr(
                        preferences,
                        "experience_level",
                        None
                    )
                    or ""
                ),

            "role_experience_level":
                getattr(
                    role_knowledge,
                    "experience_level",
                    None
                ),
        }
    )

    print(
        "[Career Twin] Skill Gap Agent completed."
    )

    # ==========================================
    # STEP 9: CAREER STATE
    # ==========================================

    career_state_data = (
        skill_gap_result.get(
            "career_state",
            {}
        )
    )

    career_state = CareerState(

        readiness_score=
            career_state_data.get(
                "readiness_score",
                0.0
            ),

        readiness_breakdown=
            career_state_data.get(
                "readiness_breakdown",
                {}
            ),

        market_alignment=
            career_state_data.get(
                "market_alignment",
                0.0
            ),

        strengths=
            career_state_data.get(
                "strengths",
                []
            ),

        weaknesses=
            career_state_data.get(
                "weaknesses",
                []
            ),

        skill_gaps=
            career_state_data.get(
                "skill_gaps",
                []
            ),

        total_required=
            career_state_data.get(
                "total_required",
                0
            ),

        total_matched=
            career_state_data.get(
                "total_matched",
                0
            ),

        total_missing=
            career_state_data.get(
                "total_missing",
                0
            ),

        total_partial=
            career_state_data.get(
                "total_partial",
                0
            ),

        prioritized_gaps=
            skill_gap_result.get(
                "prioritized_gaps",
                []
            ),

        semantic_matches=
            skill_gap_result.get(
                "semantic_matches",
                []
            )
    )

    # ==========================================
    # STEP 10: JOB OPPORTUNITIES AGENT
    # ==========================================

    print(
        "[Career Twin] Starting Job Opportunities Agent..."
    )

    preference_data = preferences.model_dump()

    preference_data["target_role"] = target_role

    job_opportunities = find_job_opportunities(

        preferences=preference_data,

        current_skills=normalized_skills
    )

    print(
        "[Career Twin] Job Opportunities Agent completed."
    )

    print(
        "[Job Agent] Opportunities found:",
        len(job_opportunities)
    )

    # ==========================================
    # STEP 10B: MARKET ALIGNMENT
    # ==========================================
    #
    # Market alignment is deliberately SEPARATE from
    # readiness_score:
    #
    # readiness     = prepared for the target role?
    # market align  = profile fit vs current opportunities
    #
    # Weighted: role demand 25% + skill demand 30%
    #           + profile-market match 30%
    #           + location fit 15%
    # (unknown components excluded, weights
    #  renormalized)

    market_alignment_details = (
        compute_market_alignment_details(

            readiness_score=
                career_state.readiness_score,

            target_role=target_role,

            experience_level=(
                getattr(
                    preferences,
                    "experience_level",
                    None
                )
                or ""
            ),

            preferences=preference_data,

            jobs=job_opportunities,

            role_experience_level=(
                getattr(
                    role_knowledge,
                    "experience_level",
                    None
                )
            ),

            current_skills=normalized_skills,
        )
    )

    career_state.market_alignment = (
        market_alignment_details["score"]
    )

    career_state.market_alignment_breakdown = (
        market_alignment_details["breakdown"]
    )

    career_state.market_alignment_explanation = (
        market_alignment_details["explanation"]
    )

    print(
        "[Market Alignment] Score:",
        career_state.market_alignment
    )

    print(
        "[Market Alignment] Breakdown:",
        career_state.market_alignment_breakdown
    )

    print(
        "[Career Twin] Market Alignment:",
        career_state.market_alignment
    )

    # ==========================================
    # STEP 11: BUILD CAREER TWIN
    # ==========================================

    career_twin = CareerTwin(

        user_id=user_id,

        profile={

            "target_role": target_role,

            "experience_level":
                (
                    getattr(
                        preferences,
                        "experience_level",
                        None
                    )
                    or "Entry Level"
                ),

            "location":
                (
                    getattr(
                        preferences,
                        "location",
                        None
                    )
                    or ""
                )
        },

        education=result.education,

        skills=normalized_skills,

        projects=result.projects,

        experience=result.experience,

        certifications=result.certifications,

        achievements=result.achievements,

        target_roles=normalized_roles,

        preferences=preferences,

        career_state=career_state,

        job_opportunities=job_opportunities,

        learning_history=[],

        twin_version=2
    )

    # ==========================================
    # STEP 12: LOG
    # ==========================================

    print(
        "\n[Career Twin] Final Career State:"
    )

    print(
        "Readiness:",
        career_state.readiness_score
    )

    print(
        "Readiness breakdown:",
        career_state.readiness_breakdown
    )

    print(
        "Market Alignment:",
        career_state.market_alignment
    )

    print(
        "Required:",
        career_state.total_required
    )

    print(
        "Matched:",
        career_state.total_matched
    )

    print(
        "Missing:",
        career_state.total_missing
    )

    print(
        "Partial (borderline):",
        career_state.total_partial
    )

    print(
        "Skill gaps:",
        career_state.skill_gaps
    )

    print(
        "=========================================="
    )

    return career_twin


# ==========================================
# 15. NORMALIZE ROLES
# ==========================================

def normalize_roles(roles):

    role_mapping = {

        "aiengineer":
            "AI Engineer",

        "ai engineer":
            "AI Engineer",

        "ai developer":
            "AI Developer",

        "generative ai engineer":
            "Generative AI Engineer",

        "genai engineer":
            "Generative AI Engineer",

        "ml engineer":
            "Machine Learning Engineer",

        "machine learning engineer":
            "Machine Learning Engineer",

        "ai/ml engineer":
            "AI/ML Engineer",

        "backend engineer":
            "Backend Engineer",

        "backend developer":
            "Backend Developer",

        "python developer":
            "Python Developer",

        "python backend developer":
            "Python Backend Developer",

        "software engineer":
            "Software Engineer",

        "software developer":
            "Software Developer",

        "full stack developer":
            "Full-Stack Developer",

        "full-stack developer":
            "Full-Stack Developer",

        "llm engineer":
            "LLM Engineer",

        "nlp engineer":
            "NLP Engineer"
    }

    normalized = []

    for role in roles:

        if not role:
            continue

        clean_role = str(
            role
        ).strip()

        key = clean_role.lower()

        normalized_role = role_mapping.get(
            key,
            clean_role
        )

        if normalized_role not in normalized:

            normalized.append(
                normalized_role
            )

    return normalized


# ==========================================
# 16. NORMALIZE SKILLS
# ==========================================

def normalize_skills(skills):

    skill_mapping = {

        "ml":
            "Machine Learning",

        "machine learning":
            "Machine Learning",

        "dl":
            "Deep Learning",

        "deep learning":
            "Deep Learning",

        "nlp":
            "Natural Language Processing",

        "natural language processing":
            "Natural Language Processing",

        "llm":
            "Large Language Models",

        "llms":
            "Large Language Models",

        "large language model":
            "Large Language Models",

        "large language models":
            "Large Language Models",

        "langchain":
            "LangChain",

        "lang chain":
            "LangChain",

        "langgraph":
            "LangGraph",

        "lang graph":
            "LangGraph",

        "fast api":
            "FastAPI",

        "fastapi":
            "FastAPI",

        "react":
            "React.js",

        "reactjs":
            "React.js",

        "react.js":
            "React.js",

        "mongo":
            "MongoDB",

        "mongodb":
            "MongoDB",

        "mysql":
            "MySQL",

        "postgres":
            "PostgreSQL",

        "postgresql":
            "PostgreSQL",

        "rest api":
            "REST APIs",

        "rest apis":
            "REST APIs",

        "rest":
            "REST APIs",

        "git hub":
            "GitHub",

        "github":
            "GitHub",

        "node":
            "Node.js",

        "nodejs":
            "Node.js",

        "node.js":
            "Node.js",

        "express":
            "Express.js",

        "expressjs":
            "Express.js",

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

        "python":
            "Python",

        "java":
            "Java",

        "c++":
            "C++",

        "c":
            "C",

        "sql":
            "SQL"
    }

    normalized = []

    for skill in skills:

        if not skill:
            continue

        clean_skill = str(
            skill
        ).strip()

        key = clean_skill.lower()

        normalized_skill = skill_mapping.get(
            key,
            clean_skill
        )

        if normalized_skill not in normalized:

            normalized.append(
                normalized_skill
            )

    return normalized