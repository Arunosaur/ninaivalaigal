#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Authentication API - Version 1

V1 authentication endpoints for signup, login, and user management.

Related: SPEC-088 API Versioning Strategy
"""

from datetime import datetime, timedelta
from typing import Any

import jwt
from database import Organization, OrganizationRegistration, User, UserInvitation
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from auth import (
    JWT_ALGORITHM,
    JWT_EXPIRATION_HOURS,
    JWT_SECRET,
    IndividualUserSignup,
    InvitationAccept,
    OrganizationSignup,
    UserLogin,
    authenticate_user,
    create_individual_user,
    generate_invitation_token,
    generate_verification_token,
    get_current_user,
    hash_password,
    send_verification_email,
    validate_email,
    verify_email_token,
)

# Create v1 router
from lib.routing.version_router import create_v1_router

router = create_v1_router(prefix="/auth", tags=["v1", "auth"])


# Database helper
def get_db():
    """Get database instance"""
    from auth import get_db as auth_get_db

    return auth_get_db()


@router.post("/signup/individual")
async def signup_individual_user(
    signup_data: IndividualUserSignup, background_tasks: BackgroundTasks
) -> dict[str, Any]:
    """
    Sign up as individual user for personal memory management.

    **V1 Response Format**:
    - snake_case field names
    - Includes verification_required flag
    - Returns user_id as string

    **Breaking changes in V2**:
    - Field names will change to camelCase
    - user_id will be UUID type
    """
    try:
        result = create_individual_user(signup_data)

        # Send verification email in background
        background_tasks.add_task(send_verification_email, result["email"], result["verification_token"])

        # Remove sensitive data from response
        result.pop("verification_token", None)

        return {
            "success": True,
            "message": "Individual user account created successfully",
            "user": result,
            "verification_required": True,
            "next_steps": ["verify_email", "create_first_context", "install_tools"],
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/signup/organization")
async def signup_organization(signup_data: OrganizationSignup, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """
    Sign up as organization with team collaboration features.

    **V1 Response Format**:
    - Returns both user and organization data
    - snake_case field names
    """
    try:
        db = get_db()

        # Validate email
        if not validate_email(signup_data.email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        # Check if user exists
        existing_user = db.query(User).filter(User.email == signup_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        user = User(
            email=signup_data.email,
            password_hash=hash_password(signup_data.password),
            account_type="organization",
            role="owner",
            email_verified=False,
            verification_token=generate_verification_token(),
        )
        db.add(user)
        db.flush()

        # Create organization
        org = Organization(
            name=signup_data.organization_name,
            owner_id=user.id,
            industry=signup_data.industry,
            size=signup_data.size,
        )
        db.add(org)
        db.commit()

        # Send verification email
        background_tasks.add_task(send_verification_email, user.email, user.verification_token)

        return {
            "success": True,
            "message": "Organization account created successfully",
            "user": {
                "user_id": str(user.id),
                "email": user.email,
                "account_type": user.account_type,
                "role": user.role,
            },
            "organization": {
                "organization_id": str(org.id),
                "name": org.name,
                "industry": org.industry,
                "size": org.size,
            },
            "verification_required": True,
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Organization signup failed: {str(e)}")


@router.post("/login")
async def login(login_data: UserLogin) -> dict[str, Any]:
    """
    Authenticate user and return JWT token.

    **V1 Response Format**:
    - Returns jwt_token field
    - Includes expires_in (seconds)
    - snake_case field names
    """
    try:
        result = authenticate_user(login_data.email, login_data.password)

        if not result:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        return {
            "success": True,
            "message": "Login successful",
            "jwt_token": result["jwt_token"],
            "user_id": result["user_id"],
            "email": result["email"],
            "account_type": result["account_type"],
            "role": result["role"],
            "expires_in": JWT_EXPIRATION_HOURS * 3600,
            "token_type": "Bearer",
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")


@router.post("/verify-email")
async def verify_email(token: str) -> dict[str, Any]:
    """
    Verify user email address.

    **V1 Response Format**:
    - Simple success/error response
    """
    try:
        result = verify_email_token(token)

        if not result:
            raise HTTPException(status_code=400, detail="Invalid or expired verification token")

        return {
            "success": True,
            "message": "Email verified successfully",
            "user_id": result["user_id"],
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email verification failed: {str(e)}")


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """
    Get current authenticated user information.

    **V1 Response Format**:
    - Returns full user object
    - snake_case field names
    """
    return {
        "success": True,
        "user": {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "account_type": current_user.account_type,
            "role": current_user.role,
            "email_verified": current_user.email_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """
    Logout current user.

    **V1 Note**: Token invalidation is client-side only.
    Server-side token blacklisting will be added in V2.
    """
    return {
        "success": True,
        "message": "Logged out successfully",
        "note": "Please delete the JWT token from client storage",
    }


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)) -> dict[str, Any]:
    """
    Refresh JWT token.

    **V1 Response Format**:
    - Returns new jwt_token
    - Same expiration time as login
    """
    try:
        # Generate new token
        payload = {
            "user_id": str(current_user.id),
            "email": current_user.email,
            "account_type": current_user.account_type,
            "role": current_user.role,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        }
        new_token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return {
            "success": True,
            "message": "Token refreshed successfully",
            "jwt_token": new_token,
            "expires_in": JWT_EXPIRATION_HOURS * 3600,
            "token_type": "Bearer",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")
