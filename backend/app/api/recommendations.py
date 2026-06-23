from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import RecommendationResponse, RoadmapResponse
from backend.app.services.recommendation_service import RecommendationService
from backend.app.services.roadmap_service import RoadmapService
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

router = APIRouter()

@router.get("/", response_model=list[RecommendationResponse])
def get_recommendations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get top AI-powered job recommendations with match scores and skill gaps.
    """
    recs = RecommendationService.get_recommendations_for_user(db, user_id=current_user.id)
    if not recs:
        # Check if user has a resume uploaded
        from backend.app.services.resume_service import ResumeService
        resume = ResumeService.get_user_resume(db, current_user.id)
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please upload a resume first to receive recommendations."
            )
    return recs

@router.get("/{job_id}/roadmap", response_model=RoadmapResponse)
def get_roadmap(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Generates a personalized career learning path from current skills to target job requirements.
    """
    try:
        return RoadmapService.generate_roadmap(db, user_id=current_user.id, job_id=job_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
