#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Team Management Router
Extracted from main.py for better code organization
"""

from typing import List, Optional
from uuid import UUID

from auth import get_current_user
from database import DatabaseManager, Team, TeamMember, User
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from rbac_middleware import require_permission

from rbac.permissions import Action, Resource


# Pydantic Models
class TeamCreateRequest(BaseModel):
    """Request model for creating a team"""

    name: str = Field(..., min_length=1, max_length=255)
    organization_id: Optional[UUID] = None
    description: Optional[str] = None


class TeamUpdateRequest(BaseModel):
    """Request model for updating a team"""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class TeamResponse(BaseModel):
    """Response model for team data"""

    id: UUID
    name: str
    organization_id: Optional[UUID]
    description: Optional[str]
    member_count: int
    created_at: str
    updated_at: str

    class Config:
        """Pydantic config"""
        from_attributes = True


class TeamMemberAddRequest(BaseModel):
    """Request model for adding a team member"""

    user_id: UUID
    role: str = Field(default="member", pattern="^(owner|admin|member|viewer)$")


class TeamMemberUpdateRequest(BaseModel):
    """Request model for updating a team member's role"""

    role: str = Field(..., pattern="^(owner|admin|member|viewer)$")


class TeamMemberResponse(BaseModel):
    """Response model for team member data"""

    id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    role: str
    joined_at: str

    class Config:
        """Pydantic config"""
        from_attributes = True


# Initialize router
router = APIRouter(prefix="/teams", tags=["teams"])


# Database manager dependency
def get_db():
    """Get database manager with dynamic configuration"""
    from config import get_dynamic_database_url

    return DatabaseManager(get_dynamic_database_url())


@router.get("", response_model=List[TeamResponse])
def list_teams(
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    List all teams accessible to the current user

    Returns teams where the user is a member.
    """
    try:
        session = db.get_session()

        # Get teams where user is a member
        memberships = session.query(TeamMember).filter(TeamMember.user_id == current_user.id).all()

        teams = []
        for membership in memberships:
            team = session.query(Team).filter(Team.id == membership.team_id).first()
            if team:
                member_count = session.query(TeamMember).filter(TeamMember.team_id == team.id).count()

                teams.append(
                    TeamResponse(
                        id=team.id,
                        name=team.name,
                        organization_id=team.organization_id,
                        description=team.description,
                        member_count=member_count,
                        created_at=team.created_at.isoformat(),
                        updated_at=team.updated_at.isoformat(),
                    )
                )

        return teams
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list teams: {str(e)}")
    finally:
        session.close()


@router.post("", response_model=TeamResponse)
@require_permission(Resource.TEAM, Action.CREATE)
def create_team(
    request: Request,
    team_data: TeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Create a new team

    Automatically adds the creator as team owner.
    """
    try:
        session = db.get_session()

        # Create team
        team = Team(
            name=team_data.name,
            organization_id=team_data.organization_id,
            description=team_data.description,
        )
        session.add(team)
        session.flush()  # Get team ID

        # Add creator as owner
        membership = TeamMember(
            team_id=team.id,
            user_id=current_user.id,
            role="owner",
        )
        session.add(membership)

        session.commit()
        session.refresh(team)

        return TeamResponse(
            id=team.id,
            name=team.name,
            organization_id=team.organization_id,
            description=team.description,
            member_count=1,
            created_at=team.created_at.isoformat(),
            updated_at=team.updated_at.isoformat(),
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")
    finally:
        session.close()


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Get team details by ID

    User must be a member of the team to view details.
    """
    try:
        session = db.get_session()

        # Check if user is a member
        membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="Access denied: not a team member")

        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        member_count = session.query(TeamMember).filter(TeamMember.team_id == team_id).count()

        return TeamResponse(
            id=team.id,
            name=team.name,
            organization_id=team.organization_id,
            description=team.description,
            member_count=member_count,
            created_at=team.created_at.isoformat(),
            updated_at=team.updated_at.isoformat(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team: {str(e)}")
    finally:
        session.close()


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: UUID,
    team_data: TeamUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Update team details

    Only team owners and admins can update team information.
    """
    try:
        session = db.get_session()

        # Check if user is owner or admin
        membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not membership or membership.role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Update fields
        if team_data.name is not None:
            team.name = team_data.name
        if team_data.description is not None:
            team.description = team_data.description

        session.commit()
        session.refresh(team)

        member_count = session.query(TeamMember).filter(TeamMember.team_id == team_id).count()

        return TeamResponse(
            id=team.id,
            name=team.name,
            organization_id=team.organization_id,
            description=team.description,
            member_count=member_count,
            created_at=team.created_at.isoformat(),
            updated_at=team.updated_at.isoformat(),
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update team: {str(e)}")
    finally:
        session.close()


@router.delete("/{team_id}")
def delete_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Delete a team

    Only team owners can delete teams.
    """
    try:
        session = db.get_session()

        # Check if user is owner
        membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id, TeamMember.role == "owner")
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="Only team owners can delete teams")

        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        # Delete team (cascade will delete members)
        session.delete(team)
        session.commit()

        return {"success": True, "message": f"Team '{team.name}' deleted successfully"}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}")
    finally:
        session.close()


@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
def get_team_members(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    List all team members

    User must be a team member to view the member list.
    """
    try:
        session = db.get_session()

        # Check if user is a member
        user_membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not user_membership:
            raise HTTPException(status_code=403, detail="Access denied: not a team member")

        # Get all members
        memberships = session.query(TeamMember).filter(TeamMember.team_id == team_id).all()

        members = []
        for membership in memberships:
            user = session.query(User).filter(User.id == membership.user_id).first()
            if user:
                members.append(
                    TeamMemberResponse(
                        id=membership.id,
                        user_id=user.id,
                        user_name=user.name,
                        user_email=user.email,
                        role=membership.role,
                        joined_at=membership.joined_at.isoformat(),
                    )
                )

        return members
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get team members: {str(e)}")
    finally:
        session.close()


@router.post("/{team_id}/members", response_model=TeamMemberResponse)
@require_permission(Resource.TEAM, Action.ADMINISTER)
def add_team_member(
    request: Request,
    team_id: UUID,
    member_data: TeamMemberAddRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Add a member to the team

    Only team owners and admins can add members.
    """
    try:
        session = db.get_session()

        # Check if current user is owner or admin
        current_membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not current_membership or current_membership.role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Check if user exists
        user = session.query(User).filter(User.id == member_data.user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if already a member
        existing = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == member_data.user_id)
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail="User is already a team member")

        # Add member
        membership = TeamMember(
            team_id=team_id,
            user_id=member_data.user_id,
            role=member_data.role,
        )
        session.add(membership)
        session.commit()
        session.refresh(membership)

        return TeamMemberResponse(
            id=membership.id,
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            role=membership.role,
            joined_at=membership.joined_at.isoformat(),
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add team member: {str(e)}")
    finally:
        session.close()


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
@require_permission(Resource.TEAM, Action.ADMINISTER)
def update_team_member_role(
    request: Request,
    team_id: UUID,
    user_id: UUID,
    member_data: TeamMemberUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Update a team member's role

    Only team owners and admins can update member roles.
    Owners cannot be demoted.
    """
    try:
        session = db.get_session()

        # Check if current user is owner or admin
        current_membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not current_membership or current_membership.role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Get member to update
        membership = (
            session.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
        )

        if not membership:
            raise HTTPException(status_code=404, detail="Team member not found")

        # Prevent changing owner role
        if membership.role == "owner" and member_data.role != "owner":
            raise HTTPException(status_code=400, detail="Cannot change owner role")

        # Update role
        membership.role = member_data.role
        session.commit()
        session.refresh(membership)

        user = session.query(User).filter(User.id == user_id).first()

        return TeamMemberResponse(
            id=membership.id,
            user_id=user.id,
            user_name=user.name,
            user_email=user.email,
            role=membership.role,
            joined_at=membership.joined_at.isoformat(),
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to update team member: {str(e)}")
    finally:
        session.close()


@router.delete("/{team_id}/members/{user_id}")
@require_permission(Resource.TEAM, Action.ADMINISTER)
def remove_team_member(
    request: Request,
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Remove a member from the team

    Only team owners and admins can remove members.
    Owners cannot be removed.
    """
    try:
        session = db.get_session()

        # Check if current user is owner or admin
        current_membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not current_membership or current_membership.role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Get member to remove
        membership = (
            session.query(TeamMember).filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id).first()
        )

        if not membership:
            raise HTTPException(status_code=404, detail="Team member not found")

        # Prevent removing owner
        if membership.role == "owner":
            raise HTTPException(status_code=400, detail="Cannot remove team owner")

        # Remove member
        session.delete(membership)
        session.commit()

        return {
            "success": True,
            "message": "User removed from team successfully",
        }
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to remove team member: {str(e)}")
    finally:
        session.close()
