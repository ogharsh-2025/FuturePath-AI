from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from backend.app.database.session import get_db
from backend.app.schemas.schemas import UserCreate, UserLogin, UserResponse, Token
from backend.app.services.auth_service import AuthService
from backend.app.api.deps import get_current_user
from backend.app.models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new candidate or recruiter account.
    """
    try:
        user = AuthService.register_user(db, user_in.model_dump())
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
def login_json(user_in: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticates user and returns a JWT access token. Accepts JSON payload.
    """
    user = AuthService.authenticate_user(db, user_in.email, user_in.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/token", response_model=Token)
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """
    Authenticates user via standard OAuth2 form payload. 
    Required to support Swagger UI 'Authorize' locks.
    """
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
def read_user_me(current_user: User = Depends(get_current_user)):
    """
    Returns profile information of the current logged-in user.
    """
    return current_user
