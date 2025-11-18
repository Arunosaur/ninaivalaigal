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
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    
    # MFA fields
    mfa_enabled = Column(Boolean, default=False)
    mfa_method = Column(String(50), nullable=True)  # totp, webauthn, sms, email
    mfa_enforced = Column(Boolean, default=False)  # Admin-enforced MFA

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


class MemoryAttachment(Base):
    """Memory Attachment model for SPEC-032

    Stores metadata about files attached to memory tokens.
    The actual files are stored in the storage backend (S3/MinIO).
    """

    __tablename__ = "memory_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    memory_id = Column(Text, nullable=False, index=True)
    user_id = Column(Text, nullable=False, index=True)
    filename = Column(Text, nullable=False)
    content_type = Column(Text, nullable=False)
    size = Column(BigInteger, nullable=False)
    storage_key = Column(Text, nullable=False, unique=True, index=True)
    storage_backend = Column(Text, nullable=False, server_default="s3")
    attachment_metadata = Column(JSONB, server_default="{}")  # Renamed from 'metadata' (SQLAlchemy reserved)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Note: Foreign key to memory_tokens not enforced via FK constraint
    # because memory_id is TEXT (memory IDs may come from external providers)
    # Indexes provide fast lookups without FK constraints


# Additional models for SPEC compliance
from sqlalchemy import Column, String, Text, DateTime, Boolean, Float, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

# Anomaly Detection Models
class AnomalyDetection(Base):
    __tablename__ = "anomaly_detections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    detection_type = Column(String(100), nullable=False)
    anomaly_score = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)
    activity_data = Column(JSON, nullable=True)
    activity_type = Column(String(50), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    is_false_positive = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="anomaly_detections")
    alerts = relationship("AnomalyAlert", back_populates="detection")

class AnomalyPattern(Base):
    __tablename__ = "anomaly_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    pattern_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    detection_rules = Column(JSON, nullable=True)
    threshold_config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnomalyDetectionModel(Base):
    __tablename__ = "anomaly_detection_models"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    model_type = Column(String(100), nullable=False)
    model_config = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    detection_id = Column(UUID(as_uuid=True), ForeignKey("anomaly_detections.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    detection = relationship("AnomalyDetection", back_populates="alerts")
    acknowledged_user = relationship("User", foreign_keys=[acknowledged_by])

class ActivityMonitoring(Base):
    __tablename__ = "activity_monitoring"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    activity_type = Column(String(50), nullable=False)
    activity_data = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="activities")

# IDS Models
class IDSSignature(Base):
    __tablename__ = "ids_signatures"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    pattern = Column(Text, nullable=False)
    pattern_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rules = relationship("IDSRule", back_populates="signature")

class IDSRule(Base):
    __tablename__ = "ids_rules"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    signature_id = Column(UUID(as_uuid=True), ForeignKey("ids_signatures.id"), nullable=False)
    rule_type = Column(String(50), nullable=False)
    conditions = Column(JSON, nullable=True)
    actions = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    signature = relationship("IDSSignature", back_populates="rules")
    detections = relationship("IDSDetection", back_populates="rule")

class IDSDetection(Base):
    __tablename__ = "ids_detections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("ids_rules.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_data = Column(JSON, nullable=True)
    severity = Column(String(20), nullable=False)
    is_false_positive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    rule = relationship("IDSRule", back_populates="detections")
    user = relationship("User", back_populates="ids_detections")
    alerts = relationship("IDSAlert", back_populates="detection")

class IDSAlert(Base):
    __tablename__ = "ids_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    detection_id = Column(UUID(as_uuid=True), ForeignKey("ids_detections.id"), nullable=False)
    alert_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    detection = relationship("IDSDetection", back_populates="alerts")
    acknowledged_user = relationship("User", foreign_keys=[acknowledged_by])

class IDSBlocklist(Base):
    __tablename__ = "ids_blocklist"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    ip_address = Column(String(45), nullable=False, unique=True)
    reason = Column(Text, nullable=True)
    blocked_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    blocked_by_user = relationship("User", foreign_keys=[blocked_by])

# Add relationships to User model
User.anomaly_detections = relationship("AnomalyDetection", back_populates="user")
User.activities = relationship("ActivityMonitoring", back_populates="user")
User.ids_detections = relationship("IDSDetection", back_populates="user")

# Behavioral Analysis Models
class BehavioralBaseline(Base):
    __tablename__ = "behavioral_baselines"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    baseline_value = Column(Float, nullable=False)
    confidence_level = Column(Float, nullable=False)
    sample_size = Column(Integer, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="behavioral_baselines")

class BehavioralDeviation(Base):
    __tablename__ = "behavioral_deviations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    baseline_id = Column(UUID(as_uuid=True), ForeignKey("behavioral_baselines.id"), nullable=False)
    deviation_score = Column(Float, nullable=False)
    threshold_exceeded = Column(Boolean, default=False)
    event_data = Column(JSON, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="behavioral_deviations")
    baseline = relationship("BehavioralBaseline")

class BehavioralProfile(Base):
    __tablename__ = "behavioral_profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    profile_data = Column(JSON, nullable=True)
    risk_score = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="behavioral_profile")

class BehavioralEvent(Base):
    __tablename__ = "behavioral_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    event_data = Column(JSON, nullable=True)
    session_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(255), nullable=True)
    location_data = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="behavioral_events")

# Add behavioral relationships to User model
User.behavioral_baselines = relationship("BehavioralBaseline", back_populates="user")
User.behavioral_deviations = relationship("BehavioralDeviation", back_populates="user")
User.behavioral_profile = relationship("BehavioralProfile", back_populates="user")
User.behavioral_events = relationship("BehavioralEvent", back_populates="user")

# Threat Intelligence Models
class ThreatIntelligenceFeed(Base):
    __tablename__ = "threat_intelligence_feeds"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    feed_url = Column(Text, nullable=True)
    feed_type = Column(String(50), nullable=False)
    is_active = Column(Boolean, default=True)
    last_updated = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    feed_id = Column(UUID(as_uuid=True), ForeignKey("threat_intelligence_feeds.id"), nullable=True)
    indicator_type = Column(String(50), nullable=False)
    value = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False)
    severity = Column(String(20), nullable=False)
    source = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    feed = relationship("ThreatIntelligenceFeed", back_populates="indicators")
    matches = relationship("ThreatMatch", back_populates="indicator")

class ThreatReputation(Base):
    __tablename__ = "threat_reputations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_value = Column(Text, nullable=False)
    reputation_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False)
    last_assessed = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

class ThreatMatch(Base):
    __tablename__ = "threat_matches"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    indicator_id = Column(UUID(as_uuid=True), ForeignKey("threat_indicators.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ip_address = Column(String(45), nullable=True)
    matched_value = Column(Text, nullable=False)
    context = Column(JSON, nullable=True)
    risk_score = Column(Float, nullable=False)
    is_false_positive = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    indicator = relationship("ThreatIndicator", back_populates="matches")
    user = relationship("User", back_populates="threat_matches")

# Add threat intelligence relationships
ThreatIntelligenceFeed.indicators = relationship("ThreatIndicator", back_populates="feed")
User.threat_matches = relationship("ThreatMatch", back_populates="user")

# GDPR Compliance Models
class GDPRConsent(Base):
    __tablename__ = "gdpr_consents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    consent_type = Column(String(100), nullable=False)
    granted = Column(Boolean, nullable=False)
    granted_at = Column(DateTime, nullable=True)
    withdrawn_at = Column(DateTime, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="gdpr_consents")

class GDPRDataSubjectRequest(Base):
    __tablename__ = "gdpr_data_subject_requests"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    request_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    request_data = Column(JSON, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", foreign_keys=[user_id], back_populates="gdpr_requests")
    processor = relationship("User", foreign_keys=[processed_by])

class GDPRDataRetentionPolicy(Base):
    __tablename__ = "gdpr_data_retention_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    data_type = Column(String(100), nullable=False)
    retention_period_days = Column(Integer, nullable=False)
    policy_description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class GDPRDataProcessingLog(Base):
    __tablename__ = "gdpr_data_processing_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    processing_activity = Column(String(255), nullable=False)
    legal_basis = Column(String(100), nullable=False)
    data_categories = Column(JSON, nullable=True)
    purpose = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="gdpr_processing_logs")

# Add GDPR relationships to User model
User.gdpr_consents = relationship("GDPRConsent", back_populates="user")
User.gdpr_requests = relationship("GDPRDataSubjectRequest", foreign_keys=[GDPRDataSubjectRequest.user_id], back_populates="user")
User.gdpr_processing_logs = relationship("GDPRDataProcessingLog", back_populates="user")

# Macro Models
class Macro(Base):
    __tablename__ = "macros"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    macro_code = Column(Text, nullable=False)
    language = Column(String(50), nullable=False)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="macros")
    audit_logs = relationship("MacroAuditLog", back_populates="macro")

class MacroAuditLog(Base):
    __tablename__ = "macro_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    macro_id = Column(UUID(as_uuid=True), ForeignKey("macros.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    macro = relationship("Macro", back_populates="audit_logs")
    user = relationship("User")

# Add Macro relationships to User model
User.macros = relationship("Macro", back_populates="user")

# Demo Model
class Demo(Base):
    __tablename__ = "demos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    demo_data = Column(JSON, nullable=True)
    is_public = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="demos")

# Add Demo relationships to User model
User.demos = relationship("Demo", back_populates="user")

# Memory-related Models
class MemoryClassification(Base):
    __tablename__ = "memory_classifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    memory_id = Column(String, nullable=False)  # Memory IDs are strings, not UUIDs
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    classification_type = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    classification_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")

class MemoryTrustScore(Base):
    __tablename__ = "memory_trust_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    memory_id = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    trust_score = Column(Float, nullable=False)
    factors = Column(JSON, nullable=True)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    feedback = relationship("MemoryTrustFeedback", back_populates="trust_score")
    history = relationship("MemoryTrustScoreHistory", back_populates="trust_score")

class MemoryTrustFeedback(Base):
    __tablename__ = "memory_trust_feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trust_score_id = Column(UUID(as_uuid=True), ForeignKey("memory_trust_scores.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    feedback_type = Column(String(50), nullable=False)  # positive, negative
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    trust_score = relationship("MemoryTrustScore", back_populates="feedback")
    user = relationship("User")

class MemoryTrustScoreHistory(Base):
    __tablename__ = "memory_trust_score_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    trust_score_id = Column(UUID(as_uuid=True), ForeignKey("memory_trust_scores.id"), nullable=False)
    previous_score = Column(Float, nullable=False)
    new_score = Column(Float, nullable=False)
    change_reason = Column(String(255), nullable=True)
    changed_at = Column(DateTime, default=datetime.utcnow)
    
    trust_score = relationship("MemoryTrustScore", back_populates="history")

# MFA Models
class MFAWebAuthnCredential(Base):
    __tablename__ = "mfa_webauthn_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    credential_id = Column(String(255), nullable=False, unique=True)
    public_key = Column(Text, nullable=False)
    sign_count = Column(Integer, nullable=False)
    device_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="webauthn_credentials")

class MFAEnforcementPolicy(Base):
    __tablename__ = "mfa_enforcement_policies"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    target_role = Column(String(50), nullable=True)  # Apply to specific role
    target_account_type = Column(String(50), nullable=True)  # Apply to specific account type
    mfa_required = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class RiskConfiguration(Base):
    __tablename__ = "risk_configurations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Risk weights (should sum to 1.0)
    device_weight = Column(Float, nullable=False, default=0.3)
    location_weight = Column(Float, nullable=False, default=0.2)
    time_weight = Column(Float, nullable=False, default=0.2)
    behavior_weight = Column(Float, nullable=False, default=0.3)
    
    # Risk thresholds
    risk_threshold_critical = Column(Float, nullable=False, default=0.8)
    risk_threshold_high = Column(Float, nullable=False, default=0.6)
    risk_threshold_medium = Column(Float, nullable=False, default=0.4)
    
    # Penalties
    vpn_penalty = Column(Float, nullable=False, default=0.4)
    proxy_penalty = Column(Float, nullable=False, default=0.3)
    tor_penalty = Column(Float, nullable=False, default=0.5)
    new_device_penalty = Column(Float, nullable=False, default=0.2)
    unusual_location_penalty = Column(Float, nullable=False, default=0.3)
    unusual_time_penalty = Column(Float, nullable=False, default=0.2)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Add MFA relationships to User model
User.webauthn_credentials = relationship("MFAWebAuthnCredential", back_populates="user")

# Authentication Security Models
class DeviceFingerprint(Base):
    __tablename__ = "device_fingerprints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    fingerprint_hash = Column(String(255), nullable=False, unique=True)
    device_info = Column(JSON, nullable=True)
    is_trusted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="device_fingerprints")

class AuthRiskScore(Base):
    __tablename__ = "auth_risk_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)
    risk_score = Column(Float, nullable=False)
    risk_factors = Column(JSON, nullable=True)
    auth_successful = Column(Boolean, nullable=True)  # Track if auth was successful
    assessed_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="auth_risk_scores")

# Add auth security relationships to User model
User.device_fingerprints = relationship("DeviceFingerprint", back_populates="user")
User.auth_risk_scores = relationship("AuthRiskScore", back_populates="user")

# User Behavior Pattern Model for Risk Assessment
class UserBehaviorPattern(Base):
    __tablename__ = "user_behavior_patterns"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pattern_type = Column(String(50), nullable=False)  # login_time, location, device
    pattern_data = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=False, default=0.5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="behavior_patterns")

# Add behavior patterns relationship to User model
User.behavior_patterns = relationship("UserBehaviorPattern", back_populates="user")
