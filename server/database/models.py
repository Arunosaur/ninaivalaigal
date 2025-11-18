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
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    """User model with authentication and RBAC support"""

    __tablename__ = "users"

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
    refresh_tokens = relationship(
        "RefreshToken", foreign_keys="[RefreshToken.user_id]", back_populates="user", cascade="all, delete-orphan"
    )

    # RBAC relationships (defined in rbac_models.py)
    # These are added dynamically by rbac_models.py to avoid circular imports

    # GDPR and HIPAA compliance relationships are defined using backref in compliance/models.py
    # This avoids circular imports and allows models to be loaded in any order


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
    # SPEC-128: Transfer & Copy tracking
    derived_from = Column(UUID(as_uuid=True), nullable=True, index=True)  # Original memory for copies
    transfer_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Transfer record ID
    copy_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # Copy record ID


class Organization(Base):
    """Organization model for multi-tenant support"""

    __tablename__ = "organizations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    domain = Column(String(255), nullable=True)  # Company domain
    settings = Column(JSON, nullable=True)  # Organization settings
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    teams = relationship("Team", foreign_keys="[Team.organization_id]", back_populates="organization")
    contexts = relationship("Context", back_populates="organization")
    permissions = relationship("ContextPermission", back_populates="organization")


class Team(Base):
    """Team model for collaborative workspaces

    Supports three types of teams based on governance_type:
    - internal: Teams within an organization (organization_id NOT NULL)
    - external: Independent teams without organization (organization_id NULL, e.g., open source)
    - shared: Cross-organization collaborative teams
    """

    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False)
    organization_id = Column(
        UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True
    )  # NULL for external/independent teams
    description = Column(Text, nullable=True)

    # Team governance and origin fields
    origin = Column(String(50), nullable=False, default="native")  # native, partner, acquired
    governance_type = Column(String(50), nullable=False, default="internal")  # internal, external, shared
    status = Column(String(50), nullable=False, default="active")  # active, inactive, sunset, transitioning
    lead_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # Team lead

    # Advanced team features
    parent_team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=True)  # For sub-teams
    acquired_from_organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    acquisition_date = Column(DateTime, nullable=True)
    provenance_metadata = Column(JSON, nullable=True)  # Additional metadata

    # Standalone team fields (from SPEC-066)
    # Note: is_standalone is now a property derived from organization_id IS NULL
    # This follows database normalization - single source of truth
    upgrade_eligible = Column(Boolean, default=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    team_invite_code = Column(String(32), unique=True, nullable=True)
    max_members = Column(Integer, default=10)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id], back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
    contexts = relationship("Context", back_populates="team")
    permissions = relationship("ContextPermission", back_populates="team")
    invitations = relationship("TeamInvitation", back_populates="team", cascade="all, delete-orphan")
    created_by_user = relationship("User", foreign_keys=[created_by_user_id])

    @property
    def is_standalone(self):
        """Derived property: team is standalone if organization_id is NULL
        
        This follows database normalization principles - organization_id
        is the single source of truth for standalone status.
        """
        return self.organization_id is None


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


class TeamInvitation(Base):
    """Team invitation for secure team joining"""

    __tablename__ = "team_invitations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    email = Column(String(255), nullable=False)
    invitation_token = Column(String(255), unique=True, nullable=False)
    role = Column(String(50), default="contributor")
    status = Column(String(50), default="pending")  # pending, accepted, expired, revoked
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(days=7))
    accepted_at = Column(DateTime)
    accepted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    team = relationship("Team", back_populates="invitations")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_user_id])


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


# US#156: Team Billing Schema Models (SPEC-026 Phase 1)


class SubscriptionStatus(str, Enum):
    """Team subscription status enum"""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"


class TeamBilling(Base):
    """Team billing model - core billing information per US#156

    Stores Stripe customer ID and billing information for teams.
    Part of SPEC-026: Standalone Teams and Billing Phase 1.
    """

    __tablename__ = "team_billing"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_id = Column(
        UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    stripe_customer_id = Column(String(255), unique=True, index=True)
    billing_email = Column(String(255), nullable=False)
    payment_method_id = Column(String(255))  # Stripe payment method ID
    default_payment_method = Column(String(255))  # Stripe default payment method
    billing_address = Column(JSONB)  # Structured billing address
    tax_id = Column(String(50))
    currency = Column(String(3), default="USD")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", backref="billing")


class TeamSubscription(Base):
    """Team subscription model - plan management per US#156

    Tracks subscription plans, status, and billing periods for teams.
    Part of SPEC-026: Standalone Teams and Billing Phase 1.
    """

    __tablename__ = "team_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_id = Column(String(50), nullable=False)  # 'free', 'starter', 'pro', 'enterprise'
    status = Column(String(50), nullable=False, default=SubscriptionStatus.ACTIVE.value)
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    trial_start = Column(DateTime, nullable=True)
    trial_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    canceled_at = Column(DateTime, nullable=True)
    subscription_metadata = Column(JSONB, nullable=True)  # Renamed from 'metadata' (reserved in SQLAlchemy)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", backref="subscriptions")

    # Indexes defined in schema SQL
    __table_args__ = {"comment": "Team subscription plans and billing periods (US#156, SPEC-026)"}


class TeamUsageMetrics(Base):
    """Team usage metrics model - tracking per US#156

    Tracks usage metrics (memory, API calls, storage) for teams over billing periods.
    Part of SPEC-026: Standalone Teams and Billing Phase 1.
    """

    __tablename__ = "team_usage_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    memory_count = Column(Integer, default=0)
    api_calls = Column(Integer, default=0)
    storage_bytes = Column(BigInteger, default=0)
    context_count = Column(Integer, default=0)
    member_count = Column(Integer, default=0)
    recorded_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    team = relationship("Team", backref="usage_metrics")

    # Constraints
    __table_args__ = (
        CheckConstraint("memory_count >= 0", name="check_memory_count_non_negative"),
        CheckConstraint("api_calls >= 0", name="check_api_calls_non_negative"),
        CheckConstraint("storage_bytes >= 0", name="check_storage_bytes_non_negative"),
        CheckConstraint("context_count >= 0", name="check_context_count_non_negative"),
        CheckConstraint("member_count >= 0", name="check_member_count_non_negative"),
        CheckConstraint("period_start <= period_end", name="usage_period_check"),
        {"comment": "Team usage metrics tracking (US#156, SPEC-026)"},
    )


# US#157: Discount & Credit System Models (SPEC-026 Phase 1)
# NOTE: DiscountCode moved to server/billing/models.py (SPEC-147)
# Use: from server.billing.models import DiscountCode


class TeamCredit(Base):
    """Team credit model - credit balance tracking per US#157

    Tracks credits granted to teams with usage tracking.
    Part of SPEC-026: Standalone Teams and Billing Phase 1.
    """

    __tablename__ = "team_credits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    amount = Column(
        "amount", Numeric(10, 2), nullable=False
    )  # Use explicit name to avoid conflict with SQLAlchemy reserved word
    used_amount = Column("used_amount", Numeric(10, 2), default=0)
    remaining_amount = Column("remaining_amount", Numeric(10, 2))  # Computed column
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=True, index=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", foreign_keys=[team_id])
    organization = relationship("Organization", foreign_keys=[org_id])
    granter = relationship("User", foreign_keys=[granted_by])
    transactions = relationship("CreditTransaction", back_populates="credit", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_amount_positive"),
        CheckConstraint("used_amount >= 0", name="check_used_amount_non_negative"),
        CheckConstraint("used_amount <= amount", name="used_amount_check"),
        CheckConstraint(
            "(team_id IS NOT NULL AND org_id IS NULL) OR (team_id IS NULL AND org_id IS NOT NULL)",
            name="credit_target_check",
        ),
        {"comment": "Team credits for billing (US#157, SPEC-026)"},
    )


class CreditTransactionType(str, Enum):
    """Credit transaction type enum"""

    GRANT = "grant"
    DEDUCT = "deduct"
    EXPIRE = "expire"
    REFUND = "refund"


class CreditTransaction(Base):
    """Credit transaction model - audit trail per US#157

    Tracks all credit transactions for audit and balance validation.
    Part of SPEC-026: Standalone Teams and Billing Phase 1.
    """

    __tablename__ = "credit_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_credit_id = Column(
        UUID(as_uuid=True), ForeignKey("team_credits.id", ondelete="CASCADE"), nullable=False, index=True
    )
    transaction_type = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    balance_before = Column(Numeric(10, 2), nullable=False)
    balance_after = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=False)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    invoice_id = Column(String(255), nullable=True)  # Reference to billing_invoices table (model not yet created)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    credit = relationship("TeamCredit", back_populates="transactions")
    performer = relationship("User", foreign_keys=[performed_by])

    # Constraints
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_amount_positive"),
        CheckConstraint("balance_before >= 0", name="check_balance_before_non_negative"),
        CheckConstraint("balance_after >= 0", name="check_balance_after_non_negative"),
        CheckConstraint("transaction_type IN ('grant', 'deduct', 'expire', 'refund')", name="check_transaction_type"),
        {"comment": "Credit transaction audit trail (US#157, SPEC-026)"},
    )


# NOTE: DiscountCodeUsage removed - replaced by DiscountApplication in SPEC-147
# Use: from server.billing.models import DiscountApplication


# US#158: Non-Profit Application System Models (SPEC-026 Phase 1)


class NonProfitApplicationStatus(str, Enum):
    """Non-profit application status enum"""

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class NonProfitApplication(Base):
    """Non-profit application model - application and approval workflow per US#158

    Tracks non-profit applications with status workflow and review tracking.
    Part of SPEC-026: Standalone Teams and Billing Phase 1.
    """

    __tablename__ = "nonprofit_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_name = Column(String(255), nullable=False)
    tax_id = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    website_url = Column(Text, nullable=True)
    documentation_urls = Column(JSON, nullable=True)  # Array of URLs for supporting documents
    status = Column(String(20), default=NonProfitApplicationStatus.PENDING.value, nullable=False, index=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    team = relationship("Team", foreign_keys=[team_id])
    organization = relationship("Organization", foreign_keys=[org_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])

    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'approved', 'rejected', 'under_review')", name="check_status_valid"),
        CheckConstraint(
            "(team_id IS NOT NULL AND org_id IS NULL) OR (team_id IS NULL AND org_id IS NOT NULL)",
            name="nonprofit_target_check",
        ),
        {"comment": "Non-profit application workflow (US#158, SPEC-026)"},
    )


# US#938: In-App Notification Storage (SPEC-148 Phase 1.3)


class InAppNotification(Base):
    """In-app notification model for real-time notification storage and delivery

    Stores in-app notifications with read/unread status, archive/delete support,
    and real-time delivery via WebSocket/SSE (SPEC-115).
    Part of SPEC-148: Unified Notification System.
    """

    __tablename__ = "in_app_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type = Column(String(100), nullable=False, index=True)  # quota_warning, alert, system, etc.
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    template_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to notification template
    notification_metadata = Column(
        JSONB, nullable=True
    )  # Additional notification data (renamed from 'metadata' - reserved in SQLAlchemy)

    # Status tracking
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime, nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    archived_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)

    # Delivery tracking
    delivered_at = Column(DateTime, nullable=True, index=True)  # When delivered via WebSocket/SSE
    opened_at = Column(DateTime, nullable=True)  # When user opened notification

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="in_app_notifications")

    # Constraints
    __table_args__ = (
        CheckConstraint("NOT (is_deleted = true AND is_archived = true)", name="check_not_deleted_and_archived"),
        {"comment": "In-app notification storage with read/unread status (US#938, SPEC-148)"},
    )


# US#939: Push Notification Support (FCM/APNs) - Device Token Management (SPEC-148 Phase 2.1)


class DeviceToken(Base):
    """Device token model for push notification device registration

    Stores device tokens for FCM (Android) and APNs (iOS) push notifications.
    Part of SPEC-148: Unified Notification System, Phase 2.1.
    NOTIF-004 (US#939): Push Notification Support (FCM/APNs)
    """

    __tablename__ = "device_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(Text, nullable=False, index=True)  # Device token from FCM or APNs
    platform = Column(String(20), nullable=False, index=True)  # "ios" or "android"
    device_info = Column(JSONB, nullable=True)  # Device information (model, OS version, etc.)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="device_tokens")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "token", "platform", name="uq_user_token_platform"),
        {"comment": "Device token storage for push notifications (US#939, SPEC-148 Phase 2.1)"},
    )


class Macro(Base):
    """
    Macro model for Unified Macro Intelligence (UMI) system.
    
    Represents a procedural macro with steps, metadata, and execution tracking.
    Supports all three macro capture modes:
    - Script-based (via eMacros)
    - Visual/Replay-based (via screen recording)
    - Implicit (via behavior analysis)
    """
    
    __tablename__ = "macros"
    __table_args__ = (
        {"comment": "SPEC-046: Procedural macro definitions with steps and context linking"},
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Macro identification
    macro_id = Column(String(255), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text(), nullable=True)
    
    # Ownership and organization
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    team_id = Column(
        UUID(as_uuid=True),
        ForeignKey("teams.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    organization_id = Column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Macro content and metadata
    steps = Column(JSONB, nullable=False)  # List of macro steps
    macro_metadata = Column("metadata", JSONB, nullable=True)  # Additional metadata
    memory_context_ids = Column(JSONB, nullable=True)  # Linked memory contexts
    tags = Column(JSONB, nullable=True)  # Tags for categorization
    
    # Macro behavior
    trigger_frequency = Column(String(50), nullable=False, server_default="manual")
    automation_level = Column(Integer(), server_default="0")
    
    # Status and visibility
    is_active = Column(Boolean(), default=True, index=True)
    is_public = Column(Boolean(), default=False, index=True)
    version = Column(Integer(), nullable=False, server_default="1")
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    last_executed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Execution statistics
    execution_count = Column(Integer(), default=0)
    success_count = Column(Integer(), default=0)
    failure_count = Column(Integer(), default=0)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    team = relationship("Team", foreign_keys=[team_id])
    organization = relationship("Organization", foreign_keys=[organization_id])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert macro to dictionary"""
        return {
            "id": str(self.id),
            "macro_id": self.macro_id,
            "name": self.name,
            "description": self.description,
            "user_id": str(self.user_id) if self.user_id else None,
            "team_id": str(self.team_id) if self.team_id else None,
            "organization_id": str(self.organization_id) if self.organization_id else None,
            "steps": self.steps,
            "metadata": self.macro_metadata,
            "memory_context_ids": self.memory_context_ids,
            "tags": self.tags,
            "trigger_frequency": self.trigger_frequency,
            "automation_level": self.automation_level,
            "is_active": self.is_active,
            "is_public": self.is_public,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_executed_at": self.last_executed_at.isoformat() if self.last_executed_at else None,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.execution_count is None or self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
    
    def get_success_rate(self) -> float:
        """Get success rate (backward compatibility method)"""
        return self.success_rate
    
    def is_executable(self) -> bool:
        """Check if macro is executable"""
        return self.is_active and self.steps is not None and len(self.steps) > 0


class MacroAuditLog(Base):
    """
    Macro audit log model for tracking macro executions.
    
    Provides comprehensive audit trail for macro executions including
    execution context, errors, performance metrics, and user tracking.
    """
    
    __tablename__ = "macro_audit_logs"
    __table_args__ = (
        {"comment": "SPEC-046: Macro execution audit trail with comprehensive logging"},
    )
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Execution identification
    execution_id = Column(String(255), nullable=False, unique=True, index=True)
    macro_id = Column(String(255), nullable=False, index=True)
    macro_name = Column(String(255), nullable=False)
    
    # User tracking
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Execution status
    status = Column(String(50), nullable=False, index=True)  # success, failure, partial, cancelled
    
    # Execution context and details
    execution_context = Column(JSONB, nullable=True)  # Full execution context
    
    # Error tracking
    error_type = Column(String(50), nullable=True)
    error_message = Column(Text(), nullable=True)
    
    # Performance metrics
    execution_time_ms = Column(Integer(), nullable=True)
    steps_executed = Column(Integer(), nullable=True)
    total_steps = Column(Integer(), nullable=True)
    completion_percentage = Column(Integer(), nullable=True)
    
    # Request tracking
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text(), nullable=True)
    
    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary"""
        return {
            "id": str(self.id),
            "execution_id": self.execution_id,
            "macro_id": self.macro_id,
            "macro_name": self.macro_name,
            "user_id": str(self.user_id) if self.user_id else None,
            "status": self.status,
            "execution_context": self.execution_context,
            "error_type": self.error_type,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "steps_executed": self.steps_executed,
            "total_steps": self.total_steps,
            "completion_percentage": self.completion_percentage,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def is_successful(self) -> bool:
        """Check if execution was successful"""
        return self.status == "success"
    
    def is_failed(self) -> bool:
        """Check if execution failed"""
        return self.status == "failure"
    
    def is_partial(self) -> bool:
        """Check if execution was partial"""
        return self.status == "partial"


class TeamUpgradeHistory(Base):
    """Track team upgrades to organizations"""

    __tablename__ = "team_upgrade_history"
    __table_args__ = {"extend_existing": True}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"))
    upgraded_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    upgrade_type = Column(String(50), nullable=False)  # to_organization, billing_enabled
    upgrade_data = Column(JSONB)  # Store upgrade-specific data
    upgraded_at = Column(DateTime, default=func.now())
    status = Column(String(50), default="completed")  # pending, completed, failed, reverted

    # Relationships
    team = relationship("Team")
    organization = relationship("Organization")
    upgraded_by = relationship("User")
