#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Add vector embeddings to graph nodes

Revision ID: 0113_vector_embeddings_on_graph
Revises: 0112_staff_management
Create Date: 2025-10-11 00:10:00.000000

This migration completes the three-tier hybrid architecture by adding
pgvector embedding columns to Apache AGE graph nodes (Token and Memory).

This enables:
- Semantic similarity search via pgvector
- Dynamic SIMILAR_TO edge computation based on embeddings
- Hybrid queries combining graph traversal + vector similarity
- Contextual relevance ranking (SPEC-041, SPEC-067)

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0113_vector_embeddings_on_graph"
down_revision = "0112_staff_management"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add vector embedding columns to graph nodes for semantic similarity."""

    # Add embedding column to Token graph node
    # Token represents atomic semantic elements (chunks, phrases, code, events)
    op.execute(
        """
        ALTER TABLE ninaivalaigal_intelligence."Token"
        ADD COLUMN IF NOT EXISTS embedding vector(1536);
    """
    )

    # Add embedding column to Memory graph node
    # Memory represents persisted intelligence or experience
    op.execute(
        """
        ALTER TABLE ninaivalaigal_intelligence."Memory"
        ADD COLUMN IF NOT EXISTS embedding vector(1536);
    """
    )

    # Optional: Add embedding to Context for high-dimensional attention windows
    op.execute(
        """
        ALTER TABLE ninaivalaigal_intelligence."Context"
        ADD COLUMN IF NOT EXISTS embedding vector(1536);
    """
    )

    # Create IVFFLAT indexes for fast approximate nearest neighbor search
    # Lists parameter: sqrt(row_count) is typical heuristic (100 for small datasets)
    # Will need tuning based on actual data volume

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_token_embedding
        ON ninaivalaigal_intelligence."Token"
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_memory_embedding
        ON ninaivalaigal_intelligence."Memory"
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_context_embedding
        ON ninaivalaigal_intelligence."Context"
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100);
    """
    )

    # Add comment explaining the hybrid architecture
    op.execute(
        """
        COMMENT ON COLUMN ninaivalaigal_intelligence."Token".embedding IS
        'OpenAI text-embedding-3-small (1536 dim) for semantic similarity search.
        Enables dynamic SIMILAR_TO edge inference and hybrid graph+vector queries.';
    """
    )

    op.execute(
        """
        COMMENT ON COLUMN ninaivalaigal_intelligence."Memory".embedding IS
        'Embedding of memory content for semantic retrieval (RAG).
        Used for contextual recall and relevance ranking within teams/users.';
    """
    )


def downgrade() -> None:
    """Remove vector embedding columns and indexes from graph nodes."""

    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS ninaivalaigal_intelligence.idx_context_embedding;")
    op.execute("DROP INDEX IF EXISTS ninaivalaigal_intelligence.idx_memory_embedding;")
    op.execute("DROP INDEX IF EXISTS ninaivalaigal_intelligence.idx_token_embedding;")

    # Drop columns
    op.execute('ALTER TABLE ninaivalaigal_intelligence."Context" DROP COLUMN IF EXISTS embedding;')
    op.execute('ALTER TABLE ninaivalaigal_intelligence."Memory" DROP COLUMN IF EXISTS embedding;')
    op.execute('ALTER TABLE ninaivalaigal_intelligence."Token" DROP COLUMN IF EXISTS embedding;')
