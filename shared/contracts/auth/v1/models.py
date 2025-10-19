# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Authentication service Pydantic models."""

from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    """User information."""

    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email")
    full_name: str = Field(..., description="User full name")
    roles: List[str] = Field(default_factory=list, description="User roles")
    is_active: bool = Field(default=True, description="Whether user is active")
    created_at: str = Field(..., description="Creation timestamp")


class RegisterRequest(BaseModel):
    """Register a new user."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    full_name: str = Field(..., min_length=1, description="User full name")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Additional metadata")


class LoginRequest(BaseModel):
    """Login with credentials."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RefreshRequest(BaseModel):
    """Refresh access token."""

    refresh_token: str = Field(..., description="Refresh token")


class ValidateRequest(BaseModel):
    """Validate token."""

    access_token: str = Field(..., description="Access token to validate")


class LogoutRequest(BaseModel):
    """Logout request."""

    access_token: str = Field(..., description="Access token to invalidate")


class AuthResponse(BaseModel):
    """Authentication response."""

    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    expires_in: int = Field(..., description="Token expiration in seconds")
    token_type: str = Field(default="Bearer", description="Token type")
    user: User = Field(..., description="User information")


class ValidateResponse(BaseModel):
    """Token validation response."""

    valid: bool = Field(..., description="Whether token is valid")
    user: Optional[User] = Field(default=None, description="User information if valid")
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")


class LogoutResponse(BaseModel):
    """Logout response."""

    success: bool = Field(..., description="Whether logout was successful")
