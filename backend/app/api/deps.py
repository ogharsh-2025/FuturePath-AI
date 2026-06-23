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
    db: Session = Depends(get_db), 
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Decodes the JWT access token and retrieves the current authenticated user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id_str: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id_str is None:
            raise credentials_exception
        token_data = TokenData(user_id=int(user_id_str), role=role)
    except (JWTError, ValueError):
        raise credentials_exception
        
    user = UserRepository.get_by_id(db, user_id=token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

def get_current_recruiter(current_user: User = Depends(get_current_user)) -> User:
    """
    Verifies that the authenticated user has the 'recruiter' role.
    """
    if current_user.role != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Recruiter access required."
        )
    return current_user
