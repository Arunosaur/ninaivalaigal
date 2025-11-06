#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Add lead_user_id column to teams table

Revision ID: 0135_add_team_lead_user
Revises: 0134_add_team_governance_status
Create Date: 2025-11-02 05:16:00.000000

TenancyGuard Integration Test Fix - Final Schema Alignment

This migration adds the missing lead_user_id column to the teams table,
which is expected by the Team model in TenancyGuard integration tests.

Changes:
--------
- Add lead_user_id column (nullable UUID, foreign key to users)
- Add index for faster lookups
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0135_add_team_lead_user"
down_revision = "0134_add_password_reset_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add lead_user_id column to teams table."""

    # Add lead_user_id column
    op.add_column(
        "teams",
        sa.Column("lead_user_id", UUID(as_uuid=True), nullable=True),
    )

    # Add foreign key constraint to users table
    op.create_foreign_key("teams_lead_user_id_fkey", "teams", "users", ["lead_user_id"], ["id"], ondelete="SET NULL")

    # Add index for faster lookups
    op.create_index(
        "ix_teams_lead_user_id",
        "teams",
        ["lead_user_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove lead_user_id column from teams table."""

    # Drop index first
    op.drop_index("ix_teams_lead_user_id", table_name="teams")

    # Drop foreign key constraint
    op.drop_constraint("teams_lead_user_id_fkey", "teams", type_="foreignkey")

    # Drop column
    op.drop_column("teams", "lead_user_id")
