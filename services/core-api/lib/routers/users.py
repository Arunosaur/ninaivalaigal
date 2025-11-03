#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
User Management Router
Extracted from main.py for better code organization
"""

from typing import Optional
from uuid import UUID

from auth_service import get_current_user
from database import DatabaseManager, User
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field

# Import models from shared contracts (SPEC-100 Task #79)
from auth.v1.models import UserProfileResponse, UserProfileUpdate


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


# NOTE: User profile models now imported from shared contracts

# Initialize router
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's profile

    Returns complete profile information for the authenticated user.
    """
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        name=current_user.name,
        account_type=current_user.account_type,
        subscription_tier=current_user.subscription_tier,
        role=current_user.role,
        email_verified=current_user.email_verified,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat(),
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
    )


@router.patch("/me", response_model=UserProfileResponse)
def update_current_user_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Update current user's profile

    Allows user to update their own name, username, and email.
    Email updates require re-verification.
    """
    try:
        session = db.get_session()
        user = session.query(User).filter(User.id == current_user.id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Update fields if provided
        if profile_update.name is not None:
            user.name = profile_update.name

        if profile_update.username is not None:
            # Check if username is already taken
            existing = (
                session.query(User).filter(User.username == profile_update.username, User.id != current_user.id).first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Username already taken")
            user.username = profile_update.username

        if profile_update.email is not None and profile_update.email != user.email:
            # Check if email is already taken
            existing = (
                session.query(User).filter(User.email == profile_update.email, User.id != current_user.id).first()
            )
            if existing:
                raise HTTPException(status_code=400, detail="Email already in use")

            user.email = profile_update.email
            user.email_verified = False  # Require re-verification

        session.commit()
        session.refresh(user)

        return UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            name=user.name,
            account_type=user.account_type,
            subscription_tier=user.subscription_tier,
            role=user.role,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_login=user.last_login.isoformat() if user.last_login else None,
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
    finally:
        session.close()


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_profile_by_id(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Get user profile by ID

    Returns public profile information for any user.
    Users can view their own full profile or public profiles of others.
    """
    try:
        session = db.get_session()
        user = session.query(User).filter(User.id == user_id).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.is_active:
            raise HTTPException(status_code=404, detail="User not found")

        # Return profile (same fields for now, can be restricted later)
        return UserProfileResponse(
            id=user.id,
            username=user.username,
            email=user.email if str(user.id) == str(current_user.id) else None,  # Hide email unless it's own profile
            name=user.name,
            account_type=user.account_type,
            subscription_tier=user.subscription_tier,
            role=user.role,
            email_verified=user.email_verified,
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            last_login=None,  # Hide last_login from other users
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user profile: {str(e)}")
    finally:
        session.close()


@router.get("/me/organizations")
def get_user_organizations(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Get organizations the current user belongs to"""
    try:
        organizations = db.get_user_organizations(current_user.id)
        return {
            "organizations": [
                {
                    "id": org.id,
                    "name": org.name,
                    "description": org.description,
                    "created_at": org.created_at.isoformat(),
                }
                for org in organizations
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user organizations: {str(e)}")


@router.get("/me/teams")
def get_user_teams(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Get teams the current user belongs to"""
    try:
        teams = db.get_user_teams(current_user.id)
        return {
            "teams": [
                {
                    "id": team.id,
                    "name": team.name,
                    "description": team.description,
                    "organization_id": team.organization_id,
                    "created_at": team.created_at.isoformat(),
                }
                for team in teams
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get user teams: {str(e)}")


@router.get("/me/contexts")
def get_user_accessible_contexts(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Get all contexts the user can access"""
    try:
        contexts = db.get_user_contexts(current_user.id)
        return {"contexts": contexts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
