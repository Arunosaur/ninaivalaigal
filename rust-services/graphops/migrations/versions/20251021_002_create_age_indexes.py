#!/usr/bin/env python3
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
"""create AGE indexes for query performance

Revision ID: 002_age_indexes
Revises: 001_initial_schema
Create Date: 2025-10-21 17:00:00.000000

Fixes 8-10x latency issue discovered in US #86 benchmarking.
Without these indexes, queries perform sequential scans resulting in 40-50ms P95 latency.
With indexes, expected P95 latency is <5ms.

"""
import os

import sqlalchemy as sa

from alembic import op

GRAPH_NAME = (
    os.getenv("GRAPHOPS_GRAPH_NAME") or os.getenv("AGE_GRAPH_NAME") or os.getenv("GRAPH_NAME") or "ninaivalaigal_graph"
)

GRAPH_SCHEMA = os.getenv("GRAPHOPS_GRAPH_SCHEMA", GRAPH_NAME)

# Apache AGE index specifications with correct agtype casting
# Format: (table_name, index_name, expression, is_edge_table)
INDEX_SPECS = [
    # Memory node indexes (vertex properties)
    ("Memory", "idx_memory_id", "(agtype_to_text(properties -> '\"id\"'::agtype))", False),
    ("Memory", "idx_memory_type", "(agtype_to_text(properties -> '\"type\"'::agtype))", False),
    ("Memory", "idx_memory_topic", "(agtype_to_text(properties -> '\"topic\"'::agtype))", False),
    ("Memory", "idx_memory_status", "(agtype_to_text(properties -> '\"status\"'::agtype))", False),
    ("Memory", "idx_memory_updated_at", "(agtype_to_text(properties -> '\"updated_at\"'::agtype))", False),
    ("Memory", "idx_memory_relevance_score", "(agtype_to_float8(properties -> '\"relevance_score\"'::agtype))", False),
    # User node indexes
    ("User", "idx_user_id", "(agtype_to_text(properties -> '\"id\"'::agtype))", False),
    ("User", "idx_user_role", "(agtype_to_text(properties -> '\"role\"'::agtype))", False),
    # Context node indexes
    ("Context", "idx_context_id", "(agtype_to_text(properties -> '\"id\"'::agtype))", False),
    # Team node indexes
    ("Team", "idx_team_id", "(agtype_to_text(properties -> '\"id\"'::agtype))", False),
    # Edge (relationship) indexes on start_id/end_id
    ("CREATED", "idx_created_start_id", "(start_id)", True),
    ("CREATED", "idx_created_end_id", "(end_id)", True),
    ("ACCESSED", "idx_accessed_start_id", "(start_id)", True),
    ("ACCESSED", "idx_accessed_end_id", "(end_id)", True),
    ("TAGGED_WITH", "idx_tagged_with_start_id", "(start_id)", True),
    ("TAGGED_WITH", "idx_tagged_with_end_id", "(end_id)", True),
    ("BELONGS_TO", "idx_belongs_to_start_id", "(start_id)", True),
    ("BELONGS_TO", "idx_belongs_to_end_id", "(end_id)", True),
]


# revision identifiers, used by Alembic.
revision = "002_age_indexes"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    """
    Create indexes on Apache AGE graph properties for query performance.

    Uses correct Apache AGE agtype casting:
    - agtype_to_text() for string properties
    - agtype_to_float8() for numeric properties
    - Direct column indexes for edge start_id/end_id
    """
    bind = op.get_bind()
    op.execute(f'SET search_path = "{GRAPH_SCHEMA}", ag_catalog, "$user", public;')

    created = []
    skipped = []

    def table_exists(label: str) -> bool:
        qualified = f'{GRAPH_SCHEMA}."{label}"'
        result = bind.execute(
            sa.text("SELECT to_regclass(:regclass)"),
            {"regclass": qualified},
        ).scalar()
        return result is not None

    for label, index_name, expression, is_edge in INDEX_SPECS:
        if not table_exists(label):
            skipped.append(f"{index_name} (table {label} missing)")
            continue

        try:
            op.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON "{GRAPH_SCHEMA}"."{label}"
                USING btree {expression}
                """
            )
            created.append(index_name)
        except Exception as e:
            # Log but continue on index creation errors
            skipped.append(f"{index_name} (error: {str(e)[:50]})")

    if created:
        print(f"✅ Created {len(created)} AGE indexes on {GRAPH_SCHEMA}")
        print(f"   Indexes: {', '.join(created[:5])}")
        if len(created) > 5:
            print(f"   ... and {len(created) - 5} more")
    if skipped:
        print(f"⚠️  Skipped {len(skipped)} indexes:")
        for skip in skipped:
            print(f"   - {skip}")


def downgrade():
    """
    Remove AGE indexes.
    """
    op.execute(f'SET search_path = "{GRAPH_SCHEMA}", ag_catalog, "$user", public;')

    dropped = []
    for _, index_name, _, _ in reversed(INDEX_SPECS):
        try:
            op.execute(f'DROP INDEX IF EXISTS "{GRAPH_SCHEMA}".{index_name}')
            dropped.append(index_name)
        except Exception:
            # Ignore errors during downgrade
            pass

    print(f"✅ Dropped {len(dropped)} AGE indexes for {GRAPH_SCHEMA}")
