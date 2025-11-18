#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Staff Management System - SPEC-085

Revision ID: 0112
Revises: 0111
Create Date: 2024-10-03 10:15:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0112_staff_management"
down_revision = "0111_memory_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create staff table
    op.create_table(
        "staff",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False),
        sa.Column("department", sa.String(100)),
        sa.Column("phone", sa.String(50)),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column("created_by", postgresql.UUID(as_uuid=True)),
        sa.Column("last_login", sa.TIMESTAMP),
        sa.Column("last_login_ip", sa.String(45)),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("deactivated_at", sa.TIMESTAMP),
        sa.Column("deactivated_by", postgresql.UUID(as_uuid=True)),
        sa.Column("notes", sa.Text),
        sa.CheckConstraint("role IN ('support', 'ops', 'analyst', 'admin')", name="staff_role_check"),
    )

    # Create indexes for staff table
    op.create_index("idx_staff_email", "staff", ["email"])
    op.create_index("idx_staff_role", "staff", ["role"])
    op.create_index("idx_staff_active", "staff", ["is_active"])

    # Create foreign key constraints
    op.create_foreign_key("fk_staff_created_by", "staff", "staff", ["created_by"], ["id"])
    op.create_foreign_key("fk_staff_deactivated_by", "staff", "staff", ["deactivated_by"], ["id"])

    # Create staff_activity_log table
    op.create_table(
        "staff_activity_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("staff_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(50)),
        sa.Column("resource_id", sa.String(255)),
        sa.Column("details", postgresql.JSONB),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )

    # Create indexes for staff_activity_log
    op.create_index("idx_staff_activity_staff", "staff_activity_log", ["staff_id"])
    op.create_index("idx_staff_activity_created", "staff_activity_log", ["created_at"])
    op.create_index("idx_staff_activity_action", "staff_activity_log", ["action"])

    # Create foreign key for staff_activity_log
    op.create_foreign_key("fk_staff_activity_staff", "staff_activity_log", "staff", ["staff_id"], ["id"])

    # Create staff_permissions table
    op.create_table(
        "staff_permissions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("staff_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("permission", sa.String(100), nullable=False),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True)),
        sa.Column("granted_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column("expires_at", sa.TIMESTAMP),
        sa.UniqueConstraint("staff_id", "permission", name="uq_staff_permission"),
    )

    # Create index for staff_permissions
    op.create_index("idx_staff_permissions_staff", "staff_permissions", ["staff_id"])

    # Create foreign keys for staff_permissions
    op.create_foreign_key("fk_staff_permissions_staff", "staff_permissions", "staff", ["staff_id"], ["id"])
    op.create_foreign_key(
        "fk_staff_permissions_granted_by",
        "staff_permissions",
        "staff",
        ["granted_by"],
        ["id"],
    )


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("staff_permissions")
    op.drop_table("staff_activity_log")
    op.drop_table("staff")
