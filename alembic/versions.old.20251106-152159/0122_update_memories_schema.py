#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Update memories schema to match application model

Revision ID: 0122_update_memories_schema
Revises: 0121_deferrable_org_fks
Create Date: 2025-10-28 13:45:00.000000

Changes:
- Rename 'content' column to 'data' (JSONB) for flexible memory storage
- Add 'context' column (String) for memory categorization
- Add 'type' column (String) for memory type classification
- Add 'source' column (String) for memory origin tracking
- Remove old embedding column (will use pgvector separately)
- Remove team_id and context_id foreign keys (not used in current model)
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0122_update_memories_schema"
down_revision = "0121_deferrable_org_fks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Update memories table to match application model."""

    from sqlalchemy import inspect

    conn = op.get_bind()
    inspector = inspect(conn)

    # Get existing columns
    existing_columns = {col["name"] for col in inspector.get_columns("memories")}
    existing_constraints = {fk["name"] for fk in inspector.get_foreign_keys("memories")}

    # Drop old foreign key constraints that are no longer used (if they exist)
    if "fk_memories_team" in existing_constraints:
        op.drop_constraint("fk_memories_team", "memories", type_="foreignkey")

    if "fk_memories_context" in existing_constraints:
        op.drop_constraint("fk_memories_context", "memories", type_="foreignkey")

    # Drop unused columns (if they exist)
    if "team_id" in existing_columns:
        op.drop_column("memories", "team_id")

    if "context_id" in existing_columns:
        op.drop_column("memories", "context_id")

    if "embedding" in existing_columns:
        op.drop_column("memories", "embedding")

    if "is_active" in existing_columns:
        op.drop_column("memories", "is_active")

    # Add data column if it doesn't exist
    if "data" not in existing_columns:
        op.add_column("memories", sa.Column("data", postgresql.JSONB, nullable=True))

        # Migrate existing content to data as JSON if content column exists
        if "content" in existing_columns:
            op.execute(
                """
                UPDATE memories
                SET data = jsonb_build_object('content', content)
                WHERE content IS NOT NULL
            """
            )

            # Drop old content column
            op.drop_column("memories", "content")

        # Make data column required
        op.execute("UPDATE memories SET data = '{}'::jsonb WHERE data IS NULL")
        op.alter_column("memories", "data", nullable=False)

    # Add new required columns if they don't exist
    if "context" not in existing_columns:
        op.add_column("memories", sa.Column("context", sa.String(255), nullable=True))
        op.execute("UPDATE memories SET context = 'migrated' WHERE context IS NULL")
        op.alter_column("memories", "context", nullable=False)
        op.create_index("idx_memories_context", "memories", ["context"])

    if "type" not in existing_columns:
        op.add_column("memories", sa.Column("type", sa.String(100), nullable=True))
        op.execute("UPDATE memories SET type = 'legacy' WHERE type IS NULL")
        op.alter_column("memories", "type", nullable=False)
        op.create_index("idx_memories_type", "memories", ["type"])

    if "source" not in existing_columns:
        op.add_column("memories", sa.Column("source", sa.String(255), nullable=True))
        op.execute("UPDATE memories SET source = 'migration' WHERE source IS NULL")
        op.alter_column("memories", "source", nullable=False)
        op.create_index("idx_memories_source", "memories", ["source"])

    # Add created_at index if it doesn't exist
    existing_indexes = {idx["name"] for idx in inspector.get_indexes("memories")}
    if "idx_memories_created_at" not in existing_indexes:
        op.create_index("idx_memories_created_at", "memories", ["created_at"])


def downgrade() -> None:
    """Revert memories table to previous schema."""

    # Drop new indexes
    op.drop_index("idx_memories_created_at", "memories")
    op.drop_index("idx_memories_source", "memories")
    op.drop_index("idx_memories_type", "memories")
    op.drop_index("idx_memories_context", "memories")

    # Drop new columns
    op.drop_column("memories", "source")
    op.drop_column("memories", "type")
    op.drop_column("memories", "context")

    # Add back content column
    op.add_column("memories", sa.Column("content", sa.Text, nullable=True))

    # Migrate data back to content
    op.execute(
        """
        UPDATE memories
        SET content = data->>'content'
        WHERE data IS NOT NULL
    """
    )

    # Drop data column
    op.drop_column("memories", "data")

    # Make content required
    op.alter_column("memories", "content", nullable=False)

    # Add back old columns
    op.add_column("memories", sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("memories", sa.Column("context_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("memories", sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True))
    op.add_column("memories", sa.Column("is_active", sa.Boolean, server_default=sa.text("true")))

    # Recreate foreign keys
    op.create_foreign_key("fk_memories_team", "memories", "teams", ["team_id"], ["id"])
    op.create_foreign_key("fk_memories_context", "memories", "contexts", ["context_id"], ["id"])
