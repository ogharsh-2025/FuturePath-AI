from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import ResumeResponse
from backend.app.services.resume_service import ResumeService
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

router = APIRouter()

@router.post("/upload", response_model=ResumeResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a resume file (PDF or DOCX). Extracts content, skills, vector embeddings,
    and dynamically builds matching recommendations.
    """
    try:
        file_bytes = await file.read()
        resume = ResumeService.upload_and_process_resume(
            db, 
            user_id=current_user.id, 
            file_bytes=file_bytes, 
            filename=file.filename
        )
        return resume
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the resume: {str(e)}"
        )

@router.get("/my-resume", response_model=ResumeResponse)
def get_my_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the current logged-in user's resume, text, and skills list.
    """
    resume = ResumeService.get_user_resume(db, user_id=current_user.id)
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume uploaded yet"
        )
    return resume

@router.delete("/reset", status_code=status.HTTP_204_NO_CONTENT)
def reset_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes the current logged-in user's resume and all associated recommendations.
    """
    import os
    resume = ResumeService.get_user_resume(db, user_id=current_user.id)
    if resume:
        from backend.app.repositories.resume_repository import ResumeRepository
        from backend.app.repositories.recommendation_repository import RecommendationRepository
        
        # Remove file physically if it exists
        if resume.resume_file and os.path.exists(resume.resume_file):
            try:
                os.remove(resume.resume_file)
            except Exception:
                pass
                
        ResumeRepository.delete(db, resume)
        RecommendationRepository.delete_by_user_id(db, current_user.id)
        
    return None
