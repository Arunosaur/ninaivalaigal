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

import json
from datetime import datetime
from typing import Literal
from uuid import UUID

from auth_service import (
    PASSWORD_REQUIREMENTS_MESSAGE,
    get_current_user,
    hash_password,
    validate_password,
    verify_password,
)
from database import DatabaseManager, Memory, RefreshToken, TeamMember, User
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func

# Import models from shared contracts (US#79 - Shared Contracts Layer)
from auth.v1.models import UserProfileResponse, UserProfileUpdate


# User profile helper models (not in contracts - service-specific)
class RoleAssignmentResponse(BaseModel):
    """Role assignment response model"""

    role: str
    scope_type: str
    scope_id: str | None = None
    granted_at: str
    is_active: bool


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


# NOTE: UserProfileResponse and UserProfileUpdate are imported from shared contracts (US#79)
# This eliminates duplicate definitions and ensures consistency across services.


# Initialize router
router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Get current user's profile

    Returns complete profile information for the authenticated user, including RBAC role assignments.
    """
    session = db.get_session()
    try:
        # Get user with role_assignments loaded
        user = session.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Build role_assignments response
        role_assignments = []
        if hasattr(user, "role_assignments") and user.role_assignments:
            for assignment in user.role_assignments:
                if assignment.is_active:
                    role_assignments.append(
                        RoleAssignmentResponse(
                            role=str(assignment.role),
                            scope_type=assignment.scope_type,
                            scope_id=assignment.scope_id,
                            granted_at=(
                                assignment.granted_at.isoformat()
                                if assignment.granted_at
                                else datetime.utcnow().isoformat()
                            ),
                            is_active=assignment.is_active,
                        )
                    )

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
            role_assignments=role_assignments,
        )
    finally:
        session.close()


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


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)
    confirm_password: str = Field(..., min_length=8)


class UserPreferences(BaseModel):
    email_notifications: bool = Field(default=True)
    theme: Literal["light", "dark", "auto"] = Field(default="auto")


class UserPreferencesResponse(UserPreferences):
    updated_at: str | None = Field(default=None)


class UserStatsResponse(BaseModel):
    total_memories: int = Field(default=0)
    active_sessions: int = Field(default=0)
    team_members: int = Field(default=1)
    storage_used_mb: float = Field(default=0.0)
    api_calls_today: int = Field(default=0)
    subscription_tier: str = Field(default="free")


@router.post("/me/password")
def change_password(
    payload: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Allow authenticated users to change their password."""

    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")

    if not validate_password(payload.new_password):
        raise HTTPException(status_code=422, detail=PASSWORD_REQUIREMENTS_MESSAGE)

    session = db.get_session()
    try:
        user = session.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not verify_password(payload.current_password, user.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        user.password_hash = hash_password(payload.new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        user.updated_at = datetime.utcnow()

        session.commit()
        return {"success": True, "message": "Password updated successfully"}
    except HTTPException:
        session.rollback()
        raise
    except Exception as exc:  # pragma: no cover - safeguard
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update password: {str(exc)}")
    finally:
        session.close()


def _load_preferences(user: User) -> tuple[UserPreferences, str | None]:
    # Return default preferences since employment_metadata column was removed
    # TODO: Add a dedicated user_preferences table if needed
    preferences = UserPreferences()
    return preferences, None


@router.get("/me/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Retrieve the authenticated user's saved preferences."""

    session = db.get_session()
    try:
        user = session.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        preferences, updated_at = _load_preferences(user)
        return UserPreferencesResponse(**preferences.model_dump(), updated_at=updated_at)
    finally:
        session.close()


@router.put("/me/preferences", response_model=UserPreferencesResponse)
def update_user_preferences(
    payload: UserPreferences,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Update the authenticated user's preferences.

    Note: Preferences are currently stored in memory only.
    TODO: Add dedicated user_preferences table for persistence.
    """
    # Return updated preferences without persisting (employment_metadata removed)
    timestamp = datetime.utcnow().isoformat()
    return UserPreferencesResponse(**payload.model_dump(), updated_at=timestamp)


@router.get("/me/stats", response_model=UserStatsResponse)
def get_user_stats(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """Return dashboard statistics for the authenticated user."""

    session = db.get_session()
    try:
        user = session.query(User).filter(User.id == current_user.id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        total_memories = session.query(func.count(Memory.id)).filter(Memory.user_id == user.id).scalar() or 0

        start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        api_calls_today = (
            session.query(func.count(Memory.id))
            .filter(Memory.user_id == user.id, Memory.created_at >= start_of_day)
            .scalar()
            or 0
        )

        active_sessions = (
            session.query(func.count(RefreshToken.id))
            .filter(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.utcnow(),
            )
            .scalar()
            or 0
        )

        team_ids = [row[0] for row in session.query(TeamMember.team_id).filter(TeamMember.user_id == user.id).all()]

        team_members = 1
        if team_ids:
            team_members = (
                session.query(func.count(func.distinct(TeamMember.user_id)))
                .filter(TeamMember.team_id.in_(team_ids))
                .scalar()
                or 1
            )

        # Calculate storage (gracefully handle if data column doesn't exist yet)
        storage_used_mb = 0.0
        try:
            memory_payloads = session.query(Memory.data).filter(Memory.user_id == user.id).all()

            storage_bytes = 0
            for (payload,) in memory_payloads:
                try:
                    storage_bytes += len(json.dumps(payload).encode("utf-8"))
                except Exception:
                    continue

            storage_used_mb = round(storage_bytes / (1024 * 1024), 2)
        except Exception:
            # If data column doesn't exist yet, fall back to count-based estimate
            storage_used_mb = round(total_memories * 0.001, 2)  # ~1KB per memory estimate

        return UserStatsResponse(
            total_memories=total_memories,
            active_sessions=active_sessions,
            team_members=team_members,
            storage_used_mb=storage_used_mb,
            api_calls_today=api_calls_today,
            subscription_tier=user.subscription_tier or "free",
        )
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
