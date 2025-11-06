#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""SPEC-147: Billing schema part 2 (payment, invoices, audit)

Revision ID: 0140_spec147_part2
Revises: 0139_spec147
Create Date: 2025-11-04 22:21:00

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0142_spec147_part2"
down_revision = "0141_spec147"
branch_labels = None
depends_on = None


def upgrade():
    """Create remaining SPEC-147 tables"""

    # 6. quota_blocks - Soft/hard enforcement
    op.create_table(
        "quota_blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("billing_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("usage_quota_id", postgresql.UUID(as_uuid=True)),
        sa.Column("block_level", sa.String(10), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("blocked_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("unblocked_at", sa.DateTime(timezone=True)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("metadata", postgresql.JSONB),
        sa.ForeignKeyConstraint(["billing_account_id"], ["billing_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usage_quota_id"], ["usage_quotas.id"], ondelete="SET NULL"),
        sa.CheckConstraint("block_level IN ('soft', 'hard')", name="check_block_level"),
    )

    op.create_index("idx_quota_block_account", "quota_blocks", ["billing_account_id", "is_active"])
    op.create_index(
        "idx_quota_block_active", "quota_blocks", ["unblocked_at"], postgresql_where=sa.text("is_active = true")
    )

    # 7. payment_configs - Payment responsibility
    op.create_table(
        "payment_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("billing_account_id", postgresql.UUID(as_uuid=True), nullable=False, unique=True),
        sa.Column("primary_payer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("backup_payer_ids", postgresql.JSONB, nullable=False, server_default="[]"),
        sa.Column("payment_method_id", sa.String(255)),
        sa.Column("billing_address", postgresql.JSONB),
        sa.Column("billing_email", sa.String(255), nullable=False),
        sa.Column("grace_period_start", sa.DateTime(timezone=True)),
        sa.Column("grace_period_end", sa.DateTime(timezone=True)),
        sa.Column("transfer_status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["billing_account_id"], ["billing_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["primary_payer_id"], ["users.id"]),
        sa.CheckConstraint("transfer_status IN ('active', 'grace', 'transferred')", name="check_transfer_status"),
    )

    op.create_index("idx_payment_config_payer", "payment_configs", ["primary_payer_id"])
    op.create_index(
        "idx_payment_config_grace",
        "payment_configs",
        ["grace_period_end"],
        postgresql_where=sa.text("transfer_status = 'grace'"),
    )

    # 8. payment_transfers - Transfer history
    op.create_table(
        "payment_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("payment_config_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("from_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.String(50), nullable=False),
        sa.Column("initiated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.ForeignKeyConstraint(["payment_config_id"], ["payment_configs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["from_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["to_user_id"], ["users.id"]),
        sa.CheckConstraint("reason IN ('left_team', 'reassigned', 'voluntary')", name="check_transfer_reason"),
        sa.CheckConstraint("status IN ('pending', 'completed', 'failed')", name="check_transfer_status_value"),
    )

    op.create_index("idx_payment_transfer_config", "payment_transfers", ["payment_config_id", "initiated_at"])

    # 9. invoices - Versioned invoices
    op.create_table(
        "invoices",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("billing_period_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("billing_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("invoice_number", sa.String(50), nullable=False),
        sa.Column("revision", sa.Integer, nullable=False, server_default="1"),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("credits_applied", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("discounts_applied", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.CHAR(3), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("due_at", sa.DateTime(timezone=True)),
        sa.Column("paid_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["billing_period_id"], ["billing_periods.id"]),
        sa.ForeignKeyConstraint(["billing_account_id"], ["billing_accounts.id"], ondelete="CASCADE"),
        sa.CheckConstraint("status IN ('draft', 'issued', 'paid', 'void')", name="check_invoice_status"),
        sa.UniqueConstraint("invoice_number", "revision", name="uq_invoice_version"),
    )

    op.create_index("idx_invoice_account", "invoices", ["billing_account_id", "created_at"])
    op.create_index("idx_invoice_number", "invoices", ["invoice_number", "revision"])

    # 10. invoice_line_items - Invoice details
    op.create_table(
        "invoice_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("invoice_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("resource_type", sa.String(20), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("quantity", sa.BigInteger, nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 4), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("is_overage", sa.Boolean, nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"], ondelete="CASCADE"),
        sa.CheckConstraint("resource_type IN ('storage', 'retrieval', 'token')", name="check_line_item_resource_type"),
        sa.CheckConstraint("quantity > 0", name="check_line_item_quantity_positive"),
        sa.CheckConstraint("amount >= 0", name="check_line_item_amount_non_negative"),
    )

    op.create_index("idx_invoice_line_item", "invoice_line_items", ["invoice_id"])

    # 11. credit_balances - Credit tracking
    op.create_table(
        "credit_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("billing_account_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("used_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("granted_by", postgresql.UUID(as_uuid=True)),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.ForeignKeyConstraint(["billing_account_id"], ["billing_accounts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["granted_by"], ["users.id"]),
        sa.CheckConstraint("amount > 0", name="check_credit_amount_positive"),
        sa.CheckConstraint("used_amount >= 0", name="check_credit_used_non_negative"),
        sa.CheckConstraint("used_amount <= amount", name="check_credit_used_valid"),
    )

    op.create_index("idx_credit_balance_account", "credit_balances", ["billing_account_id", "expires_at"])

    # 12. discount_codes - Discount management
    op.create_table(
        "discount_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("percent_off", sa.Integer),
        sa.Column("amount_off", sa.Integer),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("usage_limit", sa.Integer),
        sa.Column("used_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.CheckConstraint("percent_off >= 1 AND percent_off <= 100", name="check_percent_off_range"),
        sa.CheckConstraint("amount_off >= 1", name="check_amount_off_positive"),
        sa.CheckConstraint(
            "(percent_off IS NOT NULL AND amount_off IS NULL) OR (percent_off IS NULL AND amount_off IS NOT NULL)",
            name="check_discount_type",
        ),
    )

    op.create_index(
        "idx_discount_code_active", "discount_codes", ["code"], postgresql_where=sa.text("is_active = true")
    )

    # Continue in next message...


def downgrade():
    """Drop part 2 tables"""
    op.drop_table("discount_codes")
    op.drop_table("credit_balances")
    op.drop_table("invoice_line_items")
    op.drop_table("invoices")
    op.drop_table("payment_transfers")
    op.drop_table("payment_configs")
    op.drop_table("quota_blocks")
