from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    role: Optional[str] = None

# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str
    role: Optional[str] = "job_seeker" # "job_seeker" or "recruiter"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

# Skill Schema
class SkillResponse(BaseModel):
    id: int
    skill_name: str

    class Config:
        from_attributes = True

# Job Schemas
class JobBase(BaseModel):
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    description: str

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary: Optional[str] = None
    description: Optional[str] = None

class JobResponse(JobBase):
    id: int
    created_at: datetime
    skills: List[SkillResponse] = []

    class Config:
        from_attributes = True

# Resume Schemas
class ResumeResponse(BaseModel):
    id: int
    user_id: int
    resume_text: str
    resume_file: Optional[str] = None
    skills: List[SkillResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

# Recommendation Response Schema
class RecommendationResponse(BaseModel):
    job_id: int
    job_title: str
    company: str
    location: str
    salary: Optional[str] = None
    description: str
    match_score: float
    resume_skills: List[str]
    job_skills: List[str]
    missing_skills: List[str]

# Roadmap Step Schema
class RoadmapStep(BaseModel):
    skill: str
    topics: List[str]
    resources: List[str]
    project: str

# Roadmap Response Schema
class RoadmapResponse(BaseModel):
    job_title: str
    company: str
    current_skills: List[str]
    missing_skills: List[str]
    learning_path: List[RoadmapStep]
