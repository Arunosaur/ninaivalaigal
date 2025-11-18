"""Add memory transfers and copies schema

Revision ID: 0146
Revises: 0145
Create Date: 2025-01-27

SPEC-128 Phase 1: Memory Transfer & Copy Operations (US#846)
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0146"
down_revision = "0145"
branch_labels = None
depends_on = None


def upgrade():
    # Create memory_transfers table (immutable)
    op.create_table(
        "memory_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("memory_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("from_user_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "to_user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True
        ),  # NULL for team/org transfers
        sa.Column("to_team_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("to_org_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("transfer_type", sa.String(20), nullable=False),  # user, team, org
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="pending"
        ),  # pending, accepted, rejected, completed
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("transferred_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("accepted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Index("idx_memory_transfers_memory", "memory_id"),
        sa.Index("idx_memory_transfers_from", "from_user_id"),
        sa.Index("idx_memory_transfers_status", "status"),
        sa.Index("idx_memory_transfers_created", "created_at"),
        comment="Memory transfer history (immutable) - SPEC-128",
    )

    # Create memory_copies table
    op.create_table(
        "memory_copies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("original_memory_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("copy_memory_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True, index=True),
        sa.Column("copied_by", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("copied_to_user_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("copied_to_team_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("copied_to_org_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("copy_type", sa.String(20), nullable=False),  # user, team, org
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Index("idx_memory_copies_original", "original_memory_id"),
        sa.Index("idx_memory_copies_copy", "copy_memory_id"),
        sa.Index("idx_memory_copies_created", "created_at"),
        comment="Memory copy tracking - SPEC-128",
    )

    # Add transfer/copy tracking columns to memories table
    op.add_column("memories", sa.Column("derived_from", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("memories", sa.Column("transfer_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("memories", sa.Column("copy_id", postgresql.UUID(as_uuid=True), nullable=True))

    op.create_index("idx_memories_derived_from", "memories", ["derived_from"])
    op.create_index("idx_memories_transfer", "memories", ["transfer_id"])
    op.create_index("idx_memories_copy", "memories", ["copy_id"])

    # Create approval_requests table (for Phase 2)
    op.create_table(
        "approval_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "transfer_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("memory_transfers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "approval_type", sa.String(50), nullable=False
        ),  # personal_to_team, team_to_external, org_to_external, transfer_acceptance
        sa.Column("requested_by", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column(
            "approver_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=False
        ),  # List of approver user IDs
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="pending", index=True
        ),  # pending, approved, rejected, auto_approved
        sa.Column("approved_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("approved_at", sa.DateTime, nullable=True),
        sa.Column("rejected_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime, nullable=True),
        sa.Column("comment", sa.Text, nullable=True),
        sa.Column("rejection_reason", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index("idx_approval_requests_transfer", "transfer_id"),
        sa.Index("idx_approval_requests_status", "status"),
        sa.Index("idx_approval_requests_created", "created_at"),
        comment="Approval requests for memory transfers (SPEC-128 Phase 2)",
    )

    # Create sharing_audit_log table (for Phase 3)
    op.create_table(
        "sharing_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("action", sa.String(20), nullable=False, index=True),  # share, transfer, copy, revoke
        sa.Column("memory_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("from_entity_type", sa.String(20), nullable=False),  # user, team, org
        sa.Column("from_entity_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("to_entity_type", sa.String(20), nullable=False),  # user, team, org
        sa.Column("to_entity_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("performed_by", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("permission", sa.String(20), nullable=True),  # read, read-write, admin
        sa.Column("is_external", sa.String(10), nullable=False, server_default="false"),  # true if external sharing
        sa.Column("revoked_at", sa.DateTime, nullable=True),
        sa.Column("revoked_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Index("idx_sharing_audit_memory", "memory_id"),
        sa.Index("idx_sharing_audit_performed_by", "performed_by"),
        sa.Index("idx_sharing_audit_timestamp", "timestamp"),
        sa.Index("idx_sharing_audit_action", "action"),
        sa.Index("idx_sharing_audit_from", "from_entity_id", "from_entity_type"),
        sa.Index("idx_sharing_audit_to", "to_entity_id", "to_entity_type"),
        comment="Comprehensive audit log for memory sharing operations (SPEC-128 Phase 3)",
    )

    # Create ma_operations table (for Phase 4)
    op.create_table(
        "ma_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("from_org_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("to_org_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("operation_type", sa.String(50), nullable=False),  # org_transfer, bulk_transfer, team_migration
        sa.Column(
            "status", sa.String(20), nullable=False, server_default="pending", index=True
        ),  # pending, in_progress, completed, failed, rolled_back
        sa.Column("initiated_by", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("executed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("reason", sa.Text, nullable=True),
        sa.Column("rolled_back_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rolled_back_at", sa.DateTime, nullable=True),
        sa.Column("rollback_reason", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index("idx_ma_operations_from_org", "from_org_id"),
        sa.Index("idx_ma_operations_to_org", "to_org_id"),
        sa.Index("idx_ma_operations_status", "status"),
        sa.Index("idx_ma_operations_created", "created_at"),
        comment="M&A operations for organization transfers (SPEC-128 Phase 4)",
    )

    # Create memory_visibility table (for Phase 5)
    op.create_table(
        "memory_visibility",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("memory_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("visible_to_entity_type", sa.String(20), nullable=False),  # user, team, org, public
        sa.Column("visible_to_entity_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),  # NULL for public
        sa.Column("visibility_level", sa.String(20), nullable=False),  # private, shared, team, org, public
        sa.Column("access_level", sa.String(20), nullable=False, server_default="read"),  # read, write, admin
        sa.Column("granted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("granted_via", sa.String(50), nullable=True),  # share, transfer, copy, ma_operation, etc.
        sa.Column("source_entity_type", sa.String(20), nullable=True),  # user, team, org
        sa.Column("source_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column("revoked_at", sa.DateTime, nullable=True),
        sa.Column("revoked_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Index("idx_memory_visibility_memory", "memory_id"),
        sa.Index("idx_memory_visibility_entity", "visible_to_entity_type", "visible_to_entity_id"),
        sa.Index("idx_memory_visibility_level", "visibility_level"),
        sa.Index(
            "idx_memory_visibility_active",
            "memory_id",
            "visible_to_entity_type",
            "visible_to_entity_id",
            postgresql_where=sa.text("revoked_at IS NULL"),
        ),
        comment="Memory visibility tracking - who can see what (SPEC-128 Phase 5)",
    )


def downgrade():
    op.drop_table("memory_visibility")
    op.drop_table("ma_operations")
    op.drop_table("sharing_audit_log")
    op.drop_table("approval_requests")
    op.drop_index("idx_memories_copy", "memories")
    op.drop_index("idx_memories_transfer", "memories")
    op.drop_index("idx_memories_derived_from", "memories")
    op.drop_column("memories", "copy_id")
    op.drop_column("memories", "transfer_id")
    op.drop_column("memories", "derived_from")
    op.drop_table("memory_copies")
    op.drop_table("memory_transfers")
