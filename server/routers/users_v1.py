#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
User Management API - Version 1

V1 user management endpoints for profile, settings, and user operations.

Related: SPEC-088 API Versioning Strategy
"""

from typing import Optional
from uuid import UUID

from database import DatabaseManager, User
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

from auth import get_current_user

# Create v1 router
from lib.routing.version_router import create_v1_router

router = create_v1_router(prefix="/users", tags=["v1", "users"])


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


# Request/Response Models
class UserProfileUpdate(BaseModel):
    """Model for updating user profile"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None


class UserProfileResponse(BaseModel):
    """Model for user profile response - V1 format"""

    user_id: str  # V1 uses string, V2 will use UUID
    username: Optional[str]
    email: Optional[str]
    name: str
    account_type: str
    subscription_tier: str
    role: str
    email_verified: bool
    created_at: Optional[str]  # V1 uses ISO string, V2 will use datetime


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> dict:
    """
    Get current user's profile.

    **V1 Response Format**:
    - snake_case field names
    - user_id as string
    - created_at as ISO string
    """
    return {
        "success": True,
        "user": {
            "user_id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "name": current_user.name or "",
            "account_type": current_user.account_type,
            "subscription_tier": current_user.subscription_tier or "free",
            "role": current_user.role,
            "email_verified": current_user.email_verified,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
        },
    }


@router.put("/me")
async def update_my_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """
    Update current user's profile.

    **V1 Behavior**:
    - Partial updates supported
    - Email change requires re-verification (not implemented in V1)
    """
    try:
        # Update fields if provided
        if profile_update.name is not None:
            current_user.name = profile_update.name
        if profile_update.username is not None:
            # Check username uniqueness
            existing = (
                db.session.query(User)
                .filter(User.username == profile_update.username, User.id != current_user.id)
                .first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Username already taken")
            current_user.username = profile_update.username
        if profile_update.email is not None:
            # Check email uniqueness
            existing = (
                db.session.query(User).filter(User.email == profile_update.email, User.id != current_user.id).first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Email already registered")
            current_user.email = profile_update.email
            current_user.email_verified = False  # Require re-verification

        db.session.commit()

        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": {
                "user_id": str(current_user.id),
                "username": current_user.username,
                "email": current_user.email,
                "name": current_user.name,
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"Profile update failed: {str(e)}")


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """
    Get user by ID (public profile).

    **V1 Behavior**:
    - Returns limited public information
    - Email hidden for privacy
    """
    try:
        user = db.session.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "success": True,
            "user": {
                "user_id": str(user.id),
                "username": user.username,
                "name": user.name or "",
                "account_type": user.account_type,
                # Email hidden for privacy
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")


@router.get("/")
async def list_users(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """
    List users (admin only in V1).

    **V1 Behavior**:
    - Simple pagination with skip/limit
    - Returns public profiles only

    **V2 Changes**:
    - Cursor-based pagination
    - Advanced filtering
    """
    try:
        # V1: Simple admin check
        if current_user.role not in ["admin", "owner"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        users = db.session.query(User).offset(skip).limit(limit).all()
        total = db.session.query(User).count()

        return {
            "success": True,
            "users": [
                {
                    "user_id": str(user.id),
                    "username": user.username,
                    "name": user.name or "",
                    "account_type": user.account_type,
                    "role": user.role,
                }
                for user in users
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list users: {str(e)}")


@router.delete("/me")
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
) -> dict:
    """
    Delete current user's account.

    **V1 Behavior**:
    - Hard delete (immediate)
    - No grace period

    **V2 Changes**:
    - Soft delete with 30-day grace period
    - Data export before deletion
    """
    try:
        db.session.delete(current_user)
        db.session.commit()

        return {
            "success": True,
            "message": "Account deleted successfully",
        }

    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"Account deletion failed: {str(e)}")
