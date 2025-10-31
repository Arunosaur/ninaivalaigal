#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Database Models for ninaivalaigal
Extracted from monolithic database.py for better organization

This addresses external code review feedback:
- Break down monolithic files (database.py 1285 lines → focused modules)
- Improve code organization and maintainability
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model with authentication and RBAC support

    Note: This model matches public.users schema after database consolidation.
    Extended employment provenance fields are in ag_catalog.users materialized view
    and should be accessed via graph queries, not this ORM model.

    Schema Resolution: Uses search_path (public, ag_catalog, pg_catalog) set by migration 0123.
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(255), unique=True, nullable=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    account_type = Column(String(50), nullable=False, default="individual")
    subscription_tier = Column(String(50), nullable=False, default="free")
    personal_contexts_limit = Column(Integer, default=10)
    role = Column(String(50), nullable=False, default="user")
    created_via = Column(String(50), nullable=False, default="signup")
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # RBAC fields
    default_role = Column(String(50), default="MEMBER")
    is_system_admin = Column(Boolean, default=False)

    # Note: Employment provenance fields removed - use ag_catalog.users MV or graph queries
    # The canonical transactional user table (public.users) is intentionally simpler

    # Relationships for sharing system
    owned_contexts = relationship("Context", foreign_keys="[Context.owner_id]", back_populates="owner")
    team_memberships = relationship("TeamMember", back_populates="user")
    granted_permissions = relationship(
        "ContextPermission",
        foreign_keys="[ContextPermission.granted_by]",
        back_populates="granted_by_user",
    )
    user_permissions = relationship("ContextPermission", foreign_keys="[ContextPermission.user_id]")
    refresh_tokens = relationship(
        "RefreshToken", foreign_keys="[RefreshToken.user_id]", back_populates="user", cascade="all, delete-orphan"
    )
    revoked_refresh_tokens = relationship(
        "RefreshToken", foreign_keys="[RefreshToken.revoked_by]", back_populates="revoker"
    )

    # RBAC relationships (defined in rbac_models.py)
    # These are added dynamically by rbac_models.py to avoid circular imports


class RefreshToken(Base):
    """Refresh token model for JWT token refresh"""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    device_info = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="refresh_tokens")
    revoker = relationship("User", foreign_keys=[revoked_by], back_populates="revoked_refresh_tokens")


class Memory(Base):
    """Memory storage model"""

    __tablename__ = "memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL for backward compatibility
    context = Column(String(255), index=True, nullable=False)
    type = Column(String(100), nullable=False)
    source = Column(String(255), nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Organization(Base):
    """Organization model with multi-tenant support and corporate provenance intelligence"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)
    settings = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Organization Provenance & Corporate Intelligence
    origin = Column(
        String(50), nullable=False, default="founding"
    )  # founding, acquired, merger, subsidiary, spin_off, joint_venture
    founded_date = Column(DateTime, nullable=True)

    # Corporate Structure & Lineage
    parent_organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    acquired_by_organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True
    )
    acquisition_date = Column(DateTime, nullable=True)
    full_corporate_hierarchy = Column(JSON, nullable=True)  # Array of UUIDs

    # Organization Status & Lifecycle
    organization_status = Column(
        String(50), nullable=False, default="active"
    )  # active, acquired, merged, dissolved, dormant, bankrupt
    dissolution_date = Column(DateTime, nullable=True)

    # Operational Metadata
    legal_name = Column(String(500), nullable=True)
    tax_id = Column(String(100), nullable=True)
    headquarters_location = Column(String(255), nullable=True)
    employee_count_range = Column(String(50), nullable=True)
    revenue_tier = Column(String(50), nullable=True)
    industry_sector = Column(String(100), nullable=True)
    organization_type = Column(
        String(50), nullable=False, default="corporation"
    )  # corporation, llc, partnership, non_profit, government, sole_proprietor

    # Corporate Metadata
    corporate_metadata = Column(JSON, nullable=True)

    # Relationships
    teams = relationship("Team", foreign_keys="[Team.organization_id]", back_populates="organization")
    contexts = relationship("Context", back_populates="organization")
    permissions = relationship("ContextPermission", back_populates="organization")

    # Corporate Structure Relationships
    parent_organization = relationship("Organization", remote_side=[id], foreign_keys=[parent_organization_id])
    acquired_by_organization = relationship(
        "Organization", remote_side=[id], foreign_keys=[acquired_by_organization_id]
    )


class Team(Base):
    """Team model for collaborative workspaces

    Note: This model matches public.teams schema after database consolidation.
    Extended M&A provenance fields should be accessed via graph queries.
    """

    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )  # NULL for cross-org teams
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Note: M&A provenance fields removed - use ag_catalog or graph queries
    # The canonical transactional team table (public.teams) is intentionally simpler

    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id], back_populates="teams")
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    contexts = relationship("Context", back_populates="team")
    permissions = relationship("ContextPermission", back_populates="team")
    invitations = relationship("TeamInvitation", back_populates="team", cascade="all, delete-orphan")
    memberships = relationship("TeamMembership", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """Team membership model with role-based access"""

    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(50), nullable=False, default="member")  # owner, admin, member, viewer
    joined_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


class Context(Base):
    """Context model for memory organization and sharing"""

    __tablename__ = "contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL for team/org owned contexts
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)  # NULL for user/org owned contexts
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )  # NULL for user/team owned contexts
    visibility = Column(String(50), nullable=False, default="private")  # private, team, organization, public
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    scope = Column(String(20), nullable=True)  # personal, team, organization

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id])
    team = relationship("Team")
    organization = relationship("Organization")
    permissions = relationship("ContextPermission", back_populates="context")


class ContextPermission(Base):
    """Context permission model for fine-grained access control"""

    __tablename__ = "context_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    context_id = Column(UUID(as_uuid=True), ForeignKey("contexts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # NULL for team/org permissions
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)  # NULL for user/org permissions
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )  # NULL for user/team permissions
    permission_level = Column(String(50), nullable=False)  # owner, admin, write, read
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)

    # Relationships with explicit foreign_keys to resolve ambiguity
    context = relationship("Context", back_populates="permissions")
    user = relationship("User", foreign_keys=[user_id], overlaps="user_permissions")
    team = relationship("Team", foreign_keys=[team_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
    granted_by_user = relationship("User", foreign_keys=[granted_by])


class OrganizationRegistration(Base):
    """Organization registration model for signup tracking"""

    __tablename__ = "organization_registrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id", deferrable=True, initially="deferred"), nullable=False
    )
    creator_user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", deferrable=True, initially="deferred"), nullable=False
    )
    registration_data = Column(JSON, nullable=True)  # Additional signup data
    status = Column(String(50), nullable=False, default="active")  # active, suspended, cancelled
    billing_email = Column(String(255), nullable=False)
    company_size = Column(String(50), nullable=True)
    industry = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    creator = relationship("User")


class UserInvitation(Base):
    """User invitation model for team/organization invites"""

    __tablename__ = "user_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    invitation_token = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="user")
    status = Column(String(50), nullable=False, default="pending")  # pending, accepted, expired, cancelled
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    invitation_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization")
    team = relationship("Team")
    inviter = relationship("User")


class TeamInvitation(Base):
    """Team invitation model for inviting users to teams"""

    __tablename__ = "team_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    invitation_token = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), nullable=True)
    status = Column(String(50), nullable=True)  # pending, accepted, expired, cancelled
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime, nullable=True)
    accepted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_user_id])


class TeamMembership(Base):
    """Team membership model with enhanced tracking"""

    __tablename__ = "team_memberships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    status = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", back_populates="memberships")
    user = relationship("User", foreign_keys=[user_id])
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
