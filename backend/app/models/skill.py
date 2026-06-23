from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

# Association table for Resume and Skills (Many-to-Many)
resume_skills = Table(
    "resume_skills",
    Base.metadata,
    Column("resume_id", Integer, ForeignKey("resumes.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

# Association table for Job and Skills (Many-to-Many)
job_skills = Table(
    "job_skills",
    Base.metadata,
    Column("job_id", Integer, ForeignKey("jobs.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String, unique=True, index=True, nullable=False)

    # Relationships
    resumes = relationship("Resume", secondary=resume_skills, back_populates="skills")
    jobs = relationship("Job", secondary=job_skills, back_populates="skills")
