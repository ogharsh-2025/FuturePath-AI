from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database.session import Base, ArrayType
from backend.app.models.skill import resume_skills

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True) # One resume per user for simplicity
    resume_text = Column(Text, nullable=False)
    resume_file = Column(String, nullable=True)
    embedding = Column(ArrayType, nullable=True) # 384 dimensional vector
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="resumes")
    skills = relationship("Skill", secondary=resume_skills, back_populates="resumes")
