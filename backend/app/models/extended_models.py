from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database.session import Base

class LearningPath(Base):
    __tablename__ = "learning_paths"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    target_job = Column(String, nullable=False)
    roadmap_data = Column(JSON, nullable=False) # Roadmap weekly steps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="learning_paths")

class CareerPrediction(Base):
    __tablename__ = "career_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    predictions_data = Column(JSON, nullable=False) # 1, 3, 5 year forecasts
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="career_predictions")

class GitHubProfile(Base):
    __tablename__ = "github_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    username = Column(String, nullable=False)
    profile_data = Column(JSON, nullable=False) # Commit stats, languages, hiring score
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="github_profiles")

class PortfolioScore(Base):
    __tablename__ = "portfolio_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    score_data = Column(JSON, nullable=False) # Code quality, design metrics
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="portfolio_scores")

class SalaryPrediction(Base):
    __tablename__ = "salary_predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skills = Column(String, nullable=False)
    experience = Column(Integer, nullable=False)
    location = Column(String, nullable=False)
    min_salary = Column(Integer, nullable=False)
    avg_salary = Column(Integer, nullable=False)
    max_salary = Column(Integer, nullable=False)
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="salary_predictions")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    type = Column(String, default="system", nullable=False) # job_match, alert, system
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="notifications")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String, unique=True, index=True, nullable=False)
    history = Column(JSON, nullable=False) # List of dicts representing messages
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="chat_sessions")

class InterviewAttempt(Base):
    __tablename__ = "interview_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False) # Technical, HR, Behavioral, Coding
    difficulty = Column(String, nullable=False) # Easy, Medium, Hard
    questions = Column(JSON, nullable=False)
    answers = Column(JSON, nullable=False)
    score = Column(Integer, nullable=False)
    feedback = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="interview_attempts")

class ResumeScore(Base):
    __tablename__ = "resume_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    ats_score = Column(Integer, nullable=False)
    readability_score = Column(Integer, nullable=False)
    formatting_score = Column(Integer, nullable=False)
    keyword_score = Column(Integer, nullable=False)
    project_score = Column(Integer, nullable=False)
    suggestions = Column(JSON, nullable=False) # JSON list/dictionary of suggestions
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="resume_scores")

class JobAlert(Base):
    __tablename__ = "job_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    frequency = Column(String, default="daily", nullable=False) # daily, weekly, instant
    email_notifications = Column(Boolean, default=True, nullable=False)
    in_app_notifications = Column(Boolean, default=True, nullable=False)
    preferences = Column(JSON, nullable=False) # Dict of filters
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", backref="job_alerts")
