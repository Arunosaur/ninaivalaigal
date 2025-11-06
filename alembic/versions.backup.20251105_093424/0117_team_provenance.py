# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Add team provenance tracking for M&A scenarios

Revision ID: 0117_team_provenance
Revises: 0116_teams_org_id
Create Date: 2025-10-23 12:16:00

Supports tracking team origin and acquisition history:
- origin = 'native': Teams originally formed within the parent organization
- origin = 'acquired': Teams from a previously independent organization that was acquired
- origin = 'merged': Teams formed from merging multiple legacy teams
- origin = 'partner': Teams from partner organizations with formal collaboration
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0117_team_provenance"
down_revision = "0116_teams_org_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add team provenance fields for M&A and organizational lineage tracking"""

    # Add origin field
    op.add_column("teams", sa.Column("origin", sa.String(50), nullable=True, server_default="native"))

    # Add acquired_from_organization_id (references a different org)
    op.add_column(
        "teams",
        sa.Column(
            "acquired_from_organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Add acquisition_date
    op.add_column("teams", sa.Column("acquisition_date", sa.DateTime, nullable=True))

    # Add parent_team_id for team mergers/splits
    op.add_column(
        "teams",
        sa.Column("parent_team_id", UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="SET NULL"), nullable=True),
    )

    # Add metadata field for additional M&A context
    op.add_column("teams", sa.Column("provenance_metadata", sa.JSON, nullable=True))

    # Add indexes
    op.create_index("ix_teams_origin", "teams", ["origin"])
    op.create_index("ix_teams_acquired_from_org", "teams", ["acquired_from_organization_id"])
    op.create_index("ix_teams_parent_team_id", "teams", ["parent_team_id"])

    # Add comments
    op.execute(
        """
        COMMENT ON COLUMN teams.origin IS
        'Team origin: native (formed in current org), acquired (from M&A), merged (from team consolidation), partner (external collaboration)';

        COMMENT ON COLUMN teams.acquired_from_organization_id IS
        'Original organization ID if this team came from an acquisition';

        COMMENT ON COLUMN teams.acquisition_date IS
        'Date when the team was acquired/integrated into current organization';

        COMMENT ON COLUMN teams.parent_team_id IS
        'Parent team ID for tracking team mergers, splits, or reorganizations';

        COMMENT ON COLUMN teams.provenance_metadata IS
        'Additional M&A context: original company name, integration notes, legacy systems, transition plan, etc.';
    """
    )


def downgrade() -> None:
    """Remove team provenance tracking fields"""

    op.drop_index("ix_teams_parent_team_id", table_name="teams")
    op.drop_index("ix_teams_acquired_from_org", table_name="teams")
    op.drop_index("ix_teams_origin", table_name="teams")

    op.drop_column("teams", "provenance_metadata")
    op.drop_column("teams", "parent_team_id")
    op.drop_column("teams", "acquisition_date")
    op.drop_column("teams", "acquired_from_organization_id")
    op.drop_column("teams", "origin")
