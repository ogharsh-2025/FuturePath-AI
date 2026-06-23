from sqlalchemy.orm import Session
from backend.app.repositories.job_repository import JobRepository
from backend.app.repositories.skill_repository import SkillRepository
from backend.app.ai.embeddings import EmbeddingEngine
from backend.app.ai.skill_extractor import SkillExtractor
from backend.app.models.job import Job

class JobService:
    @staticmethod
    def get_job(db: Session, job_id: int) -> Job | None:
        return JobRepository.get_by_id(db, job_id)

    @staticmethod
    def get_all_jobs(db: Session) -> list[Job]:
        return JobRepository.get_all(db)

    @staticmethod
    def create_job(db: Session, job_in: dict) -> Job:
        """
        Creates a new job post, generates its embedding, extracts skills, and saves it.
        """
        # Combine title and description to enrich embedding context
        combined_text = f"{job_in['title']}. {job_in['description']}"
        embedding = EmbeddingEngine.get_embedding(combined_text)
        
        # Detect and link skills
        extracted_skills = SkillExtractor.extract_skills(job_in['description'])
        db_skills = SkillRepository.get_or_create_multiple(db, extracted_skills)
        
        job_data = {
            "title": job_in["title"],
            "company": job_in["company"],
            "location": job_in["location"],
            "salary": job_in.get("salary"),
            "description": job_in["description"],
            "embedding": embedding
        }
        return JobRepository.create(db, job_data, db_skills)

    @staticmethod
    def update_job(db: Session, job_id: int, job_in: dict) -> Job | None:
        """
        Updates an existing job post, recalculates embeddings and skills if text changes.
        """
        db_job = JobRepository.get_by_id(db, job_id)
        if not db_job:
            return None
            
        update_data = job_in.copy()
        
        # If title or description changed, regenerate embedding and skills
        if "description" in update_data or "title" in update_data:
            title = update_data.get("title", db_job.title)
            desc = update_data.get("description", db_job.description)
            combined_text = f"{title}. {desc}"
            update_data["embedding"] = EmbeddingEngine.get_embedding(combined_text)
            
            extracted_skills = SkillExtractor.extract_skills(desc)
            db_skills = SkillRepository.get_or_create_multiple(db, extracted_skills)
        else:
            db_skills = None
            
        return JobRepository.update(db, db_job, update_data, db_skills)

    @staticmethod
    def delete_job(db: Session, job_id: int) -> bool:
        """
        Deletes a job post by ID. Returns True if successful.
        """
        db_job = JobRepository.get_by_id(db, job_id)
        if not db_job:
            return False
        JobRepository.delete(db, db_job)
        return True
