# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Unit tests for auth.py core functions."""

from datetime import datetime, timedelta

import pytest
from jose import jwt

# Import auth core functions
from src.auth import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    get_password_policy_message,
    verify_password,
)

# Test configuration
SECRET_KEY = "test-secret-key-for-unit-tests"  # pragma: allowlist secret
ALGORITHM = "HS256"


class TestPasswordHashing:
    """Test password hashing and verification."""

    def test_hash_password(self):
        """Test password is hashed correctly."""
        password = "SecurePass123!"  # pragma: allowlist secret
        hashed = get_password_hash(password)

        # Hash should not equal plaintext
        assert hashed != password
        # Hash should start with bcrypt prefix
        assert hashed.startswith("$2b$")

    def test_verify_correct_password(self):
        """Test correct password verification."""
        password = "SecurePass123!"  # pragma: allowlist secret
        hashed = get_password_hash(password)

        # Correct password should verify
        assert verify_password(password, hashed) is True

    def test_verify_wrong_password(self):
        """Test wrong password rejected."""
        password = "SecurePass123!"  # pragma: allowlist secret
        hashed = get_password_hash(password)

        # Wrong password should not verify
        assert verify_password("WrongPassword", hashed) is False

    def test_different_hashes_for_same_password(self):
        """Test bcrypt creates unique salts."""
        password = "SecurePass123!"  # pragma: allowlist secret
        hash1 = get_password_hash(password)
        hash2 = get_password_hash(password)

        # Different hashes due to unique salts
        assert hash1 != hash2
        # But both verify the same password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTTokens:
    """Test JWT token creation and validation."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        data = {"sub": "user123"}
        token = create_access_token(data, SECRET_KEY, expires_delta=timedelta(hours=1))

        # Token should be a string
        assert isinstance(token, str)
        # Should have 3 parts (header.payload.signature)
        assert token.count(".") == 2

    def test_decode_valid_token(self):
        """Test decoding valid JWT token."""
        user_id = "user123"
        data = {"sub": user_id}
        token = create_access_token(data, SECRET_KEY)

        # Decode token
        payload = decode_access_token(token, SECRET_KEY)

        assert payload is not None
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_decode_expired_token(self):
        """Test expired token is rejected."""
        data = {"sub": "user123"}
        # Create token that expires immediately
        token = create_access_token(data, SECRET_KEY, expires_delta=timedelta(seconds=-1))  # Already expired

        # Decoding should return None (expired)
        payload = decode_access_token(token, SECRET_KEY)
        assert payload is None

    def test_decode_invalid_token(self):
        """Test invalid token format rejected."""
        invalid_token = "not.a.valid.jwt.token"

        payload = decode_access_token(invalid_token, SECRET_KEY)
        assert payload is None

    def test_decode_tampered_token(self):
        """Test tampered token is rejected."""
        data = {"sub": "user123"}
        token = create_access_token(data, SECRET_KEY)

        # Tamper with token (change one character)
        tampered = token[:-10] + "TAMPERED" + token[-2:]

        payload = decode_access_token(tampered, SECRET_KEY)
        assert payload is None

    def test_token_contains_expiration(self):
        """Test token includes expiration claim."""
        data = {"sub": "user123"}
        token = create_access_token(data, SECRET_KEY)

        # Manually decode to check structure
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        assert "exp" in payload
        assert "sub" in payload
        assert payload["sub"] == "user123"


class TestPasswordPolicy:
    """Test password policy message."""

    def test_password_policy_message_exists(self):
        """Test password policy message is not empty."""
        message = get_password_policy_message()

        assert message is not None
        assert len(message) > 0
        assert isinstance(message, str)

    def test_password_policy_mentions_requirements(self):
        """Test policy message mentions key requirements."""
        message = get_password_policy_message().lower()

        # Should mention minimum length
        assert "8" in message or "eight" in message
        # Should mention some requirement keywords
        assert any(word in message for word in ["character", "letter", "number", "symbol"])


class TestTokenExpiration:
    """Test token expiration handling."""

    def test_custom_expiration(self):
        """Test custom expiration time."""
        data = {"sub": "user123"}
        expires_in = timedelta(minutes=30)
        token = create_access_token(data, SECRET_KEY, expires_delta=expires_in)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()

        # Expiration should be ~30 minutes from now (with 1 min tolerance)
        time_diff = (exp_time - now).total_seconds()
        assert 29 * 60 < time_diff < 31 * 60

    def test_default_expiration(self):
        """Test default expiration time."""
        data = {"sub": "user123"}
        token = create_access_token(data, SECRET_KEY)

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_time = datetime.fromtimestamp(payload["exp"])
        now = datetime.utcnow()

        # Default should be 24 hours
        time_diff = (exp_time - now).total_seconds()
        assert 23 * 3600 < time_diff < 25 * 3600  # 23-25 hours tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
