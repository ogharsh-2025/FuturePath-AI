from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database.session import Base, ArrayType
from backend.app.models.skill import job_skills

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False)
    salary = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    embedding = Column(ArrayType, nullable=True) # 384 dimensional vector
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    skills = relationship("Skill", secondary=job_skills, back_populates="jobs")
    recommendations = relationship("Recommendation", back_populates="job", cascade="all, delete-orphan")
