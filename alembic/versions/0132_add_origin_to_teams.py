#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Add origin column to teams table for TenancyGuard

Revision ID: 0131_add_origin_to_teams
Revises: 0130_admin_activity_logs
Create Date: 2025-11-02 04:40:00.000000

TenancyGuard Integration Test Fix

This migration adds the missing 'origin' column to the teams table
that is expected by the Team model in TenancyGuard integration tests.

Changes:
--------
- Add origin column to teams table (nullable string)
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0132_add_origin_to_teams"
down_revision = "0131_admin_activity_logs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add origin column to teams table."""
    # Add origin column (nullable for backward compatibility)
    op.add_column(
        "teams",
        sa.Column("origin", sa.String(length=255), nullable=True),
    )

    # Add index for origin column for faster queries
    op.create_index(
        "ix_teams_origin",
        "teams",
        ["origin"],
        unique=False,
    )


def downgrade() -> None:
    """Remove origin column from teams table."""
    # Drop index first
    op.drop_index("ix_teams_origin", table_name="teams")

    # Drop column
    op.drop_column("teams", "origin")
