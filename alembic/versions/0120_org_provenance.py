# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Organization Provenance Intelligence v1.0

Revision ID: 0120_org_provenance
Revises: 0119_user_provenance
Create Date: 2025-10-23 12:40:00

Adds enterprise organization intelligence for M&A, subsidiaries, and corporate structure:
- Organization Origin (founding, acquired, merger, subsidiary, spin_off)
- Organization Status (active, acquired, merged, dissolved, dormant)
- Corporate Lineage (parent_organization_id, acquired_by, acquisition_date)
- Operational Metadata (headquarters, employee_count, revenue_tier, industry)
- Full corporate hierarchy for group structures
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0120_org_provenance"
down_revision = "0119_user_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add organization provenance and corporate intelligence"""

    # ========================================
    # ORGANIZATION ORIGIN & PROVENANCE
    # ========================================

    op.add_column("organizations", sa.Column("origin", sa.String(50), nullable=False, server_default="founding"))

    op.add_column("organizations", sa.Column("founded_date", sa.DateTime, nullable=True))

    # ========================================
    # CORPORATE STRUCTURE & LINEAGE
    # ========================================

    # Parent company (for subsidiaries and divisions)
    op.add_column(
        "organizations",
        sa.Column(
            "parent_organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # Acquiring company (for M&A tracking)
    op.add_column(
        "organizations",
        sa.Column(
            "acquired_by_organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.add_column("organizations", sa.Column("acquisition_date", sa.DateTime, nullable=True))

    # Full corporate hierarchy path
    op.add_column("organizations", sa.Column("full_corporate_hierarchy", ARRAY(UUID(as_uuid=True)), nullable=True))

    # ========================================
    # ORGANIZATION STATUS & LIFECYCLE
    # ========================================

    op.add_column(
        "organizations", sa.Column("organization_status", sa.String(50), nullable=False, server_default="active")
    )

    op.add_column("organizations", sa.Column("dissolution_date", sa.DateTime, nullable=True))

    # ========================================
    # OPERATIONAL METADATA
    # ========================================

    op.add_column("organizations", sa.Column("legal_name", sa.String(500), nullable=True))

    op.add_column("organizations", sa.Column("tax_id", sa.String(100), nullable=True))

    op.add_column("organizations", sa.Column("headquarters_location", sa.String(255), nullable=True))

    op.add_column("organizations", sa.Column("employee_count_range", sa.String(50), nullable=True))

    op.add_column("organizations", sa.Column("revenue_tier", sa.String(50), nullable=True))

    op.add_column("organizations", sa.Column("industry_sector", sa.String(100), nullable=True))

    op.add_column(
        "organizations", sa.Column("organization_type", sa.String(50), nullable=False, server_default="corporation")
    )

    # ========================================
    # CORPORATE METADATA
    # ========================================

    op.add_column("organizations", sa.Column("corporate_metadata", sa.JSON, nullable=True))

    # ========================================
    # INDEXES FOR ANALYTICS
    # ========================================

    op.create_index("ix_organizations_origin", "organizations", ["origin"])
    op.create_index("ix_organizations_status", "organizations", ["organization_status"])
    op.create_index("ix_organizations_type", "organizations", ["organization_type"])
    op.create_index("ix_organizations_parent", "organizations", ["parent_organization_id"])
    op.create_index("ix_organizations_acquired_by", "organizations", ["acquired_by_organization_id"])
    op.create_index("ix_organizations_industry", "organizations", ["industry_sector"])

    # Composite indexes
    op.create_index("ix_organizations_origin_status", "organizations", ["origin", "organization_status"])
    op.create_index(
        "ix_organizations_parent_status", "organizations", ["parent_organization_id", "organization_status"]
    )

    # GIN index for corporate hierarchy
    op.create_index(
        "ix_organizations_hierarchy_gin", "organizations", ["full_corporate_hierarchy"], postgresql_using="gin"
    )

    # ========================================
    # DATA INTEGRITY CONSTRAINTS
    # ========================================

    # Acquired orgs must have acquirer
    op.create_check_constraint(
        "chk_orgs_acquired_by", "organizations", "origin != 'acquired' OR acquired_by_organization_id IS NOT NULL"
    )

    # Subsidiaries must have parent
    op.create_check_constraint(
        "chk_orgs_subsidiary_parent", "organizations", "origin != 'subsidiary' OR parent_organization_id IS NOT NULL"
    )

    # No self-parenting
    op.create_check_constraint(
        "chk_orgs_no_self_parent", "organizations", "parent_organization_id IS NULL OR parent_organization_id != id"
    )

    # Valid origin values
    op.create_check_constraint(
        "chk_orgs_valid_origin",
        "organizations",
        "origin IN ('founding', 'acquired', 'merger', 'subsidiary', 'spin_off', 'joint_venture')",
    )

    # Valid status values
    op.create_check_constraint(
        "chk_orgs_valid_status",
        "organizations",
        "organization_status IN ('active', 'acquired', 'merged', 'dissolved', 'dormant', 'bankrupt')",
    )

    # Valid org types
    op.create_check_constraint(
        "chk_orgs_valid_type",
        "organizations",
        "organization_type IN ('corporation', 'llc', 'partnership', 'non_profit', 'government', 'sole_proprietor')",
    )

    # ========================================
    # TRIGGER: AUTO-UPDATE corporate_hierarchy
    # ========================================

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_org_corporate_hierarchy()
        RETURNS TRIGGER AS $$
        DECLARE
            parent_hierarchy UUID[];
            max_depth INTEGER := 20;
            current_depth INTEGER := 0;
        BEGIN
            IF NEW.parent_organization_id IS NOT NULL THEN
                -- Get parent's corporate hierarchy
                SELECT full_corporate_hierarchy INTO parent_hierarchy
                FROM organizations
                WHERE id = NEW.parent_organization_id;

                -- Check depth
                IF parent_hierarchy IS NOT NULL THEN
                    current_depth := array_length(parent_hierarchy, 1);
                END IF;

                IF current_depth < max_depth THEN
                    -- Append current org to parent's hierarchy
                    IF parent_hierarchy IS NULL THEN
                        NEW.full_corporate_hierarchy := ARRAY[NEW.parent_organization_id, NEW.id];
                    ELSE
                        NEW.full_corporate_hierarchy := parent_hierarchy || NEW.id;
                    END IF;
                ELSE
                    RAISE WARNING 'Corporate hierarchy depth exceeded for org %', NEW.id;
                    NEW.full_corporate_hierarchy := ARRAY[NEW.parent_organization_id, NEW.id];
                END IF;
            ELSE
                -- Root organization (parent company)
                NEW.full_corporate_hierarchy := ARRAY[NEW.id];
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_update_org_corporate_hierarchy
        BEFORE INSERT OR UPDATE OF parent_organization_id ON organizations
        FOR EACH ROW
        EXECUTE FUNCTION update_org_corporate_hierarchy();
        """
    )

    # ========================================
    # COMMENTS
    # ========================================

    op.execute(
        """
        COMMENT ON COLUMN organizations.origin IS
        'Organization origin: founding (originally created), acquired (bought by another co), merger (combined companies), subsidiary (division of parent), spin_off (separated from parent), joint_venture (co-owned)';

        COMMENT ON COLUMN organizations.organization_status IS
        'Org lifecycle: active (operating), acquired (now part of parent), merged (combined with another), dissolved (shut down), dormant (inactive), bankrupt (insolvent)';

        COMMENT ON COLUMN organizations.parent_organization_id IS
        'Parent company for subsidiaries, divisions, and corporate groups';

        COMMENT ON COLUMN organizations.acquired_by_organization_id IS
        'Acquiring company if this org was purchased via M&A';

        COMMENT ON COLUMN organizations.full_corporate_hierarchy IS
        'Array of org UUIDs from parent company to current org for corporate structure traversal';

        COMMENT ON COLUMN organizations.organization_type IS
        'Legal entity type: corporation, llc, partnership, non_profit, government, sole_proprietor';

        COMMENT ON COLUMN organizations.corporate_metadata IS
        'Additional corporate context: stock ticker, valuation, board members, funding rounds, etc.';
    """
    )


def downgrade() -> None:
    """Remove organization provenance tracking"""

    op.execute("DROP TRIGGER IF EXISTS trg_update_org_corporate_hierarchy ON organizations;")
    op.execute("DROP FUNCTION IF EXISTS update_org_corporate_hierarchy();")

    op.drop_constraint("chk_orgs_valid_type", "organizations")
    op.drop_constraint("chk_orgs_valid_status", "organizations")
    op.drop_constraint("chk_orgs_valid_origin", "organizations")
    op.drop_constraint("chk_orgs_no_self_parent", "organizations")
    op.drop_constraint("chk_orgs_subsidiary_parent", "organizations")
    op.drop_constraint("chk_orgs_acquired_by", "organizations")

    op.drop_index("ix_organizations_hierarchy_gin", table_name="organizations")
    op.drop_index("ix_organizations_parent_status", table_name="organizations")
    op.drop_index("ix_organizations_origin_status", table_name="organizations")
    op.drop_index("ix_organizations_industry", table_name="organizations")
    op.drop_index("ix_organizations_acquired_by", table_name="organizations")
    op.drop_index("ix_organizations_parent", table_name="organizations")
    op.drop_index("ix_organizations_type", table_name="organizations")
    op.drop_index("ix_organizations_status", table_name="organizations")
    op.drop_index("ix_organizations_origin", table_name="organizations")

    op.drop_column("organizations", "corporate_metadata")
    op.drop_column("organizations", "organization_type")
    op.drop_column("organizations", "industry_sector")
    op.drop_column("organizations", "revenue_tier")
    op.drop_column("organizations", "employee_count_range")
    op.drop_column("organizations", "headquarters_location")
    op.drop_column("organizations", "tax_id")
    op.drop_column("organizations", "legal_name")
    op.drop_column("organizations", "dissolution_date")
    op.drop_column("organizations", "organization_status")
    op.drop_column("organizations", "full_corporate_hierarchy")
    op.drop_column("organizations", "acquisition_date")
    op.drop_column("organizations", "acquired_by_organization_id")
    op.drop_column("organizations", "parent_organization_id")
    op.drop_column("organizations", "founded_date")
    op.drop_column("organizations", "origin")
