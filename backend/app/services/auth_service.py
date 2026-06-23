from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.repositories.user_repository import UserRepository
from backend.app.models.user import User

# Setup password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """
        Generates a secure JSON Web Token (JWT) containing the user payload.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @classmethod
    def register_user(cls, db: Session, user_reg_data: dict) -> User:
        """
        Registers a new user after verifying that the email is unique.
        """
        existing_user = UserRepository.get_by_email(db, user_reg_data["email"])
        if existing_user:
            raise ValueError("Email already registered")
            
        # Hash password and prepare DB dict
        password_hash = cls.hash_password(user_reg_data["password"])
        db_user_data = {
            "name": user_reg_data["name"],
            "email": user_reg_data["email"],
            "password_hash": password_hash,
            "role": user_reg_data.get("role", "job_seeker")
        }
        
        return UserRepository.create(db, db_user_data)

    @classmethod
    def authenticate_user(cls, db: Session, email: str, password: str) -> User | None:
        """
        Authenticates a user email and password. Returns the User model if valid.
        """
        user = UserRepository.get_by_email(db, email)
        if not user:
            return None
        if not cls.verify_password(password, user.password_hash):
            return None
        return user
