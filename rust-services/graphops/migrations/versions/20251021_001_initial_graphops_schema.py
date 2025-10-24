#!/usr/bin/env python3
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
#
"""initial graphops schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-10-21 16:00:00.000000

This migration tracks the existing Apache AGE schema created by init scripts.
It does not create the schema (already exists), but establishes the migration baseline.

"""
import os

import sqlalchemy as sa

from alembic import op

GRAPH_NAME = (
    os.getenv("GRAPHOPS_GRAPH_NAME") or os.getenv("AGE_GRAPH_NAME") or os.getenv("GRAPH_NAME") or "ninaivalaigal_graph"
)


# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """
    Record baseline - Apache AGE graph schema already exists.

    Schema was created by:
    - containers/graph-db/init-scripts/01-init-age.sql
    - containers/graph-db/init-scripts/02-create-graph.sql

    This migration establishes the Alembic version control baseline.
    """
    bind = op.get_bind()
    bind.execute(sa.text("SELECT 1 FROM pg_extension WHERE extname = 'age'"))

    exists = bind.execute(
        sa.text("SELECT 1 FROM ag_catalog.ag_graph WHERE name = :graph_name"),
        {"graph_name": GRAPH_NAME},
    ).scalar()

    if exists is None:
        raise RuntimeError(f"Apache AGE graph '{GRAPH_NAME}' is not registered")

    print("✅ Verified Apache AGE schema baseline")
    print("   - AGE extension installed")
    print(f"   - {GRAPH_NAME} exists")
    print("   - Ready for index optimizations")


def downgrade():
    """
    Cannot downgrade baseline migration.
    AGE schema is foundational and managed by init scripts.
    """
    print("⚠️  Cannot downgrade baseline migration")
    print("   AGE schema is managed by init scripts")
