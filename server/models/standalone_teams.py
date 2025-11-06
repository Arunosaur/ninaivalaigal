#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-066: Standalone Team Accounts - Manager Classes Only
All database models have been consolidated into database.py to avoid duplication.

CONSOLIDATED MODELS (now in database.py):
- Team: Enhanced with standalone team fields (is_standalone, upgrade_eligible, etc.)
- User: Enhanced with standalone_team_id field
- UserInvitation: Enhanced to support both org and team invitations with accepted_by tracking
- TeamMembership: Single source of truth for team memberships with invitation tracking

REMOVED DUPLICATE MODELS:
- TeamInvitation (was duplicate of UserInvitation)
- TeamMember (was less feature-complete than TeamMembership)
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from database import Base, Organization, Team, TeamMembership, User, UserInvitation
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import foreign, relationship
from sqlalchemy.sql import func


class TeamUpgradeHistory(Base):
    """Track team upgrades to organizations"""

    __tablename__ = "team_upgrade_history"
    __table_args__ = {"extend_existing": True}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    team_id = Column(PGUUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    organization_id = Column(PGUUID(as_uuid=True), ForeignKey("organizations.id"))
    upgraded_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upgrade_type = Column(String(50), nullable=False)  # to_organization, billing_enabled
    upgrade_data = Column(JSONB)  # Store upgrade-specific data
    upgraded_at = Column(DateTime, default=func.now())
    status = Column(String(50), default="completed")  # pending, completed, failed, reverted

    # Relationships
    team = relationship("Team")
    organization = relationship("Organization")
    upgraded_by = relationship("User")


class StandaloneTeamManager:
    """Manager class for standalone team operations"""

    def __init__(self, db_session):
        """Initialize instance."""
        self.session = db_session

    def create_standalone_team(self, name: str, created_by_user_id: UUID, max_members: int = 10) -> "Team":
        """Create a new standalone team"""
        team = Team(
            name=name,
            is_standalone=True,
            created_by_user_id=created_by_user_id,
            max_members=max_members,
            upgrade_eligible=True,
        )

        self.session.add(team)
        self.session.flush()  # Get the team ID

        # Add creator as admin member
        membership = TeamMembership(
            team_id=team.id,
            user_id=created_by_user_id,
            role="admin",
            status="active",
            invited_by_user_id=created_by_user_id,  # Self-invited as creator
        )
        self.session.add(membership)

        return team

    def invite_user_to_team(
        self,
        team_id: UUID,
        email: str,
        invited_by_user_id: UUID,
        role: str = "contributor",
        message: str = None,
    ) -> UserInvitation:
        """Create team invitation using consolidated UserInvitation model"""
        invitation = UserInvitation(
            email=email,
            team_id=team_id,
            invited_by=invited_by_user_id,
            role=role,
            status="pending",
            expires_at=datetime.utcnow() + timedelta(days=7),
            invitation_message=message,
        )

        self.session.add(invitation)
        return invitation

    def accept_invitation(self, invitation_token: str, user_id: UUID) -> Optional[TeamMembership]:
        """Accept team invitation and create membership"""
        invitation = self.session.query(UserInvitation).filter_by(invitation_token=invitation_token).first()

        if not invitation or not self._is_invitation_valid(invitation):
            return None

        # Check if team has space
        if not self.can_user_join_team(invitation.team_id):
            return None

        # Create membership
        membership = TeamMembership(
            team_id=invitation.team_id,
            user_id=user_id,
            role=invitation.role,
            invited_by_user_id=invitation.invited_by,
            status="active",
        )
        self.session.add(membership)

        # Update invitation status
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by = user_id

        return membership

    def _is_invitation_valid(self, invitation: UserInvitation) -> bool:
        """Check if invitation is valid for acceptance"""
        return invitation.status == "pending" and datetime.utcnow() < invitation.expires_at

    def can_user_join_team(self, team_id: UUID) -> bool:
        """Check if team has space for new member"""
        team = self.session.query(Team).filter_by(id=team_id).first()
        if not team:
            return False

        current_members = self.session.query(TeamMembership).filter_by(team_id=team_id, status="active").count()

        return current_members < team.max_members

    def get_team_members(self, team_id: UUID) -> List[TeamMembership]:
        """Get all active team members"""
        return self.session.query(TeamMembership).filter_by(team_id=team_id, status="active").all()

    def upgrade_team_to_organization(
        self, team_id: UUID, upgraded_by_user_id: UUID, org_data: dict
    ) -> Optional["Organization"]:
        """Upgrade standalone team to organization"""
        team = self.session.query(Team).filter_by(id=team_id, is_standalone=True, upgrade_eligible=True).first()
        if not team:
            return None

        # Create organization
        organization = Organization(
            name=org_data.get("name", team.name),
            domain=org_data.get("domain"),
            size=org_data.get("size", "startup"),
            industry=org_data.get("industry"),
        )
        self.session.add(organization)
        self.session.flush()

        # Update team to be part of organization
        team.is_standalone = False
        team.organization_id = organization.id

        # Record upgrade history
        upgrade_history = TeamUpgradeHistory(
            team_id=team_id,
            organization_id=organization.id,
            upgraded_by_user_id=upgraded_by_user_id,
            upgrade_type="to_organization",
            upgrade_data=org_data,
            status="completed",
        )
        self.session.add(upgrade_history)

        return organization

    def get_pending_invitations(self, team_id: UUID) -> List[UserInvitation]:
        """Get all pending invitations for a team"""
        return self.session.query(UserInvitation).filter_by(team_id=team_id, status="pending").all()

    def revoke_invitation(self, invitation_id: UUID) -> bool:
        """Revoke a pending invitation"""
        invitation = self.session.query(UserInvitation).filter_by(id=invitation_id, status="pending").first()

        if not invitation:
            return False

        invitation.status = "cancelled"
        return True
