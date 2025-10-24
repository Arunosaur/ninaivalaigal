# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Authentication service Pydantic models."""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


# ============================================================================
# Core API Specific Models (Task #79 - Integration)
# ============================================================================


class IndividualUserSignup(BaseModel):
    """Individual user signup request."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    name: str = Field(..., description="User full name")
    account_type: str = Field(default="individual", description="Account type")


class OrganizationSignup(BaseModel):
    """Organization signup request with creator user."""

    user: Dict[str, str] = Field(..., description="User details (email, password, name)")
    organization: Dict[str, str] = Field(..., description="Organization details (name, domain, size, industry)")


class UserLogin(BaseModel):
    """User login request (alias for LoginRequest)."""

    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")


class InvitationAccept(BaseModel):
    """Accept team invitation."""

    invitation_token: str = Field(..., description="Invitation token")
    user: Dict[str, str] = Field(..., description="User details (password, name)")


class UserInvitation(BaseModel):
    """Team user invitation."""

    email: EmailStr = Field(..., description="Invitee email")
    team_id: str = Field(..., description="Team ID")
    role: str = Field(default="member", description="Role (admin, member)")
    message: Optional[str] = Field(default=None, description="Invitation message")


class Token(BaseModel):
    """JWT token response."""

    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="Bearer", description="Token type")


class TokenData(BaseModel):
    """Decoded token data."""

    username: Optional[str] = Field(default=None, description="Username")
    user_id: Optional[str] = Field(default=None, description="User ID (UUID)")


class ApiKeyCreate(BaseModel):
    """Create API key request."""

    name: str = Field(..., description="API key name")
    scopes: List[str] = Field(default_factory=list, description="Access scopes")
    expiration: Optional[int] = Field(default=None, description="Expiration in days (None = never)")


class ApiKeyResponse(BaseModel):
    """API key response."""

    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="API key name")
    key: Optional[str] = Field(default=None, description="API key (only on creation)")
    key_preview: str = Field(..., description="Key preview (first 8 chars)")
    scopes: List[str] = Field(default_factory=list, description="Access scopes")
    created_at: str = Field(..., description="Creation timestamp")
    expires_at: Optional[str] = Field(default=None, description="Expiration timestamp")
    last_used: Optional[str] = Field(default=None, description="Last used timestamp")
    is_active: bool = Field(default=True, description="Whether key is active")


class TokenUsage(BaseModel):
    """Token usage statistics."""

    requests_today: int = Field(default=0, description="Requests made today")


class UserProfileUpdate(BaseModel):
    """Update user profile request."""

    name: Optional[str] = Field(None, min_length=1, max_length=255, description="User full name")
    username: Optional[str] = Field(None, min_length=3, max_length=255, description="Username")
    email: Optional[EmailStr] = Field(None, description="User email")


class UserProfileResponse(BaseModel):
    """User profile response."""

    id: str = Field(..., description="User ID (UUID)")
    username: Optional[str] = Field(None, description="Username")
    email: Optional[str] = Field(None, description="User email")
    name: str = Field(..., description="User full name")
    account_type: str = Field(..., description="Account type")
    subscription_tier: str = Field(..., description="Subscription tier")
    role: str = Field(..., description="User role")
    email_verified: bool = Field(..., description="Email verification status")
    is_active: bool = Field(..., description="Active status")
    created_at: str = Field(..., description="Creation timestamp")
    last_login: Optional[str] = Field(None, description="Last login timestamp")

    model_config = ConfigDict(from_attributes=True)
