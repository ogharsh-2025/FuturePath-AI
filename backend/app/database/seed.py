import sys
import os

# Append the parent directory to system path so backend modules are resolvable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from sqlalchemy.orm import Session
from backend.app.database.session import engine, SessionLocal
from backend.app.database.base import Base
from backend.app.repositories.skill_repository import SkillRepository
from backend.app.services.job_service import JobService
from backend.app.ai.skill_extractor import TECHNICAL_SKILLS

def seed_db():
    print("Initializing Database Tables...")
    # Create tables
    Base.metadata.create_all(bind=engine)
    print("Database Tables successfully verified/created.")
    
    db = SessionLocal()
    try:
        # Check and seed skills list
        existing_skills = SkillRepository.get_all(db)
        if not existing_skills:
            print("Seeding base technical skills dictionary...")
            SkillRepository.get_or_create_multiple(db, TECHNICAL_SKILLS)
            print(f"Successfully seeded {len(TECHNICAL_SKILLS)} skill sets.")
            
        # Check and seed sample job posts
        from backend.app.models.job import Job
        job_count = db.query(Job).count()
        if job_count == 0:
            print("Seeding sample job board posts...")
            sample_jobs = [
                {
                    "title": "Backend Developer (Python/FastAPI)",
                    "company": "Tech Giants Corp",
                    "location": "San Francisco, CA (Hybrid)",
                    "salary": "$125,000 - $155,000",
                    "description": "We are seeking a Python Software Engineer to build scalable backend systems. Requirements: strong experience with Python, FastAPI, Docker, and PostgreSQL. Familiarity with AWS and Git is required. Passion for APIs and scalable code is key."
                },
                {
                    "title": "Frontend Software Engineer (React)",
                    "company": "Creative UI Labs",
                    "location": "New York, NY (Remote)",
                    "salary": "$95,000 - $120,000",
                    "description": "Join our dynamic team building next-generation web applications. You should have expertise in HTML, CSS, JavaScript, and React. Experience with Next.js, Tailwind, Git, and REST APIs is a major plus."
                },
                {
                    "title": "DevOps & Infrastructure Engineer",
                    "company": "Secure Cloud Solutions",
                    "location": "Austin, TX (Onsite)",
                    "salary": "$135,000 - $165,000",
                    "description": "Looking for a cloud and deployment automation engineer. Required skills: Docker, Kubernetes, Terraform, AWS, Linux, Git, and CI/CD pipelines."
                },
                {
                    "title": "Full Stack Developer",
                    "company": "Fast-Paced Startup",
                    "location": "Seattle, WA (Remote)",
                    "salary": "$115,000 - $145,000",
                    "description": "Full Stack developer wanted. Stack includes Python, FastAPI, React, PostgreSQL, Redis, Docker, and GitHub Actions. You will work on greenfield projects and take ownership of end-to-end features."
                },
                {
                    "title": "Machine Learning Engineer",
                    "company": "DeepMinded AI",
                    "location": "Boston, MA (Hybrid)",
                    "salary": "$145,000 - $185,000",
                    "description": "Develop and deploy neural network models. Skills needed: Python, PyTorch, TensorFlow, Numpy, Pandas, Git, Docker, and AWS. Experience with sentence-transformers is a plus."
                }
            ]
            
            for job in sample_jobs:
                JobService.create_job(db, job)
            print(f"Successfully seeded {len(sample_jobs)} sample jobs with precalculated embeddings.")
        else:
            print("Job listings database already seeded.")
            
    except Exception as e:
        print(f"Error seeding database: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
