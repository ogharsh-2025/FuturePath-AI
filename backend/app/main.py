import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.api import auth, jobs, resumes, recommendations, career_intelligence

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI-Powered Job Recommendations and Skill Gap Analysis",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])
app.include_router(career_intelligence.router, prefix="/api", tags=["Career Intelligence"])


# Global exception handler for debugging 500 errors in deployment
import traceback
from fastapi import Request, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.app.database.session import get_db, engine

@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "traceback": traceback.format_exc()
        }
    )

@app.get("/api/db-check")
def db_check(db: Session = Depends(get_db)):
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        return {
            "status": "connected",
            "tables": tables,
            "database_url": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else settings.DATABASE_URL
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

# Dynamic mapping of the static files
# Resolves: backend/app/main.py -> ../../frontend
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "frontend"))

if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    @app.get("/")
    def read_root():
        return {
            "status": "online",
            "message": "AI-Powered Job Recommendation Platform Backend is running. Frontend directory not found.",
            "docs_url": "/docs"
        }

def seed_sample_jobs():
    """
    Seeds default high-quality sample jobs on startup if database is empty.
    """
    from backend.app.database.session import SessionLocal
    from backend.app.models.job import Job
    from backend.app.services.job_service import JobService
    
    db = SessionLocal()
    try:
        job_count = db.query(Job).count()
        if job_count == 0:
            print("[Database]: Seeding default tech job postings...")
            sample_jobs = [
                {
                    "title": "Machine Learning Specialist",
                    "company": "DeepMinded AI",
                    "location": "London, UK (Hybrid)",
                    "salary": "$120,000 - $150,000",
                    "description": "We are looking for an ML Specialist to design and deploy models. Required skills: Python, PyTorch, Docker, Kubernetes, Linux."
                },
                {
                    "title": "Frontend Engineer",
                    "company": "FuturePath Labs",
                    "location": "New York, NY (Remote)",
                    "salary": "$90,000 - $120,000",
                    "description": "Join our team to build next-generation SPA dashboards. Required skills: HTML, CSS, JavaScript, TypeScript, React, Next.js, Git."
                },
                {
                    "title": "Backend Developer",
                    "company": "Octocat Systems",
                    "location": "San Francisco, CA (Remote)",
                    "salary": "$110,000 - $140,000",
                    "description": "Building robust cloud microservices and REST APIs. Required skills: Python, FastAPI, PostgreSQL, Redis, Docker, Git, CI/CD."
                },
                {
                    "title": "DevOps Engineer",
                    "company": "CloudScale Co",
                    "location": "Seattle, WA (Remote)",
                    "salary": "$130,000 - $160,000",
                    "description": "Scaling cloud infrastructures and automating deployment pipelines. Required skills: AWS, Docker, Kubernetes, Terraform, Jenkins, Linux, Bash, Git."
                }
            ]
            for job_data in sample_jobs:
                JobService.create_job(db, job_data)
            print("[Database]: Seeding complete.")
    except Exception as e:
        print(f"[Database Error]: Seeding jobs failed: {str(e)}")
    finally:
        db.close()

import threading

@app.on_event("startup")
def run_migrations():
    """
    Runs programmatic database creation on startup in a background thread.
    Ensures database schema is established without blocking startup or causing port timeouts.
    """
    def create_tables():
        try:
            # Create all tables programmatically first
            from backend.app.database.base import Base
            Base.metadata.create_all(bind=engine)
            print("[Database]: Tables created/verified successfully in background.")
            # Seed default job listings if empty
            seed_sample_jobs()
        except Exception as e:
            print(f"[Database Error]: Background database setup failed: {str(e)}")

    thread = threading.Thread(target=create_tables)
    thread.daemon = True
    thread.start()
