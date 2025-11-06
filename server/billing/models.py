#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Clean Billing Schema - SQLAlchemy Models
# Developer D - January 2025

"""
SPEC-147 Billing Models

Unified polymorphic billing architecture supporting Organizations, Teams, and Users.
All models follow the SPEC-147 schema design.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import CHAR, INET, JSONB, UUID
from sqlalchemy.orm import relationship

# Import Base from shared models to ensure consistency
try:
    from server.database.models import Base
except ImportError:
    # Fallback for when running from different paths
    try:
        from database.models import Base
    except ImportError:
        # Last resort - create new base (shouldn't happen in normal operation)
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()


# Enums
class AccountType(str, Enum):
    """Billing account types"""

    ORGANIZATION = "organization"
    TEAM = "team"
    USER = "user"


class PlanTier(str, Enum):
    """Subscription plan tiers"""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class AccountStatus(str, Enum):
    """Billing account status"""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    CANCELED = "canceled"
    DELETED = "deleted"


class ResourceType(str, Enum):
    """Three-dimensional resource types"""

    STORAGE = "storage"
    RETRIEVAL = "retrieval"
    TOKEN = "token"


class BlockLevel(str, Enum):
    """Quota block levels"""

    SOFT = "soft"
    HARD = "hard"


class TransferStatus(str, Enum):
    """Payment transfer status"""

    ACTIVE = "active"
    GRACE = "grace"
    TRANSFERRED = "transferred"


class InvoiceStatus(str, Enum):
    """Invoice status"""

    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    VOID = "void"


class BillingPeriodStatus(str, Enum):
    """Billing period status"""

    ACTIVE = "active"
    CLOSED = "closed"
    INVOICED = "invoiced"


class BillingAccount(Base):
    """SPEC-147: Polymorphic billing account for Org/Team/User

    Supports unified billing for organizations, teams, and users
    with polymorphic design using account_type and account_id.
    """

    __tablename__ = "billing_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    account_type = Column(String(20), nullable=False, index=True)
    account_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    plan_tier = Column(String(20), nullable=False, server_default=PlanTier.FREE.value)
    currency = Column(CHAR(3), nullable=False, server_default="USD")
    status = Column(String(20), nullable=False, server_default=AccountStatus.ACTIVE.value)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    usage_quotas = relationship("UsageQuota", back_populates="billing_account", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="billing_account", cascade="all, delete-orphan")
    billing_periods = relationship("BillingPeriod", back_populates="billing_account", cascade="all, delete-orphan")
    quota_blocks = relationship("QuotaBlock", back_populates="billing_account", cascade="all, delete-orphan")
    payment_config = relationship(
        "PaymentConfig", back_populates="billing_account", uselist=False, cascade="all, delete-orphan"
    )
    invoices = relationship("Invoice", back_populates="billing_account", cascade="all, delete-orphan")
    credit_balances = relationship("CreditBalance", back_populates="billing_account", cascade="all, delete-orphan")
    discount_applications = relationship(
        "DiscountApplication", back_populates="billing_account", cascade="all, delete-orphan"
    )
    stripe_customer = relationship(
        "StripeCustomer", back_populates="billing_account", uselist=False, cascade="all, delete-orphan"
    )
    audit_logs = relationship("AuditLog", back_populates="billing_account", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("account_type IN ('organization', 'team', 'user')", name="check_account_type"),
        CheckConstraint("plan_tier IN ('free', 'starter', 'pro', 'enterprise')", name="check_plan_tier"),
        CheckConstraint("char_length(currency) = 3", name="check_currency_length"),
        CheckConstraint("status IN ('active', 'suspended', 'canceled', 'deleted')", name="check_status"),
        CheckConstraint(
            "(status = 'deleted' AND deleted_at IS NOT NULL) OR (status != 'deleted' AND deleted_at IS NULL)",
            name="check_deleted_status",
        ),
        {"comment": "SPEC-147: Polymorphic billing accounts for Org/Team/User"},
    )


class PricingTier(Base):
    """SPEC-147: Multi-currency pricing configuration"""

    __tablename__ = "pricing_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_tier = Column(String(20), nullable=False)
    resource_type = Column(String(20), nullable=False)
    currency = Column(CHAR(3), nullable=False)
    region = Column(String(50), nullable=False, server_default="global")
    quota_limit = Column(Numeric(20, 0), nullable=False)  # BigInteger as Numeric
    overage_rate = Column(Numeric(10, 4), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False)
    effective_to = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint("resource_type IN ('storage', 'retrieval', 'token')", name="check_resource_type"),
        CheckConstraint("quota_limit >= 0", name="check_quota_limit_positive"),
        CheckConstraint("overage_rate >= 0", name="check_overage_rate_positive"),
        CheckConstraint("base_price >= 0", name="check_base_price_positive"),
    )


class UsageQuota(Base):
    """SPEC-147: Three-dimensional usage quotas (storage/retrieval/token)"""

    __tablename__ = "usage_quotas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_account_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    resource_type = Column(String(20), nullable=False, index=True)
    quota_limit = Column(Numeric(20, 0), nullable=False)  # BigInteger as Numeric
    quota_used = Column(Numeric(20, 0), nullable=False, server_default="0")
    overage_rate = Column(Numeric(10, 4), nullable=False, server_default="0")
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    billing_account = relationship("BillingAccount", back_populates="usage_quotas")
    quota_blocks = relationship("QuotaBlock", back_populates="usage_quota")

    __table_args__ = (
        CheckConstraint("resource_type IN ('storage', 'retrieval', 'token')", name="check_quota_resource_type"),
        CheckConstraint("quota_limit >= 0", name="check_quota_limit_non_negative"),
        CheckConstraint("quota_used >= 0", name="check_quota_used_non_negative"),
        CheckConstraint("period_start < period_end", name="check_quota_period_valid"),
        {"comment": "SPEC-147: Three-dimensional usage quotas (storage/retrieval/token)"},
    )


class BillingPeriod(Base):
    """SPEC-147: Monthly billing cycles"""

    __tablename__ = "billing_periods"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_account_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(20), nullable=False, server_default=BillingPeriodStatus.ACTIVE.value)
    usage_summary = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    billing_account = relationship("BillingAccount", back_populates="billing_periods")
    usage_events = relationship("UsageEvent", back_populates="billing_period")
    invoices = relationship("Invoice", back_populates="billing_period")

    __table_args__ = (
        CheckConstraint("status IN ('active', 'closed', 'invoiced')", name="check_period_status"),
        CheckConstraint("period_start < period_end", name="check_billing_period_valid"),
    )


class UsageEvent(Base):
    """SPEC-147: Partitioned usage event tracking

    Note: This table is partitioned by recorded_at. The partition key
    is included in the primary key for partitioned tables.
    """

    __tablename__ = "usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_account_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    billing_period_id = Column(UUID(as_uuid=True), ForeignKey("billing_periods.id"), nullable=False, index=True)
    resource_type = Column(String(20), nullable=False)
    quantity = Column(Numeric(20, 0), nullable=False)  # BigInteger as Numeric
    cost_at_record_time = Column(Numeric(10, 4), nullable=True)
    event_metadata = Column("metadata", JSONB, nullable=True)
    recorded_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    processed = Column(Boolean, nullable=False, server_default=text("false"))

    # Relationships
    billing_account = relationship("BillingAccount", back_populates="usage_events")
    billing_period = relationship("BillingPeriod", back_populates="usage_events")

    __table_args__ = (
        CheckConstraint("resource_type IN ('storage', 'retrieval', 'token')", name="check_usage_event_resource_type"),
        CheckConstraint("quantity > 0", name="check_usage_event_quantity_positive"),
        {"comment": "SPEC-147: Partitioned usage event tracking with cost audit"},
    )


class QuotaBlock(Base):
    """SPEC-147: Soft/hard quota enforcement records"""

    __tablename__ = "quota_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_account_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    usage_quota_id = Column(UUID(as_uuid=True), ForeignKey("usage_quotas.id", ondelete="SET NULL"), nullable=True)
    block_level = Column(String(10), nullable=False)
    reason = Column(Text, nullable=False)
    blocked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    unblocked_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    event_metadata = Column("metadata", JSONB, nullable=True)

    # Relationships
    billing_account = relationship("BillingAccount", back_populates="quota_blocks")
    usage_quota = relationship("UsageQuota", back_populates="quota_blocks")

    __table_args__ = (
        CheckConstraint("block_level IN ('soft', 'hard')", name="check_block_level"),
        {"comment": "SPEC-147: Soft/hard quota enforcement records"},
    )


class PaymentConfig(Base):
    """SPEC-147: Payment responsibility with 30-day grace period"""

    __tablename__ = "payment_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("billing_accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    primary_payer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    backup_payer_ids = Column(JSONB, nullable=False, server_default="[]")
    payment_method_id = Column(String(255), nullable=True)
    billing_address = Column(JSONB, nullable=True)
    billing_email = Column(String(255), nullable=False)
    grace_period_start = Column(DateTime(timezone=True), nullable=True)
    grace_period_end = Column(DateTime(timezone=True), nullable=True)
    transfer_status = Column(String(20), nullable=False, server_default=TransferStatus.ACTIVE.value)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    billing_account = relationship("BillingAccount", back_populates="payment_config")
    payment_transfers = relationship("PaymentTransfer", back_populates="payment_config")

    __table_args__ = (
        CheckConstraint("transfer_status IN ('active', 'grace', 'transferred')", name="check_transfer_status"),
        {"comment": "SPEC-147: Payment responsibility with 30-day grace period"},
    )


class PaymentTransfer(Base):
    """SPEC-147: Payment transfer history"""

    __tablename__ = "payment_transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_config_id = Column(
        UUID(as_uuid=True), ForeignKey("payment_configs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    from_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reason = Column(String(50), nullable=False)
    initiated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, server_default="pending")

    # Relationships
    payment_config = relationship("PaymentConfig", back_populates="payment_transfers")

    __table_args__ = (
        CheckConstraint("reason IN ('left_team', 'reassigned', 'voluntary')", name="check_transfer_reason"),
        CheckConstraint("status IN ('pending', 'completed', 'failed')", name="check_transfer_status_value"),
    )


class Invoice(Base):
    """SPEC-147: Versioned invoices with multi-currency support"""

    __tablename__ = "invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_period_id = Column(UUID(as_uuid=True), ForeignKey("billing_periods.id"), nullable=False)
    billing_account_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invoice_number = Column(String(50), nullable=False)
    revision = Column(Integer, nullable=False, server_default="1")
    subtotal = Column(Numeric(10, 2), nullable=False)
    credits_applied = Column(Numeric(10, 2), nullable=False, server_default="0")
    discounts_applied = Column(Numeric(10, 2), nullable=False, server_default="0")
    tax_amount = Column(Numeric(10, 2), nullable=False, server_default="0")
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(CHAR(3), nullable=False)
    status = Column(String(20), nullable=False, server_default=InvoiceStatus.DRAFT.value)
    issued_at = Column(DateTime(timezone=True), nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    billing_period = relationship("BillingPeriod", back_populates="invoices")
    billing_account = relationship("BillingAccount", back_populates="invoices")
    line_items = relationship("InvoiceLineItem", back_populates="invoice", cascade="all, delete-orphan")
    stripe_invoice = relationship(
        "StripeInvoice", back_populates="invoice", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("status IN ('draft', 'issued', 'paid', 'void')", name="check_invoice_status"),
        {"comment": "SPEC-147: Versioned invoices with multi-currency support"},
    )


class InvoiceLineItem(Base):
    """SPEC-147: Invoice line item details"""

    __tablename__ = "invoice_line_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(20), nullable=False)
    description = Column(Text, nullable=False)
    quantity = Column(Numeric(20, 0), nullable=False)  # BigInteger as Numeric
    unit_price = Column(Numeric(10, 4), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    is_overage = Column(Boolean, nullable=False, server_default=text("false"))

    # Relationships
    invoice = relationship("Invoice", back_populates="line_items")

    __table_args__ = (
        CheckConstraint("resource_type IN ('storage', 'retrieval', 'token')", name="check_line_item_resource_type"),
        CheckConstraint("quantity > 0", name="check_line_item_quantity_positive"),
        CheckConstraint("amount >= 0", name="check_line_item_amount_non_negative"),
    )


class CreditBalance(Base):
    """SPEC-147: Credit balance tracking"""

    __tablename__ = "credit_balances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_account_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount = Column(Numeric(10, 2), nullable=False)
    used_amount = Column(Numeric(10, 2), nullable=False, server_default="0")
    reason = Column(Text, nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    billing_account = relationship("BillingAccount", back_populates="credit_balances")

    __table_args__ = (
        CheckConstraint("amount > 0", name="check_credit_amount_positive"),
        CheckConstraint("used_amount >= 0", name="check_credit_used_non_negative"),
        CheckConstraint("used_amount <= amount", name="check_credit_used_valid"),
    )


class DiscountCode(Base):
    """SPEC-147: Discount code management

    Note: This replaces the SPEC-026 DiscountCode model.
    The table is extended with SPEC-147 enhancements.

    Since the table already exists from SPEC-026, we use extend_existing
    to allow SQLAlchemy to extend the existing table definition.
    """

    __tablename__ = "discount_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True, index=True)
    percent_off = Column(Integer, nullable=True)
    amount_off = Column(Integer, nullable=True)  # In cents
    expires_at = Column(DateTime(timezone=True), nullable=True)
    usage_limit = Column(Integer, nullable=True)
    used_count = Column(Integer, nullable=False, server_default="0")
    is_active = Column(Boolean, nullable=False, server_default=text("true"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    applications = relationship(
        "server.billing.models.DiscountApplication", back_populates="discount_code", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint("percent_off >= 1 AND percent_off <= 100", name="check_percent_off_range"),
        CheckConstraint("amount_off >= 1", name="check_amount_off_positive"),
        CheckConstraint(
            "(percent_off IS NOT NULL AND amount_off IS NULL) OR (percent_off IS NULL AND amount_off IS NOT NULL)",
            name="check_discount_type",
        ),
        {"extend_existing": True, "comment": "SPEC-147: Discount code management (replaces SPEC-026)"},
    )


class DiscountApplication(Base):
    """SPEC-147: Applied discount codes"""

    __tablename__ = "discount_applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    discount_code_id = Column(UUID(as_uuid=True), ForeignKey("discount_codes.id", ondelete="CASCADE"), nullable=False)
    billing_account_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    applied_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    applied_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    discount_code = relationship("server.billing.models.DiscountCode", back_populates="applications")
    billing_account = relationship("BillingAccount", back_populates="discount_applications")


class StripeCustomer(Base):
    """SPEC-147: Stripe customer sync"""

    __tablename__ = "stripe_customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("billing_accounts.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    stripe_customer_id = Column(String(255), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False)
    event_metadata = Column("metadata", JSONB, nullable=True)
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    billing_account = relationship("BillingAccount", back_populates="stripe_customer")
    subscriptions = relationship("StripeSubscription", back_populates="stripe_customer", cascade="all, delete-orphan")


class StripeSubscription(Base):
    """SPEC-147: Stripe subscription sync"""

    __tablename__ = "stripe_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stripe_customer_id = Column(
        UUID(as_uuid=True), ForeignKey("stripe_customers.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stripe_subscription_id = Column(String(255), nullable=False, unique=True, index=True)
    plan_id = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end = Column(Boolean, nullable=False, server_default=text("false"))
    last_synced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    stripe_customer = relationship("StripeCustomer", back_populates="subscriptions")

    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'past_due', 'canceled', 'trialing', 'incomplete')",
            name="check_stripe_subscription_status",
        ),
    )


class StripeInvoice(Base):
    """SPEC-147: Stripe invoice sync"""

    __tablename__ = "stripe_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    stripe_invoice_id = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(String(20), nullable=False)
    synced_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    invoice = relationship("Invoice", back_populates="stripe_invoice")

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'open', 'paid', 'void', 'uncollectible')", name="check_stripe_invoice_status"
        ),
    )


class AuditLog(Base):
    """SPEC-147: Immutable audit trail with event hashing"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    billing_account_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSONB, nullable=False)
    event_hash = Column(String(64), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    ip_address = Column(INET, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)

    # Relationships
    billing_account = relationship("BillingAccount", back_populates="audit_logs")

    __table_args__ = {"comment": "SPEC-147: Immutable audit trail with event hashing"}

    # Note: Immutability is enforced by database rule (audit_log_no_update)
    # This prevents updates at the SQL level


class BillingEvent(Base):
    """SPEC-147: Event sourcing for observability and ML"""

    __tablename__ = "billing_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False, index=True)
    aggregate_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    aggregate_type = Column(String(20), nullable=False, index=True)
    event_data = Column(JSONB, nullable=False)
    event_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    published_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "event_type IN ('usage.recorded', 'quota.exceeded', 'invoice.generated', 'payment.transferred', 'block.applied', 'block.removed')",
            name="check_billing_event_type",
        ),
        CheckConstraint(
            "aggregate_type IN ('billing_account', 'invoice', 'quota', 'payment')", name="check_aggregate_type"
        ),
        {"comment": "SPEC-147: Event sourcing for observability and ML"},
    )
