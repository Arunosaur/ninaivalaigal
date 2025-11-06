# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

"""Add refresh tokens table

Revision ID: 0114_refresh_tokens
Revises: 0113_vector_embeddings_on_graph
Create Date: 2025-10-12 18:40:00

"""

import uuid

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = "0114_refresh_tokens"
down_revision = "0113_vector_embeddings_on_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add refresh_tokens table for JWT token refresh functionality"""

    op.create_table(
        "refresh_tokens",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime, nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime, nullable=True),
        sa.Column("revoked_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("device_info", sa.JSON, nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text, nullable=True),
    )

    # Add indexes for performance
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("ix_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("ix_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    # Add comment
    op.execute(
        """
        COMMENT ON TABLE refresh_tokens IS 'Stores refresh tokens for JWT authentication';
        COMMENT ON COLUMN refresh_tokens.token_hash IS 'SHA256 hash of refresh token for security';
        COMMENT ON COLUMN refresh_tokens.expires_at IS 'Refresh tokens valid for 30 days';
        COMMENT ON COLUMN refresh_tokens.revoked_at IS 'Timestamp when token was explicitly revoked';
        COMMENT ON COLUMN refresh_tokens.device_info IS 'Device information for security tracking';
    """
    )


def downgrade() -> None:
    """Remove refresh_tokens table"""

    op.drop_index("ix_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("ix_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
