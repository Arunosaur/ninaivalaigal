#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""SPEC-032: Memory Attachments Database Schema

Revision ID: 0143_memory_attachments
Revises: 0142_spec147_part3
Create Date: 2025-01-15 10:00:00

US#326: Memory Attachments Database Schema
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0144_memory_attachments"
down_revision = "0143_memory_attachments"
branch_labels = None
depends_on = None


def upgrade():
    """Create memory_attachments table for SPEC-032"""

    op.create_table(
        "memory_attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("memory_id", sa.Text, nullable=False),
        sa.Column("user_id", sa.Text, nullable=False),
        sa.Column("filename", sa.Text, nullable=False),
        sa.Column("content_type", sa.Text, nullable=False),
        sa.Column("size", sa.BigInteger, nullable=False),
        sa.Column("storage_key", sa.Text, nullable=False),
        sa.Column("storage_backend", sa.Text, nullable=False, server_default="s3"),
        sa.Column("attachment_metadata", postgresql.JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )

    # Create indexes for performance
    op.create_index("ix_memory_attachments_memory_id", "memory_attachments", ["memory_id"])

    op.create_index("ix_memory_attachments_user_id", "memory_attachments", ["user_id"])

    op.create_index("ix_memory_attachments_storage_key", "memory_attachments", ["storage_key"], unique=True)

    op.create_index("ix_memory_attachments_created_at", "memory_attachments", ["created_at"])

    # Composite index for common queries (list attachments by memory and user)
    op.create_index("ix_memory_attachments_memory_user", "memory_attachments", ["memory_id", "user_id", "created_at"])


def downgrade():
    """Drop memory_attachments table"""
    op.drop_index("ix_memory_attachments_memory_user", table_name="memory_attachments")
    op.drop_index("ix_memory_attachments_created_at", table_name="memory_attachments")
    op.drop_index("ix_memory_attachments_storage_key", table_name="memory_attachments")
    op.drop_index("ix_memory_attachments_user_id", table_name="memory_attachments")
    op.drop_index("ix_memory_attachments_memory_id", table_name="memory_attachments")
    op.drop_table("memory_attachments")
