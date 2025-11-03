#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Expand alembic_version.version_num to varchar(64)

Revision ID: 0126a_expand_alembic_version
Revises: 0126_spec026_team_billing
Create Date: 2025-11-02 02:43:00.000000

This migration expands the alembic_version.version_num column from varchar(32)
to varchar(64) to allow more descriptive revision identifiers.

Background:
-----------
The default Alembic setup creates a varchar(32) column, but descriptive revision
IDs like "0127_spec074_gdpr_compliance_schema" exceed this limit. Expanding to
varchar(64) allows developers to use more meaningful revision identifiers while
maintaining compatibility with Alembic's revision tracking.

This is a safe operation that:
- Does not affect existing data (all current IDs are < 32 chars)
- Allows future migrations to use longer, more descriptive IDs
- Follows PostgreSQL best practices for schema evolution
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0129_expand_alembic_version"
down_revision = "0128_us121_hipaa"
branch_labels = None
depends_on = None


def upgrade():
    """Expand alembic_version.version_num to varchar(64)"""

    # Note: Alembic's version table is in ag_catalog schema (Apache AGE)
    # We need to use raw SQL to modify it since it's Alembic's own table
    op.execute("ALTER TABLE ag_catalog.alembic_version " "ALTER COLUMN version_num TYPE varchar(64)")


def downgrade():
    """Revert alembic_version.version_num to varchar(32)"""

    # Note: This downgrade will fail if any version_num exceeds 32 characters
    # This is intentional - you should not downgrade if using longer IDs
    op.execute("ALTER TABLE ag_catalog.alembic_version " "ALTER COLUMN version_num TYPE varchar(32)")
