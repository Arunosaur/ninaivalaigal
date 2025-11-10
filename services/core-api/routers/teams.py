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

import secrets
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from auth_service import get_current_user
from database import DatabaseManager, Team, TeamInvitation, TeamMember, User
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from rbac_middleware import require_permission

from rbac.permissions import Action, Resource

# LangSmith tracing (US#139)
try:
    from langsmith import traceable
except ImportError:
    # No-op decorator if langsmith not available
    def traceable(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


# Pydantic models
class TeamCreateRequest(BaseModel):
    """Request model for creating a team"""

    name: str
    organization_id: Optional[UUID] = None
    description: Optional[str] = None


class TeamUpdateRequest(BaseModel):
    """Request model for updating a team"""

    name: Optional[str] = None
    description: Optional[str] = None


class TeamResponse(BaseModel):
    """Response model for team data"""

    id: str  # Use string for UUID serialization
    name: str
    organization_id: Optional[str] = None  # Use string for UUID
    description: Optional[str] = None
    member_count: int
    created_at: str
    updated_at: str


class TeamMemberAddRequest(BaseModel):
    """Request model for adding a team member"""

    user_id: UUID
    role: str = Field(default="member", pattern="^(owner|admin|member|viewer)$")


class TeamMemberUpdateRequest(BaseModel):
    """Request model for updating a team member's role"""

    role: str = Field(..., pattern="^(owner|admin|member|viewer)$")


class TeamMemberResponse(BaseModel):
    """Response model for team member data"""

    id: str  # Membership ID
    user_id: str  # Use string for UUID
    user_name: str
    user_email: str
    role: str
    joined_at: str


class TeamInvitationRequest(BaseModel):
    """Request model for inviting someone to a team by email"""

    email: EmailStr = Field(..., description="Email address of the person to invite")
    role: str = Field(default="member", pattern="^(owner|admin|member|viewer)$")


class TeamInvitationResponse(BaseModel):
    """Response model for team invitation data"""

    id: str
    team_id: str
    email: str
    role: str
    status: str
    expires_at: str
    created_at: str
    invited_by_user_id: str


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
                        id=str(team.id),
                        name=team.name,
                        organization_id=str(team.organization_id) if team.organization_id else None,
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
            id=str(team.id),
            name=team.name,
            organization_id=str(team.organization_id) if team.organization_id else None,
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
                        id=str(membership.id),
                        user_id=str(user.id),
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
def add_team_member(
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
            id=str(membership.id),
            user_id=str(user.id),
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
def update_team_member_role(
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
            id=str(membership.id),
            user_id=str(user.id),
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
def remove_team_member(
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


# ============================================================================
# TEAM INVITATION ENDPOINTS
# ============================================================================


@router.post("/{team_id}/invitations", response_model=TeamInvitationResponse)
@traceable(name="team_invitation")  # US#139: LangSmith tracing
def create_team_invitation(
    team_id: UUID,
    invitation_data: TeamInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Invite someone to a team by email

    - If user exists: Add them directly to the team
    - If not: Create invitation and send email
    """
    try:
        session = db.get_session()

        # Check if current user is owner or admin
        membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not membership or membership.role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Only team owners and admins can invite members")

        # Check if team exists
        team = session.query(Team).filter(Team.id == team_id).first()
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        email = str(invitation_data.email).lower()

        # Check if user already exists
        existing_user = session.query(User).filter(User.email == email).first()

        if existing_user:
            # User exists - check if already a member
            existing_member = (
                session.query(TeamMember)
                .filter(TeamMember.team_id == team_id, TeamMember.user_id == existing_user.id)
                .first()
            )

            if existing_member:
                raise HTTPException(status_code=400, detail="User is already a team member")

            # Add user directly to team
            new_member = TeamMember(
                team_id=team_id,
                user_id=existing_user.id,
                role=invitation_data.role,
            )
            session.add(new_member)
            session.commit()

            # Create a "accepted" invitation record for tracking
            invitation = TeamInvitation(
                team_id=team_id,
                invited_by_user_id=current_user.id,
                email=email,
                invitation_token=secrets.token_urlsafe(32),
                role=invitation_data.role,
                status="accepted",
                expires_at=datetime.utcnow() + timedelta(days=7),
                accepted_at=datetime.utcnow(),
                accepted_by_user_id=existing_user.id,
            )
            session.add(invitation)
            session.commit()
            session.refresh(invitation)

            return TeamInvitationResponse(
                id=str(invitation.id),
                team_id=str(invitation.team_id),
                email=invitation.email,
                role=invitation.role,
                status=invitation.status,
                expires_at=invitation.expires_at.isoformat(),
                created_at=invitation.created_at.isoformat(),
                invited_by_user_id=str(invitation.invited_by_user_id),
            )

        # User doesn't exist - create invitation
        # Check for existing pending invitation
        existing_invitation = (
            session.query(TeamInvitation)
            .filter(
                TeamInvitation.team_id == team_id, TeamInvitation.email == email, TeamInvitation.status == "pending"
            )
            .first()
        )

        if existing_invitation:
            raise HTTPException(status_code=400, detail="Invitation already sent to this email")

        # Create new invitation
        invitation = TeamInvitation(
            team_id=team_id,
            invited_by_user_id=current_user.id,
            email=email,
            invitation_token=secrets.token_urlsafe(32),
            role=invitation_data.role,
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),  # 7 day expiration
        )
        session.add(invitation)
        session.commit()
        session.refresh(invitation)

        # TODO: Send invitation email
        # send_invitation_email(
        #     to_email=email,
        #     team_name=team.name,
        #     inviter_name=current_user.name,
        #     invitation_token=invitation.invitation_token
        # )

        return TeamInvitationResponse(
            id=str(invitation.id),
            team_id=str(invitation.team_id),
            email=invitation.email,
            role=invitation.role,
            status=invitation.status,
            expires_at=invitation.expires_at.isoformat(),
            created_at=invitation.created_at.isoformat(),
            invited_by_user_id=str(invitation.invited_by_user_id),
        )
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create invitation: {str(e)}")
    finally:
        session.close()


@router.get("/{team_id}/invitations", response_model=List[TeamInvitationResponse])
def list_team_invitations(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    List all pending invitations for a team

    Only team owners and admins can view invitations.
    """
    try:
        session = db.get_session()

        # Check if current user is owner or admin
        membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not membership or membership.role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Only team owners and admins can view invitations")

        # Get all pending invitations
        invitations = (
            session.query(TeamInvitation)
            .filter(TeamInvitation.team_id == team_id, TeamInvitation.status == "pending")
            .all()
        )

        return [
            TeamInvitationResponse(
                id=str(inv.id),
                team_id=str(inv.team_id),
                email=inv.email,
                role=inv.role,
                status=inv.status,
                expires_at=inv.expires_at.isoformat(),
                created_at=inv.created_at.isoformat(),
                invited_by_user_id=str(inv.invited_by_user_id),
            )
            for inv in invitations
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list invitations: {str(e)}")
    finally:
        session.close()


@router.post("/invitations/{token}/accept")
def accept_team_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Accept a team invitation

    User must be logged in and the invitation must be for their email.
    """
    try:
        session = db.get_session()

        # Find invitation by token
        invitation = session.query(TeamInvitation).filter(TeamInvitation.invitation_token == token).first()

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Check if invitation is still valid
        if invitation.status != "pending":
            raise HTTPException(status_code=400, detail=f"Invitation is {invitation.status}")

        if invitation.expires_at < datetime.utcnow():
            invitation.status = "expired"
            session.commit()
            raise HTTPException(status_code=400, detail="Invitation has expired")

        # Check if user's email matches invitation
        if current_user.email.lower() != invitation.email.lower():
            raise HTTPException(status_code=403, detail="This invitation is for a different email address")

        # Check if user is already a member
        existing_member = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == invitation.team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if existing_member:
            # Update invitation status
            invitation.status = "accepted"
            invitation.accepted_at = datetime.utcnow()
            invitation.accepted_by_user_id = current_user.id
            session.commit()
            raise HTTPException(status_code=400, detail="You are already a member of this team")

        # Add user to team
        new_member = TeamMember(
            team_id=invitation.team_id,
            user_id=current_user.id,
            role=invitation.role,
        )
        session.add(new_member)

        # Update invitation status
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by_user_id = current_user.id

        session.commit()

        # Get team info for response
        team = session.query(Team).filter(Team.id == invitation.team_id).first()

        return {
            "success": True,
            "message": f"You have joined the team '{team.name}'",
            "team_id": str(team.id),
            "team_name": team.name,
            "role": invitation.role,
        }
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to accept invitation: {str(e)}")
    finally:
        session.close()


@router.delete("/{team_id}/invitations/{invitation_id}")
def cancel_team_invitation(
    team_id: UUID,
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: DatabaseManager = Depends(get_db),
):
    """
    Cancel a pending team invitation

    Only team owners and admins can cancel invitations.
    """
    try:
        session = db.get_session()

        # Check if current user is owner or admin
        membership = (
            session.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.user_id == current_user.id)
            .first()
        )

        if not membership or membership.role not in ["owner", "admin"]:
            raise HTTPException(status_code=403, detail="Only team owners and admins can cancel invitations")

        # Find invitation
        invitation = (
            session.query(TeamInvitation)
            .filter(TeamInvitation.id == invitation_id, TeamInvitation.team_id == team_id)
            .first()
        )

        if not invitation:
            raise HTTPException(status_code=404, detail="Invitation not found")

        # Update status instead of deleting (for audit trail)
        invitation.status = "cancelled"
        invitation.updated_at = datetime.utcnow()
        session.commit()

        return {"success": True, "message": "Invitation cancelled"}
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to cancel invitation: {str(e)}")
    finally:
        session.close()
