#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""init pgvector memory schema"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0111_memory_pgvector"
down_revision = "0003_core_tables"
branch_labels = None
depends_on = None


def upgrade():
    """Add memory_records table with pgvector support."""
    # Extensions already installed in 0001, just create table
    op.execute(
        """
    CREATE TABLE IF NOT EXISTS memory_records (
      id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      scope TEXT NOT NULL CHECK (scope IN ('personal','team','organization')),
      user_id TEXT NOT NULL,
      team_id TEXT,
      org_id  TEXT,
      kind    TEXT NOT NULL,
      text    TEXT NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
      embedding vector(8),
      created_at TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """
    )


def downgrade():
    """Remove memory_records table."""
    op.execute("DROP TABLE IF EXISTS memory_records;")
