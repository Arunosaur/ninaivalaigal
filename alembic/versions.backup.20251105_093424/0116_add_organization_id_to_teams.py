# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Add organization_id to teams table

Revision ID: 0116_add_organization_id_to_teams
Revises: 0115_add_missing_user_columns
Create Date: 2025-10-23 12:10:00

Supports both ad-hoc community teams and institutional corporate teams:
- organization_id = NULL: Ad-hoc/community teams (open-source, side projects)
- organization_id = <uuid>: Institutional teams (corporate, formal affiliation)
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0116_teams_org_id"
down_revision = "0115_user_columns"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add organization_id column to teams table for dual team model support"""

    # Add organization_id column (nullable for ad-hoc teams)
    op.add_column(
        "teams", sa.Column("organization_id", UUID(as_uuid=True), sa.ForeignKey("organizations.id"), nullable=True)
    )

    # Add index for performance
    op.create_index("ix_teams_organization_id", "teams", ["organization_id"])

    # Add comment
    op.execute(
        """
        COMMENT ON COLUMN teams.organization_id IS
        'Organization affiliation: NULL for ad-hoc/community teams, UUID for institutional/corporate teams';
    """
    )


def downgrade() -> None:
    """Remove organization_id from teams table"""

    op.drop_index("ix_teams_organization_id", table_name="teams")
    op.drop_column("teams", "organization_id")
