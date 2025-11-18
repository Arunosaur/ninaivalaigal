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

from admin.helpers import get_admin_user_id_from_request, log_admin_action_async
from database import DatabaseManager, Team, TeamMembership, User
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from rbac_middleware import require_permission
from routers.admin_activity import get_activity_logger

from auth import get_current_user
from rbac.permissions import Action, Resource


# Pydantic Models
class TeamCreateRequest(BaseModel):
    """Request model for creating a team"""

    name: str = Field(..., min_length=1, max_length=255)
    organization_id: Optional[UUID] = None
    description: Optional[str] = None
    governance_type: Optional[str] = Field(default="internal", pattern="^(internal|external|shared)$")


class ExternalTeamCreateRequest(BaseModel):
    """Request model for creating an external/independent team (no organization)"""

    name: str = Field(..., min_length=1, max_length=255, description="Team name")
    description: Optional[str] = Field(None, description="Team description")
    purpose: Optional[str] = Field(None, description="Purpose (e.g., open-source, freelance, study group)")
    is_public: bool = Field(default=False, description="Whether team is public or invite-only")


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
    governance_type: str  # internal, external, shared
    origin: str  # native, partner, acquired
    status: str  # active, inactive, sunset
    member_count: int
    is_external: bool  # Helper field: True if governance_type == 'external'
    created_at: str
    updated_at: str

    class Config:
        """Pydantic config"""

        from_attributes = True


class TeamMembershipAddRequest(BaseModel):
    """Request model for adding a team member"""

    user_id: UUID
    role: str = Field(default="member", pattern="^(owner|admin|member|viewer)$")


class TeamMembershipUpdateRequest(BaseModel):
    """Request model for updating a team member's role"""

    role: str = Field(..., pattern="^(owner|admin|member|viewer)$")


class TeamMembershipResponse(BaseModel):
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
    from server.config import get_dynamic_database_url

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
        memberships = session.query(TeamMembership).filter(TeamMembership.user_id == current_user.id).all()

        teams = []
        for membership in memberships:
            team = session.query(Team).filter(Team.id == membership.team_id).first()
            if team:
                member_count = session.query(TeamMembership).filter(TeamMembership.team_id == team.id).count()

                teams.append(
                    TeamResponse(
                        id=team.id,
                        name=team.name,
                        organization_id=team.organization_id,
                        description=team.description,
                        governance_type=getattr(team, "governance_type", "internal"),
                        origin=getattr(team, "origin", "native"),
                        status=getattr(team, "status", "active"),
                        member_count=member_count,
                        is_external=getattr(team, "governance_type", "internal") == "external",
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
async def create_team(
    request: Request,
    team_data: TeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
):
    """
    Create a new team

    Automatically adds the creator as team owner.
    """
    try:
        session = db.get_session()

        # Determine governance type based on organization presence
        governance_type = team_data.governance_type
        if team_data.organization_id is None and governance_type == "internal":
            governance_type = "external"  # No org = external team

        # Create team
        team = Team(
            name=team_data.name,
            organization_id=team_data.organization_id,
            description=team_data.description,
            governance_type=governance_type,
            origin="native",
            status="active",
            lead_user_id=current_user.id,
        )
        session.add(team)
        session.flush()  # Get team ID

        # Add creator as owner
        membership = TeamMembership(
            team_id=team.id,
            user_id=current_user.id,
            role="owner",
        )
        session.add(membership)

        session.commit()
        session.refresh(team)

        # Log admin action (if user is system admin)
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.id) if hasattr(current_user, "id") else current_user.get("user_id", "")}
        )
        if admin_user_id and activity_logger:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="create_team",
                target_type="team",
                target_id=team.id,
                details={
                    "team_name": team_data.name,
                    "organization_id": str(team_data.organization_id) if team_data.organization_id else None,
                    "governance_type": governance_type,
                },
                request=request,
            )

        return TeamResponse(
            id=team.id,
            name=team.name,
            organization_id=team.organization_id,
            description=team.description,
            governance_type=team.governance_type,
            origin=team.origin,
            status=team.status,
            member_count=1,
            is_external=team.governance_type == "external",
            created_at=team.created_at.isoformat(),
            updated_at=team.updated_at.isoformat(),
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create team: {str(e)}")
    finally:
        session.close()


@router.post("/external", response_model=TeamResponse)
def create_external_team(
    team_data: ExternalTeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Create an external/independent team (no organization required)

    Perfect for:
    - Open source project teams
    - Freelancer collaborations
    - Study groups
    - Community projects
    - Any team that doesn't belong to an organization

    Individual users can create external teams to collaborate with others.
    """
    try:
        session = db.get_session()

        # Store purpose in provenance_metadata if provided
        metadata = {}
        if team_data.purpose:
            metadata["purpose"] = team_data.purpose
        if team_data.is_public:
            metadata["is_public"] = team_data.is_public

        # Create external team
        team = Team(
            name=team_data.name,
            organization_id=None,  # External teams have no organization
            description=team_data.description,
            governance_type="external",  # Explicitly external
            origin="native",
            status="active",
            lead_user_id=current_user.id,
            provenance_metadata=metadata if metadata else None,
        )
        session.add(team)
        session.flush()

        # Add creator as owner
        membership = TeamMembership(
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
            organization_id=None,
            description=team.description,
            governance_type="external",
            origin="native",
            status="active",
            member_count=1,
            is_external=True,
            created_at=team.created_at.isoformat(),
            updated_at=team.updated_at.isoformat(),
        )
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create external team: {str(e)}")
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
            session.query(TeamMembership)
            .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="Access denied: not a team member")

        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        member_count = session.query(TeamMembership).filter(TeamMembership.team_id == team_id).count()

        return TeamResponse(
            id=team.id,
            name=team.name,
            organization_id=team.organization_id,
            description=team.description,
            governance_type=getattr(team, "governance_type", "internal"),
            origin=getattr(team, "origin", "native"),
            status=getattr(team, "status", "active"),
            member_count=member_count,
            is_external=getattr(team, "governance_type", "internal") == "external",
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
async def update_team(
    request: Request,
    team_id: UUID,
    team_data: TeamUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
):
    """
    Update team details

    Only team owners and admins can update team information.
    """
    try:
        session = db.get_session()

        # Check if user is owner or admin
        membership = (
            session.query(TeamMembership)
            .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
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

        # Log admin action (if user is system admin)
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.id) if hasattr(current_user, "id") else current_user.get("user_id", "")}
        )
        if admin_user_id and activity_logger:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="update_team",
                target_type="team",
                target_id=team_id,
                details={
                    "name": team_data.name,
                    "description": team_data.description,
                },
                request=request,
            )

        member_count = session.query(TeamMembership).filter(TeamMembership.team_id == team_id).count()

        return TeamResponse(
            id=team.id,
            name=team.name,
            organization_id=team.organization_id,
            description=team.description,
            governance_type=getattr(team, "governance_type", "internal"),
            origin=getattr(team, "origin", "native"),
            status=getattr(team, "status", "active"),
            member_count=member_count,
            is_external=getattr(team, "governance_type", "internal") == "external",
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
async def delete_team(
    request: Request,
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
):
    """
    Delete a team

    Only team owners can delete teams.
    """
    try:
        session = db.get_session()

        # Check if user is owner
        membership = (
            session.query(TeamMembership)
            .filter(
                TeamMembership.team_id == team_id,
                TeamMembership.user_id == current_user.id,
                TeamMembership.role == "owner",
            )
            .first()
        )

        if not membership:
            raise HTTPException(status_code=403, detail="Only team owners can delete teams")

        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        team_name = team.name  # Save for logging before delete
        # Delete team (cascade will delete members)
        session.delete(team)
        session.commit()

        # Log admin action (if user is system admin)
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.id) if hasattr(current_user, "id") else current_user.get("user_id", "")}
        )
        if admin_user_id and activity_logger:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="delete_team",
                target_type="team",
                target_id=team_id,
                details={
                    "team_name": team_name,
                },
                request=request,
            )

        return {"success": True, "message": f"Team '{team_name}' deleted successfully"}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete team: {str(e)}")
    finally:
        session.close()


@router.get("/{team_id}/members", response_model=List[TeamMembershipResponse])
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
            session.query(TeamMembership)
            .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
            .first()
        )

        if not user_membership:
            raise HTTPException(status_code=403, detail="Access denied: not a team member")

        # Get all members
        memberships = session.query(TeamMembership).filter(TeamMembership.team_id == team_id).all()

        members = []
        for membership in memberships:
            user = session.query(User).filter(User.id == membership.user_id).first()
            if user:
                members.append(
                    TeamMembershipResponse(
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


@router.post("/{team_id}/members", response_model=TeamMembershipResponse)
@require_permission(Resource.TEAM, Action.ADMINISTER)
async def add_team_member(
    request: Request,
    team_id: UUID,
    member_data: TeamMembershipAddRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
):
    """
    Add a member to the team

    Only team owners and admins can add members.
    """
    try:
        session = db.get_session()

        # Check if current user is owner or admin
        current_membership = (
            session.query(TeamMembership)
            .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
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
            session.query(TeamMembership)
            .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == member_data.user_id)
            .first()
        )

        if existing:
            raise HTTPException(status_code=400, detail="User is already a team member")

        # Add member
        membership = TeamMembership(
            team_id=team_id,
            user_id=member_data.user_id,
            role=member_data.role,
        )
        session.add(membership)
        session.commit()
        session.refresh(membership)

        # Log admin action (if user is system admin)
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.id) if hasattr(current_user, "id") else current_user.get("user_id", "")}
        )
        if admin_user_id and activity_logger:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="add_team_member",
                target_type="team",
                target_id=team_id,
                details={
                    "member_user_id": str(member_data.user_id),
                    "role": member_data.role,
                },
                request=request,
            )

        return TeamMembershipResponse(
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


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMembershipResponse)
@require_permission(Resource.TEAM, Action.ADMINISTER)
async def update_team_member_role(
    request: Request,
    team_id: UUID,
    user_id: UUID,
    member_data: TeamMembershipUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
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
            session.query(TeamMembership)
            .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
            .first()
        )

        if not current_membership or current_membership.role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Get member to update
        membership = (
            session.query(TeamMembership)
            .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == user_id)
            .first()
        )

        if not membership:
            raise HTTPException(status_code=404, detail="Team member not found")

        # Prevent changing owner role
        if membership.role == "owner" and member_data.role != "owner":
            raise HTTPException(status_code=400, detail="Cannot change owner role")

        old_role = membership.role  # Save for logging
        # Update role
        membership.role = member_data.role
        session.commit()
        session.refresh(membership)

        user = session.query(User).filter(User.id == user_id).first()

        # Log admin action (if user is system admin)
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.id) if hasattr(current_user, "id") else current_user.get("user_id", "")}
        )
        if admin_user_id and activity_logger:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="change_team_role",
                target_type="team",
                target_id=team_id,
                details={
                    "member_user_id": str(user_id),
                    "old_role": old_role,
                    "new_role": member_data.role,
                },
                request=request,
            )

        return TeamMembershipResponse(
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
async def remove_team_member(
    request: Request,
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
    activity_logger=Depends(get_activity_logger),
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
            session.query(TeamMembership)
            .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == current_user.id)
            .first()
        )

        if not current_membership or current_membership.role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Admin access required")

        # Get member to remove
        membership = (
            session.query(TeamMembership)
            .filter(TeamMembership.team_id == team_id, TeamMembership.user_id == user_id)
            .first()
        )

        if not membership:
            raise HTTPException(status_code=404, detail="Team member not found")

        # Prevent removing owner
        if membership.role == "owner":
            raise HTTPException(status_code=400, detail="Cannot remove team owner")

        member_user_id = membership.user_id  # Save for logging
        # Remove member
        session.delete(membership)
        session.commit()

        # Log admin action (if user is system admin)
        admin_user_id = get_admin_user_id_from_request(
            {"user_id": str(current_user.id) if hasattr(current_user, "id") else current_user.get("user_id", "")}
        )
        if admin_user_id and activity_logger:
            await log_admin_action_async(
                activity_logger,
                admin_user_id=admin_user_id,
                action="remove_team_member",
                target_type="team",
                target_id=team_id,
                details={
                    "member_user_id": str(member_user_id),
                },
                request=request,
            )

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
