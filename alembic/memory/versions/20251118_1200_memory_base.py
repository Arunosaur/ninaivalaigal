"""memory_base

Create base schema for Memory service.

Revision ID: 20251118_1200_memory_base
Revises: 
Create Date: 2025-11-18 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251118_1200_memory_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create memory schema
    op.execute("CREATE SCHEMA IF NOT EXISTS memory")
    
    # Memory relationships
    op.create_table(
        "memory_relationships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_memory_id", sa.Integer(), nullable=False),
        sa.Column("target_memory_id", sa.Integer(), nullable=False),
        sa.Column("relationship_type", sa.String(length=50), nullable=False),
        sa.Column("strength", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="memory",
    )


def downgrade() -> None:
    op.drop_table("memory_relationships", schema="memory")
