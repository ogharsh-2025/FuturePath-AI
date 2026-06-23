from sqlalchemy.orm import Session
from backend.app.models.user import User

class UserRepository:
    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, user_data: dict) -> User:
        db_user = User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
