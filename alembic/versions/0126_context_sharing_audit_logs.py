#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Create context sharing audit logs table

Revision ID: 0125_context_sharing_audit_logs
Revises: 0124_memory_schema
Create Date: 2025-11-01 12:00:00.000000

SPEC-004: Team Collaboration
US-94: Context Sharing Audit Trail

This migration creates the audit trail table for context sharing operations,
providing compliance logging for security investigations and access tracking.

Changes:
--------
- Create context_sharing_audit_logs table
- Add indexes for common query patterns
- Support 90-day retention policy (via timestamp indexing)
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0126_context_sharing_audit_logs"
down_revision = "0125_memory_schema"
branch_labels = None
depends_on = None


def upgrade():
    """Create context_sharing_audit_logs table for audit trail."""

    # Create audit logs table using Alembic's table creation API
    op.create_table(
        "context_sharing_audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("context_id", UUID(as_uuid=True), sa.ForeignKey("contexts.id", ondelete="CASCADE"), nullable=False),
        # Action performed
        sa.Column("action", sa.String(50), nullable=False),
        # Actor (who performed the action)
        sa.Column("actor_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        # Target (who/what was affected)
        sa.Column("target_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column(
            "target_organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
        # Permission changes
        sa.Column("old_permission_level", sa.String(50), nullable=True),
        sa.Column("new_permission_level", sa.String(50), nullable=True),
        # Audit metadata
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),  # IPv6 support
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata", JSONB, server_default="{}", nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Add check constraint for action values
    op.execute(
        "ALTER TABLE context_sharing_audit_logs ADD CONSTRAINT check_action "
        "CHECK (action IN ('share', 'unshare', 'permission_change', 'access_granted', 'access_denied'))"
    )

    # Create indexes for common query patterns
    op.create_index("idx_context_sharing_audit_context_id", "context_sharing_audit_logs", ["context_id"])
    op.create_index("idx_context_sharing_audit_actor_user_id", "context_sharing_audit_logs", ["actor_user_id"])
    op.create_index("idx_context_sharing_audit_target_user_id", "context_sharing_audit_logs", ["target_user_id"])
    op.create_index("idx_context_sharing_audit_action", "context_sharing_audit_logs", ["action"])
    op.create_index(
        "idx_context_sharing_audit_timestamp", "context_sharing_audit_logs", ["timestamp"], postgresql_using="btree"
    )

    # Composite index for common queries (context + timestamp)
    op.create_index(
        "idx_context_sharing_audit_context_timestamp",
        "context_sharing_audit_logs",
        ["context_id", "timestamp"],
        postgresql_ops={"timestamp": "DESC"},
    )

    # Partial index for access denied queries (security monitoring)
    op.execute(
        "CREATE INDEX idx_context_sharing_audit_denied "
        "ON context_sharing_audit_logs(context_id, timestamp DESC) "
        "WHERE action = 'access_denied'"
    )

    # GIN index for metadata JSONB queries
    op.execute("CREATE INDEX idx_context_sharing_audit_metadata " "ON context_sharing_audit_logs USING gin (metadata)")


def downgrade():
    """Drop context_sharing_audit_logs table and indexes."""
    op.execute("DROP TABLE IF EXISTS context_sharing_audit_logs CASCADE;")
