import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.api import auth, jobs, resumes, recommendations

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Backend API for AI-Powered Job Recommendations and Skill Gap Analysis",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["Recommendations"])

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
