#!/usr/bin/env python3
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
"""add GIN indexes for AGE Cypher containment queries

Revision ID: 003_gin_indexes
Revises: 002_age_indexes
Create Date: 2025-10-22 02:21:00.000000

Fixes latency issue where AGE Cypher planner uses properties @> containment
checks instead of extracted property expressions. GIN indexes with agtype_ops
support the @> operator used by Cypher's pattern matching.

Based on Developer A's investigation showing:
- AGE Cypher: properties @> '{"id": "perf_user_001"}'::agtype
- Previous indexes: agtype_to_text(...) = '...' (not matched by planner)
- Solution: GIN indexes on properties column for fast containment checks

"""
import os

import sqlalchemy as sa

from alembic import op

GRAPH_NAME = (
    os.getenv("GRAPHOPS_GRAPH_NAME") or os.getenv("AGE_GRAPH_NAME") or os.getenv("GRAPH_NAME") or "ninaivalaigal_graph"
)

GRAPH_SCHEMA = os.getenv("GRAPHOPS_GRAPH_SCHEMA", GRAPH_NAME)

# GIN indexes for Cypher containment queries
# These support the @> operator used by AGE's query planner
GIN_INDEX_SPECS = [
    ("User", "idx_user_properties_gin"),
    ("Memory", "idx_memory_properties_gin"),
    ("Context", "idx_context_properties_gin"),
    ("Team", "idx_team_properties_gin"),
    ("Agent", "idx_agent_properties_gin"),
    ("Organization", "idx_organization_properties_gin"),
]


# revision identifiers, used by Alembic.
revision = "003_gin_indexes"
down_revision = "002_age_indexes"
branch_labels = None
depends_on = None


def upgrade():
    """
    Create GIN indexes on properties column for AGE Cypher queries.

    AGE's Cypher planner rewrites queries like:
      MATCH (u:User {id: 'value'})
    Into:
      WHERE properties @> '{"id": "value"}'::agtype

    GIN indexes with agtype_ops support the @> containment operator.
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

    for label, index_name in GIN_INDEX_SPECS:
        if not table_exists(label):
            skipped.append(f"{index_name} (table {label} missing)")
            continue

        try:
            # Create GIN index on properties with agtype_ops
            op.execute(
                f"""
                CREATE INDEX IF NOT EXISTS {index_name}
                ON "{GRAPH_SCHEMA}"."{label}"
                USING gin (properties)
                """
            )
            created.append(index_name)
        except Exception as e:
            skipped.append(f"{index_name} (error: {str(e)[:50]})")

    if created:
        print(f"✅ Created {len(created)} GIN indexes on {GRAPH_SCHEMA}")
        print(f"   Indexes: {', '.join(created)}")
        print(f"   These support AGE Cypher containment queries (@> operator)")
    if skipped:
        print(f"⚠️  Skipped {len(skipped)} indexes:")
        for skip in skipped:
            print(f"   - {skip}")


def downgrade():
    """
    Remove GIN indexes.
    """
    op.execute(f'SET search_path = "{GRAPH_SCHEMA}", ag_catalog, "$user", public;')

    dropped = []
    for _, index_name in reversed(GIN_INDEX_SPECS):
        try:
            op.execute(f'DROP INDEX IF EXISTS "{GRAPH_SCHEMA}".{index_name}')
            dropped.append(index_name)
        except Exception:
            pass

    print(f"✅ Dropped {len(dropped)} GIN indexes for {GRAPH_SCHEMA}")
