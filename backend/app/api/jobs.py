from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import JobCreate, JobUpdate, JobResponse
from backend.app.services.job_service import JobService
from backend.app.api.deps import get_current_user, get_current_recruiter
from backend.app.models.user import User

router = APIRouter()

@router.get("/", response_model=list[JobResponse])
def read_jobs(
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get all jobs. Authenticated users only.
    """
    return JobService.get_all_jobs(db)

@router.get("/{job_id}", response_model=JobResponse)
def read_job(
    job_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific job by ID.
    """
    job = JobService.get_job(db, job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job

@router.post("/", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_job(
    job_in: JobCreate,
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter)
):
    """
    Create a new job post. Recruiters only.
    """
    return JobService.create_job(db, job_in.model_dump())

@router.put("/{job_id}", response_model=JobResponse)
def update_job(
    job_id: int,
    job_in: JobUpdate,
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter)
):
    """
    Update an existing job post. Recruiters only.
    """
    job = JobService.update_job(db, job_id, job_in.model_dump(exclude_unset=True))
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    recruiter: User = Depends(get_current_recruiter)
):
    """
    Delete a job post. Recruiters only.
    """
    success = JobService.delete_job(db, job_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    return None
