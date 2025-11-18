"""intelligence_base

Create base schema for Intelligence service.

Revision ID: 20251118_1200_intelligence_base
Revises: 
Create Date: 2025-11-18 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251118_1200_intelligence_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create intelligence_graph schema
    op.execute("CREATE SCHEMA IF NOT EXISTS intelligence_graph")
    
    # Intelligence insights
    op.create_table(
        "intelligence_insights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("insight_type", sa.String(length=100), nullable=False),
        sa.Column("confidence_score", sa.Float(), nullable=False),
        sa.Column("insight_data", sa.JSON(), nullable=False),
        sa.Column("source_memory_ids", postgresql.ARRAY(sa.Integer()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="intelligence_graph",
    )


def downgrade() -> None:
    op.drop_table("intelligence_insights", schema="intelligence_graph")
