# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Unit tests for auth contracts."""

import pytest

# Test import paths work
from ninaivalaigal_contracts.auth.v1 import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    Token,
    User,
)
from pydantic import ValidationError


class TestLoginRequest:
    """Test LoginRequest contract."""

    def test_valid_login_request(self):
        """Test valid login request creation."""
        request = LoginRequest(email="test@example.com", password="SecurePass123!")
        assert request.email == "test@example.com"
        assert request.password == "SecurePass123!"  # pragma: allowlist secret

    def test_invalid_email(self):
        """Test invalid email format rejected."""
        with pytest.raises(ValidationError) as exc_info:
            LoginRequest(email="not-an-email", password="SecurePass123!")  # pragma: allowlist secret
        errors = exc_info.value.errors()
        assert any("email" in str(e).lower() for e in errors)

    def test_missing_password(self):
        """Test missing password rejected."""
        with pytest.raises(ValidationError):
            LoginRequest(email="test@example.com")


class TestRegisterRequest:
    """Test RegisterRequest contract."""

    def test_valid_register_request(self):
        """Test valid registration request."""
        request = RegisterRequest(email="newuser@example.com", password="SecurePass123!", full_name="New User")
        assert request.email == "newuser@example.com"
        assert len(request.password) >= 8

    def test_password_too_short(self):
        """Test password length validation."""
        with pytest.raises(ValidationError) as exc_info:
            RegisterRequest(
                email="test@example.com", password="short", full_name="Test User"  # pragma: allowlist secret
            )
        errors = exc_info.value.errors()
        assert any("password" in str(e).lower() for e in errors)

    def test_empty_full_name(self):
        """Test empty full name rejected."""
        with pytest.raises(ValidationError):
            RegisterRequest(
                email="test@example.com", password="SecurePass123!", full_name=""  # pragma: allowlist secret
            )


class TestAuthResponse:
    """Test AuthResponse contract."""

    def test_valid_auth_response(self):
        """Test valid auth response creation."""
        user = User(
            id="user123",
            email="test@example.com",
            full_name="Test User",
            roles=["user"],
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
        )
        response = AuthResponse(
            access_token="eyJ0...", refresh_token="eyJ1...", expires_in=86400, token_type="Bearer", user=user
        )
        assert response.access_token == "eyJ0..."
        assert response.expires_in == 86400
        assert response.user.email == "test@example.com"

    def test_default_token_type(self):
        """Test default token type is Bearer."""
        user = User(
            id="user123",
            email="test@example.com",
            full_name="Test User",
            roles=[],
            is_active=True,
            created_at="2025-01-01T00:00:00Z",
        )
        response = AuthResponse(access_token="token", refresh_token="refresh", expires_in=3600, user=user)
        assert response.token_type == "Bearer"


class TestSerialization:
    """Test JSON serialization."""

    def test_login_request_json_roundtrip(self):
        """Test serialization and deserialization."""
        original = LoginRequest(email="test@example.com", password="SecurePass123!")
        json_str = original.model_dump_json()
        restored = LoginRequest.model_validate_json(json_str)
        assert restored.email == original.email
        assert restored.password == original.password

    def test_token_serialization(self):
        """Test Token model serialization."""
        token = Token(access_token="eyJ0...", token_type="Bearer")
        json_data = token.model_dump()
        assert json_data["access_token"] == "eyJ0..."
        assert json_data["token_type"] == "Bearer"
