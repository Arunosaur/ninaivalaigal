# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Enterprise Team Intelligence Model v1.1

Revision ID: 0118_team_intelligence
Revises: 0117_team_provenance
Create Date: 2025-10-23 12:29:00

Adds Dimensions 5 & 6 plus analytical enhancements:
- Dimension 5: Operational Status (active, dormant, sunset, transitioning)
- Dimension 6: Governance & Role Alignment (internal, shared, external)
- Analytical: full_lineage_path for graph traversal
- Composite indexes for team provenance queries
- Validation: CHECK constraints for data integrity
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0118_team_intelligence"
down_revision = "0117_team_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add operational status, governance, and analytical enhancements"""

    # ========================================
    # DIMENSION 5: OPERATIONAL STATUS
    # ========================================
    op.add_column("teams", sa.Column("status", sa.String(50), nullable=False, server_default="active"))

    # ========================================
    # DIMENSION 6: GOVERNANCE & ROLE ALIGNMENT
    # ========================================
    op.add_column("teams", sa.Column("governance_type", sa.String(50), nullable=False, server_default="internal"))

    op.add_column(
        "teams",
        sa.Column("lead_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    # ========================================
    # ANALYTICAL ENHANCEMENTS
    # ========================================

    # Full lineage path for graph traversal (array of UUIDs)
    op.add_column("teams", sa.Column("full_lineage_path", ARRAY(UUID(as_uuid=True)), nullable=True))

    # ========================================
    # INDEXES FOR ANALYTICS & FILTERING
    # ========================================

    # Status filtering (common dashboard query)
    op.create_index("ix_teams_status", "teams", ["status"])

    # Governance type filtering
    op.create_index("ix_teams_governance_type", "teams", ["governance_type"])

    # Lead user lookups
    op.create_index("ix_teams_lead_user_id", "teams", ["lead_user_id"])

    # Composite index for team provenance queries
    # "Show me all acquired teams that are still transitioning"
    op.create_index("ix_teams_origin_status", "teams", ["origin", "status"])

    # Composite index for org hierarchy queries
    # "Show me all active teams in this organization"
    op.create_index("ix_teams_org_status", "teams", ["organization_id", "status"])

    # GIN index for lineage path queries (PostgreSQL specific)
    op.create_index("ix_teams_lineage_path_gin", "teams", ["full_lineage_path"], postgresql_using="gin")

    # ========================================
    # DATA INTEGRITY CONSTRAINTS
    # ========================================

    # Constraint: organization_id IS NULL → must have origin='native' or 'partner'
    # (Ad-hoc teams can't be "acquired")
    op.create_check_constraint(
        "chk_teams_adhoc_origin", "teams", "organization_id IS NOT NULL OR origin IN ('native', 'partner')"
    )

    # Constraint: acquired_from_organization_id NOT NULL → origin='acquired'
    op.create_check_constraint(
        "chk_teams_acquired_origin", "teams", "acquired_from_organization_id IS NULL OR origin = 'acquired'"
    )

    # Constraint: parent_team_id != id (prevent self-reference)
    op.create_check_constraint("chk_teams_no_self_reference", "teams", "parent_team_id IS NULL OR parent_team_id != id")

    # Constraint: Valid status values
    op.create_check_constraint(
        "chk_teams_valid_status", "teams", "status IN ('active', 'inactive', 'sunset', 'transitioning')"
    )

    # Constraint: Valid governance types
    op.create_check_constraint(
        "chk_teams_valid_governance", "teams", "governance_type IN ('internal', 'shared', 'external')"
    )

    # ========================================
    # TRIGGER: AUTO-SET acquisition_date
    # ========================================

    # Create trigger function
    op.execute(
        """
        CREATE OR REPLACE FUNCTION set_acquisition_date()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.acquired_from_organization_id IS NOT NULL
               AND NEW.origin = 'acquired'
               AND NEW.acquisition_date IS NULL
            THEN
                NEW.acquisition_date := NOW();
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Attach trigger to teams table
    op.execute(
        """
        CREATE TRIGGER trg_set_acquisition_date
        BEFORE INSERT OR UPDATE ON teams
        FOR EACH ROW
        EXECUTE FUNCTION set_acquisition_date();
        """
    )

    # ========================================
    # TRIGGER: AUTO-UPDATE full_lineage_path
    # ========================================

    # Create recursive lineage path builder
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_team_lineage_path()
        RETURNS TRIGGER AS $$
        DECLARE
            parent_path UUID[];
        BEGIN
            IF NEW.parent_team_id IS NOT NULL THEN
                -- Get parent's lineage path
                SELECT full_lineage_path INTO parent_path
                FROM teams
                WHERE id = NEW.parent_team_id;

                -- Append current team to parent's path
                IF parent_path IS NULL THEN
                    NEW.full_lineage_path := ARRAY[NEW.parent_team_id, NEW.id];
                ELSE
                    NEW.full_lineage_path := parent_path || NEW.id;
                END IF;
            ELSE
                -- Root team (no parent)
                NEW.full_lineage_path := ARRAY[NEW.id];
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    # Attach trigger
    op.execute(
        """
        CREATE TRIGGER trg_update_team_lineage_path
        BEFORE INSERT OR UPDATE OF parent_team_id ON teams
        FOR EACH ROW
        EXECUTE FUNCTION update_team_lineage_path();
        """
    )

    # ========================================
    # COMMENTS FOR DOCUMENTATION
    # ========================================

    op.execute(
        """
        COMMENT ON COLUMN teams.status IS
        'Operational status: active (fully operational), inactive (temporarily dormant), sunset (legacy reference only), transitioning (integration/merger in progress)';

        COMMENT ON COLUMN teams.governance_type IS
        'Governance model: internal (fully governed by parent org), shared (jointly managed with partner), external (partner-owned, connected for cross-org projects)';

        COMMENT ON COLUMN teams.lead_user_id IS
        'Optional direct link to team lead/owner for quick lookups and org charts';

        COMMENT ON COLUMN teams.full_lineage_path IS
        'Array of team UUIDs representing full ancestry path from root to current team. Enables efficient graph traversal for lineage queries.';

        COMMENT ON CONSTRAINT chk_teams_adhoc_origin ON teams IS
        'Ad-hoc teams (no organization_id) must be native or partner origin';

        COMMENT ON CONSTRAINT chk_teams_acquired_origin ON teams IS
        'Teams with acquired_from_organization_id must have origin=acquired';

        COMMENT ON CONSTRAINT chk_teams_no_self_reference ON teams IS
        'Teams cannot be their own parent (prevents circular references)';
    """
    )


def downgrade() -> None:
    """Remove team intelligence enhancements"""

    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trg_update_team_lineage_path ON teams;")
    op.execute("DROP TRIGGER IF EXISTS trg_set_acquisition_date ON teams;")
    op.execute("DROP FUNCTION IF EXISTS update_team_lineage_path();")
    op.execute("DROP FUNCTION IF EXISTS set_acquisition_date();")

    # Drop constraints
    op.drop_constraint("chk_teams_valid_governance", "teams")
    op.drop_constraint("chk_teams_valid_status", "teams")
    op.drop_constraint("chk_teams_no_self_reference", "teams")
    op.drop_constraint("chk_teams_acquired_origin", "teams")
    op.drop_constraint("chk_teams_adhoc_origin", "teams")

    # Drop indexes
    op.drop_index("ix_teams_lineage_path_gin", table_name="teams")
    op.drop_index("ix_teams_org_status", table_name="teams")
    op.drop_index("ix_teams_origin_status", table_name="teams")
    op.drop_index("ix_teams_lead_user_id", table_name="teams")
    op.drop_index("ix_teams_governance_type", table_name="teams")
    op.drop_index("ix_teams_status", table_name="teams")

    # Drop columns
    op.drop_column("teams", "full_lineage_path")
    op.drop_column("teams", "lead_user_id")
    op.drop_column("teams", "governance_type")
    op.drop_column("teams", "status")
