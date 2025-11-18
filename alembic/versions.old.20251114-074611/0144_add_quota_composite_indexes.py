"""Add composite indexes for quota enforcement queries

Revision ID: 0144
Revises: 0143
Create Date: 2025-11-10

BILL-003: Soft/hard quota enforcement with composite indexes (US#766)
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0144"
down_revision = "0143"
branch_labels = None
depends_on = None


def upgrade():
    """Add composite indexes for quota enforcement performance optimization"""

    # Composite index for quota_blocks: (billing_account_id, usage_quota_id, is_active)
    # Used in get_active_block() when querying by usage_quota_id
    op.create_index(
        "idx_quota_block_account_quota_active",
        "quota_blocks",
        ["billing_account_id", "usage_quota_id", "is_active"],
        postgresql_where=sa.text("is_active = true"),
        unique=False,
    )

    # Composite index for quota_blocks: (billing_account_id, block_level, is_active)
    # Used in create_soft_block() and create_hard_block() when checking for existing blocks
    op.create_index(
        "idx_quota_block_account_level_active",
        "quota_blocks",
        ["billing_account_id", "block_level", "is_active"],
        postgresql_where=sa.text("is_active = true"),
        unique=False,
    )

    # Partial composite index for usage_quotas: (billing_account_id, resource_type, period_start, period_end)
    # Used for active period lookups - already exists but ensure it's optimized
    # The existing idx_quota_active_lookup should cover this, but we'll add a more specific one
    op.create_index(
        "idx_usage_quota_account_resource_active",
        "usage_quotas",
        ["billing_account_id", "resource_type", "period_start", "period_end"],
        postgresql_where=sa.text("period_start <= NOW() AND period_end > NOW()"),
        unique=False,
    )

    # Composite index for usage_events: (billing_account_id, resource_type, recorded_at)
    # Used in cost tracking and usage aggregation queries
    op.create_index(
        "idx_usage_event_account_resource_time",
        "usage_events",
        ["billing_account_id", "resource_type", "recorded_at"],
        unique=False,
    )

    # Composite index for usage_events: (billing_period_id, resource_type, processed)
    # Used in usage aggregation queries
    op.create_index(
        "idx_usage_event_period_resource_processed",
        "usage_events",
        ["billing_period_id", "resource_type", "processed"],
        postgresql_where=sa.text("processed = false"),
        unique=False,
    )


def downgrade():
    """Remove composite indexes added for quota enforcement"""
    op.drop_index("idx_usage_event_period_resource_processed", table_name="usage_events")
    op.drop_index("idx_usage_event_account_resource_time", table_name="usage_events")
    op.drop_index("idx_usage_quota_account_resource_active", table_name="usage_quotas")
    op.drop_index("idx_quota_block_account_level_active", table_name="quota_blocks")
    op.drop_index("idx_quota_block_account_quota_active", table_name="quota_blocks")
