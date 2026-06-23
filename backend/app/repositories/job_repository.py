from sqlalchemy.orm import Session
from backend.app.models.job import Job

class JobRepository:
    @staticmethod
    def get_by_id(db: Session, job_id: int) -> Job | None:
        return db.query(Job).filter(Job.id == job_id).first()

    @staticmethod
    def get_all(db: Session) -> list[Job]:
        return db.query(Job).order_by(Job.created_at.desc()).all()

    @staticmethod
    def create(db: Session, job_data: dict, skills: list = None) -> Job:
        db_job = Job(**job_data)
        if skills:
            db_job.skills = skills
        db.add(db_job)
        db.commit()
        db.refresh(db_job)
        return db_job

    @staticmethod
    def update(db: Session, db_job: Job, update_data: dict, skills: list = None) -> Job:
        for key, value in update_data.items():
            setattr(db_job, key, value)
        if skills is not None:
            db_job.skills = skills
        db.commit()
        db.refresh(db_job)
        return db_job

    @staticmethod
    def delete(db: Session, db_job: Job) -> None:
        db.delete(db_job)
        db.commit()
