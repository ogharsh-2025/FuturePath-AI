import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import get_db

@pytest.fixture
def mock_db():
    """
    Provides a mocked SQLAlchemy Session for isolating tests from the database.
    """
    db = MagicMock()
    # Default query responses to mimic a clean empty database
    db.query.return_value.filter.return_value.first.return_value = None
    db.query.return_value.filter.return_value.all.return_value = []
    db.query.return_value.order_by.return_value.all.return_value = []
    return db

@pytest.fixture
def client(mock_db):
    """
    FastAPI TestClient with overridden get_db dependency to use the mock database session.
    """
    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
