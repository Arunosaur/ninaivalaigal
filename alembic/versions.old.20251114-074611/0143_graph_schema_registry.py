"""Add graph schema registry tables

Revision ID: 0143
Revises: 0142
Create Date: 2025-11-09

GRAPH-FED-001: Graph Schema Registry (US#984)
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0143"
down_revision = "0142"
branch_labels = None
depends_on = None


def upgrade():
    # Create graph_schemas table
    op.create_table(
        "graph_schemas",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("service_name", sa.String(100), nullable=False),
        sa.Column("schema_name", sa.String(100), nullable=False),
        sa.Column("version", sa.String(50), nullable=False, server_default="1.0.0"),
        sa.Column("vertex_labels", postgresql.JSONB, nullable=False),
        sa.Column("edge_labels", postgresql.JSONB, nullable=False),
        sa.Column("properties", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index("idx_graph_schemas_service", "service_name"),
        sa.Index("idx_graph_schemas_name_version", "service_name", "schema_name", "version"),
        comment="Graph schema registry for cross-service federation (GRAPH-FED-001)",
    )

    # Create schema_mappings table
    op.create_table(
        "schema_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_schema_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("graph_schemas.id"), nullable=False),
        sa.Column("target_schema_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("graph_schemas.id"), nullable=False),
        sa.Column("mapping_rules", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Index("idx_schema_mappings_source", "source_schema_id"),
        sa.Index("idx_schema_mappings_target", "target_schema_id"),
        comment="Schema mappings for cross-service graph federation (GRAPH-FED-001)",
    )

    # Create schema_versions table
    op.create_table(
        "schema_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("schema_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("graph_schemas.id"), nullable=False),
        sa.Column("version", sa.String(50), nullable=False),
        sa.Column("schema_definition", postgresql.JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Index("idx_schema_versions_schema", "schema_id"),
        sa.Index("idx_schema_versions_created", "created_at"),
        comment="Schema version history for graph schemas (GRAPH-FED-001)",
    )


def downgrade():
    op.drop_table("schema_versions")
    op.drop_table("schema_mappings")
    op.drop_table("graph_schemas")
