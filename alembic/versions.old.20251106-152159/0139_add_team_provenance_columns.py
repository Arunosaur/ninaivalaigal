#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Add provenance columns to teams table

Revision ID: 0138_add_team_provenance_columns
Revises: 0137_add_parent_team_id
Create Date: 2025-11-02 05:29:00.000000

TenancyGuard Integration Test Fix - Final Team Provenance Columns

This migration adds the missing provenance tracking columns to the teams table:
- acquired_from_organization_id: Track team acquisitions/transfers
- acquisition_date: When team was acquired
- provenance_metadata: Additional metadata about team origin/history

Changes:
--------
- Add acquired_from_organization_id column (nullable UUID, FK to organizations)
- Add acquisition_date column (nullable TIMESTAMP)
- Add provenance_metadata column (nullable JSONB)
- Add indexes for faster lookups
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0139_add_team_provenance_columns"
down_revision = "0138_add_parent_team_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add provenance columns to teams table."""

    # Add acquired_from_organization_id column
    op.add_column(
        "teams",
        sa.Column("acquired_from_organization_id", UUID(as_uuid=True), nullable=True),
    )

    # Add foreign key constraint to organizations table
    op.create_foreign_key(
        "teams_acquired_from_organization_id_fkey",
        "teams",
        "organizations",
        ["acquired_from_organization_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add acquisition_date column
    op.add_column(
        "teams",
        sa.Column("acquisition_date", sa.DateTime(), nullable=True),
    )

    # Add provenance_metadata column (JSONB for flexible metadata storage)
    op.add_column(
        "teams",
        sa.Column("provenance_metadata", JSONB, nullable=True),
    )

    # Add indexes for faster lookups
    op.create_index(
        "ix_teams_acquired_from_organization_id",
        "teams",
        ["acquired_from_organization_id"],
        unique=False,
    )

    op.create_index(
        "ix_teams_acquisition_date",
        "teams",
        ["acquisition_date"],
        unique=False,
    )


def downgrade() -> None:
    """Remove provenance columns from teams table."""

    # Drop indexes first
    op.drop_index("ix_teams_acquisition_date", table_name="teams")
    op.drop_index("ix_teams_acquired_from_organization_id", table_name="teams")

    # Drop columns
    op.drop_column("teams", "provenance_metadata")
    op.drop_column("teams", "acquisition_date")

    # Drop foreign key constraint
    op.drop_constraint("teams_acquired_from_organization_id_fkey", "teams", type_="foreignkey")

    # Drop column
    op.drop_column("teams", "acquired_from_organization_id")
