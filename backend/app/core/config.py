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
        # Prioritize system environment variables over the .env file
        env_file_encoding = 'utf-8'

settings = Settings()

# Force environment overrides if DATABASE_URL is in OS environment variables
if "DATABASE_URL" in os.environ:
    db_url = os.environ["DATABASE_URL"]
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    settings.DATABASE_URL = db_url

# Configure HuggingFace/SentenceTransformers cache paths for Vercel's read-only environment
if os.environ.get("VERCEL"):
    os.environ["HF_HOME"] = "/tmp/huggingface"
    os.environ["SENTENCE_TRANSFORMERS_HOME"] = "/tmp/sentence_transformers"
    settings.UPLOAD_DIR = "/tmp/uploads"

# Ensure uploads directory exists
try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except Exception:
    pass
