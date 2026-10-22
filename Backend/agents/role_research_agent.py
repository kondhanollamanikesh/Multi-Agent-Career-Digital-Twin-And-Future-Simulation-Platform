from typing import List
from pydantic import BaseModel, Field

from langchain_nvidia_ai_endpoints import ChatNVIDIA

import os
from dotenv import load_dotenv

from models import RoleKnowledge

from structured_llm import StructuredLLM

load_dotenv()


# ==========================================
# LLM
# ==========================================

client = ChatNVIDIA(
    model=os.getenv(
        "NVIDIA_LLM_MODEL",
        "nvidia/nemotron-3.5-super-vl-120b-a12b"
    ),
    api_key=os.getenv("NVIDIA_API_KEY"),
    temperature=0.2,
    top_p=1,
    max_completion_tokens=4096,
    timeout=300
)


# ==========================================
# EXTRACTION SCHEMA
# ==========================================

class RoleResearchExtraction(BaseModel):

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

    responsibilities: List[str] = Field(
        default_factory=list
    )


structured_model = StructuredLLM(
    client,
    RoleResearchExtraction
)


# ==========================================
# ROLE RESEARCH
# ==========================================

def research_role(
    target_role: str,
    experience_level: str = "Entry Level",
    industry: str = "Artificial Intelligence"
) -> RoleKnowledge:

    prompt = f"""
You are a career role research system.

Research and identify the skills and knowledge generally
required for the following career role.

Target Role:
{target_role}

Experience Level:
{experience_level}

Industry:
{industry}

Return structured information.

IMPORTANT:

1. Focus on skills relevant to the specified role.
2. Separate required skills from preferred skills.
3. Include important tools and technologies.
4. Include relevant cloud technologies if applicable.
5. Include common responsibilities.
6. Do not invent highly specialized requirements unnecessarily.
7. Prefer currently relevant industry requirements.
8. Do not provide salary information.
9. Do not provide individual job recommendations.

Return only structured role knowledge.
"""

    result = structured_model.invoke(prompt)

    return RoleKnowledge(

        role=target_role,

        experience_level=experience_level,

        industry=industry,

        required_skills=result.required_skills,

        preferred_skills=result.preferred_skills,

        tools=result.tools,

        cloud=result.cloud,

        responsibilities=result.responsibilities,

        sources=[]
    )
