# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
"""add_invoice_management_tables

US#185: US-232: Invoice Management Database Migration

Revision ID: 20251110_130436
Revises: 0c7bc7ca39df
Create Date: 2025-11-10 13:04:36

This migration creates 4 new tables for invoice management:
- invoice_preferences: Team-level invoice display preferences
- invoice_portal_tokens: Customer portal access tokens
- exchange_rates: Currency exchange rates for multi-currency support
- accounting_integrations: Accounting system integration configurations

Note: invoice_corrections, invoice_audit_trail, tax_configurations, and tax_exemptions
already exist from previous migrations.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20251110_130436"  # pragma: allowlist secret
down_revision = "0c7bc7ca39df"  # merge_all_heads
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create invoice management tables"""

    # Create invoice_preferences table
    op.create_table(
        "invoice_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("company_name", sa.String(255), nullable=True),
        sa.Column("company_logo_url", sa.Text(), nullable=True),
        sa.Column("invoice_footer", sa.Text(), nullable=True),
        sa.Column("payment_terms", sa.Text(), nullable=True),
        sa.Column("custom_fields", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("team_id"),
        comment="US#185: Invoice display preferences per team",
    )
    op.create_index("ix_invoice_preferences_team_id", "invoice_preferences", ["team_id"])

    # Create invoice_portal_tokens table
    op.create_table(
        "invoice_portal_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column("access_token", sa.String(255), nullable=False, unique=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accessed_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_accessed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        comment="US#185: Customer portal access tokens",
    )
    op.create_index("ix_invoice_portal_tokens_team_id", "invoice_portal_tokens", ["team_id"])
    op.create_index("ix_invoice_portal_tokens_customer_email", "invoice_portal_tokens", ["customer_email"])
    op.create_index("ix_invoice_portal_tokens_access_token", "invoice_portal_tokens", ["access_token"])
    op.create_index("ix_invoice_portal_tokens_expires_at", "invoice_portal_tokens", ["expires_at"])

    # Create exchange_rates table
    op.create_table(
        "exchange_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("from_currency", sa.CHAR(3), nullable=False),
        sa.Column("to_currency", sa.CHAR(3), nullable=False),
        sa.Column("rate", sa.Numeric(10, 6), nullable=False),
        sa.Column("effective_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("rate > 0", name="check_exchange_rate_positive"),
        sa.CheckConstraint("from_currency != to_currency", name="check_different_currencies"),
        comment="US#185: Currency exchange rates",
    )
    op.create_index("ix_exchange_rates_from_currency", "exchange_rates", ["from_currency"])
    op.create_index("ix_exchange_rates_to_currency", "exchange_rates", ["to_currency"])
    op.create_index("ix_exchange_rates_effective_date", "exchange_rates", ["effective_date"])

    # Create accounting_integrations table
    op.create_table(
        "accounting_integrations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("integration_type", sa.String(50), nullable=False),
        sa.Column("integration_name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("oauth_token", sa.Text(), nullable=True),
        sa.Column("oauth_refresh_token", sa.Text(), nullable=True),
        sa.Column("oauth_token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_settings", postgresql.JSONB(), nullable=True),
        sa.Column("export_preferences", postgresql.JSONB(), nullable=True),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_status", sa.String(50), nullable=True),
        sa.Column("last_sync_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.CheckConstraint(
            "integration_type IN ('quickbooks', 'xero', 'sage', 'freshbooks', 'zoho', 'other')",
            name="check_integration_type",
        ),
        comment="US#185: Accounting system integrations",
    )
    op.create_index("ix_accounting_integrations_team_id", "accounting_integrations", ["team_id"])
    op.create_index("ix_accounting_integrations_integration_type", "accounting_integrations", ["integration_type"])


def downgrade() -> None:
    """Drop invoice management tables"""
    op.drop_index("ix_accounting_integrations_integration_type", table_name="accounting_integrations")
    op.drop_index("ix_accounting_integrations_team_id", table_name="accounting_integrations")
    op.drop_table("accounting_integrations")

    op.drop_index("ix_exchange_rates_effective_date", table_name="exchange_rates")
    op.drop_index("ix_exchange_rates_to_currency", table_name="exchange_rates")
    op.drop_index("ix_exchange_rates_from_currency", table_name="exchange_rates")
    op.drop_table("exchange_rates")

    op.drop_index("ix_invoice_portal_tokens_expires_at", table_name="invoice_portal_tokens")
    op.drop_index("ix_invoice_portal_tokens_access_token", table_name="invoice_portal_tokens")
    op.drop_index("ix_invoice_portal_tokens_customer_email", table_name="invoice_portal_tokens")
    op.drop_index("ix_invoice_portal_tokens_team_id", table_name="invoice_portal_tokens")
    op.drop_table("invoice_portal_tokens")

    op.drop_index("ix_invoice_preferences_team_id", table_name="invoice_preferences")
    op.drop_table("invoice_preferences")
