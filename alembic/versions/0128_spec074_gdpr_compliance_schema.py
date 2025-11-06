#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Add SPEC-074 GDPR Compliance Schema (US#558)

Revision ID: 0127_spec074_gdpr_compliance_schema
Revises: 0126_spec026_team_billing_schema
Create Date: 2025-11-02 12:00:00.000000

SPEC-074: GDPR Compliance
US#558: GDPR Compliance Implementation

This migration creates the database schema for GDPR (General Data Protection Regulation)
compliance functionality, including data subject requests and encrypted data exports.

Changes:
--------
- Create data_subject_requests table (DSAR, erasure, portability, etc.)
- Create data_exports table (encrypted export tracking)
- Create indexes for performance
- All tables in public schema (cross-domain infrastructure)

GDPR Requirements:
-----------------
- Article 15: Right of Access (DSAR)
- Article 16: Right to Rectification
- Article 17: Right to Erasure ("Right to be Forgotten")
- Article 18: Right to Restrict Processing
- Article 20: Right to Data Portability
- Article 21: Right to Object

All tables include:
- Foreign key constraints with CASCADE delete to users
- Performance indexes on key columns
- CHECK constraints for data integrity
- UUID primary keys with gen_random_uuid()
- Timestamp tracking (created_at, completed_at, expires_at)
"""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import text

from alembic import op

# revision identifiers, used by Alembic.
revision = "0128_spec074_gdpr_compliance_schema"
down_revision = "0127_spec026_team_billing_schema"
branch_labels = None
depends_on = None


def upgrade():
    """Create SPEC-074 GDPR compliance schema tables."""

    # Data Subject Requests table - GDPR compliance requests
    op.create_table(
        "data_subject_requests",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "request_type",
            sa.String(50),
            nullable=False,
            comment="Type: access, rectification, erasure, portability, restriction, objection",
        ),
        sa.Column(
            "status",
            sa.String(50),
            server_default="pending",
            nullable=False,
            comment="Status: pending, in_progress, completed, partial, rejected, expired",
        ),
        sa.Column("description", sa.Text, nullable=True, comment="Optional description or notes from user"),
        sa.Column(
            "response_data",
            JSONB,
            nullable=True,
            comment="Response data (export_id, erasure_summary, retained_data_categories, etc.)",
        ),
        sa.Column("rejection_reason", sa.Text, nullable=True, comment="Reason if request was rejected"),
        sa.Column(
            "retained_data_categories",
            JSONB,
            nullable=True,
            comment="Categories of data retained (for partial erasures due to legal obligations)",
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True, comment="When request was completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint(
            "request_type IN ('access', 'rectification', 'erasure', 'portability', 'restriction', 'objection')",
            name="check_request_type_valid",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'partial', 'rejected', 'expired')",
            name="check_status_valid",
        ),
        comment="GDPR data subject requests (DSAR, erasure, portability, etc.) - US#558, SPEC-074",
    )

    # Indexes for data_subject_requests
    op.create_index("idx_data_subject_requests_user_id", "data_subject_requests", ["user_id"])
    op.create_index("idx_data_subject_requests_status", "data_subject_requests", ["status"])
    op.create_index("idx_data_subject_requests_request_type", "data_subject_requests", ["request_type"])
    op.create_index("idx_data_subject_requests_created_at", "data_subject_requests", ["created_at"])
    op.create_index(
        "idx_data_subject_requests_user_status",
        "data_subject_requests",
        ["user_id", "status"],
        postgresql_where=text("status IN ('pending', 'in_progress')"),
    )

    # Data Exports table - Encrypted export tracking for GDPR Article 15 & 20
    op.create_table(
        "data_exports",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "request_id",
            UUID(as_uuid=True),
            sa.ForeignKey("data_subject_requests.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
            comment="Link to originating data subject request (if applicable)",
        ),
        sa.Column(
            "format",
            sa.String(50),
            nullable=False,
            comment="Export format: json, xml, csv",
        ),
        sa.Column(
            "status",
            sa.String(50),
            server_default="pending",
            nullable=False,
            comment="Status: pending, generating, ready, expired, downloaded, failed",
        ),
        sa.Column(
            "download_url",
            sa.String(500),
            nullable=True,
            comment="Secure download URL (expires after expiry period)",
        ),
        sa.Column(
            "encryption_key_id",
            sa.String(255),
            nullable=True,
            comment="Identifier for encryption key used (not the key itself)",
        ),
        sa.Column("file_size", sa.BigInteger, nullable=True, comment="Export file size in bytes"),
        sa.Column(
            "expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When download link expires (default: 30 days per GDPR)",
        ),
        sa.Column(
            "downloaded_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When export was downloaded (track first download)",
        ),
        sa.Column("error_message", sa.Text, nullable=True, comment="Error message if export generation failed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint(
            "format IN ('json', 'xml', 'csv')",
            name="check_format_valid",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'generating', 'ready', 'expired', 'downloaded', 'failed')",
            name="check_export_status_valid",
        ),
        sa.CheckConstraint("file_size >= 0 OR file_size IS NULL", name="check_file_size_non_negative"),
        comment="Encrypted data exports for GDPR Article 15 (DSAR) and Article 20 (Portability) - US#558, SPEC-074",
    )

    # Indexes for data_exports
    op.create_index("idx_data_exports_user_id", "data_exports", ["user_id"])
    op.create_index("idx_data_exports_request_id", "data_exports", ["request_id"])
    op.create_index("idx_data_exports_status", "data_exports", ["status"])
    op.create_index("idx_data_exports_expires_at", "data_exports", ["expires_at"])
    op.create_index(
        "idx_data_exports_user_status",
        "data_exports",
        ["user_id", "status"],
        postgresql_where=text("status IN ('pending', 'generating', 'ready')"),
    )

    # Trigger to auto-update updated_at timestamp
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_gdpr_tables_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_data_subject_requests_updated_at
            BEFORE UPDATE ON data_subject_requests
            FOR EACH ROW
            EXECUTE FUNCTION update_gdpr_tables_updated_at();
    """
    )

    op.execute(
        """
        CREATE TRIGGER update_data_exports_updated_at
            BEFORE UPDATE ON data_exports
            FOR EACH ROW
            EXECUTE FUNCTION update_gdpr_tables_updated_at();
    """
    )


def downgrade():
    """Drop SPEC-074 GDPR compliance schema tables."""

    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS update_data_exports_updated_at ON data_exports;")
    op.execute("DROP TRIGGER IF EXISTS update_data_subject_requests_updated_at ON data_subject_requests;")
    op.execute("DROP FUNCTION IF EXISTS update_gdpr_tables_updated_at();")

    # Drop tables in reverse order of dependencies
    op.drop_table("data_exports")
    op.drop_table("data_subject_requests")
