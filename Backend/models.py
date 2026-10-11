from typing import List, Optional

from pydantic import BaseModel, Field


# ==========================================
# USER PREFERENCES
# ==========================================

class Preferences(BaseModel):

    target_role: Optional[str] = None

    location: Optional[str] = None

    work_mode: Optional[str] = None

    employment_type: Optional[str] = None

    salary_expectation: Optional[str] = None

    relocation: Optional[bool] = None

    preferred_industry: Optional[str] = None

    experience_level: Optional[str] = None


# ==========================================
# CAREER PROFILE
# ==========================================

class CareerProfile(BaseModel):

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
# ROLE KNOWLEDGE
# ==========================================

class RoleKnowledge(BaseModel):

    role: str = ""

    experience_level: Optional[str] = None

    category: Optional[str] = None

    industry: Optional[str] = None

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

    sources: List[str] = Field(
        default_factory=list
    )