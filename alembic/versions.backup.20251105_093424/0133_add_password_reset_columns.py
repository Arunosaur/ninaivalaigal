#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Add password reset columns to users table

Revision ID: 0133_add_password_reset_columns
Revises: 0132_make_context_org_optional
Create Date: 2025-11-02 04:56:00.000000

Test Fix: GDPR/HIPAA Compliance Tests

This migration adds the missing password_reset_token and password_reset_expires
columns to the users table, which are required for password reset functionality
and tested in the compliance test suite.

Changes:
--------
- Add password_reset_token column (nullable string)
- Add password_reset_expires column (nullable timestamp)
- Add index on password_reset_token for faster lookups
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "0133_add_password_reset_columns"
down_revision = "0132_make_context_org_optional"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add password reset columns to users table."""

    # Add password_reset_token column
    op.add_column(
        "users",
        sa.Column("password_reset_token", sa.String(length=255), nullable=True),
    )

    # Add password_reset_expires column
    op.add_column(
        "users",
        sa.Column("password_reset_expires", sa.DateTime(), nullable=True),
    )

    # Add index on password_reset_token for faster lookups
    op.create_index(
        "ix_users_password_reset_token",
        "users",
        ["password_reset_token"],
        unique=False,
    )


def downgrade() -> None:
    """Remove password reset columns from users table."""

    # Drop index first
    op.drop_index("ix_users_password_reset_token", table_name="users")

    # Drop columns
    op.drop_column("users", "password_reset_expires")
    op.drop_column("users", "password_reset_token")
