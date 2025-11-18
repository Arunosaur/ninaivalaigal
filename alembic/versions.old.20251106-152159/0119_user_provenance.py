# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""User Provenance Intelligence v1.0

Revision ID: 0119_user_provenance
Revises: 0118_team_intelligence
Create Date: 2025-10-23 12:38:00

Adds enterprise user intelligence for M&A, contractors, and HR integration:
- User Origin (native, acquired, contractor, partner)
- Employment Status (active, on_leave, offboarded, alumni, contractor_expired)
- Employment Lineage (acquired_from_org, hire_date, manager_id, employment_type)
- Employment Governance (employee, contractor, partner, consultant)
- Reporting hierarchy and org chart support
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0119_user_provenance"
down_revision = "0118_team_intelligence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user provenance and employment intelligence"""

    # ========================================
    # USER ORIGIN & PROVENANCE
    # ========================================

    op.add_column("users", sa.Column("origin", sa.String(50), nullable=False, server_default="native"))

    op.add_column(
        "users",
        sa.Column(
            "acquired_from_organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    op.add_column("users", sa.Column("acquisition_date", sa.DateTime, nullable=True))

    # ========================================
    # EMPLOYMENT STATUS & LIFECYCLE
    # ========================================

    op.add_column("users", sa.Column("employment_status", sa.String(50), nullable=False, server_default="active"))

    op.add_column("users", sa.Column("employment_type", sa.String(50), nullable=False, server_default="full_time"))

    # ========================================
    # EMPLOYMENT GOVERNANCE
    # ========================================

    op.add_column("users", sa.Column("employment_governance", sa.String(50), nullable=False, server_default="employee"))

    op.add_column(
        "users",
        sa.Column(
            "vendor_organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ========================================
    # EMPLOYMENT DATES & HIERARCHY
    # ========================================

    op.add_column("users", sa.Column("hire_date", sa.DateTime, nullable=True))

    op.add_column("users", sa.Column("termination_date", sa.DateTime, nullable=True))

    op.add_column("users", sa.Column("contract_start_date", sa.DateTime, nullable=True))

    op.add_column("users", sa.Column("contract_end_date", sa.DateTime, nullable=True))

    # Reporting hierarchy
    op.add_column(
        "users",
        sa.Column("manager_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
    )

    # Primary organization affiliation
    op.add_column(
        "users",
        sa.Column(
            "primary_organization_id",
            UUID(as_uuid=True),
            sa.ForeignKey("organizations.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )

    # ========================================
    # METADATA & PROVENANCE
    # ========================================

    op.add_column("users", sa.Column("employment_metadata", sa.JSON, nullable=True))

    # Full reporting chain for org chart
    op.add_column("users", sa.Column("full_reporting_chain", ARRAY(UUID(as_uuid=True)), nullable=True))

    # ========================================
    # INDEXES FOR ANALYTICS
    # ========================================

    op.create_index("ix_users_origin", "users", ["origin"])
    op.create_index("ix_users_employment_status", "users", ["employment_status"])
    op.create_index("ix_users_employment_type", "users", ["employment_type"])
    op.create_index("ix_users_employment_governance", "users", ["employment_governance"])
    op.create_index("ix_users_acquired_from_org", "users", ["acquired_from_organization_id"])
    op.create_index("ix_users_vendor_org", "users", ["vendor_organization_id"])
    op.create_index("ix_users_manager_id", "users", ["manager_id"])
    op.create_index("ix_users_primary_org", "users", ["primary_organization_id"])

    # Composite indexes for common queries
    op.create_index("ix_users_org_status", "users", ["primary_organization_id", "employment_status"])
    op.create_index("ix_users_origin_status", "users", ["origin", "employment_status"])

    # GIN index for reporting chain queries
    op.create_index("ix_users_reporting_chain_gin", "users", ["full_reporting_chain"], postgresql_using="gin")

    # ========================================
    # DATA INTEGRITY CONSTRAINTS
    # ========================================

    # Acquired users must have source org
    op.create_check_constraint(
        "chk_users_acquired_origin", "users", "acquired_from_organization_id IS NULL OR origin = 'acquired'"
    )

    # Contractors must have vendor org
    op.create_check_constraint(
        "chk_users_contractor_vendor",
        "users",
        "employment_governance != 'contractor' OR vendor_organization_id IS NOT NULL",
    )

    # No self-management
    op.create_check_constraint("chk_users_no_self_manager", "users", "manager_id IS NULL OR manager_id != id")

    # Valid origin values
    op.create_check_constraint(
        "chk_users_valid_origin", "users", "origin IN ('native', 'acquired', 'contractor', 'partner', 'intern')"
    )

    # Valid employment status
    op.create_check_constraint(
        "chk_users_valid_employment_status",
        "users",
        "employment_status IN ('active', 'on_leave', 'offboarded', 'alumni', 'contractor_expired')",
    )

    # Valid employment type
    op.create_check_constraint(
        "chk_users_valid_employment_type",
        "users",
        "employment_type IN ('full_time', 'part_time', 'contractor', 'intern', 'consultant')",
    )

    # Valid governance
    op.create_check_constraint(
        "chk_users_valid_employment_governance",
        "users",
        "employment_governance IN ('employee', 'contractor', 'partner', 'consultant')",
    )

    # ========================================
    # TRIGGER: AUTO-UPDATE reporting_chain
    # ========================================

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_user_reporting_chain()
        RETURNS TRIGGER AS $$
        DECLARE
            manager_chain UUID[];
            max_depth INTEGER := 20;  -- Prevent infinite loops
            current_depth INTEGER := 0;
        BEGIN
            IF NEW.manager_id IS NOT NULL THEN
                -- Get manager's reporting chain
                SELECT full_reporting_chain INTO manager_chain
                FROM users
                WHERE id = NEW.manager_id;

                -- Check depth to prevent cycles
                IF manager_chain IS NOT NULL THEN
                    current_depth := array_length(manager_chain, 1);
                END IF;

                IF current_depth < max_depth THEN
                    -- Append current user to manager's chain
                    IF manager_chain IS NULL THEN
                        NEW.full_reporting_chain := ARRAY[NEW.manager_id, NEW.id];
                    ELSE
                        NEW.full_reporting_chain := manager_chain || NEW.id;
                    END IF;
                ELSE
                    -- Chain too deep, log warning and set to direct manager only
                    RAISE WARNING 'Reporting chain depth exceeded for user %', NEW.id;
                    NEW.full_reporting_chain := ARRAY[NEW.manager_id, NEW.id];
                END IF;
            ELSE
                -- No manager (CEO/founder)
                NEW.full_reporting_chain := ARRAY[NEW.id];
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )

    op.execute(
        """
        CREATE TRIGGER trg_update_user_reporting_chain
        BEFORE INSERT OR UPDATE OF manager_id ON users
        FOR EACH ROW
        EXECUTE FUNCTION update_user_reporting_chain();
        """
    )

    # ========================================
    # COMMENTS
    # ========================================

    op.execute(
        """
        COMMENT ON COLUMN users.origin IS
        'User origin: native (hired directly), acquired (M&A), contractor (temp engagement), partner (external), intern (student)';

        COMMENT ON COLUMN users.employment_status IS
        'Employment lifecycle: active (current), on_leave (sabbatical/parental), offboarded (terminated/resigned), alumni (former for records), contractor_expired (contract ended)';

        COMMENT ON COLUMN users.employment_type IS
        'Employment classification: full_time, part_time, contractor, intern, consultant';

        COMMENT ON COLUMN users.employment_governance IS
        'Employment governance: employee (W2), contractor (1099/corp-to-corp), partner (external collaboration), consultant (advisory)';

        COMMENT ON COLUMN users.vendor_organization_id IS
        'Contracting/consulting firm for non-employees (e.g., Acme Consulting LLC)';

        COMMENT ON COLUMN users.manager_id IS
        'Direct manager/supervisor for org chart and reporting hierarchy';

        COMMENT ON COLUMN users.full_reporting_chain IS
        'Array of user UUIDs from CEO to current user for org chart traversal';

        COMMENT ON COLUMN users.employment_metadata IS
        'Additional employment context: original title, retention bonus, visa status, location, cost center, etc.';
    """
    )


def downgrade() -> None:
    """Remove user provenance tracking"""

    op.execute("DROP TRIGGER IF EXISTS trg_update_user_reporting_chain ON users;")
    op.execute("DROP FUNCTION IF EXISTS update_user_reporting_chain();")

    op.drop_constraint("chk_users_valid_employment_governance", "users")
    op.drop_constraint("chk_users_valid_employment_type", "users")
    op.drop_constraint("chk_users_valid_employment_status", "users")
    op.drop_constraint("chk_users_valid_origin", "users")
    op.drop_constraint("chk_users_no_self_manager", "users")
    op.drop_constraint("chk_users_contractor_vendor", "users")
    op.drop_constraint("chk_users_acquired_origin", "users")

    op.drop_index("ix_users_reporting_chain_gin", table_name="users")
    op.drop_index("ix_users_origin_status", table_name="users")
    op.drop_index("ix_users_org_status", table_name="users")
    op.drop_index("ix_users_primary_org", table_name="users")
    op.drop_index("ix_users_manager_id", table_name="users")
    op.drop_index("ix_users_vendor_org", table_name="users")
    op.drop_index("ix_users_acquired_from_org", table_name="users")
    op.drop_index("ix_users_employment_governance", table_name="users")
    op.drop_index("ix_users_employment_type", table_name="users")
    op.drop_index("ix_users_employment_status", table_name="users")
    op.drop_index("ix_users_origin", table_name="users")

    op.drop_column("users", "full_reporting_chain")
    op.drop_column("users", "employment_metadata")
    op.drop_column("users", "primary_organization_id")
    op.drop_column("users", "manager_id")
    op.drop_column("users", "contract_end_date")
    op.drop_column("users", "contract_start_date")
    op.drop_column("users", "termination_date")
    op.drop_column("users", "hire_date")
    op.drop_column("users", "vendor_organization_id")
    op.drop_column("users", "employment_governance")
    op.drop_column("users", "employment_type")
    op.drop_column("users", "employment_status")
    op.drop_column("users", "acquisition_date")
    op.drop_column("users", "acquired_from_organization_id")
    op.drop_column("users", "origin")
