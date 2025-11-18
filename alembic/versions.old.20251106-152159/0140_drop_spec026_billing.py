#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Drop SPEC-026 billing tables for clean SPEC-147 start

Revision ID: 0139_drop_spec026
Revises: 0138_add_team_provenance_columns
Create Date: 2025-11-04 22:58:00

"""

from alembic import op

revision = "0140_drop_spec026"
down_revision = "0139_add_team_provenance_columns"
branch_labels = None
depends_on = None


def upgrade():
    """Drop old SPEC-026 billing tables for clean SPEC-147 start"""

    # Drop in reverse dependency order
    op.execute("DROP TABLE IF EXISTS discount_code_usage CASCADE")
    op.execute("DROP TABLE IF EXISTS credit_transactions CASCADE")
    op.execute("DROP TABLE IF EXISTS team_credits CASCADE")
    op.execute("DROP TABLE IF EXISTS discount_codes CASCADE")
    op.execute("DROP TABLE IF EXISTS team_usage_metrics CASCADE")
    op.execute("DROP TABLE IF EXISTS team_subscriptions CASCADE")
    op.execute("DROP TABLE IF EXISTS team_billing CASCADE")

    print("✅ Dropped all SPEC-026 billing tables")
    print("🧹 Database ready for clean SPEC-147 implementation")


def downgrade():
    """Cannot restore dropped tables - this is a one-way migration"""
    print("⚠️  Cannot restore SPEC-026 tables - backup required for rollback")
    pass
