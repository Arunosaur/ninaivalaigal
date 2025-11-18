"""Add memory versioning system tables

Revision ID: 0148_memory_versioning_system
Revises: 0147_offline_storage_metadata
Create Date: 2025-01-XX

SPEC-035: Memory Versioning System Implementation
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0148_memory_versioning_system"
down_revision = "0147_offline_storage_metadata"
branch_labels = None
depends_on = None


def upgrade():
    # Create memory_versions table
    op.create_table(
        "memory_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("memory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("parent_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(64), nullable=False),
        sa.Column("metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("change_type", sa.String(50), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False),
        sa.Column("is_snapshot", sa.Boolean(), nullable=False),
        sa.Column("snapshot_label", sa.String(255), nullable=True),
        sa.ForeignKeyConstraint(
            ["memory_id"],
            ["memories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_version_id"],
            ["memory_versions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("memory_id", "version_number", name="uq_memory_version"),
    )
    op.create_index("ix_memory_versions_id", "memory_versions", ["id"])
    op.create_index("ix_memory_versions_memory_id", "memory_versions", ["memory_id"])
    op.create_index("ix_memory_versions_version_number", "memory_versions", ["version_number"])
    op.create_index("ix_memory_versions_parent_version_id", "memory_versions", ["parent_version_id"])
    op.create_index("ix_memory_versions_content_hash", "memory_versions", ["content_hash"])
    op.create_index("ix_memory_versions_created_by", "memory_versions", ["created_by"])
    op.create_index("ix_memory_versions_created_at", "memory_versions", ["created_at"])
    op.create_index("ix_memory_versions_is_current", "memory_versions", ["is_current"])
    op.create_index("ix_memory_versions_is_snapshot", "memory_versions", ["is_snapshot"])

    # Create version_lineage table
    op.create_table(
        "version_lineage",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("memory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("parent_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("branch_name", sa.String(100), nullable=True),
        sa.Column("merge_from_version_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["memory_id"],
            ["memories.id"],
        ),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["memory_versions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["parent_version_id"],
            ["memory_versions.id"],
        ),
        sa.ForeignKeyConstraint(
            ["merge_from_version_id"],
            ["memory_versions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_version_lineage_id", "version_lineage", ["id"])
    op.create_index("ix_version_lineage_memory_id", "version_lineage", ["memory_id"])
    op.create_index("ix_version_lineage_version_id", "version_lineage", ["version_id"])
    op.create_index("ix_version_lineage_parent_version_id", "version_lineage", ["parent_version_id"])

    # Create version_metadata table
    op.create_table(
        "version_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("version_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tags", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("custom_metadata", postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column("content_length", sa.Integer(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("character_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["version_id"],
            ["memory_versions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("version_id"),
    )
    op.create_index("ix_version_metadata_id", "version_metadata", ["id"])
    op.create_index("ix_version_metadata_version_id", "version_metadata", ["version_id"])


def downgrade():
    op.drop_index("ix_version_metadata_version_id", table_name="version_metadata")
    op.drop_index("ix_version_metadata_id", table_name="version_metadata")
    op.drop_table("version_metadata")
    op.drop_index("ix_version_lineage_parent_version_id", table_name="version_lineage")
    op.drop_index("ix_version_lineage_version_id", table_name="version_lineage")
    op.drop_index("ix_version_lineage_memory_id", table_name="version_lineage")
    op.drop_index("ix_version_lineage_id", table_name="version_lineage")
    op.drop_table("version_lineage")
    op.drop_index("ix_memory_versions_is_snapshot", table_name="memory_versions")
    op.drop_index("ix_memory_versions_is_current", table_name="memory_versions")
    op.drop_index("ix_memory_versions_created_at", table_name="memory_versions")
    op.drop_index("ix_memory_versions_created_by", table_name="memory_versions")
    op.drop_index("ix_memory_versions_content_hash", table_name="memory_versions")
    op.drop_index("ix_memory_versions_parent_version_id", table_name="memory_versions")
    op.drop_index("ix_memory_versions_version_number", table_name="memory_versions")
    op.drop_index("ix_memory_versions_memory_id", table_name="memory_versions")
    op.drop_index("ix_memory_versions_id", table_name="memory_versions")
    op.drop_table("memory_versions")
