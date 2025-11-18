"""core_api_base

Create base schema for core API application with single source of truth.
All main application tables in core_api schema.

Revision ID: 20251118_1200_core_api_base
Revises: 
Create Date: 2025-11-18 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251118_1200_core_api_base"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create core_api schema
    op.execute("CREATE SCHEMA IF NOT EXISTS core_api")
    
    # Users table with all fields
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.Column("mfa_enabled", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mfa_enforced", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("mfa_method", sa.String(length=50), nullable=True),
        sa.Column("phone_number", sa.String(length=20), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("risk_score", sa.Float(), nullable=True),
        sa.Column("last_login", sa.DateTime(), nullable=True),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        schema="core_api",
    )
    op.create_index(op.f("ix_core_api_users_id"), "users", ["id"], unique=False, schema="core_api")
    op.create_index(op.f("ix_core_api_users_username"), "users", ["username"], unique=True, schema="core_api")
    op.create_index(op.f("ix_core_api_users_email"), "users", ["email"], unique=True, schema="core_api")

    # MFA TOTP Secrets
    op.create_table(
        "mfa_totp_secrets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("secret", sa.String(length=32), nullable=False),
        sa.Column("backup_codes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        schema="core_api",
    )

    # MFA WebAuthn Credentials
    op.create_table(
        "mfa_webauthn_credentials",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("credential_id", sa.String(length=255), nullable=False),
        sa.Column("public_key", sa.Text(), nullable=False),
        sa.Column("sign_count", sa.Integer(), nullable=False),
        sa.Column("device_name", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        sa.UniqueConstraint("credential_id"),
        schema="core_api",
    )

    # MFA Enforcement Policies
    op.create_table(
        "mfa_enforcement_policies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("target_role", sa.String(length=50), nullable=True),
        sa.Column("target_account_type", sa.String(length=50), nullable=True),
        sa.Column("mfa_required", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="core_api",
    )

    # SSO Providers
    op.create_table(
        "sso_providers",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("provider_type", sa.String(length=50), nullable=False),
        sa.Column("client_id", sa.String(length=255), nullable=False),
        sa.Column("client_secret", sa.String(length=255), nullable=False),
        sa.Column("authorization_url", sa.String(length=500), nullable=False),
        sa.Column("token_url", sa.String(length=500), nullable=False),
        sa.Column("userinfo_url", sa.String(length=500), nullable=False),
        sa.Column("scope", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="core_api",
    )

    # User SSO Accounts
    op.create_table(
        "user_sso_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("provider_id", sa.Integer(), nullable=False),
        sa.Column("provider_user_id", sa.String(length=255), nullable=False),
        sa.Column("provider_email", sa.String(length=255), nullable=True),
        sa.Column("provider_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        sa.ForeignKeyConstraint(["provider_id"], ["core_api.sso_providers.id"]),
        sa.UniqueConstraint("provider_id", "provider_user_id"),
        schema="core_api",
    )

    # Security Events
    op.create_table(
        "security_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("event_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        schema="core_api",
    )

    # Anomaly Detections
    op.create_table(
        "anomaly_detections",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("detection_type", sa.String(length=100), nullable=False),
        sa.Column("anomaly_score", sa.Float(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("activity_data", sa.JSON(), nullable=True),
        sa.Column("activity_type", sa.String(length=50), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True),
        sa.Column("is_false_positive", sa.Boolean(), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        schema="core_api",
    )

    # Device Fingerprints
    op.create_table(
        "device_fingerprints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("fingerprint_hash", sa.String(length=255), nullable=False),
        sa.Column("device_info", sa.JSON(), nullable=True),
        sa.Column("is_trusted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["core_api.users.id"]),
        sa.UniqueConstraint("fingerprint_hash"),
        schema="core_api",
    )

    # Risk Configurations
    op.create_table(
        "risk_configurations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("device_weight", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("location_weight", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("time_weight", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("behavior_weight", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("risk_threshold_critical", sa.Float(), nullable=False, server_default="0.8"),
        sa.Column("risk_threshold_high", sa.Float(), nullable=False, server_default="0.6"),
        sa.Column("risk_threshold_medium", sa.Float(), nullable=False, server_default="0.4"),
        sa.Column("vpn_penalty", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("proxy_penalty", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("tor_penalty", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("new_device_penalty", sa.Float(), nullable=False, server_default="0.3"),
        sa.Column("unusual_location_penalty", sa.Float(), nullable=False, server_default="0.2"),
        sa.Column("unusual_time_penalty", sa.Float(), nullable=False, server_default="0.1"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="core_api",
    )


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table("risk_configurations", schema="core_api")
    op.drop_table("device_fingerprints", schema="core_api")
    op.drop_table("anomaly_detections", schema="core_api")
    op.drop_table("security_events", schema="core_api")
    op.drop_table("user_sso_accounts", schema="core_api")
    op.drop_table("sso_providers", schema="core_api")
    op.drop_table("mfa_enforcement_policies", schema="core_api")
    op.drop_table("mfa_webauthn_credentials", schema="core_api")
    op.drop_table("mfa_totp_secrets", schema="core_api")
    op.drop_table("users", schema="core_api")
    
    # Note: Keep the core_api schema for potential reuse
