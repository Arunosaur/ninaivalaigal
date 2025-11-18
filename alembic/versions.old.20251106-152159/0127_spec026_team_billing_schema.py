#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Add SPEC-026 Team Billing Schema (US#156, US#157, US#158)

Revision ID: 0126_spec026_team_billing_schema
Revises: 0125_context_sharing_audit_logs
Create Date: 2025-11-01 20:30:00.000000

SPEC-026: Standalone Teams & Flexible Billing System
US#156: Team Billing Schema Design
US#157: Discount & Credit System Schema
US#158: Non-Profit Application System Schema

This migration creates the database schema for team billing infrastructure,
including team billing tables, discount codes, credit system, and non-profit
application workflow.

Changes:
--------
US#156:
- Create team_billing table (Stripe customer integration)
- Create team_subscriptions table (plan management)
- Create team_usage_metrics table (usage tracking)

US#157:
- Create discount_codes table (discount code management)
- Create team_credits table (credit balance tracking)
- Create credit_transactions table (audit trail)
- Create discount_code_usage table (redemption tracking)

US#158:
- Create nonprofit_applications table (non-profit workflow)

All tables include:
- Foreign key constraints with CASCADE delete
- Performance indexes on key columns
- CHECK constraints for data integrity
- UUID primary keys with gen_random_uuid()
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "0127_spec026_team_billing_schema"
down_revision = "0126_context_sharing_audit_logs"
branch_labels = None
depends_on = None


def upgrade():
    """Create SPEC-026 billing schema tables."""

    # US#156: Team Billing Core Tables

    # Team billing table - core billing information
    op.create_table(
        "team_billing",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            unique=True,
            nullable=False,
            index=True,
        ),
        sa.Column("stripe_customer_id", sa.String(255), unique=True, index=True, nullable=True),
        sa.Column("billing_email", sa.String(255), nullable=False),
        sa.Column("payment_method_id", sa.String(255), nullable=True),
        sa.Column("default_payment_method", sa.String(255), nullable=True),
        sa.Column("billing_address", JSONB, nullable=True),
        sa.Column("tax_id", sa.String(50), nullable=True),
        sa.Column("currency", sa.String(3), server_default="USD", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Index("idx_team_billing_team_id", "team_id"),
        sa.Index("idx_team_billing_stripe_customer_id", "stripe_customer_id"),
        comment="Team billing information with Stripe integration (US#156, SPEC-026)",
    )

    # Team subscriptions table - plan management
    op.create_table(
        "team_subscriptions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("plan_id", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), server_default="active", nullable=False),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trial_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trial_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_at_period_end", sa.Boolean, server_default=sa.false(), nullable=False),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("subscription_metadata", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Index("idx_team_subscriptions_team_id", "team_id"),
        sa.Index("idx_team_subscriptions_status", "status"),
        sa.CheckConstraint("current_period_start <= current_period_end", name="check_subscription_period"),
        comment="Team subscription plans and billing periods (US#156, SPEC-026)",
    )

    # Team usage metrics table - tracking
    op.create_table(
        "team_usage_metrics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "team_id",
            UUID(as_uuid=True),
            sa.ForeignKey("teams.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("memory_count", sa.BigInteger, server_default="0", nullable=False),
        sa.Column("api_calls", sa.BigInteger, server_default="0", nullable=False),
        sa.Column("storage_bytes", sa.BigInteger, server_default="0", nullable=False),
        sa.Column("context_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("member_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Index("idx_team_usage_metrics_team_id", "team_id"),
        sa.Index("idx_team_usage_metrics_period", "team_id", "period_start", "period_end"),
        sa.CheckConstraint("memory_count >= 0", name="check_memory_count_non_negative"),
        sa.CheckConstraint("api_calls >= 0", name="check_api_calls_non_negative"),
        sa.CheckConstraint("storage_bytes >= 0", name="check_storage_bytes_non_negative"),
        sa.CheckConstraint("context_count >= 0", name="check_context_count_non_negative"),
        sa.CheckConstraint("member_count >= 0", name="check_member_count_non_negative"),
        sa.CheckConstraint("period_start <= period_end", name="usage_period_check"),
        comment="Team usage metrics tracking (US#156, SPEC-026)",
    )

    # US#157: Discount & Credit System Tables

    # Discount codes table
    op.create_table(
        "discount_codes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(50), unique=True, nullable=False),
        sa.Column("percent_off", sa.Integer, nullable=True),
        sa.Column("amount_off", sa.Integer, nullable=True),  # in cents
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("usage_limit", sa.Integer, nullable=True),
        sa.Column("used_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.true(), nullable=False),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint("percent_off >= 1 AND percent_off <= 100", name="check_percent_off_range"),
        sa.CheckConstraint("amount_off >= 1", name="check_amount_off_positive"),
        sa.CheckConstraint("usage_limit >= 1", name="check_usage_limit_positive"),
        sa.CheckConstraint("used_count >= 0", name="check_used_count_non_negative"),
        sa.CheckConstraint(
            "(percent_off IS NOT NULL AND amount_off IS NULL) OR (percent_off IS NULL AND amount_off IS NOT NULL)",
            name="discount_type_check",
        ),
        sa.CheckConstraint("usage_limit IS NULL OR used_count <= usage_limit", name="usage_limit_check"),
        comment="Discount codes for billing (US#157, SPEC-026)",
    )
    op.create_index("idx_discount_codes_code", "discount_codes", ["code"], postgresql_where=text("is_active = TRUE"))
    op.create_index(
        "idx_discount_codes_expires_at", "discount_codes", ["expires_at"], postgresql_where=text("is_active = TRUE")
    )

    # Team credits table
    op.create_table(
        "team_credits",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("used_amount", sa.Numeric(10, 2), server_default="0", nullable=False),
        sa.Column(
            "remaining_amount", sa.Numeric(10, 2), server_computed=sa.text("amount - used_amount"), nullable=True
        ),
        sa.Column("granted_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint("amount > 0", name="check_amount_positive"),
        sa.CheckConstraint("used_amount >= 0", name="check_used_amount_non_negative"),
        sa.CheckConstraint("used_amount <= amount", name="used_amount_check"),
        sa.CheckConstraint(
            "(team_id IS NOT NULL AND org_id IS NULL) OR (team_id IS NULL AND org_id IS NOT NULL)",
            name="credit_target_check",
        ),
        comment="Team credits for billing (US#157, SPEC-026)",
    )
    op.create_index(
        "idx_team_credits_team_id", "team_credits", ["team_id"], postgresql_where=text("team_id IS NOT NULL")
    )
    op.create_index("idx_team_credits_org_id", "team_credits", ["org_id"], postgresql_where=text("org_id IS NOT NULL"))
    op.create_index("idx_team_credits_expires_at", "team_credits", ["expires_at"])

    # Credit transactions table - audit trail
    op.create_table(
        "credit_transactions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "team_credit_id",
            UUID(as_uuid=True),
            sa.ForeignKey("team_credits.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("transaction_type", sa.String(20), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("balance_before", sa.Numeric(10, 2), nullable=False),
        sa.Column("balance_after", sa.Numeric(10, 2), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("performed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("invoice_id", sa.String(255), nullable=True),  # Reference to billing_invoices (model not yet created)
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint("amount > 0", name="check_amount_positive"),
        sa.CheckConstraint("balance_before >= 0", name="check_balance_before_non_negative"),
        sa.CheckConstraint("balance_after >= 0", name="check_balance_after_non_negative"),
        sa.CheckConstraint(
            "transaction_type IN ('grant', 'deduct', 'expire', 'refund')", name="check_transaction_type"
        ),
        sa.CheckConstraint(
            "(transaction_type = 'grant' AND balance_after = balance_before + amount) OR "
            "(transaction_type = 'deduct' AND balance_after = balance_before - amount) OR "
            "(transaction_type = 'expire' AND balance_after = balance_before - amount) OR "
            "(transaction_type = 'refund' AND balance_after = balance_before + amount)",
            name="balance_consistency_check",
        ),
        comment="Credit transaction audit trail (US#157, SPEC-026)",
    )
    op.create_index("idx_credit_transactions_credit_id", "credit_transactions", ["team_credit_id"])
    op.create_index("idx_credit_transactions_type", "credit_transactions", ["transaction_type"])
    op.create_index(
        "idx_credit_transactions_performed_by",
        "credit_transactions",
        ["performed_by"],
        postgresql_where=text("performed_by IS NOT NULL"),
    )
    op.create_index(
        "idx_credit_transactions_invoice_id",
        "credit_transactions",
        ["invoice_id"],
        postgresql_where=text("invoice_id IS NOT NULL"),
    )
    op.create_index(
        "idx_credit_transactions_created_at",
        "credit_transactions",
        ["created_at"],
        postgresql_ops={"created_at": "DESC"},
    )

    # Discount code usage tracking
    op.create_table(
        "discount_code_usage",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "discount_code_id",
            UUID(as_uuid=True),
            sa.ForeignKey("discount_codes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("invoice_id", sa.String(255), nullable=True),  # Reference to billing_invoices (model not yet created)
        sa.Column("amount_discounted", sa.Numeric(10, 2), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint("amount_discounted >= 0", name="check_amount_discounted_non_negative"),
        sa.CheckConstraint(
            "(team_id IS NOT NULL AND org_id IS NULL) OR (team_id IS NULL AND org_id IS NOT NULL)",
            name="discount_usage_target_check",
        ),
        comment="Discount code usage tracking (US#157, SPEC-026)",
    )
    op.create_index("idx_discount_code_usage_code_id", "discount_code_usage", ["discount_code_id"])
    op.create_index(
        "idx_discount_code_usage_team_id",
        "discount_code_usage",
        ["team_id"],
        postgresql_where=text("team_id IS NOT NULL"),
    )
    op.create_index(
        "idx_discount_code_usage_org_id", "discount_code_usage", ["org_id"], postgresql_where=text("org_id IS NOT NULL")
    )

    # US#158: Non-Profit Application System Table

    op.create_table(
        "nonprofit_applications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=True),
        sa.Column("org_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
        sa.Column("organization_name", sa.String(255), nullable=False),
        sa.Column("tax_id", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("website_url", sa.Text, nullable=True),
        sa.Column("documentation_urls", JSONB, nullable=True),  # Array of URLs
        sa.Column("status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected', 'under_review')", name="check_status_valid"),
        sa.CheckConstraint(
            "(team_id IS NOT NULL AND org_id IS NULL) OR (team_id IS NULL AND org_id IS NOT NULL)",
            name="nonprofit_target_check",
        ),
        comment="Non-profit application workflow (US#158, SPEC-026)",
    )
    op.create_index(
        "idx_nonprofit_applications_team_id",
        "nonprofit_applications",
        ["team_id"],
        postgresql_where=text("team_id IS NOT NULL"),
    )
    op.create_index(
        "idx_nonprofit_applications_org_id",
        "nonprofit_applications",
        ["org_id"],
        postgresql_where=text("org_id IS NOT NULL"),
    )
    op.create_index("idx_nonprofit_applications_status", "nonprofit_applications", ["status"])
    op.create_index("idx_nonprofit_applications_submitted_at", "nonprofit_applications", ["submitted_at"])


def downgrade():
    """Drop SPEC-026 billing schema tables."""

    # Drop in reverse order of dependencies
    op.drop_table("nonprofit_applications")
    op.drop_table("discount_code_usage")
    op.drop_table("credit_transactions")
    op.drop_table("team_credits")
    op.drop_table("discount_codes")
    op.drop_table("team_usage_metrics")
    op.drop_table("team_subscriptions")
    op.drop_table("team_billing")
