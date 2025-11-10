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
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """User model with authentication and RBAC support"""

    __tablename__ = "users"
    __table_args__ = {"schema": "core_api"}  # US-655: Schema Separation (Phase 2)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(255), unique=True, nullable=True, index=True)  # Made nullable for email-only signup
    email = Column(String(255), unique=True, nullable=False, index=True)  # Made required
    name = Column(String(255), nullable=False)  # Full name
    password_hash = Column(String(255), nullable=False)
    account_type = Column(
        String(50), nullable=False, default="individual"
    )  # individual, team_member, organization_admin
    subscription_tier = Column(String(50), nullable=False, default="free")  # free, team, enterprise
    personal_contexts_limit = Column(Integer, default=10)
    role = Column(String(50), nullable=False, default="user")  # user, admin, super_admin
    created_via = Column(String(50), nullable=False, default="signup")  # signup, invite, admin
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # RBAC fields
    default_role = Column(String(50), default="MEMBER")
    is_system_admin = Column(Boolean, default=False)

    # Relationships for sharing system
    owned_contexts = relationship("Context", foreign_keys="[Context.owner_id]", back_populates="owner")
    team_memberships = relationship("TeamMember", back_populates="user")
    granted_permissions = relationship(
        "ContextPermission",
        foreign_keys="[ContextPermission.granted_by]",
        back_populates="granted_by_user",
    )
    user_permissions = relationship("ContextPermission", foreign_keys="[ContextPermission.user_id]")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    # RBAC relationships (defined in rbac_models.py)
    # These are added dynamically by rbac_models.py to avoid circular imports


class RefreshToken(Base):
    """Refresh token model for JWT token refresh"""

    __tablename__ = "refresh_tokens"
    __table_args__ = {"schema": "core_api"}  # US-655: Schema Separation (Phase 2)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("core_api.users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(UUID(as_uuid=True), ForeignKey("core_api.users.id", ondelete="SET NULL"), nullable=True)
    device_info = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="refresh_tokens")


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


class Demo(Base):
    """Demo model for narrative memory macros (SPEC-047)

    Stores demo recordings (screen + audio) as narrative memories with
    transcription, timeline, and metadata.
    """

    __tablename__ = "demos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    demo_id = Column(String(255), unique=True, nullable=False, index=True)  # Human-readable demo ID

    # Basic information
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    author = Column(String(255), nullable=True)

    # Owner information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Memory association
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="SET NULL"), nullable=True, index=True)
    memory_context_ids = Column(JSONB, nullable=True)  # Array of memory context IDs this demo is linked to

    # Media files
    video_url = Column(String(500), nullable=True)  # URL to video file in object storage
    audio_url = Column(String(500), nullable=True)  # URL to audio file in object storage
    thumbnail_url = Column(String(500), nullable=True)  # URL to thumbnail image

    # Transcription and timeline
    transcription = Column(Text, nullable=True)  # Full transcription text
    timeline = Column(JSONB, nullable=True)  # Timestamped timeline of events

    # Metadata
    tags = Column(JSONB, nullable=True)  # Array of tags
    demo_metadata = Column(
        JSONB, nullable=True, name="metadata"
    )  # Additional metadata (renamed from 'metadata' - SQLAlchemy reserved)

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False, index=True)  # Public demos can be shared

    # Recording information
    recording_duration_seconds = Column(Integer, nullable=True)  # Duration in seconds
    file_size_bytes = Column(BigInteger, nullable=True)  # Total file size
    recording_format = Column(String(50), nullable=True)  # Video format (mp4, webm, etc.)

    # Processing status
    processing_status = Column(String(50), default="pending", index=True)  # pending, processing, completed, failed
    transcription_status = Column(String(50), nullable=True)  # pending, processing, completed, failed

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    recorded_at = Column(DateTime, nullable=True)  # When the demo was recorded

    # View statistics
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    team = relationship("Team", foreign_keys=[team_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
    memory = relationship("Memory", foreign_keys=[memory_id])

    __table_args__ = {
        "comment": "SPEC-047: Narrative memory macros (screen + voice capture) with transcription and timeline"
    }


class MemoryClassification(Base):
    """Memory classification model for memory intent classifier (SPEC-048)

    Stores classification results and metadata for memory classification into
    contextual, procedural (macro), or narrative types.
    """

    __tablename__ = "memory_classifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)

    # Memory association
    memory_id = Column(UUID(as_uuid=True), ForeignKey("memories.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Classification result
    classification_type = Column(String(50), nullable=False, index=True)  # contextual, procedural, narrative
    confidence_score = Column(Integer, nullable=False)  # 0-100 confidence percentage

    # Classification metadata
    suggested_type = Column(String(50), nullable=True)  # Suggested type if different from classification
    classification_source = Column(String(50), nullable=False, default="heuristic")  # heuristic, ml, user
    classification_method = Column(
        String(100), nullable=True
    )  # Method used (e.g., "repetition_detection", "audio_signal")

    # User feedback
    user_confirmed = Column(Boolean, nullable=True)  # True if user confirmed, False if rejected, None if not reviewed
    user_feedback = Column(Text, nullable=True)  # User feedback or correction

    # Classification details
    classification_metadata = Column(JSONB, nullable=True)  # Additional classification data
    detection_signals = Column(JSONB, nullable=True)  # Signals that led to classification

    # Reclassification support
    is_reclassification = Column(Boolean, default=False, index=True)  # True if this is a reclassification
    previous_classification_id = Column(
        UUID(as_uuid=True), ForeignKey("memory_classifications.id", ondelete="SET NULL"), nullable=True
    )

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    memory = relationship("Memory", foreign_keys=[memory_id])
    user = relationship("User", foreign_keys=[user_id])
    previous_classification = relationship(
        "MemoryClassification", remote_side=[id], foreign_keys=[previous_classification_id]
    )

    __table_args__ = {"comment": "SPEC-048: Memory intent classifier results and metadata with audit trail"}


class Organization(Base):
    """Organization model for multi-tenant support"""

    __tablename__ = "organizations"
    __table_args__ = {"schema": "core_api"}  # US-655: Schema Separation (Phase 2)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)  # Company domain
    settings = Column(JSON, nullable=True)  # Organization settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teams = relationship("Team", back_populates="organization")
    contexts = relationship("Context", back_populates="organization")
    permissions = relationship("ContextPermission", back_populates="organization")


class Team(Base):
    """Team model for collaborative workspaces"""

    __tablename__ = "teams"
    __table_args__ = {"schema": "core_api"}  # US-655: Schema Separation (Phase 2)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )  # NULL for cross-org teams
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
    contexts = relationship("Context", back_populates="team")
    permissions = relationship("ContextPermission", back_populates="team")
    invitations = relationship("TeamInvitation", back_populates="team", cascade="all, delete-orphan")
    memberships = relationship("TeamMembership", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """Team membership model with role-based access"""

    __tablename__ = "team_members"
    __table_args__ = {"schema": "core_api"}  # US-655: Schema Separation (Phase 2)

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
    __table_args__ = {"schema": "core_api"}  # US-655: Schema Separation (Phase 2)

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
    __table_args__ = {"schema": "core_api"}  # US-655: Schema Separation (Phase 2)

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
    __table_args__ = {"schema": "core_api"}  # US-655: Schema Separation (Phase 2)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    creator_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
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
    __table_args__ = {"schema": "core_api"}  # US-655: Schema Separation (Phase 2)

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


class Macro(Base):
    """Macro model for procedural memory system

    SPEC-046: Stores macro definitions with steps, metadata, and context linking.
    """

    __tablename__ = "macros"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    macro_id = Column(String(255), unique=True, nullable=False, index=True)  # Human-readable macro ID

    # Basic information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Owner information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Macro definition
    steps = Column(JSONB, nullable=False)  # Array of macro steps (actions, events, etc.)
    macro_metadata = Column(
        JSONB, nullable=True, name="metadata"
    )  # Additional metadata (renamed from 'metadata' - SQLAlchemy reserved)

    # Context linking
    memory_context_ids = Column(JSONB, nullable=True)  # Array of memory IDs this macro is linked to
    tags = Column(JSONB, nullable=True)  # Array of tags for categorization

    # Execution settings
    trigger_frequency = Column(String(50), nullable=False, default="manual")  # manual, scheduled, event
    automation_level = Column(Integer, default=0)  # 0-100 automation level

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_public = Column(Boolean, default=False, index=True)  # Public macros can be shared

    # Versioning
    version = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_executed_at = Column(DateTime, nullable=True)

    # Execution statistics
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    team = relationship("Team", foreign_keys=[team_id])
    organization = relationship("Organization", foreign_keys=[organization_id])

    __table_args__ = {"comment": "SPEC-046: Procedural macro definitions with steps and context linking"}


class MacroAuditLog(Base):
    """Macro execution audit log model

    SPEC-046: Comprehensive audit trail for macro execution.
    Logs all macro executions with timestamps, user information, execution context,
    success/failure status, and error details.
    """

    __tablename__ = "macro_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    execution_id = Column(String(255), unique=True, nullable=False, index=True)  # Unique execution identifier

    # Macro identification
    macro_id = Column(String(255), nullable=False, index=True)
    macro_name = Column(String(255), nullable=False)

    # User information
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Execution status
    status = Column(
        String(50), nullable=False, index=True
    )  # started, in_progress, completed, failed, cancelled, timeout

    # Execution context (environment, parameters, memory context, etc.)
    execution_context = Column(JSONB, nullable=True)

    # Error information (if failed)
    error_type = Column(String(50), nullable=True)  # validation_error, runtime_error, permission_denied, etc.
    error_message = Column(Text, nullable=True)

    # Execution metrics
    execution_time_ms = Column(Integer, nullable=True)  # Execution time in milliseconds
    steps_executed = Column(Integer, nullable=True)  # Number of steps executed
    total_steps = Column(Integer, nullable=True)  # Total number of steps in macro
    completion_percentage = Column(Integer, nullable=True)  # Percentage of completion

    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

    __table_args__ = {"comment": "SPEC-046: Macro execution audit trail with comprehensive logging"}


class SearchIndex(Base):
    """Search index model for PostgreSQL full-text search (SPEC-152, US-944)"""

    __tablename__ = "search_index"
    __table_args__ = {"schema": "core_api", "comment": "US-944: SPEC-152: Search index for PostgreSQL full-text search"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    memory_id = Column(
        UUID(as_uuid=True), ForeignKey("core_api.memories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content_text = Column(Text, nullable=False)
    tags = Column(ARRAY(String), default=[], nullable=False)
    scope_type = Column(String(50), nullable=True, index=True)
    scope_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    search_vector = Column(TSVECTOR, nullable=True)

    # Relationships
    memory = relationship("Memory", foreign_keys=[memory_id])


class TagHierarchy(Base):
    """Hierarchical tag structure for SPEC-034 (US-335)"""

    __tablename__ = "tag_hierarchy"
    __table_args__ = {"schema": "memory", "comment": "US-335: SPEC-034: Hierarchical Memory Tag System"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    tag_name = Column(Text, nullable=False)
    parent_id = Column(
        UUID(as_uuid=True), ForeignKey("memory.tag_hierarchy.id", ondelete="CASCADE"), nullable=True, index=True
    )
    depth = Column(Integer, nullable=False, default=0)  # 0-3 levels
    path = Column(Text, nullable=False, index=True)  # Materialized path (e.g., "work/projects/urgent")
    scope_type = Column(String(50), nullable=False)  # 'user', 'team', 'organization'
    scope_id = Column(UUID(as_uuid=True), nullable=False, index=True)  # user_id, team_id, or org_id
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    parent = relationship("TagHierarchy", remote_side=[id], backref="children")
    memory_tags = relationship("MemoryHierarchicalTag", back_populates="tag", cascade="all, delete-orphan")


class MemoryHierarchicalTag(Base):
    """Junction table linking memories to hierarchical tags"""

    __tablename__ = "memory_hierarchical_tags"
    __table_args__ = {"schema": "memory", "comment": "Junction table linking memories to hierarchical tags"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(
        UUID(as_uuid=True), ForeignKey("core_api.memories.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tag_id = Column(
        UUID(as_uuid=True), ForeignKey("memory.tag_hierarchy.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    memory = relationship("Memory", foreign_keys=[memory_id])
    tag = relationship("TagHierarchy", foreign_keys=[tag_id], back_populates="memory_tags")


class EmbeddingModelRegistry(Base):
    """Embedding model registry for SPEC-138 (US-358)"""

    __tablename__ = "embedding_model_registry"
    __table_args__ = {"schema": "public", "comment": "US-358: SPEC-138: Embedding Model Registry"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    hook_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    provider = Column(String(50), nullable=False, index=True)  # e.g., "openai", "cohere", "custom"
    endpoint_url = Column(Text, nullable=False)
    api_key_encrypted = Column(Text, nullable=True)  # Encrypted API key
    dimensions = Column(Integer, nullable=False)  # Embedding dimensions (1-10000)
    max_batch_size = Column(Integer, nullable=True)  # Optional max batch size (1-1000)
    supports_streaming = Column(Boolean, nullable=False, default=False)
    timeout_seconds = Column(Integer, nullable=False, default=30)  # 1-300 seconds
    status = Column(String(20), nullable=False, default="testing", index=True)  # active, inactive, error, testing
    model_metadata = Column(
        JSONB, nullable=False, default={}, name="metadata"
    )  # Additional metadata (renamed from 'metadata' - SQLAlchemy reserved)
    version = Column(String(50), nullable=True)  # Model version (e.g., "1.0.0", "v2")
    capabilities = Column(JSONB, nullable=False, default={})  # e.g., {"batching": true, "streaming": false}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(
        UUID(as_uuid=True), ForeignKey("core_api.users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("core_api.organizations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("core_api.teams.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
