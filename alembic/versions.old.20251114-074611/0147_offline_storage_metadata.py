"""Add offline storage metadata tables

Revision ID: 0147_offline_storage_metadata
Revises: 0146_memory_transfers_copies
Create Date: 2025-01-XX

SPEC-142 Phase 1.1: Database Setup & Basic Operations
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0147_offline_storage_metadata"
down_revision = "0146_memory_transfers_copies"
branch_labels = None
depends_on = None


def upgrade():
    # Create offline_storage_metadata table
    op.create_table(
        "offline_storage_metadata",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("cached_at", sa.DateTime(), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("sync_status", sa.String(), nullable=True),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_offline_storage_metadata_user_id", "offline_storage_metadata", ["user_id"])
    op.create_index("ix_offline_storage_metadata_entity_id", "offline_storage_metadata", ["entity_id"])

    # Create sync_queue table
    op.create_table(
        "sync_queue",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.String(), nullable=False),
        sa.Column("operation_type", sa.String(), nullable=False),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=True),
        sa.Column("operation_data", postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column("priority", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sync_queue_user_id", "sync_queue", ["user_id"])


def downgrade():
    op.drop_index("ix_sync_queue_user_id", table_name="sync_queue")
    op.drop_table("sync_queue")
    op.drop_index("ix_offline_storage_metadata_entity_id", table_name="offline_storage_metadata")
    op.drop_index("ix_offline_storage_metadata_user_id", table_name="offline_storage_metadata")
    op.drop_table("offline_storage_metadata")
