#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-066: Standalone Team Accounts - Database Models
Supports team creation without organization requirement
"""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID, uuid4

from database import Base
from database.models import Organization, Team, User
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
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class TeamInvitation(Base):
    """Team invitation for secure team joining"""

    __tablename__ = "team_invitations"
    __table_args__ = {"extend_existing": True}

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    team_id = Column(PGUUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    invited_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    invitation_token = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), default="contributor")
    status = Column(String(50), default="pending")  # pending, accepted, expired, revoked
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=7))
    accepted_at = Column(DateTime)
    accepted_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships - use backref instead of back_populates to avoid circular dependency
    # The Team.invitations relationship will be set up by extend_team_model()
    # Note: team relationship is created via backref in extend_team_model(), don't define here to avoid conflict
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_user_id])

    def is_expired(self) -> bool:
        """Check if invitation has expired"""
        return datetime.utcnow() > self.expires_at

    def is_valid(self) -> bool:
        """Check if invitation is valid for acceptance"""
        return self.status == "pending" and not self.is_expired()


class TeamMembership(Base):
    """Team membership tracking with roles"""

    __tablename__ = "team_memberships"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="unique_team_membership"), {"extend_existing": True})
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    team_id = Column(PGUUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False, default="contributor")  # admin, contributor, viewer
    joined_at = Column(DateTime, default=func.now())
    invited_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="active")  # active, inactive, removed
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Unique constraint to prevent duplicate memberships
    # Relationships - use backref instead of back_populates to avoid circular dependency
    # Note: team relationship is created via backref in extend_team_model(), don't define here to avoid conflict
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])

    def is_admin(self) -> bool:
        """Check if member has admin role"""
        return self.role == "admin" and self.status == "active"

    def can_invite_members(self) -> bool:
        """Check if member can invite others"""
        return self.role in ["admin", "contributor"] and self.status == "active"


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


# Extend existing Team model with standalone team fields
def extend_team_model():
    """Add standalone team fields to existing Team model"""
    # Check if already extended to avoid duplicate attribute errors
    if hasattr(Team, "_standalone_extended"):
        return

    # These would be added to the existing Team class in database.py
    if not hasattr(Team, "is_standalone"):
        Team.is_standalone = Column(Boolean, default=False)
    if not hasattr(Team, "upgrade_eligible"):
        Team.upgrade_eligible = Column(Boolean, default=True)
    if not hasattr(Team, "created_by_user_id"):
        Team.created_by_user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"))
    if not hasattr(Team, "team_invite_code"):
        Team.team_invite_code = Column(String(32), unique=True)
    if not hasattr(Team, "max_members"):
        Team.max_members = Column(Integer, default=10)

    # Relationships - use backref to avoid needing TeamInvitation to be fully configured
    if not hasattr(Team, "invitations"):
        Team.invitations = relationship("TeamInvitation", backref="team", cascade="all, delete-orphan")
    if not hasattr(Team, "memberships"):
        Team.memberships = relationship("TeamMembership", backref="team", cascade="all, delete-orphan")
    if not hasattr(Team, "created_by"):
        Team.created_by = relationship("User", foreign_keys=[Team.created_by_user_id])

    Team._standalone_extended = True


# Extend existing User model with standalone team reference
def extend_user_model():
    """Add standalone team reference to existing User model"""
    # This would be added to the existing User class in database.py
    User.standalone_team_id = Column(PGUUID(as_uuid=True), ForeignKey("teams.id"))

    # Relationships
    User.standalone_team = relationship("Team", foreign_keys=[User.standalone_team_id])


class StandaloneTeamManager:
    """Manager class for standalone team operations"""

    def __init__(self, db_session):
        """Initialize instance."""
        self.session = db_session

    def create_standalone_team(self, name: str, created_by_user_id: UUID, max_members: int = 10) -> "Team":
        """Create a new standalone team"""
        from database import Team  # Import here to avoid circular imports

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
        membership = TeamMembership(team_id=team.id, user_id=created_by_user_id, role="admin", status="active")
        self.session.add(membership)

        return team

    def invite_user_to_team(
        self,
        team_id: UUID,
        email: str,
        invited_by_user_id: UUID,
        role: str = "contributor",
    ) -> TeamInvitation:
        """Create team invitation"""
        invitation = TeamInvitation(
            team_id=team_id,
            invited_by_user_id=invited_by_user_id,
            email=email,
            role=role,
            status="pending",
        )

        self.session.add(invitation)
        return invitation

    def accept_invitation(self, invitation_token: str, user_id: UUID) -> Optional[TeamMembership]:
        """Accept team invitation and create membership"""
        invitation = self.session.query(TeamInvitation).filter_by(invitation_token=invitation_token).first()

        if not invitation or not invitation.is_valid():
            return None

        # Check if team has space
        if not self.can_user_join_team(invitation.team_id):
            return None

        # Create membership
        membership = TeamMembership(
            team_id=invitation.team_id,
            user_id=user_id,
            role=invitation.role,
            invited_by_user_id=invitation.invited_by_user_id,
            status="active",
        )
        self.session.add(membership)

        # Update invitation status
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by_user_id = user_id

        return membership

    def can_user_join_team(self, team_id: UUID) -> bool:
        """Check if team has space for new member"""
        from database import Team  # Import here to avoid circular imports

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
        from database import Organization, Team  # Import here to avoid circular imports

        team = self.session.query(Team).filter_by(id=team_id, is_standalone=True).first()
        if not team or not team.upgrade_eligible:
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
