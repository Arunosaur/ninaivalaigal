#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Team Management API - Version 1

V1 team endpoints for creating, managing, and collaborating in teams.

Related: SPEC-088 API Versioning Strategy
"""

from typing import List, Optional
from uuid import UUID

from database import DatabaseManager, Team, TeamMember, User
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from rbac_middleware import require_permission

from auth import get_current_user

# Create v1 router
from lib.routing.version_router import create_v1_router
from rbac.permissions import Action, Resource

router = create_v1_router(prefix="/teams", tags=["v1", "teams"])


# Pydantic Models
class TeamCreateRequest(BaseModel):
    """Request model for creating a team"""

    name: str = Field(..., min_length=1, max_length=255)
    organization_id: Optional[UUID] = None
    description: Optional[str] = None
    governance_type: Optional[str] = Field(default="internal", pattern="^(internal|external|shared)$")


class TeamUpdateRequest(BaseModel):
    """Request model for updating a team"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class TeamMemberAddRequest(BaseModel):
    """Request model for adding a team member"""

    user_id: UUID
    role: str = Field(default="member", pattern="^(owner|admin|member)$")


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from server.config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


@router.post("")
@require_permission(Resource.TEAM, Action.CREATE)
async def create_team(
    request: Request,
    team_data: TeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Create a new team.

    **V1 Behavior**:
    - Creator becomes team owner
    - Optional organization association
    - Returns team_id as string

    **V2 Changes**:
    - Enhanced team templates
    - Automatic workspace creation
    - Team onboarding workflow
    """
    try:
        # Create team
        team = Team(
            name=team_data.name,
            organization_id=team_data.organization_id,
            description=team_data.description,
            governance_type=team_data.governance_type or "internal",
            status="active",
        )
        db.session.add(team)
        db.session.flush()

        # Add creator as owner
        member = TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role="owner",
        )
        db.session.add(member)
        db.session.commit()

        return {
            "success": True,
            "message": "Team created successfully",
            "team": {
                "team_id": str(team.id),
                "name": team.name,
                "organization_id": str(team.organization_id) if team.organization_id else None,
                "description": team.description,
                "governance_type": team.governance_type,
                "status": team.status,
                "created_at": team.created_at.isoformat() if team.created_at else None,
            },
        }

    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")


@router.get("")
async def list_teams(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    List teams for current user.

    **V1 Behavior**:
    - Returns teams where user is a member
    - Simple skip/limit pagination

    **V2 Changes**:
    - Cursor-based pagination
    - Filter by role, status
    - Include team statistics
    """
    try:
        # Get teams where user is a member
        teams = (
            db.session.query(Team)
            .join(TeamMember)
            .filter(TeamMember.user_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .all()
        )

        total = db.session.query(Team).join(TeamMember).filter(TeamMember.user_id == current_user.id).count()

        return {
            "success": True,
            "teams": [
                {
                    "team_id": str(team.id),
                    "name": team.name,
                    "description": team.description,
                    "governance_type": team.governance_type,
                    "status": team.status,
                }
                for team in teams
            ],
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total,
            },
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {str(e)}")


@router.get("/{team_id}")
async def get_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Get team details.

    **V1 Behavior**:
    - Returns full team information
    - Includes member count
    """
    try:
        # Check if user is a member
        membership = (
            db.session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="Not a team member")

        team = db.session.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Get member count
        member_count = db.session.query(TeamMember).filter(TeamMember.team_id == team_id).count()

        return {
            "success": True,
            "team": {
                "team_id": str(team.id),
                "name": team.name,
                "organization_id": str(team.organization_id) if team.organization_id else None,
                "description": team.description,
                "governance_type": team.governance_type,
                "status": team.status,
                "member_count": member_count,
                "your_role": membership.role,
                "created_at": team.created_at.isoformat() if team.created_at else None,
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team: {str(e)}")


@router.put("/{team_id}")
@require_permission(Resource.TEAM, Action.UPDATE)
async def update_team(
    request: Request,
    team_id: UUID,
    team_update: TeamUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Update team information.

    **V1 Behavior**:
    - Requires admin or owner role
    - Partial updates supported
    """
    try:
        # Check if user is admin/owner
        membership = (
            db.session.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id,
                TeamMember.role.in_(["owner", "admin"]),
            )
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="Admin or owner role required")

        team = db.session.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Update fields
        if team_update.name is not None:
            team.name = team_update.name
        if team_update.description is not None:
            team.description = team_update.description

        db.session.commit()

        return {
            "success": True,
            "message": "Team updated successfully",
            "team": {
                "team_id": str(team.id),
                "name": team.name,
                "description": team.description,
            },
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")


@router.delete("/{team_id}")
@require_permission(Resource.TEAM, Action.DELETE)
async def delete_team(
    request: Request,
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Delete a team.

    **V1 Behavior**:
    - Requires owner role
    - Hard delete (immediate)

    **V2 Changes**:
    - Soft delete with recovery period
    - Data export before deletion
    """
    try:
        # Check if user is owner
        membership = (
            db.session.query(TeamMember)
            .filter(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id,
                TeamMember.role == "owner",
            )
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="Owner role required")

        team = db.session.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        db.session.delete(team)
        db.session.commit()

        return {
            "success": True,
            "message": "Team deleted successfully",
            "team_id": str(team_id),
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        db.session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}")


@router.get("/{team_id}/members")
async def list_team_members(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    List team members.

    **V1 Behavior**:
    - Returns all members with roles
    - Requires team membership
    """
    try:
        # Check if user is a member
        membership = (
            db.session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="Not a team member")

        # Get all members
        members = (
            db.session.query(TeamMember, User)
            .join(User, TeamMember.user_id == User.id)
            .filter(TeamMember.team_id == team_id)
            .all()
        )

        return {
            "success": True,
            "members": [
                {
                    "user_id": str(user.id),
                    "username": user.username,
                    "name": user.name or "",
                    "role": member.role,
                    "joined_at": (
                        member.created_at.isoformat() if hasattr(member, "created_at") and member.created_at else None
                    ),
                }
                for member, user in members
            ],
            "count": len(members),
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list members: {str(e)}")
