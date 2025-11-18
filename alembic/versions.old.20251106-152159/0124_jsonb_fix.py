#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Fix public.memories table: Convert JSON to JSONB

Revision ID: 0123a_jsonb_fix
Revises: 0123_consolidate_user_tables
Create Date: 2025-10-31 00:54:00.000000

ARCHITECTURAL FIX:
==================
This migration fixes a data type issue in the old public.memories table.
PostgreSQL best practice is to use JSONB (binary JSON) instead of JSON for:
- Better performance
- Indexing support (GIN indexes)
- More efficient storage
- Native operators

This migration:
1. Converts the 'data' column from JSON to JSONB
2. Ensures data integrity during conversion
3. Prepares the table for proper migration in 0124

This is a prerequisite for the clean schema migration (0124).
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0124_jsonb_fix"
down_revision = "0123_consolidate_user_tables"
branch_labels = None
depends_on = None


def upgrade():
    """Convert public.memories.data from JSON to JSONB."""

    # Check if public.memories table exists and has JSON data column
    op.execute(
        """
        DO $$
        BEGIN
            -- Check if table exists and has 'data' column as JSON
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'memories'
                AND column_name = 'data'
                AND data_type = 'json'
            ) THEN
                -- Convert JSON to JSONB (PostgreSQL handles this automatically)
                ALTER TABLE public.memories
                ALTER COLUMN data TYPE JSONB USING data::jsonb;

                RAISE NOTICE 'Converted public.memories.data from JSON to JSONB';
            ELSE
                RAISE NOTICE 'Table public.memories.data is already JSONB or does not exist';
            END IF;
        END $$;
    """
    )


def downgrade():
    """Revert JSONB back to JSON (not recommended)."""

    op.execute(
        """
        DO $$
        BEGIN
            -- Check if table exists and has 'data' column as JSONB
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'memories'
                AND column_name = 'data'
                AND data_type = 'jsonb'
            ) THEN
                -- Convert JSONB back to JSON
                ALTER TABLE public.memories
                ALTER COLUMN data TYPE JSON USING data::json;

                RAISE NOTICE 'Converted public.memories.data from JSONB back to JSON';
            END IF;
        END $$;
    """
    )
