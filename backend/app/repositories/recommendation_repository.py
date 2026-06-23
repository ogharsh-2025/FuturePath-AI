from sqlalchemy.orm import Session
from backend.app.models.recommendation import Recommendation

class RecommendationRepository:
    @staticmethod
    def get_by_user_id(db: Session, user_id: int) -> list[Recommendation]:
        return db.query(Recommendation).filter(Recommendation.user_id == user_id).order_by(Recommendation.match_score.desc()).all()

    @staticmethod
    def delete_by_user_id(db: Session, user_id: int) -> None:
        db.query(Recommendation).filter(Recommendation.user_id == user_id).delete(synchronize_session=False)
        db.commit()

    @staticmethod
    def create_multiple(db: Session, recommendations_data: list[dict]) -> list[Recommendation]:
        db_recs = [Recommendation(**data) for data in recommendations_data]
        db.add_all(db_recs)
        db.commit()
        return db_recs
