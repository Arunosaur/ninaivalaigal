#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Add governance_type and status columns to teams table

Revision ID: 0134_add_team_governance_status
Revises: 0133_add_password_reset_columns
Create Date: 2025-11-02 04:58:00.000000

TenancyGuard Integration Test Fix

This migration adds the missing governance_type and status columns to the teams
table, which are expected by the Team model in TenancyGuard integration tests.

Changes:
--------
- Add governance_type column (nullable string, default 'standard')
- Add status column (nullable string, default 'active')
- Add indexes for common query patterns
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0134_add_team_governance_status"
down_revision = "0133_add_password_reset_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add governance_type and status columns to teams table."""

    # Add governance_type column
    op.add_column(
        "teams",
        sa.Column("governance_type", sa.String(length=50), nullable=True, server_default="standard"),
    )

    # Add status column
    op.add_column(
        "teams",
        sa.Column("status", sa.String(length=50), nullable=True, server_default="active"),
    )

    # Add indexes for common query patterns
    op.create_index(
        "ix_teams_governance_type",
        "teams",
        ["governance_type"],
        unique=False,
    )

    op.create_index(
        "ix_teams_status",
        "teams",
        ["status"],
        unique=False,
    )

    # Update existing rows to have default values
    op.execute("UPDATE teams SET governance_type = 'standard' WHERE governance_type IS NULL")
    op.execute("UPDATE teams SET status = 'active' WHERE status IS NULL")


def downgrade() -> None:
    """Remove governance_type and status columns from teams table."""

    # Drop indexes first
    op.drop_index("ix_teams_status", table_name="teams")
    op.drop_index("ix_teams_governance_type", table_name="teams")

    # Drop columns
    op.drop_column("teams", "status")
    op.drop_column("teams", "governance_type")
