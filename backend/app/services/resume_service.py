import os
from sqlalchemy.orm import Session
from backend.app.repositories.resume_repository import ResumeRepository
from backend.app.repositories.skill_repository import SkillRepository
from backend.app.repositories.recommendation_repository import RecommendationRepository
from backend.app.repositories.job_repository import JobRepository
from backend.app.ai.parser import ResumeParser
from backend.app.ai.embeddings import EmbeddingEngine
from backend.app.ai.skill_extractor import SkillExtractor
from backend.app.ai.recommender import RecommenderEngine
from backend.app.core.config import settings
from backend.app.models.resume import Resume

class ResumeService:
    @staticmethod
    def get_user_resume(db: Session, user_id: int) -> Resume | None:
        """
        Retrieves the resume profile for a given user.
        """
        return ResumeRepository.get_by_user_id(db, user_id)

    @classmethod
    def upload_and_process_resume(cls, db: Session, user_id: int, file_bytes: bytes, filename: str) -> Resume:
        """
        Validates, uploads, parses, generates embedding, extracts skills, and triggers recommendations.
        """
        # Validate format
        filename_lower = filename.lower()
        if not (filename_lower.endswith(".pdf") or filename_lower.endswith(".docx")):
            raise ValueError("Unsupported file format. Please upload PDF or DOCX.")
            
        # Validate size (5MB limit)
        if len(file_bytes) > 5 * 1024 * 1024:
            raise ValueError("File size exceeds 5MB limit.")

        # Ensure upload folder exists and write the file
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
        # Make the filename unique to prevent collisions
        safe_filename = f"user_{user_id}_{filename}"
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # Parse text and information
        parsed_data = ResumeParser.parse_resume(file_bytes, filename)
        resume_text = parsed_data["text"]

        # Detect and insert skills
        skill_names = SkillExtractor.extract_skills(resume_text)
        db_skills = SkillRepository.get_or_create_multiple(db, skill_names)

        # Generate embedding
        embedding = EmbeddingEngine.get_embedding(resume_text)

        # Save to DB (Create or update)
        resume_data = {
            "resume_text": resume_text,
            "resume_file": file_path,
            "embedding": embedding
        }
        resume = ResumeRepository.create_or_update(db, user_id, resume_data, db_skills)

        # Recalculate and cache user's recommendations
        cls.generate_recommendations(db, user_id, embedding)

        return resume

    @staticmethod
    def generate_recommendations(db: Session, user_id: int, resume_embedding: list[float]) -> None:
        """
        Recalculates scores between the user's resume embedding and all active jobs.
        Saves scores to the recommendations table.
        """
        # Wipe existing recommendations for the user
        RecommendationRepository.delete_by_user_id(db, user_id)

        # Fetch all available jobs
        jobs = JobRepository.get_all(db)
        if not jobs:
            return

        # Rank jobs and get recommendations
        ranked_jobs = RecommenderEngine.recommend_jobs(resume_embedding, jobs, top_n=20)

        # Format and save
        recs_data = []
        for item in ranked_jobs:
            recs_data.append({
                "user_id": user_id,
                "job_id": item["job_id"],
                "match_score": item["match_score"]
            })
            
        RecommendationRepository.create_multiple(db, recs_data)
