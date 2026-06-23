from sqlalchemy.orm import Session
from backend.app.models.resume import Resume

class ResumeRepository:
    @staticmethod
    def get_by_id(db: Session, resume_id: int) -> Resume | None:
        return db.query(Resume).filter(Resume.id == resume_id).first()

    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> Resume | None:
        return db.query(Resume).filter(Resume.user_id == user_id).first()

    @staticmethod
    def create_or_update(db: Session, user_id: int, resume_data: dict, skills: list = None) -> Resume:
        db_resume = db.query(Resume).filter(Resume.user_id == user_id).first()
        if db_resume:
            for key, value in resume_data.items():
                setattr(db_resume, key, value)
            if skills is not None:
                db_resume.skills = skills
        else:
            db_resume = Resume(user_id=user_id, **resume_data)
            if skills:
                db_resume.skills = skills
            db.add(db_resume)
        db.commit()
        db.refresh(db_resume)
        return db_resume

    @staticmethod
    def delete(db: Session, db_resume: Resume) -> None:
        db.delete(db_resume)
        db.commit()
