# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Make OrganizationRegistration FKs deferrable for PgBouncer compatibility

Revision ID: 0121_deferrable_org_fks
Revises: 0120_org_provenance
Create Date: 2025-10-24 15:30:00

Fixes FK constraints on organization_registrations table to be DEFERRABLE INITIALLY DEFERRED.
This allows SQLAlchemy flush() to work properly with PgBouncer transaction pooling mode.

Issue: With non-deferrable FKs, PgBouncer transaction mode checks FK constraints immediately
on INSERT, before the referenced row is visible in the same transaction.

Solution: Make FKs deferrable so constraint checking happens at COMMIT time.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0121_deferrable_org_fks"
down_revision = "0120_org_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make organization_registrations FK constraints deferrable"""

    # Drop and recreate organization_id FK as deferrable
    op.execute(
        """
        ALTER TABLE organization_registrations
        DROP CONSTRAINT IF EXISTS organization_registrations_organization_id_fkey;
    """
    )

    op.execute(
        """
        ALTER TABLE organization_registrations
        ADD CONSTRAINT organization_registrations_organization_id_fkey
        FOREIGN KEY (organization_id) REFERENCES organizations(id)
        DEFERRABLE INITIALLY DEFERRED;
    """
    )

    # Drop and recreate creator_user_id FK as deferrable
    op.execute(
        """
        ALTER TABLE organization_registrations
        DROP CONSTRAINT IF EXISTS organization_registrations_creator_user_id_fkey;
    """
    )

    op.execute(
        """
        ALTER TABLE organization_registrations
        ADD CONSTRAINT organization_registrations_creator_user_id_fkey
        FOREIGN KEY (creator_user_id) REFERENCES users(id)
        DEFERRABLE INITIALLY DEFERRED;
    """
    )


def downgrade() -> None:
    """Revert FK constraints to non-deferrable (original state)"""

    # Revert organization_id FK to non-deferrable
    op.execute(
        """
        ALTER TABLE organization_registrations
        DROP CONSTRAINT IF EXISTS organization_registrations_organization_id_fkey;
    """
    )

    op.execute(
        """
        ALTER TABLE organization_registrations
        ADD CONSTRAINT organization_registrations_organization_id_fkey
        FOREIGN KEY (organization_id) REFERENCES organizations(id);
    """
    )

    # Revert creator_user_id FK to non-deferrable
    op.execute(
        """
        ALTER TABLE organization_registrations
        DROP CONSTRAINT IF EXISTS organization_registrations_creator_user_id_fkey;
    """
    )

    op.execute(
        """
        ALTER TABLE organization_registrations
        ADD CONSTRAINT organization_registrations_creator_user_id_fkey
        FOREIGN KEY (creator_user_id) REFERENCES users(id);
    """
    )
