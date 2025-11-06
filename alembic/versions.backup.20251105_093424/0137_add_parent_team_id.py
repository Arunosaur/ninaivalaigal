#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Add parent_team_id column to teams table

Revision ID: 0137_add_parent_team_id
Revises: 0136_merge_heads
Create Date: 2025-11-02 05:24:00.000000

TenancyGuard Integration Test Fix - Add parent_team_id

This migration adds the missing parent_team_id column to the teams table,
which is expected by the Team model for hierarchical team structures.

Changes:
--------
- Add parent_team_id column (nullable UUID, self-referential foreign key)
- Add index for faster lookups
- Support team hierarchies (parent-child relationships)
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0137_add_parent_team_id"
down_revision = "0136_merge_heads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add parent_team_id column to teams table."""

    # Add parent_team_id column (self-referential foreign key)
    op.add_column(
        "teams",
        sa.Column("parent_team_id", UUID(as_uuid=True), nullable=True),
    )

    # Add foreign key constraint (self-referential to teams table)
    op.create_foreign_key(
        "teams_parent_team_id_fkey", "teams", "teams", ["parent_team_id"], ["id"], ondelete="SET NULL"
    )

    # Add index for faster lookups
    op.create_index(
        "ix_teams_parent_team_id",
        "teams",
        ["parent_team_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove parent_team_id column from teams table."""

    # Drop index first
    op.drop_index("ix_teams_parent_team_id", table_name="teams")

    # Drop foreign key constraint
    op.drop_constraint("teams_parent_team_id_fkey", "teams", type_="foreignkey")

    # Drop column
    op.drop_column("teams", "parent_team_id")
