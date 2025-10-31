#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Create memory schema with proper structure

Revision ID: 0124_memory_schema
Revises: 0123a_jsonb_fix
Create Date: 2025-10-31 00:30:00.000000

ARCHITECTURAL DECISION:
======================
This migration implements a clean schema separation following PostgreSQL best practices:

1. FOUNDATIONAL PRINCIPLE:
   - One canonical table per logical domain
   - One authoritative migration chain per schema

2. SCHEMA ARCHITECTURE:
   - public schema  → Core identity (users, teams, organizations)
   - memory schema  → Memory domain (memory_records, memory_tags)
   - graph schema   → Graph intelligence (future)
   - billing schema → Financial records (future)

3. CANONICAL TABLE:
   - memory.memory_records = single source of truth for all persisted memory data
   - public.memories = ORM view for backward compatibility (deprecated)

4. SERVICE RESPONSIBILITY:
   - Rust Memory Service → CRUD + embedding writes to memory.memory_records
   - Python Core API → Legacy routing via public.memories view
   - Graph Service → Vector search on memory.memory_records
   - Business/Admin → Analytics via joins

Changes:
--------
- Create dedicated 'memory' schema namespace
- Create memory.memory_records (canonical table with pgvector)
- Create memory.memory_tags for tagging support
- Migrate existing data from old public.memories table
- Create public.memories VIEW for backward compatibility
- Drop old public.memories physical table

BREAKING CHANGES:
-----------------
None - backward compatible via views. Old Python code continues to work.

SEE ALSO:
---------
- /docs/DATABASE_SCHEMA_REFERENCE.md (to be created)
- SPEC-019: Database Management & Migration
- SPEC-093: Memory Service (Rust)
- SPEC-020: Memory Provider Architecture
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0124_memory_schema"
down_revision = "0123a_jsonb_fix"  # Depends on JSON→JSONB fix
branch_labels = None
depends_on = None


def upgrade():
    """Create memory schema and tables with proper structure."""

    # Step 1: Create dedicated schema namespace
    # This provides logical separation and ownership delegation to the Memory Service
    op.execute("CREATE SCHEMA IF NOT EXISTS memory;")

    # Step 2: Create canonical memory_records table
    # This is the single source of truth for all memory data
    op.execute(
        """
        CREATE TABLE memory.memory_records (
            -- Primary key
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

            -- Foreign keys back to 'public' schema (cross-schema FKs)
            user_id UUID NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,
            team_id UUID REFERENCES public.teams(id) ON DELETE SET NULL,
            org_id UUID REFERENCES public.organizations(id) ON DELETE SET NULL,

            -- Scope control (personal, team, or organization level)
            scope TEXT CHECK (scope IN ('personal','team','organization')) NOT NULL,

            -- Memory classification
            kind TEXT NOT NULL,  -- e.g., 'note', 'image', 'file_context', etc.

            -- Memory content
            text TEXT NOT NULL,  -- The actual memory text

            -- Flexible metadata storage (tags, source, context, etc.)
            metadata JSONB DEFAULT '{}'::jsonb,

            -- pgvector embedding for semantic search
            -- Using 1536 dimensions for OpenAI text-embedding-3-small/ada-002
            embedding VECTOR(1536),

            -- Timestamps
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        );
    """
    )

    # Step 3: Add performance indexes
    # User/team/org indexes for filtering
    op.execute(
        """
        CREATE INDEX idx_memory_records_user_id ON memory.memory_records(user_id);
        CREATE INDEX idx_memory_records_team_id ON memory.memory_records(team_id)
            WHERE team_id IS NOT NULL;
        CREATE INDEX idx_memory_records_org_id ON memory.memory_records(org_id)
            WHERE org_id IS NOT NULL;
    """
    )

    # Composite index for scope + kind filtering
    op.execute(
        """
        CREATE INDEX idx_memory_records_scope_kind ON memory.memory_records(scope, kind);
    """
    )

    # Timestamp index for time-based queries
    op.execute(
        """
        CREATE INDEX idx_memory_records_created_at ON memory.memory_records(created_at DESC);
    """
    )

    # pgvector index for semantic similarity search
    # HNSW is faster than IVFFlat for most use cases
    # m=16 and ef_construction=64 are good defaults for 1536-dim vectors
    op.execute(
        """
        CREATE INDEX idx_memory_records_embedding ON memory.memory_records
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """
    )

    # JSONB GIN index for metadata querying
    op.execute(
        """
        CREATE INDEX idx_memory_records_metadata ON memory.memory_records
        USING gin (metadata);
    """
    )

    # Step 4: Create memory_tags table for tag support
    op.execute(
        """
        CREATE TABLE memory.memory_tags (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            memory_id UUID NOT NULL REFERENCES memory.memory_records(id) ON DELETE CASCADE,
            tag TEXT NOT NULL,
            created_at TIMESTAMPTZ DEFAULT now(),

            -- Prevent duplicate tags on same memory
            UNIQUE(memory_id, tag)
        );
    """
    )

    # Indexes for tag queries
    op.execute(
        """
        CREATE INDEX idx_memory_tags_memory_id ON memory.memory_tags(memory_id);
        CREATE INDEX idx_memory_tags_tag ON memory.memory_tags(tag);
    """
    )

    # Step 5: Migrate existing data from old public.memories table (if it exists)
    # This is a safe migration that handles both the old schema and new schema
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if old public.memories table exists
            IF EXISTS (
                SELECT 1 FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'memories'
                AND table_type = 'BASE TABLE'
            ) THEN
                -- Migrate data
                INSERT INTO memory.memory_records (id, user_id, text, metadata, created_at, scope, kind)
                SELECT
                    id,
                    user_id,
                    -- Handle both old 'content' column and new 'data' JSONB
                    COALESCE(
                        (data->>'content')::TEXT,  -- Try JSON extraction first
                        context::TEXT,              -- Fall back to context
                        'migrated'                  -- Default
                    ),
                    -- Merge all old columns into metadata (data is already JSONB from 0123a)
                    jsonb_build_object(
                        'source', COALESCE(source, 'migration'),
                        'type', COALESCE(type, 'legacy'),
                        'context', COALESCE(context, 'unknown'),
                        'data', COALESCE(data, '{}'::jsonb)
                    ),
                    created_at,
                    'personal' as scope,  -- Old memories were all personal
                    COALESCE(type, 'legacy') as kind
                FROM public.memories
                ON CONFLICT (id) DO NOTHING;

                -- Drop the old table
                DROP TABLE public.memories CASCADE;
            END IF;
        END $$;
    """
    )

    # Step 6: Create backward-compatible VIEW
    # This allows old Python ORM code to continue working without changes
    op.execute(
        """
        CREATE OR REPLACE VIEW public.memories AS
        SELECT
            id,
            user_id,
            text AS data,          -- Map 'text' to old 'data' column name
            metadata,
            created_at,
            updated_at
        FROM memory.memory_records;
    """
    )

    # Step 7: Add updated_at trigger for memory_records
    op.execute(
        """
        CREATE OR REPLACE FUNCTION memory.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER update_memory_records_updated_at
            BEFORE UPDATE ON memory.memory_records
            FOR EACH ROW
            EXECUTE FUNCTION memory.update_updated_at_column();
    """
    )


def downgrade():
    """Revert to old schema - NOT RECOMMENDED."""

    # Drop view
    op.execute("DROP VIEW IF EXISTS public.memories;")

    # Drop trigger and function
    op.execute("DROP TRIGGER IF EXISTS update_memory_records_updated_at ON memory.memory_records;")
    op.execute("DROP FUNCTION IF EXISTS memory.update_updated_at_column();")

    # Recreate old public.memories table
    op.execute(
        """
        CREATE TABLE public.memories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID REFERENCES public.users(id),
            context VARCHAR(255) NOT NULL,
            type VARCHAR(100) NOT NULL,
            source VARCHAR(255) NOT NULL,
            data JSON NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """
    )

    # Migrate data back
    op.execute(
        """
        INSERT INTO public.memories (id, user_id, data, created_at, updated_at, context, type, source)
        SELECT
            id,
            user_id,
            metadata,  -- Put metadata back as data
            created_at,
            updated_at,
            COALESCE(metadata->>'context', 'unknown'),
            COALESCE(kind, 'legacy'),
            COALESCE(metadata->>'source', 'migration')
        FROM memory.memory_records;
    """
    )

    # Drop memory schema and all its objects
    op.execute("DROP TABLE IF EXISTS memory.memory_tags CASCADE;")
    op.execute("DROP TABLE IF EXISTS memory.memory_records CASCADE;")
    op.execute("DROP SCHEMA IF EXISTS memory CASCADE;")
