"""Core Tables - Users, Teams, Memories

Revision ID: 0003_core_tables
Revises: 0002_apache_age_graph
Create Date: 2025-10-10 22:02:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_core_tables"
down_revision = "0002_apache_age_graph"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create core application tables."""

    # Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(50), nullable=False, server_default="individual"),
        sa.Column("subscription_tier", sa.String(50), nullable=False, server_default="free"),
        sa.Column("role", sa.String(50), nullable=False, server_default="user"),
        sa.Column("created_via", sa.String(50), nullable=False, server_default="api"),
        sa.Column("email_verified", sa.Boolean, server_default=sa.text("true")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_account_type", "users", ["account_type"])
    op.create_index("idx_users_subscription_tier", "users", ["subscription_tier"])

    # Teams table
    op.create_table(
        "teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_teams_owner_id", "teams", ["owner_id"])
    op.create_foreign_key("fk_teams_owner", "teams", "users", ["owner_id"], ["id"])

    # Organizations table
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("domain", sa.String(255)),
        sa.Column("settings", postgresql.JSONB),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_organizations_domain", "organizations", ["domain"])

    # Team memberships table
    op.create_table(
        "team_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="member"),
        sa.Column("joined_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("team_id", "user_id", name="uq_team_user"),
    )
    op.create_index("idx_team_memberships_team", "team_memberships", ["team_id"])
    op.create_index("idx_team_memberships_user", "team_memberships", ["user_id"])
    op.create_foreign_key("fk_team_memberships_team", "team_memberships", "teams", ["team_id"], ["id"])
    op.create_foreign_key("fk_team_memberships_user", "team_memberships", "users", ["user_id"], ["id"])

    # Memories table
    op.create_table(
        "memories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float), nullable=True),  # Will be upgraded to vector in 0111
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("team_id", postgresql.UUID(as_uuid=True)),
        sa.Column("context_id", postgresql.UUID(as_uuid=True)),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_memories_user_id", "memories", ["user_id"])
    op.create_index("idx_memories_team_id", "memories", ["team_id"])
    op.create_index("idx_memories_context_id", "memories", ["context_id"])

    # Contexts table
    op.create_table(
        "contexts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("team_id", postgresql.UUID(as_uuid=True)),
        sa.Column("metadata", postgresql.JSONB),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_contexts_user_id", "contexts", ["user_id"])
    op.create_index("idx_contexts_team_id", "contexts", ["team_id"])

    # Add foreign keys for memories
    op.create_foreign_key("fk_memories_user", "memories", "users", ["user_id"], ["id"])
    op.create_foreign_key("fk_memories_team", "memories", "teams", ["team_id"], ["id"])
    op.create_foreign_key("fk_memories_context", "memories", "contexts", ["context_id"], ["id"])

    # Add foreign keys for contexts
    op.create_foreign_key("fk_contexts_user", "contexts", "users", ["user_id"], ["id"])
    op.create_foreign_key("fk_contexts_team", "contexts", "teams", ["team_id"], ["id"])

    # Tokens table
    op.create_table(
        "tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("token_value", sa.String(255), nullable=False),
        sa.Column("memory_id", postgresql.UUID(as_uuid=True)),
        sa.Column("user_id", postgresql.UUID(as_uuid=True)),
        sa.Column("context_id", postgresql.UUID(as_uuid=True)),
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()")),
    )
    op.create_index("idx_tokens_user_id", "tokens", ["user_id"])
    op.create_index("idx_tokens_memory_id", "tokens", ["memory_id"])
    op.create_foreign_key("fk_tokens_user", "tokens", "users", ["user_id"], ["id"])
    op.create_foreign_key("fk_tokens_memory", "tokens", "memories", ["memory_id"], ["id"])
    op.create_foreign_key("fk_tokens_context", "tokens", "contexts", ["context_id"], ["id"])

    # Insert test user with known UUID for development/testing
    op.execute(
        """
        INSERT INTO users (id, email, name, password_hash, account_type, subscription_tier, role, created_via, email_verified, is_active)
        VALUES (
            '00000000-0000-0000-0000-000000000001'::UUID,
            'test@ninaivalaigal.com',
            'Test User',
            '$2b$12$LQv3c1yqBwEHxPuNYuTuT.BVf1ejmflPDcwLcaekRWC/vUiKvRg/2',
            'individual',
            'free',
            'user',
            'api',
            true,
            true
        ) ON CONFLICT (id) DO NOTHING;
    """
    )


def downgrade() -> None:
    """Drop core tables in reverse order."""

    op.drop_table("tokens")
    op.drop_table("memories")
    op.drop_table("contexts")
    op.drop_table("team_memberships")
    op.drop_table("organizations")
    op.drop_table("teams")
    op.drop_table("users")
