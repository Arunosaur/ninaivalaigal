"""Add context bridges schema

Revision ID: 0145
Revises: 0144
Create Date: 2025-01-27

SPEC-127 Phase 1: Context Bridge Foundation (US#841)
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0145"
down_revision = "0144"
branch_labels = None
depends_on = None


def upgrade():
    # Create context_bridges table
    op.create_table(
        "context_bridges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("mode", sa.String(20), nullable=False, server_default="reference"),  # reference, clone, hybrid
        sa.Column("trust_score", sa.Numeric(5, 2), nullable=False, server_default="50.0"),  # 0-100
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),  # pending, active, revoked
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime, nullable=True),
        sa.Index("idx_context_bridges_source", "source_context_id"),
        sa.Index("idx_context_bridges_target", "target_context_id"),
        sa.Index("idx_context_bridges_status", "status"),
        sa.Index("idx_context_bridges_source_target", "source_context_id", "target_context_id"),
        sa.UniqueConstraint("source_context_id", "target_context_id", "status", name="uq_context_bridges_active"),
        comment="Context bridges for cross-context memory sharing (SPEC-127)",
    )

    # Create trust_scores table
    op.create_table(
        "trust_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("trust_score", sa.Numeric(5, 2), nullable=False),  # 0-100
        sa.Column("components", postgresql.JSONB, nullable=True),  # Breakdown: org_reputation, access_history, etc.
        sa.Column("calculated_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime, nullable=True),  # For caching
        sa.Index("idx_trust_scores_source", "source_context_id"),
        sa.Index("idx_trust_scores_target", "target_context_id"),
        sa.Index("idx_trust_scores_source_target", "source_context_id", "target_context_id"),
        sa.Index("idx_trust_scores_calculated", "calculated_at"),
        sa.UniqueConstraint("source_context_id", "target_context_id", name="uq_trust_scores_contexts"),
        comment="Trust score cache and history (SPEC-127)",
    )

    # Create bridge_access_history table
    op.create_table(
        "bridge_access_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "bridge_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("context_bridges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("accessor_context_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("access_type", sa.String(20), nullable=False),  # read, write, sync, create, revoke
        sa.Column("trust_score_at_access", sa.Numeric(5, 2), nullable=False),
        sa.Column("success", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("accessed_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Index("idx_bridge_access_bridge", "bridge_id"),
        sa.Index("idx_bridge_access_accessor", "accessor_context_id"),
        sa.Index("idx_bridge_access_type", "access_type"),
        sa.Index("idx_bridge_access_accessed", "accessed_at"),
        sa.Index("idx_bridge_access_success", "success"),
        comment="Audit trail for bridge access (SPEC-127)",
    )

    # Create sync_policies table (for Phase 2, but included in schema)
    op.create_table(
        "sync_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "bridge_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("context_bridges.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "sync_trigger", sa.String(20), nullable=False, server_default="manual"
        ),  # on_update, scheduled, manual
        sa.Column("schedule_config", postgresql.JSONB, nullable=True),  # For scheduled syncs
        sa.Column("last_synced_at", sa.DateTime, nullable=True),
        sa.Column("next_sync_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index("idx_sync_policies_bridge", "bridge_id"),
        sa.Index("idx_sync_policies_next_sync", "next_sync_at"),
        comment="Sync policies for hybrid mode bridges (SPEC-127 Phase 2)",
    )


def downgrade():
    op.drop_table("sync_policies")
    op.drop_table("bridge_access_history")
    op.drop_table("trust_scores")
    op.drop_table("context_bridges")
