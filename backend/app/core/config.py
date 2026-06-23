import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered Job Recommendation Platform"
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/jobrec"
    SECRET_KEY: str = "9a6c9dfdfc89e13a9609249767852debb081e7d23d8c1c4f5f5ff771a3962d3a"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
