from sqlalchemy.orm import Session
from backend.app.repositories.recommendation_repository import RecommendationRepository
from backend.app.repositories.resume_repository import ResumeRepository
from backend.app.ai.recommender import RecommenderEngine

class RecommendationService:
    @staticmethod
    def get_recommendations_for_user(db: Session, user_id: int) -> list[dict]:
        """
        Retrieves recommended jobs for the user, augmenting each match with skill gap details.
        """
        # Retrieve candidate's resume
        resume = ResumeRepository.get_by_user_id(db, user_id)
        if not resume:
            return []
            
        resume_skills = [s.skill_name for s in resume.skills]

        # Retrieve saved recommendations (sorted by score desc)
        db_recs = RecommendationRepository.get_by_user_id(db, user_id)
        
        results = []
        for rec in db_recs:
            job = rec.job
            job_skills = [s.skill_name for s in job.skills]
            
            # Check which skills the candidate is missing for this job
            missing_skills = RecommenderEngine.analyze_skill_gap(resume_skills, job_skills)
            
            results.append({
                "id": rec.id,
                "job_id": job.id,
                "job_title": job.title,
                "company": job.company,
                "location": job.location,
                "salary": job.salary,
                "description": job.description,
                "match_score": round(rec.match_score, 1),
                "resume_skills": resume_skills,
                "job_skills": job_skills,
                "missing_skills": missing_skills
            })
            
        return results
