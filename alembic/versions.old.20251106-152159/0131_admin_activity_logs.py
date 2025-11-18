#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Create admin activity logs table

Revision ID: 0130_admin_activity_logs
Revises: 0129_expand_alembic_version
Create Date: 2025-11-02 09:00:00.000000

SPEC-005: Admin Dashboard
US-100: Admin Activity Logging System

This migration creates the audit trail table for admin operations,
providing compliance logging for security investigations and accountability.

Changes:
--------
- Create admin_activity_log table
- Add indexes for common query patterns
- Support retention policy (via timestamp indexing)
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0131_admin_activity_logs"
down_revision = "0130_expand_alembic_version"
branch_labels = None
depends_on = None


def upgrade():
    """Create admin_activity_log table for audit trail."""

    # Create admin activity logs table using Alembic's table creation API
    op.create_table(
        "admin_activity_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        # Admin user who performed the action
        sa.Column("admin_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        # Action performed
        sa.Column("action", sa.String(100), nullable=False),
        # Target resource information
        sa.Column("target_type", sa.String(50), nullable=True),  # e.g., 'user', 'team', 'organization', 'context'
        sa.Column("target_id", UUID(as_uuid=True), nullable=True),  # UUID of target resource
        # Additional details
        sa.Column("details", JSONB, server_default="{}", nullable=False),
        # Audit metadata
        sa.Column("ip_address", sa.String(45), nullable=True),  # IPv6 support
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Create indexes for common query patterns
    op.create_index("idx_admin_activity_admin_user_id", "admin_activity_log", ["admin_user_id"])
    op.create_index("idx_admin_activity_action", "admin_activity_log", ["action"])
    op.create_index("idx_admin_activity_target_type", "admin_activity_log", ["target_type"])
    op.create_index("idx_admin_activity_target_id", "admin_activity_log", ["target_id"])
    op.create_index("idx_admin_activity_timestamp", "admin_activity_log", ["timestamp"], postgresql_using="btree")

    # Composite index for common queries (admin + timestamp)
    op.create_index(
        "idx_admin_activity_admin_timestamp",
        "admin_activity_log",
        ["admin_user_id", "timestamp"],
        postgresql_ops={"timestamp": "DESC"},
    )

    # Composite index for target queries (target_type + target_id + timestamp)
    op.create_index(
        "idx_admin_activity_target_timestamp",
        "admin_activity_log",
        ["target_type", "target_id", "timestamp"],
        postgresql_ops={"timestamp": "DESC"},
    )

    # GIN index for details JSONB queries
    op.execute("CREATE INDEX idx_admin_activity_details " "ON admin_activity_log USING gin (details)")

    # Partial index for specific admin actions (security monitoring)
    op.execute(
        "CREATE INDEX idx_admin_activity_security_actions "
        "ON admin_activity_log(admin_user_id, timestamp DESC) "
        "WHERE action IN ('delete_user', 'deactivate_user', 'change_permissions', 'override_access')"
    )


def downgrade():
    """Drop admin_activity_log table and indexes."""
    op.execute("DROP TABLE IF EXISTS admin_activity_log CASCADE;")
