#!/usr/bin/env python3
"""
Comprehensive test coverage for server/auth.py functions
Target: Increase from 15% to 80% coverage
"""
import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest

# Set test environment
os.environ.setdefault("NINAIVALAIGAL_JWT_SECRET", "test_secret_key_for_testing")
os.environ.setdefault("NINAIVALAIGAL_ENV", "test")

# Import the actual functions from auth.py
from server.auth import (
    authenticate_user,
    create_access_token,
    create_individual_user,
    generate_invitation_token,
    generate_verification_token,
    hash_password,
    validate_email,
    validate_password,
    verify_password,
    verify_token,
)


class TestPasswordValidation:
    """Test password validation functionality."""

    def test_validate_password_valid_strong_password(self):
        """Test password validation with strong password."""
        strong_password = "StrongPass123!"  # pragma: allowlist secret
        assert validate_password(strong_password) is True

    def test_validate_password_too_short(self):
        """Test password validation with too short password."""
        short_password = "short"  # pragma: allowlist secret
        assert validate_password(short_password) is False

    def test_validate_password_minimum_length(self):
        """Test password validation with minimum length."""
        min_password = "12345678"  # pragma: allowlist secret  # Exactly 8 characters
        assert validate_password(min_password) is True

    def test_validate_password_empty_string(self):
        """Test password validation with empty string."""
        empty_password = ""  # pragma: allowlist secret
        assert validate_password(empty_password) is False


class TestEmailValidation:
    """Test email validation functionality."""

    def test_validate_email_valid_format(self):
        """Test email validation with valid email format."""
        valid_email = "test@example.com"
        result = validate_email(valid_email)
        assert result == valid_email.lower()

    def test_validate_email_uppercase_conversion(self):
        """Test email validation converts to lowercase."""
        uppercase_email = "TEST@EXAMPLE.COM"
        result = validate_email(uppercase_email)
        assert result == "test@example.com"

    def test_validate_email_invalid_format(self):
        """Test email validation with invalid format."""
        invalid_email = "not-an-email"
        with pytest.raises(ValueError):
            validate_email(invalid_email)

    def test_validate_email_missing_domain(self):
        """Test email validation with missing domain."""
        invalid_email = "test@"
        with pytest.raises(ValueError):
            validate_email(invalid_email)


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password_creates_valid_hash(self):
        """Test that password hashing creates a valid bcrypt hash."""
        password = "test_password_123"  # pragma: allowlist secret
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed != password
        assert hashed.startswith("$2b$")

    def test_verify_password_correct_password(self):
        """Test password verification with correct password."""
        password = "test_password_123"  # pragma: allowlist secret
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = "test_password_123"  # pragma: allowlist secret
        wrong_password = "wrong_password"  # pragma: allowlist secret
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "test_password_123"  # pragma: allowlist secret
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2  # Different salts should produce different hashes
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenGeneration:
    """Test token generation functions."""

    def test_generate_verification_token_format(self):
        """Test verification token generation format."""
        token = generate_verification_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20  # URL-safe tokens are typically longer

    def test_generate_verification_token_uniqueness(self):
        """Test that verification tokens are unique."""
        token1 = generate_verification_token()
        token2 = generate_verification_token()

        assert token1 != token2

    def test_generate_invitation_token_format(self):
        """Test invitation token generation format."""
        token = generate_invitation_token()

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 20

    def test_generate_invitation_token_uniqueness(self):
        """Test that invitation tokens are unique."""
        token1 = generate_invitation_token()
        token2 = generate_invitation_token()

        assert token1 != token2


class TestJWTTokens:
    """Test JWT token creation and verification."""

    def test_create_access_token_basic(self):
        """Test creating access token with basic data."""
        user_data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data=user_data)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT tokens are typically long

    def test_create_access_token_with_expiration(self):
        """Test creating access token with custom expiration."""
        user_data = {"sub": "test@example.com", "user_id": "123"}
        expires_delta = timedelta(minutes=30)
        token = create_access_token(data=user_data, expires_delta=expires_delta)

        assert token is not None
        assert isinstance(token, str)

    def test_verify_token_valid(self):
        """Test verifying valid JWT token."""
        user_data = {"sub": "test@example.com", "user_id": "123"}
        token = create_access_token(data=user_data)

        token_data = verify_token(token)

        assert token_data is not None
        assert token_data.username == "test@example.com"  # pragma: allowlist secret
        assert token_data.user_id == "123"  # pragma: allowlist secret

    def test_verify_token_invalid(self):
        """Test verifying invalid JWT token."""
        invalid_token = "invalid.jwt.token"  # pragma: allowlist secret

        with pytest.raises(Exception):  # Should raise JWT decode error
            verify_token(invalid_token)

    def test_verify_token_expired(self):
        """Test verifying expired JWT token."""
        user_data = {"sub": "test@example.com", "user_id": "123"}
        # Create token that expires immediately
        expires_delta = timedelta(seconds=-1)
        token = create_access_token(data=user_data, expires_delta=expires_delta)

        with pytest.raises(Exception):  # Should raise expired token error
            verify_token(token)


class TestUserAuthentication:
    """Test user authentication functions."""

    @patch("server.auth.get_db")
    def test_authenticate_user_success(self, mock_get_db):
        """Test successful user authentication."""
        # Mock database and session
        mock_db = Mock()
        mock_session = Mock()
        mock_get_db.return_value = mock_db
        mock_db.get_session.return_value = mock_session

        # Mock user query result
        mock_user = Mock()
        mock_user.id = "123"
        mock_user.email = "test@example.com"
        mock_user.name = "Test User"
        mock_user.hashed_password = hash_password("correct_password"  # pragma: allowlist secret)
        mock_user.is_verified = True

        mock_session.query().filter().first.return_value = mock_user

        result = authenticate_user("test@example.com", "correct_password")

        assert result is not None
        assert result["user_id"] == "123"
        assert result["email"] == "test@example.com"
        mock_session.close.assert_called_once()

    @patch("server.auth.get_db")
    def test_authenticate_user_wrong_password(self, mock_get_db):
        """Test authentication with wrong password."""
        mock_db = Mock()
        mock_session = Mock()
        mock_get_db.return_value = mock_db
        mock_db.get_session.return_value = mock_session

        mock_user = Mock()
        mock_user.hashed_password = hash_password("correct_password"  # pragma: allowlist secret)
        mock_user.is_verified = True

        mock_session.query().filter().first.return_value = mock_user

        result = authenticate_user("test@example.com", "wrong_password")

        assert result is None
        mock_session.close.assert_called_once()

    @patch("server.auth.get_db")
    def test_authenticate_user_not_found(self, mock_get_db):
        """Test authentication with non-existent user."""
        mock_db = Mock()
        mock_session = Mock()
        mock_get_db.return_value = mock_db
        mock_db.get_session.return_value = mock_session

        mock_session.query().filter().first.return_value = None

        result = authenticate_user("nonexistent@example.com", "password")

        assert result is None
        mock_session.close.assert_called_once()

    @patch("server.auth.get_db")
    def test_authenticate_user_unverified(self, mock_get_db):
        """Test authentication with unverified user."""
        mock_db = Mock()
        mock_session = Mock()
        mock_get_db.return_value = mock_db
        mock_db.get_session.return_value = mock_session

        mock_user = Mock()
        mock_user.hashed_password = hash_password("correct_password"  # pragma: allowlist secret)
        mock_user.is_verified = False  # Unverified user

        mock_session.query().filter().first.return_value = mock_user

        result = authenticate_user("test@example.com", "correct_password")

        assert result is None
        mock_session.close.assert_called_once()


class TestUserCreation:
    """Test user creation functionality."""

    @patch("server.auth.get_db")
    @patch("server.auth.send_verification_email")
    def test_create_individual_user_success(self, mock_send_email, mock_get_db):
        """Test successful individual user creation."""
        from server.auth import IndividualUserSignup

        # Mock database
        mock_db = Mock()
        mock_session = Mock()
        mock_get_db.return_value = mock_db
        mock_db.get_session.return_value = mock_session

        # Mock successful user creation
        mock_user = Mock()
        mock_user.id = "123"
        mock_user.email = "test@example.com"
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()

        # Create signup data
        signup_data = Mock()
        signup_data.email = "test@example.com"
        signup_data.password = "secure_password"  # pragma: allowlist secret
        signup_data.name = "Test User"

        # Mock the User class constructor
        with patch("server.auth.User") as mock_user_class:
            mock_user_class.return_value = mock_user

            result = create_individual_user(signup_data)

            assert result is not None
            assert result["user_id"] == "123"
            assert result["email"] == "test@example.com"
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_send_email.assert_called_once()
            mock_session.close.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
