from unittest.mock import MagicMock
from datetime import datetime
from backend.app.services.auth_service import AuthService
from backend.app.models.user import User

def test_password_hashing():
    """
    Test passlib bcrypt password hashing and verification.
    """
    pwd = "super_secure_pass"
    hashed = AuthService.hash_password(pwd)
    
    assert hashed != pwd
    assert AuthService.verify_password(pwd, hashed)
    assert not AuthService.verify_password("wrong_password", hashed)

def test_api_login_unauthorized(client):
    """
    Checks that calling login with incorrect credentials yields 401.
    """
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@user.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert "detail" in response.json()

def test_api_register_user(client, mock_db):
    """
    Checks that registration API processes post queries and registers user.
    """
    mock_user = User(
        id=10,
        name="Alice Tester",
        email="alice@test.com",
        password_hash="hashed_code",
        role="job_seeker",
        created_at=datetime.utcnow()
    )
    
    # Mock registration service to return static user record
    original_register = AuthService.register_user
    AuthService.register_user = MagicMock(return_value=mock_user)
    
    try:
        response = client.post(
            "/api/auth/register",
            json={
                "name": "Alice Tester",
                "email": "alice@test.com",
                "password": "password123",
                "role": "job_seeker"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "alice@test.com"
        assert data["name"] == "Alice Tester"
        assert data["role"] == "job_seeker"
    finally:
        # Restore mock modifications
        AuthService.register_user = original_register
