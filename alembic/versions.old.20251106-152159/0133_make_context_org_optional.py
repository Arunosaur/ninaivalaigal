#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Make context organization_id truly optional

Revision ID: 0132_make_context_org_optional
Revises: 0131_add_origin_to_teams
Create Date: 2025-11-02 04:50:00.000000

TenancyGuard Integration Test Fix

This migration makes organization_id in contexts table truly optional
by dropping the foreign key constraint and recreating it with ON DELETE SET NULL.
This allows contexts to exist without organizations for testing purposes.

Changes:
--------
- Drop existing foreign key constraint on contexts.organization_id
- Recreate foreign key with ON DELETE SET NULL
- Ensure organization_id is nullable
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0133_make_context_org_optional"
down_revision = "0132_add_origin_to_teams"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Make organization_id optional in contexts."""

    # Drop existing foreign key constraint
    op.drop_constraint("contexts_organization_id_fkey", "contexts", type_="foreignkey")

    # Recreate foreign key with ON DELETE SET NULL
    # This allows contexts to exist without organizations
    op.create_foreign_key(
        "contexts_organization_id_fkey", "contexts", "organizations", ["organization_id"], ["id"], ondelete="SET NULL"
    )

    # Ensure column is nullable (should already be, but make it explicit)
    op.alter_column("contexts", "organization_id", existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    """Revert to original foreign key constraint."""

    # Drop the modified foreign key
    op.drop_constraint("contexts_organization_id_fkey", "contexts", type_="foreignkey")

    # Recreate original foreign key without ON DELETE SET NULL
    op.create_foreign_key("contexts_organization_id_fkey", "contexts", "organizations", ["organization_id"], ["id"])
