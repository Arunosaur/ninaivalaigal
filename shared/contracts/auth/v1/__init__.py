# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""Authentication service contracts v1."""

from .models import (  # User models; Request models; Response models; Core API specific
    ApiKeyCreate,
    ApiKeyResponse,
    AuthResponse,
    IndividualUserSignup,
    InvitationAccept,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    OrganizationSignup,
    RefreshRequest,
    RegisterRequest,
    Token,
    TokenData,
    TokenUsage,
    User,
    UserInvitation,
    UserLogin,
    UserProfileResponse,
    UserProfileUpdate,
    ValidateRequest,
    ValidateResponse,
)

__all__ = [
    # User models
    "User",
    # Request models
    "RegisterRequest",
    "LoginRequest",
    "RefreshRequest",
    "ValidateRequest",
    "LogoutRequest",
    # Response models
    "AuthResponse",
    "ValidateResponse",
    "LogoutResponse",
    # Core API specific
    "IndividualUserSignup",
    "OrganizationSignup",
    "UserLogin",
    "InvitationAccept",
    "UserInvitation",
    "Token",
    "TokenData",
    "ApiKeyCreate",
    "ApiKeyResponse",
    "TokenUsage",
    "UserProfileUpdate",
    "UserProfileResponse",
]
