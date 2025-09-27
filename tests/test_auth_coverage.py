#!/usr/bin/env python3
"""
Comprehensive test coverage for server/auth.py
Target: Increase from 15% to 80% coverage
"""
import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

# Set test environment
os.environ.setdefault("NINAIVALAIGAL_JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("NINAIVALAIGAL_ENV", "test")

from server.auth import (
    create_access_token,
    verify_token,
    get_current_user,
    hash_password,
    verify_password,
    authenticate_user,
    create_user,
    get_user_by_email,
    get_user_by_id
)


class TestPasswordHashing:
    """Test password hashing and verification functions."""
    
    def test_hash_password_creates_valid_hash(self):
        """Test that password hashing creates a valid bcrypt hash."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password  # Should be hashed, not plain text
        assert hashed.startswith("$2b$")  # bcrypt hash format
    
    def test_verify_password_with_correct_password(self):
        """Test password verification with correct password."""
        password = "test_password_123"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_with_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"
        wrong_password = "wrong_password"
        hashed = hash_password(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_verify_password_with_invalid_hash(self):
        """Test password verification with invalid hash."""
        password = "test_password_123"
        invalid_hash = "not_a_valid_hash"
        
        assert verify_password(password, invalid_hash) is False


class TestJWTTokens:
    """Test JWT token creation and verification."""
    
    def test_create_access_token_with_valid_data(self):
        """Test creating access token with valid user data."""
        user_data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data=user_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long
    
    def test_create_access_token_with_expiration(self):
        """Test creating access token with custom expiration."""
        from datetime import timedelta
        
        user_data = {"sub": "test@example.com", "user_id": "123"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data=user_data, expires_delta=expires_delta)
        
        assert token is not None
        assert isinstance(token, str)
    
    @patch('server.auth.jwt.decode')
    def test_verify_token_with_valid_token(self, mock_decode):
        """Test token verification with valid token."""
        mock_decode.return_value = {"sub": "test@example.com", "user_id": "123"}
        
        token = "valid_jwt_token"
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test@example.com"
        assert payload["user_id"] == "123"
    
    @patch('server.auth.jwt.decode')
    def test_verify_token_with_invalid_token(self, mock_decode):
        """Test token verification with invalid token."""
        from jose import JWTError
        mock_decode.side_effect = JWTError("Invalid token")
        
        token = "invalid_jwt_token"
        payload = verify_token(token)
        
        assert payload is None
    
    @patch('server.auth.jwt.decode')
    def test_verify_token_with_expired_token(self, mock_decode):
        """Test token verification with expired token."""
        from jose import ExpiredSignatureError
        mock_decode.side_effect = ExpiredSignatureError("Token expired")
        
        token = "expired_jwt_token"
        payload = verify_token(token)
        
        assert payload is None


class TestUserAuthentication:
    """Test user authentication functions."""
    
    @patch('server.auth.get_user_by_email')
    def test_authenticate_user_with_valid_credentials(self, mock_get_user):
        """Test user authentication with valid credentials."""
        # Mock user data
        hashed_password = hash_password("correct_password")
        mock_user = {
            "id": "123",
            "email": "test@example.com",
            "hashed_password": hashed_password,
            "is_active": True
        }
        mock_get_user.return_value = mock_user
        
        result = authenticate_user("test@example.com", "correct_password")
        
        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["id"] == "123"
    
    @patch('server.auth.get_user_by_email')
    def test_authenticate_user_with_invalid_email(self, mock_get_user):
        """Test user authentication with invalid email."""
        mock_get_user.return_value = None
        
        result = authenticate_user("nonexistent@example.com", "password")
        
        assert result is None
    
    @patch('server.auth.get_user_by_email')
    def test_authenticate_user_with_wrong_password(self, mock_get_user):
        """Test user authentication with wrong password."""
        hashed_password = hash_password("correct_password")
        mock_user = {
            "id": "123",
            "email": "test@example.com",
            "hashed_password": hashed_password,
            "is_active": True
        }
        mock_get_user.return_value = mock_user
        
        result = authenticate_user("test@example.com", "wrong_password")
        
        assert result is None
    
    @patch('server.auth.get_user_by_email')
    def test_authenticate_user_with_inactive_user(self, mock_get_user):
        """Test user authentication with inactive user."""
        hashed_password = hash_password("correct_password")
        mock_user = {
            "id": "123",
            "email": "test@example.com",
            "hashed_password": hashed_password,
            "is_active": False
        }
        mock_get_user.return_value = mock_user
        
        result = authenticate_user("test@example.com", "correct_password")
        
        assert result is None


class TestUserManagement:
    """Test user creation and retrieval functions."""
    
    @patch('server.auth.database.execute_query')
    def test_create_user_with_valid_data(self, mock_execute):
        """Test user creation with valid data."""
        mock_execute.return_value = [{"id": "123"}]
        
        user_data = {
            "email": "test@example.com",
            "password": "secure_password",
            "full_name": "Test User"
        }
        
        result = create_user(user_data)
        
        assert result is not None
        assert result["id"] == "123"
        mock_execute.assert_called_once()
    
    @patch('server.auth.database.execute_query')
    def test_create_user_with_duplicate_email(self, mock_execute):
        """Test user creation with duplicate email."""
        from psycopg2 import IntegrityError
        mock_execute.side_effect = IntegrityError("Duplicate email")
        
        user_data = {
            "email": "existing@example.com",
            "password": "secure_password",
            "full_name": "Test User"
        }
        
        with pytest.raises(HTTPException) as exc_info:
            create_user(user_data)
        
        assert exc_info.value.status_code == 400
        assert "already registered" in str(exc_info.value.detail)
    
    @patch('server.auth.database.execute_query')
    def test_get_user_by_email_existing_user(self, mock_execute):
        """Test retrieving existing user by email."""
        mock_user = {
            "id": "123",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True
        }
        mock_execute.return_value = [mock_user]
        
        result = get_user_by_email("test@example.com")
        
        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["id"] == "123"
    
    @patch('server.auth.database.execute_query')
    def test_get_user_by_email_nonexistent_user(self, mock_execute):
        """Test retrieving nonexistent user by email."""
        mock_execute.return_value = []
        
        result = get_user_by_email("nonexistent@example.com")
        
        assert result is None
    
    @patch('server.auth.database.execute_query')
    def test_get_user_by_id_existing_user(self, mock_execute):
        """Test retrieving existing user by ID."""
        mock_user = {
            "id": "123",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True
        }
        mock_execute.return_value = [mock_user]
        
        result = get_user_by_id("123")
        
        assert result is not None
        assert result["id"] == "123"
        assert result["email"] == "test@example.com"
    
    @patch('server.auth.database.execute_query')
    def test_get_user_by_id_nonexistent_user(self, mock_execute):
        """Test retrieving nonexistent user by ID."""
        mock_execute.return_value = []
        
        result = get_user_by_id("nonexistent_id")
        
        assert result is None


class TestCurrentUserDependency:
    """Test get_current_user dependency function."""
    
    @patch('server.auth.verify_token')
    @patch('server.auth.get_user_by_email')
    def test_get_current_user_with_valid_token(self, mock_get_user, mock_verify):
        """Test getting current user with valid token."""
        # Mock token verification
        mock_verify.return_value = {"sub": "test@example.com", "user_id": "123"}
        
        # Mock user retrieval
        mock_user = {
            "id": "123",
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True
        }
        mock_get_user.return_value = mock_user
        
        token = "valid_jwt_token"
        result = get_current_user(token)
        
        assert result is not None
        assert result["email"] == "test@example.com"
        assert result["id"] == "123"
    
    @patch('server.auth.verify_token')
    def test_get_current_user_with_invalid_token(self, mock_verify):
        """Test getting current user with invalid token."""
        mock_verify.return_value = None
        
        token = "invalid_jwt_token"
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token)
        
        assert exc_info.value.status_code == 401
        assert "Could not validate credentials" in str(exc_info.value.detail)
    
    @patch('server.auth.verify_token')
    @patch('server.auth.get_user_by_email')
    def test_get_current_user_with_nonexistent_user(self, mock_get_user, mock_verify):
        """Test getting current user when user doesn't exist."""
        mock_verify.return_value = {"sub": "test@example.com", "user_id": "123"}
        mock_get_user.return_value = None
        
        token = "valid_jwt_token"
        
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
