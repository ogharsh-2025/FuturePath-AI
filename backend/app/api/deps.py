from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.database.session import get_db
from backend.app.repositories.user_repository import UserRepository
from backend.app.models.user import User
from backend.app.schemas.schemas import TokenData

# OAuth2 login scheme (points to register/login token path)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_current_user(
    db: Session = Depends(get_db)
) -> User:
    """
    Bypasses authentication and always returns a default guest user.
    """
    user = UserRepository.get_by_email(db, "guest@example.com")
    if not user:
        user_data = {
            "name": "Guest User",
            "email": "guest@example.com",
            "password_hash": "guest_password_hash",
            "role": "recruiter"
        }
        user = UserRepository.create(db, user_data)
    return user

def get_current_recruiter(current_user: User = Depends(get_current_user)) -> User:
    """
    Bypasses role checking and returns the current guest user.
    """
    return current_user
