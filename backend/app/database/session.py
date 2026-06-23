from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.types import TypeDecorator, JSON
from backend.app.core.config import settings

# SQLite connection args configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

# Create sessionmaker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

class ArrayType(TypeDecorator):
    """
    Natively supports PostgreSQL ARRAY(Float) type,
    and falls back to JSON serialization on SQLite/other databases.
    """
    impl = JSON

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import ARRAY
            from sqlalchemy import Float
            return dialect.type_descriptor(ARRAY(Float))
        return dialect.type_descriptor(JSON())

def get_db() -> Generator:
    """
    Database session dependency. Yields a database session and ensures
    proper cleanup when the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
