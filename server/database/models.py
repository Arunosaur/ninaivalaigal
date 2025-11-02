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
from enum import Enum

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
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

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
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

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
    teams = relationship("Team", back_populates="organization")
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

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    organization = relationship("Organization", foreign_keys=[organization_id], back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
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

class DiscountCode(Base):
    """Discount code model - discount codes for teams per US#157

    Supports both percentage and fixed amount discounts.
    Part of SPEC-026: Standalone Teams and Billing Phase 1.
    """

    __tablename__ = "discount_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    percent_off = Column(Integer, nullable=True)  # 1-100
    amount_off = Column(Integer, nullable=True)  # in cents
    expires_at = Column(DateTime, nullable=True, index=True)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    usages = relationship("DiscountCodeUsage", back_populates="discount_code", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("percent_off >= 1 AND percent_off <= 100", name="check_percent_off_range"),
        CheckConstraint("amount_off >= 1", name="check_amount_off_positive"),
        CheckConstraint("usage_limit >= 1", name="check_usage_limit_positive"),
        CheckConstraint("used_count >= 0", name="check_used_count_non_negative"),
        CheckConstraint(
            "(percent_off IS NOT NULL AND amount_off IS NULL) OR (percent_off IS NULL AND amount_off IS NOT NULL)",
            name="discount_type_check",
        ),
        CheckConstraint("usage_limit IS NULL OR used_count <= usage_limit", name="usage_limit_check"),
        {"comment": "Discount codes for billing (US#157, SPEC-026)"},
    )


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
    team_credit_id = Column(UUID(as_uuid=True), ForeignKey("team_credits.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    balance_before = Column(Numeric(10, 2), nullable=False)
    balance_after = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=False)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("billing_invoices.id"), nullable=True, index=True)
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


class DiscountCodeUsage(Base):
    """Discount code usage tracking model

    Tracks when and how discount codes are applied.
    Part of SPEC-026: Standalone Teams and Billing Phase 1.
    """

    __tablename__ = "discount_code_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    discount_code_id = Column(UUID(as_uuid=True), ForeignKey("discount_codes.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=True, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)
    invoice_id = Column(String(255), nullable=True)  # Reference to billing_invoices table (model not yet created)
    amount_discounted = Column(Numeric(10, 2), nullable=False)
    used_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    discount_code = relationship("DiscountCode", back_populates="usages")
    team = relationship("Team", foreign_keys=[team_id])
    organization = relationship("Organization", foreign_keys=[org_id])

    # Constraints
    __table_args__ = (
        CheckConstraint("amount_discounted >= 0", name="check_amount_discounted_non_negative"),
        CheckConstraint(
            "(team_id IS NOT NULL AND org_id IS NULL) OR (team_id IS NULL AND org_id IS NOT NULL)",
            name="discount_usage_target_check",
        ),
        {"comment": "Discount code usage tracking (US#157, SPEC-026)"},
    )
