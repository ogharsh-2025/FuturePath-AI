from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# Chat Schemas
class ChatMessage(BaseModel):
    role: str # user or assistant
    content: str

class ChatQuery(BaseModel):
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    session_id: str
    reply: str
    history: List[ChatMessage]

# Learning Path Schemas
class LearningPathGenerate(BaseModel):
    target_job: str

class LearningPathResponse(BaseModel):
    id: int
    target_job: str
    roadmap_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Career Prediction Schemas
class CareerPredictionResponse(BaseModel):
    id: int
    predictions_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# GitHub & Portfolio Schemas
class GitHubAnalyzeRequest(BaseModel):
    username: str

class GitHubProfileResponse(BaseModel):
    id: int
    username: str
    profile_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

class PortfolioScoreResponse(BaseModel):
    id: int
    score_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Salary Prediction Schemas
class SalaryPredictRequest(BaseModel):
    skills: List[str]
    experience: int
    location: str

class SalaryPredictResponse(BaseModel):
    min_salary: int
    avg_salary: int
    max_salary: int
    confidence_score: float

# Notification Schemas
class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    type: str
    created_at: datetime

    class Config:
        from_attributes = True

# Job Alert Schemas
class JobAlertSettings(BaseModel):
    frequency: str # daily, weekly, instant
    email_notifications: bool
    in_app_notifications: bool
    preferences: Dict[str, Any]

class JobAlertResponse(BaseModel):
    id: int
    frequency: str
    email_notifications: bool
    in_app_notifications: bool
    preferences: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Interview Prep Schemas
class InterviewQuestionsRequest(BaseModel):
    category: str # Technical, HR, Behavioral, Coding
    difficulty: str # Easy, Medium, Hard

class InterviewQuestionsResponse(BaseModel):
    category: str
    difficulty: str
    questions: List[str]

class InterviewSubmitRequest(BaseModel):
    category: str
    difficulty: str
    questions: List[str]
    answers: List[str]

class InterviewAttemptResponse(BaseModel):
    id: int
    category: str
    difficulty: str
    questions: List[str]
    answers: List[str]
    score: int
    feedback: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

# Resume Optimizer Schemas
class ResumeOptimizeResponse(BaseModel):
    ats_score: int
    readability_score: int
    formatting_score: int
    keyword_score: int
    project_score: int
    suggestions: Dict[str, Any]

class ResumeJDAnalyzeRequest(BaseModel):
    job_description: str
