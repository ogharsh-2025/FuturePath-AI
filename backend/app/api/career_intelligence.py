from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from backend.app.database.session import get_db
from backend.app.api.deps import get_current_user
from backend.app.models.user import User
from backend.app.models.extended_models import (
    LearningPath,
    CareerPrediction,
    GitHubProfile,
    PortfolioScore,
    SalaryPrediction,
    Notification,
    ChatSession,
    InterviewAttempt,
    ResumeScore,
    JobAlert
)
from backend.app.models.resume import Resume
from backend.app.models.job import Job
from backend.app.models.recommendation import Recommendation

from backend.app.schemas.extended_schemas import (
    ChatQuery,
    ChatResponse,
    LearningPathGenerate,
    LearningPathResponse,
    CareerPredictionResponse,
    GitHubAnalyzeRequest,
    GitHubProfileResponse,
    PortfolioScoreResponse,
    SalaryPredictRequest,
    SalaryPredictResponse,
    NotificationResponse,
    JobAlertSettings,
    JobAlertResponse,
    InterviewQuestionsRequest,
    InterviewQuestionsResponse,
    InterviewSubmitRequest,
    InterviewAttemptResponse,
    ResumeOptimizeResponse,
    ResumeJDAnalyzeRequest
)

from backend.app.services.ai_resume_optimizer import AIResumeOptimizer
from backend.app.services.career_coach_service import CareerCoachService
from backend.app.services.interview_prep_service import InterviewPrepService
from backend.app.services.github_analyzer_service import GitHubAnalyzerService
from backend.app.services.salary_prediction_service import SalaryPredictionService
from backend.app.services.roadmap_service import RoadmapService

router = APIRouter()

# ----------------- 1. AI Resume Optimizer & ATS Generator -----------------
@router.post("/resume-optimizer/analyze", response_model=ResumeOptimizeResponse)
def analyze_resume(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="No resume found. Please upload a resume first.")
    
    analysis = AIResumeOptimizer.analyze_resume_text(resume.resume_text)
    
    # Save score to db
    db_score = db.query(ResumeScore).filter(ResumeScore.user_id == current_user.id).first()
    if db_score:
        db_score.ats_score = analysis["ats_score"]
        db_score.readability_score = analysis["readability_score"]
        db_score.formatting_score = analysis["formatting_score"]
        db_score.keyword_score = analysis["keyword_score"]
        db_score.project_score = analysis["project_score"]
        db_score.suggestions = analysis["suggestions"]
    else:
        db_score = ResumeScore(
            user_id=current_user.id,
            ats_score=analysis["ats_score"],
            readability_score=analysis["readability_score"],
            formatting_score=analysis["formatting_score"],
            keyword_score=analysis["keyword_score"],
            project_score=analysis["project_score"],
            suggestions=analysis["suggestions"]
        )
        db.add(db_score)
    db.commit()
    
    return analysis

@router.get("/resume-optimizer/generate-ats")
def generate_ats_resume(
    template: str = "professional", 
    format: str = "docx", 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Please upload a resume first.")
    
    resume_bytes = AIResumeOptimizer.generate_ats_resume(resume.resume_text, template, format)
    
    media_types = {
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "pdf": "application/pdf"
    }
    
    filename = f"ATS_Resume_{template}.{format}"
    return Response(
        content=resume_bytes,
        media_type=media_types.get(format, "application/octet-stream"),
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ----------------- 2. Personalized Learning Path Generator -----------------
@router.post("/learning-paths/generate", response_model=LearningPathResponse)
def generate_learning_path(
    payload: LearningPathGenerate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Try to find a matching sample job in db first, else mock job for matching
    job = db.query(Job).filter(Job.title.ilike(f"%{payload.target_job}%")).first()
    if not job:
        # Create a transient mock job to execute standard roadmap analysis
        job = Job(
            title=payload.target_job,
            company="FuturePath Target Enterprise",
            location="Remote",
            description=f"Requires deep knowledge of {payload.target_job} skills and modern technologies."
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Link a couple sample skills to the job
        from backend.app.models.skill import Skill
        sample_skills = ["FastAPI", "Docker", "Kubernetes", "PostgreSQL", "AWS"]
        for sname in sample_skills:
            skill_obj = db.query(Skill).filter(Skill.skill_name == sname).first()
            if skill_obj:
                job.skills.append(skill_obj)
        db.commit()

    roadmap = RoadmapService.generate_roadmap(db, current_user.id, job.id)
    
    # Save learning path to db
    db_path = LearningPath(
        user_id=current_user.id,
        target_job=payload.target_job,
        roadmap_data=roadmap
    )
    db.add(db_path)
    db.commit()
    db.refresh(db_path)
    
    return db_path

@router.get("/learning-paths/history", response_model=List[LearningPathResponse])
def get_learning_paths(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    paths = db.query(LearningPath).filter(LearningPath.user_id == current_user.id).order_by(LearningPath.created_at.desc()).all()
    return paths

# ----------------- 3. AI Career Coach Chatbot -----------------
@router.post("/career-coach/chat", response_model=ChatResponse)
def chat_with_coach(
    query: ChatQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return CareerCoachService.process_chat_message(db, current_user.id, query.message, query.session_id)

@router.get("/career-coach/history", response_model=List[ChatResponse])
def get_chat_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    
    formatted = []
    for s in sessions:
        # Reconstruct chat response
        reply = s.history[-1]["content"] if s.history else ""
        formatted.append({
            "session_id": s.session_id,
            "reply": reply,
            "history": s.history
        })
    return formatted

# ----------------- 4. Job Success Probability Score -----------------
@router.get("/job-success-probability/{job_id}")
def get_success_probability(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    # Calculate probability: based on skill match + experience check
    probability = 50
    reasons = []
    
    if resume:
        # Check skill overlap
        resume_skills = {s.skill_name.lower() for s in resume.skills}
        job_skills = {s.skill_name.lower() for s in job.skills}
        
        if job_skills:
            matched = resume_skills.intersection(job_skills)
            skill_pct = (len(matched) / len(job_skills)) * 50
            probability += skill_pct
            reasons.append(f"Your skills match {len(matched)} of {len(job_skills)} required tags (+{int(skill_pct)}%).")
            
            missing = job_skills - resume_skills
            if missing:
                reasons.append(f"Missing core competencies: {', '.join(list(missing)[:3])}.")
        else:
            probability += 20
            reasons.append("Generic tech job skills matched (+20%).")
            
        # Check portfolio context
        gh_profile = db.query(GitHubProfile).filter(GitHubProfile.user_id == current_user.id).first()
        if gh_profile:
            hiring_readiness = gh_profile.profile_data.get("hiring_readiness", 60)
            if hiring_readiness >= 75:
                probability += 10
                reasons.append(f"Highly-rated GitHub profile adds a competitive premium (+10%).")
    else:
        reasons.append("Upload a resume to get custom alignment insights.")
        
    probability = min(98, max(25, int(probability)))
    
    return {
        "success_probability": probability,
        "reasons": reasons,
        "job_title": job.title,
        "company": job.company
    }

# ----------------- 5. Project Recommendation Engine -----------------
@router.get("/project-recommendations")
def get_project_recommendations(role: str = "Backend Developer"):
    projects_db = {
        "Backend Developer": [
            {
                "title": "OAuth2 API Gateway Service",
                "difficulty": "Advanced",
                "description": "Architect a centralized API Gateway supporting token validation, dynamic rate-limiting, and request forwarding.",
                "skills": ["FastAPI", "Redis", "Docker", "JWT", "PostgreSQL"],
                "time": "3 Weeks",
                "portfolio_impact": "Demonstrates enterprise security and scale patterns."
            },
            {
                "title": "Containerized Task Queue Worker",
                "difficulty": "Intermediate",
                "description": "Build an asynchronous worker handling heavy video processing tasks with progress updates via WebSockets.",
                "skills": ["Python", "Docker", "Redis", "WebSockets"],
                "time": "2 Weeks",
                "portfolio_impact": "High proof of async architecture & queuing knowledge."
            },
            {
                "title": "CRUD Expense Tracker API",
                "difficulty": "Beginner",
                "description": "Build a secure RESTful API with SQLite database supporting multiple users and expense statistics.",
                "skills": ["Python", "FastAPI", "SQLAlchemy", "SQLite"],
                "time": "1 Week",
                "portfolio_impact": "Fundamental database and API design proof."
            }
        ],
        "Frontend Developer": [
            {
                "title": "SaaS Billing Analytics Panel",
                "difficulty": "Advanced",
                "description": "Build an enterprise dashboard using ChartJS/Recharts, glassmorphism UI, light/dark modes, and client caching.",
                "skills": ["React", "TypeScript", "TailwindCSS", "ChartJS"],
                "time": "3 Weeks",
                "portfolio_impact": "Stunning visuals showing production-grade dashboard skills."
            },
            {
                "title": "Realtime Kanban Planner",
                "difficulty": "Intermediate",
                "description": "Create a drag-and-drop workflow planner with persistence and sub-task lists.",
                "skills": ["JavaScript", "React", "CSS Modules", "HTML5"],
                "time": "2 Weeks",
                "portfolio_impact": "Proves state management and user interaction complexity."
            },
            {
                "title": "Personal Portfolio Site",
                "difficulty": "Beginner",
                "description": "Write a clean, responsive single-page resume site with subtle CSS animations and contact forms.",
                "skills": ["HTML", "CSS", "Vanilla JS"],
                "time": "3 Days",
                "portfolio_impact": "Creates a centralized professional landing hub."
            }
        ],
        "Machine Learning Engineer": [
            {
                "title": "Sentence embedding search engine",
                "difficulty": "Advanced",
                "description": "Deploy a semantic search API vectorizing unstructured text inputs and matching against cached local vector spaces.",
                "skills": ["Python", "FastAPI", "PyTorch", "NumPy", "Docker"],
                "time": "3 Weeks",
                "portfolio_impact": "OOM-safe vector embedding service demonstration."
            },
            {
                "title": "Spam Classifier API",
                "difficulty": "Intermediate",
                "description": "Train and deploy a Naive Bayes model classifying messages as spam with high accuracy metrics.",
                "skills": ["Python", "scikit-learn", "Flask", "NLTK"],
                "time": "1 Week",
                "portfolio_impact": "Standard NLP pipeline and REST integration demonstration."
            }
        ],
        "DevOps Engineer": [
            {
                "title": "Automated AWS GitOps Pipeline",
                "difficulty": "Advanced",
                "description": "Automate local minikube setups with GitHub Actions and Terraform provisioning standard VPC nodes.",
                "skills": ["AWS", "Terraform", "Kubernetes", "GitOps", "GitHub Actions"],
                "time": "3 Weeks",
                "portfolio_impact": "Ultimate infrastructure automation proof."
            },
            {
                "title": "CI/CD Docker Multi-stage Setup",
                "difficulty": "Intermediate",
                "description": "Build a optimized Docker pipeline compiling static frontend bundle and FastAPI server in single compose file.",
                "skills": ["Docker", "Nginx", "Git", "Bash"],
                "time": "1 Week",
                "portfolio_impact": "Demonstrates container compilation and hosting best practices."
            }
        ]
    }
    
    # Fallback to backend developer
    return projects_db.get(role, projects_db["Backend Developer"])

# ----------------- 6. AI Interview Preparation System -----------------
@router.post("/interview-prep/questions", response_model=InterviewQuestionsResponse)
def get_interview_questions(payload: InterviewQuestionsRequest):
    questions = InterviewPrepService.get_questions(payload.category, payload.difficulty)
    return {
        "category": payload.category,
        "difficulty": payload.difficulty,
        "questions": questions
    }

@router.post("/interview-prep/submit", response_model=InterviewAttemptResponse)
def submit_interview(
    payload: InterviewSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return InterviewPrepService.submit_attempt(
        db, current_user.id, payload.category, payload.difficulty, payload.questions, payload.answers
    )

@router.get("/interview-prep/history", response_model=List[InterviewAttemptResponse])
def get_interview_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return InterviewPrepService.get_attempts_history(db, current_user.id)

# ----------------- 7. Resume vs Job Description Analyzer -----------------
@router.post("/resume-optimizer/analyze-jd")
def analyze_vs_jd(
    payload: ResumeJDAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Please upload a resume first.")

    res_text = resume.resume_text.lower()
    jd_text = payload.job_description.lower()
    
    # Extract matching & missing keywords using common tech database
    all_kws = AIResumeOptimizer.COMMON_TECH_KEYWORDS
    matched = []
    missing = []
    
    for kw in all_kws:
        if kw in jd_text:
            if kw in res_text:
                matched.append(kw.title())
            else:
                missing.append(kw.title())
                
    # Calculate fit
    total_jd_skills = len(matched) + len(missing)
    match_pct = int((len(matched) / max(1, total_jd_skills)) * 100)
    
    ats_score = int(match_pct * 0.8 + 20)
    ats_score = min(100, max(30, ats_score))
    
    return {
        "match_percentage": match_pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "ats_compatibility_score": ats_score,
        "suggestions": [
            f"Incorporate the following missing keywords into your resume text: {', '.join(missing[:4])}.",
            "Quantify your achievements under experiences that relate directly to the job description keywords.",
            "Write a strong summary section aligning your core developer capabilities with the requirements."
        ]
    }

# ----------------- 8. Skill Trend Analysis Dashboard -----------------
@router.get("/salary-prediction/trends")
def get_skill_trends():
    return SalaryPredictionService.get_skill_trends()

# ----------------- 9. Salary Prediction System -----------------
@router.post("/salary-prediction/predict", response_model=SalaryPredictResponse)
def predict_salary(
    payload: SalaryPredictRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return SalaryPredictionService.predict_salary(
        db, current_user.id, payload.skills, payload.experience, payload.location
    )

# ----------------- 10. Smart Job Alerts & Notifications -----------------
@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Automatically seed some notifications for visual appeal on first load
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).all()
    if not notifs:
        default_notifs = [
            Notification(
                user_id=current_user.id,
                title="New Job Match Alert",
                message="DeepMinded AI just added 'Machine Learning Specialist' matching your skills! Match Score: 88%.",
                type="job_match"
            ),
            Notification(
                user_id=current_user.id,
                title="GitHub Analysis Completed",
                message="GitHub profile analyzed. Your hiring readiness index is rated as 'Intermediate' (68/100).",
                type="alert"
            ),
            Notification(
                user_id=current_user.id,
                title="Resume Scores Synced",
                message="Your resume optimized metrics have been compiled. Current ATS Score: 80.",
                type="system"
            )
        ]
        for dn in default_notifs:
            db.add(dn)
        db.commit()
        notifs = db.query(Notification).filter(Notification.user_id == current_user.id).all()
        
    return notifs

@router.post("/notifications/read/{notif_id}")
def mark_read(notif_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    notif = db.query(Notification).filter(Notification.id == notif_id, Notification.user_id == current_user.id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.is_read = True
    db.commit()
    return {"status": "success"}

@router.post("/job-alerts/settings", response_model=JobAlertResponse)
def save_alert_settings(
    payload: JobAlertSettings,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_alert = db.query(JobAlert).filter(JobAlert.user_id == current_user.id).first()
    if db_alert:
        db_alert.frequency = payload.frequency
        db_alert.email_notifications = payload.email_notifications
        db_alert.in_app_notifications = payload.in_app_notifications
        db_alert.preferences = payload.preferences
    else:
        db_alert = JobAlert(
            user_id=current_user.id,
            frequency=payload.frequency,
            email_notifications=payload.email_notifications,
            in_app_notifications=payload.in_app_notifications,
            preferences=payload.preferences
        )
        db.add(db_alert)
        
    db.commit()
    db.refresh(db_alert)
    return db_alert

@router.get("/job-alerts/settings", response_model=JobAlertResponse)
def get_alert_settings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_alert = db.query(JobAlert).filter(JobAlert.user_id == current_user.id).first()
    if not db_alert:
        db_alert = JobAlert(
            user_id=current_user.id,
            frequency="daily",
            email_notifications=True,
            in_app_notifications=True,
            preferences={"target_role": "Backend Engineer", "location": "Remote"}
        )
        db.add(db_alert)
        db.commit()
        db.refresh(db_alert)
    return db_alert

# ----------------- 11. AI Skill Gap Simulator -----------------
@router.post("/skill-gap-simulator")
def simulate_skill_gap(
    skills_to_add: List[str],
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
        
    # Get current resume skills
    resume_skills = [s.skill_name.lower() for s in resume.skills] if resume else []
    
    # Combined simulated skills list
    simulated_skills = list(set(resume_skills + [s.lower() for s in skills_to_add]))
    
    job_skills = [s.skill_name.lower() for s in job.skills]
    
    # Match percentage calculations
    if not job_skills:
        current_match = 50
        simulated_match = 75
    else:
        current_matched = set(resume_skills).intersection(set(job_skills))
        current_match = int((len(current_matched) / len(job_skills)) * 100)
        
        simulated_matched = set(simulated_skills).intersection(set(job_skills))
        simulated_match = int((len(simulated_matched) / len(job_skills)) * 100)
        
    return {
        "job_title": job.title,
        "company": job.company,
        "current_match_score": current_match,
        "simulated_match_score": simulated_match,
        "gained_match": max(0, simulated_match - current_match)
    }

# ----------------- 12. AI Career Path Predictor -----------------
@router.get("/career-path-predictor")
def predict_career_path(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()
    skills = [s.skill_name.lower() for s in resume.skills] if resume else []
    
    # Simple heuristic predictor logic based on skills
    is_ml = any(s in skills for s in ["pytorch", "tensorflow", "machine learning", "deep learning"])
    is_devops = any(s in skills for s in ["docker", "kubernetes", "aws", "terraform", "ansible"])
    
    if is_ml:
        path_type = "Machine Learning Engineer"
        one_year_role = "Senior ML Engineer"
        three_year_role = "ML Architect"
        five_year_role = "Director of AI / VP of ML"
    elif is_devops:
        path_type = "DevOps Engineer"
        one_year_role = "Senior DevOps Engineer"
        three_year_role = "Cloud Platform Architect"
        five_year_role = "VP of Infrastructure / Head of Cloud"
    else:
        path_type = "Full Stack Engineer"
        one_year_role = "Senior Full Stack Engineer"
        three_year_role = "Principal Architect"
        five_year_role = "Chief Technology Officer (CTO)"
        
    predictions_data = {
        "path_type": path_type,
        "timeline": [
            {
                "term": "1 Year",
                "role": one_year_role,
                "skills_to_learn": ["Kubernetes", "Advanced System Design", "Terraform"],
                "expected_salary": "$135,000",
                "responsibilities": "Lead project modules, design REST API schemas, mentor junior staff."
            },
            {
                "term": "3 Years",
                "role": three_year_role,
                "skills_to_learn": ["Distributed Databases", "Multi-region Failovers", "Team Leadership"],
                "expected_salary": "$175,000",
                "responsibilities": "Architect full service grids, negotiate vendor cloud budgets, lead team design reviews."
            },
            {
                "term": "5 Years",
                "role": five_year_role,
                "skills_to_learn": ["Strategic Management", "FinOps", "Product Roadmap Planning"],
                "expected_salary": "$230,000",
                "responsibilities": "Align engineering milestones with corporate strategy, hire principal architects, drive tech stack consolidation."
            }
        ]
    }
    
    # Save prediction to db
    db_pred = db.query(CareerPrediction).filter(CareerPrediction.user_id == current_user.id).first()
    if db_pred:
        db_pred.predictions_data = predictions_data
    else:
        db_pred = CareerPrediction(
            user_id=current_user.id,
            predictions_data=predictions_data
        )
        db.add(db_pred)
    db.commit()
    db.refresh(db_pred)
    
    return predictions_data

# ----------------- 13. GitHub Portfolio Analyzer & Scorer -----------------
@router.post("/github-analyzer/analyze", response_model=GitHubProfileResponse)
async def analyze_github_profile(
    payload: GitHubAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    profile = await GitHubAnalyzerService.analyze_profile(db, current_user.id, payload.username)
    
    db_profile = db.query(GitHubProfile).filter(
        GitHubProfile.user_id == current_user.id,
        GitHubProfile.username == payload.username
    ).first()
    
    return db_profile
