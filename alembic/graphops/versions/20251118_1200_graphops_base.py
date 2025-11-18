"""graphops_base

Create base schema for GraphOps service.

Revision ID: 20251118_1200_graphops_base
Revises: 
Create Date: 2025-11-18 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251118_1200_graphops_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Note: ag_catalog schema is created by Apache AGE extension
    # We only create our application-specific tables here
    
    # GraphOps registry tables
    op.create_table(
        "graph_schema_registry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("schema_name", sa.String(length=100), nullable=False),
        sa.Column("schema_version", sa.String(length=20), nullable=False),
        sa.Column("schema_definition", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("schema_name", "schema_version"),
        schema="ag_catalog",
    )


def downgrade() -> None:
    op.drop_table("graph_schema_registry", schema="ag_catalog")
