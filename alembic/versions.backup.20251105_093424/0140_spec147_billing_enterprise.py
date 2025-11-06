#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""SPEC-147: Enterprise-grade billing schema

Revision ID: 0139_spec147
Revises: 0138_add_team_provenance_columns
Create Date: 2025-11-04 22:20:00

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = "0140_spec147"
down_revision = "0139_drop_spec026"
branch_labels = None
depends_on = None


def upgrade():
    """Create SPEC-147 enterprise billing schema"""

    # 1. billing_accounts - Polymorphic billing for Org/Team/User
    op.create_table(
        "billing_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("account_type", sa.String(20), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plan_tier", sa.String(20), nullable=False, server_default="free"),
        sa.Column("currency", sa.CHAR(3), nullable=False, server_default="USD"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("account_type IN ('organization', 'team', 'user')", name="check_account_type"),
        sa.CheckConstraint("plan_tier IN ('free', 'starter', 'pro', 'enterprise')", name="check_plan_tier"),
        sa.CheckConstraint("char_length(currency) = 3", name="check_currency_length"),
        sa.CheckConstraint("status IN ('active', 'suspended', 'canceled', 'deleted')", name="check_status"),
        sa.CheckConstraint(
            "(status = 'deleted' AND deleted_at IS NOT NULL) OR (status != 'deleted' AND deleted_at IS NULL)",
            name="check_deleted_status",
        ),
        sa.UniqueConstraint("account_type", "account_id", name="uq_billing_account_entity"),
    )

    op.create_index("idx_billing_account_lookup", "billing_accounts", ["account_type", "account_id"])
    op.create_index(
        "idx_billing_account_active", "billing_accounts", ["id"], postgresql_where=sa.text("status != 'deleted'")
    )
    op.create_index("idx_billing_account_currency", "billing_accounts", ["currency", "plan_tier"])

    # 2. pricing_tiers - Multi-currency pricing configuration
    op.create_table(
        "pricing_tiers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("plan_tier", sa.String(20), nullable=False),
        sa.Column("resource_type", sa.String(20), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("region", sa.String(50), nullable=False, server_default="global"),
        sa.Column("quota_limit", sa.BigInteger, nullable=False),
        sa.Column("overage_rate", sa.Numeric(10, 4), nullable=False),
        sa.Column("base_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_to", sa.DateTime(timezone=True)),
        sa.CheckConstraint("resource_type IN ('storage', 'retrieval', 'token')", name="check_resource_type"),
        sa.CheckConstraint("quota_limit >= 0", name="check_quota_limit_positive"),
        sa.CheckConstraint("overage_rate >= 0", name="check_overage_rate_positive"),
        sa.CheckConstraint("base_price >= 0", name="check_base_price_positive"),
        sa.UniqueConstraint(
            "plan_tier", "resource_type", "currency", "region", "effective_from", name="uq_pricing_tier_config"
        ),
    )

    op.create_index(
        "idx_pricing_tiers_lookup",
        "pricing_tiers",
        ["plan_tier", "currency", "region", "effective_from", "effective_to"],
    )

    # 3. usage_quotas - Three-dimensional quota limits
    op.create_table(
        "usage_quotas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("billing_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(20), nullable=False),
        sa.Column("quota_limit", sa.BigInteger, nullable=False),
        sa.Column("quota_used", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("overage_rate", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["billing_account_id"], ["billing_accounts.id"], ondelete="CASCADE"),
        sa.CheckConstraint("resource_type IN ('storage', 'retrieval', 'token')", name="check_quota_resource_type"),
        sa.CheckConstraint("quota_limit >= 0", name="check_quota_limit_non_negative"),
        sa.CheckConstraint("quota_used >= 0", name="check_quota_used_non_negative"),
        sa.CheckConstraint("period_start < period_end", name="check_quota_period_valid"),
        sa.UniqueConstraint("billing_account_id", "resource_type", "period_start", name="uq_usage_quota_period"),
    )

    op.create_index("idx_usage_quota_account", "usage_quotas", ["billing_account_id", "resource_type"])
    op.create_index(
        "idx_quota_active_lookup", "usage_quotas", ["billing_account_id", "resource_type", "period_start", "period_end"]
    )

    # 4. billing_periods - Monthly billing cycles
    op.create_table(
        "billing_periods",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("billing_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("period_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("period_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("usage_summary", postgresql.JSONB),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["billing_account_id"], ["billing_accounts.id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('active', 'closed', 'invoiced')", name="check_period_status"),
        sa.CheckConstraint("period_start < period_end", name="check_billing_period_valid"),
        sa.UniqueConstraint("billing_account_id", "period_start", name="uq_billing_period"),
    )

    op.create_index("idx_billing_period_account", "billing_periods", ["billing_account_id", "period_start"])

    # 5. usage_events - Partitioned usage tracking (will be partitioned separately)
    op.execute(
        """
        CREATE TABLE usage_events (
            id UUID DEFAULT gen_random_uuid(),
            billing_account_id UUID NOT NULL REFERENCES billing_accounts(id) ON DELETE CASCADE,
            billing_period_id UUID NOT NULL REFERENCES billing_periods(id),
            resource_type VARCHAR(20) NOT NULL CHECK (resource_type IN ('storage', 'retrieval', 'token')),
            quantity BIGINT NOT NULL CHECK (quantity > 0),
            cost_at_record_time NUMERIC(10,4),
            metadata JSONB,
            recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            processed BOOLEAN NOT NULL DEFAULT FALSE,
            PRIMARY KEY (id, recorded_at)
        ) PARTITION BY RANGE (recorded_at)
    """
    )

    # Create initial partitions for current and next month
    op.execute(
        """
        CREATE TABLE usage_events_2025_11 PARTITION OF usage_events
        FOR VALUES FROM ('2025-11-01') TO ('2025-12-01')
    """
    )

    op.execute(
        """
        CREATE TABLE usage_events_2025_12 PARTITION OF usage_events
        FOR VALUES FROM ('2025-12-01') TO ('2026-01-01')
    """
    )

    op.create_index("idx_usage_event_account_time", "usage_events", ["billing_account_id", "recorded_at"])
    op.create_index(
        "idx_usage_event_period", "usage_events", ["billing_period_id"], postgresql_where=sa.text("NOT processed")
    )
    op.create_index(
        "idx_usage_event_cost",
        "usage_events",
        ["billing_account_id", "cost_at_record_time"],
        postgresql_where=sa.text("cost_at_record_time IS NOT NULL"),
    )

    # Continue in next part...


def downgrade():
    """Drop SPEC-147 billing schema"""

    # Drop in reverse order
    op.drop_table("usage_events")
    op.drop_table("billing_periods")
    op.drop_table("usage_quotas")
    op.drop_table("pricing_tiers")
    op.drop_table("billing_accounts")
