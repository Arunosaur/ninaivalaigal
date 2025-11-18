# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Add missing user columns for auth system

Revision ID: 0115_add_missing_user_columns
Revises: 0114_refresh_tokens
Create Date: 2025-10-23 11:30:00

"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0115_user_columns"
down_revision = "0114_refresh_tokens"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to users table"""

    # Add username column (nullable since existing users won't have it)
    op.add_column("users", sa.Column("username", sa.String(255), nullable=True))

    # Add personal_contexts_limit
    op.add_column("users", sa.Column("personal_contexts_limit", sa.Integer, nullable=True, server_default="10"))

    # Add verification_token
    op.add_column("users", sa.Column("verification_token", sa.String(255), nullable=True))

    # Add password reset fields
    op.add_column("users", sa.Column("password_reset_token", sa.String(255), nullable=True))
    op.add_column("users", sa.Column("password_reset_expires", sa.DateTime, nullable=True))

    # Add last_login
    op.add_column("users", sa.Column("last_login", sa.DateTime, nullable=True))

    # Add RBAC fields
    op.add_column("users", sa.Column("default_role", sa.String(50), nullable=True, server_default="MEMBER"))
    op.add_column("users", sa.Column("is_system_admin", sa.Boolean, nullable=True, server_default="false"))

    # Add indexes for performance
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_index("ix_users_id", "users", ["id"])

    # Add comments
    op.execute(
        """
        COMMENT ON COLUMN users.username IS 'Optional username for login (email is primary)';
        COMMENT ON COLUMN users.personal_contexts_limit IS 'Max personal contexts allowed per user';
        COMMENT ON COLUMN users.verification_token IS 'Email verification token';
        COMMENT ON COLUMN users.password_reset_token IS 'Token for password reset flow';
        COMMENT ON COLUMN users.password_reset_expires IS 'Expiration time for password reset token';
        COMMENT ON COLUMN users.last_login IS 'Timestamp of last successful login';
        COMMENT ON COLUMN users.default_role IS 'Default RBAC role for new contexts';
        COMMENT ON COLUMN users.is_system_admin IS 'System-wide admin privileges';
    """
    )


def downgrade() -> None:
    """Remove added columns from users table"""

    op.drop_index("ix_users_id", table_name="users")
    op.drop_index("ix_users_username", table_name="users")

    op.drop_column("users", "is_system_admin")
    op.drop_column("users", "default_role")
    op.drop_column("users", "last_login")
    op.drop_column("users", "password_reset_expires")
    op.drop_column("users", "password_reset_token")
    op.drop_column("users", "verification_token")
    op.drop_column("users", "personal_contexts_limit")
    op.drop_column("users", "username")
