#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""US-121: HIPAA Compliance Schema

Create database tables for HIPAA compliance:
- hipaa_audit_logs: HIPAA-compliant audit trail (7-year retention)
- hipaa_breach_incidents: Breach incident tracking
- hipaa_phi_detections: PHI detection records

Revision ID: 0128_us121_hipaa
Revises: 0127_spec074_gdpr_compliance_schema
Create Date: 2025-11-02 12:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0129_us121_hipaa"
down_revision = "0128_spec074_gdpr_compliance_schema"
branch_labels = None
depends_on = None


def upgrade():
    """Create HIPAA compliance tables"""

    # HIPAA Audit Logs - Required for HIPAA compliance (7-year retention)
    op.create_table(
        "hipaa_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(50), nullable=False, comment="Action performed: view, edit, delete, export"),
        sa.Column("resource_type", sa.String(100), nullable=False, comment="Type of resource: memory, context, etc."),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True, comment="ID of resource accessed"),
        sa.Column("phi_accessed", sa.Boolean(), nullable=False, default=False, comment="Whether PHI was accessed"),
        sa.Column("phi_categories", postgresql.ARRAY(sa.String()), nullable=True, comment="PHI categories accessed"),
        sa.Column("ip_address", sa.String(45), nullable=True, comment="IP address of access"),
        sa.Column("user_agent", sa.String(500), nullable=True, comment="User agent string"),
        sa.Column("success", sa.Boolean(), nullable=False, default=True, comment="Whether action was successful"),
        sa.Column("compliance", sa.String(20), nullable=False, default="HIPAA", comment="Compliance framework"),
        sa.Column(
            "retention_until",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("(CURRENT_TIMESTAMP + INTERVAL '7 years')"),
            comment="Retention until date (7 years per HIPAA)",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        schema="public",
        comment="HIPAA-compliant audit trail logs. Required 7-year retention per HIPAA regulations.",
    )

    # Foreign key to users table
    op.create_foreign_key(
        "fk_hipaa_audit_logs_user_id",
        "hipaa_audit_logs",
        "users",
        ["user_id"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="CASCADE",
    )

    # Indexes for HIPAA audit logs
    op.create_index("idx_hipaa_audit_logs_user_id", "hipaa_audit_logs", ["user_id"], schema="public")
    op.create_index(
        "idx_hipaa_audit_logs_resource", "hipaa_audit_logs", ["resource_type", "resource_id"], schema="public"
    )
    op.create_index("idx_hipaa_audit_logs_phi", "hipaa_audit_logs", ["phi_accessed"], schema="public")
    op.create_index("idx_hipaa_audit_logs_created", "hipaa_audit_logs", ["created_at"], schema="public")
    op.create_index("idx_hipaa_audit_logs_retention", "hipaa_audit_logs", ["retention_until"], schema="public")

    # HIPAA Breach Incidents - Track potential breaches
    op.create_table(
        "hipaa_breach_incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "incident_type",
            sa.String(50),
            nullable=False,
            comment="Type: unauthorized_access, improper_disclosure, encryption_bypassed, etc.",
        ),
        sa.Column("phi_affected", postgresql.ARRAY(sa.String()), nullable=True, comment="PHI categories affected"),
        sa.Column(
            "risk_level",
            sa.String(20),
            nullable=False,
            default="low",
            comment="Risk level: low, medium, high, critical",
        ),
        sa.Column(
            "is_breach", sa.Boolean(), nullable=False, default=False, comment="Whether incident constitutes a breach"
        ),
        sa.Column("phi_records_affected", sa.Integer(), nullable=True, comment="Number of PHI records affected"),
        sa.Column(
            "notification_required",
            sa.Boolean(),
            nullable=False,
            default=False,
            comment="Whether notification is required",
        ),
        sa.Column(
            "notification_deadline",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="Deadline for breach notification (60 days from discovery)",
        ),
        sa.Column(
            "notification_sent_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="When breach notification was sent",
        ),
        sa.Column("description", sa.Text(), nullable=True, comment="Incident description"),
        sa.Column("remediation_steps", postgresql.JSONB(), nullable=True, comment="Remediation steps taken"),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            default="pending",
            comment="Status: pending, assessed, notified, resolved",
        ),
        sa.Column("reported_by", postgresql.UUID(as_uuid=True), nullable=True, comment="User who reported incident"),
        sa.Column("assessed_by", postgresql.UUID(as_uuid=True), nullable=True, comment="User who assessed incident"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True, comment="When incident was resolved"),
        schema="public",
        comment="HIPAA breach incident tracking and notification management",
    )

    # Foreign keys for breach incidents
    op.create_foreign_key(
        "fk_hipaa_breach_reported_by",
        "hipaa_breach_incidents",
        "users",
        ["reported_by"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_hipaa_breach_assessed_by",
        "hipaa_breach_incidents",
        "users",
        ["assessed_by"],
        ["id"],
        source_schema="public",
        referent_schema="public",
        ondelete="SET NULL",
    )

    # Indexes for breach incidents
    op.create_index("idx_hipaa_breach_status", "hipaa_breach_incidents", ["status"], schema="public")
    op.create_index("idx_hipaa_breach_is_breach", "hipaa_breach_incidents", ["is_breach"], schema="public")
    op.create_index("idx_hipaa_breach_deadline", "hipaa_breach_incidents", ["notification_deadline"], schema="public")
    op.create_index("idx_hipaa_breach_created", "hipaa_breach_incidents", ["created_at"], schema="public")

    # HIPAA PHI Detections - Track PHI detection events
    op.create_table(
        "hipaa_phi_detections",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("resource_type", sa.String(100), nullable=False, comment="Type of resource scanned"),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True, comment="ID of resource scanned"),
        sa.Column("has_phi", sa.Boolean(), nullable=False, comment="Whether PHI was detected"),
        sa.Column("phi_categories", postgresql.ARRAY(sa.String()), nullable=True, comment="PHI categories detected"),
        sa.Column("risk_level", sa.String(20), nullable=False, default="low", comment="Risk level: low, medium, high"),
        sa.Column(
            "detection_method",
            sa.String(50),
            nullable=True,
            comment="Method used: pattern_matching, ml_model, manual_review",
        ),
        sa.Column("data_sample", sa.Text(), nullable=True, comment="Sample of detected data (redacted)"),
        sa.Column(
            "protection_applied", sa.Boolean(), nullable=False, default=False, comment="Whether protection was applied"
        ),
        sa.Column("detected_by", postgresql.UUID(as_uuid=True), nullable=True, comment="User/system that detected PHI"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        schema="public",
        comment="PHI detection events for compliance tracking",
    )

    # Indexes for PHI detections
    op.create_index("idx_hipaa_phi_detections_has_phi", "hipaa_phi_detections", ["has_phi"], schema="public")
    op.create_index(
        "idx_hipaa_phi_detections_resource", "hipaa_phi_detections", ["resource_type", "resource_id"], schema="public"
    )
    op.create_index("idx_hipaa_phi_detections_created", "hipaa_phi_detections", ["created_at"], schema="public")

    # Add comment to document HIPAA requirements
    op.execute(
        """
        COMMENT ON TABLE public.hipaa_audit_logs IS
        'HIPAA-compliant audit trail. Per 45 CFR 164.308(a)(1)(ii)(D) and 164.312(b),
         covered entities must maintain audit logs for 6 years. This table stores
         audit logs with 7-year retention for compliance.';

        COMMENT ON TABLE public.hipaa_breach_incidents IS
        'HIPAA breach incident tracking. Per 45 CFR 164.400-414, breaches affecting
         500+ individuals must be reported to HHS within 60 days. This table tracks
         breach incidents and notification deadlines.';

        COMMENT ON TABLE public.hipaa_phi_detections IS
        'PHI detection events for compliance monitoring. Tracks when and where PHI
         is detected in the system to ensure proper protection measures are applied.';
    """
    )


def downgrade():
    """Drop HIPAA compliance tables"""
    op.drop_index("idx_hipaa_phi_detections_created", table_name="hipaa_phi_detections", schema="public")
    op.drop_index("idx_hipaa_phi_detections_resource", table_name="hipaa_phi_detections", schema="public")
    op.drop_index("idx_hipaa_phi_detections_has_phi", table_name="hipaa_phi_detections", schema="public")
    op.drop_table("hipaa_phi_detections", schema="public")

    op.drop_index("idx_hipaa_breach_created", table_name="hipaa_breach_incidents", schema="public")
    op.drop_index("idx_hipaa_breach_deadline", table_name="hipaa_breach_incidents", schema="public")
    op.drop_index("idx_hipaa_breach_is_breach", table_name="hipaa_breach_incidents", schema="public")
    op.drop_index("idx_hipaa_breach_status", table_name="hipaa_breach_incidents", schema="public")
    op.drop_table("hipaa_breach_incidents", schema="public")

    op.drop_index("idx_hipaa_audit_logs_retention", table_name="hipaa_audit_logs", schema="public")
    op.drop_index("idx_hipaa_audit_logs_created", table_name="hipaa_audit_logs", schema="public")
    op.drop_index("idx_hipaa_audit_logs_phi", table_name="hipaa_audit_logs", schema="public")
    op.drop_index("idx_hipaa_audit_logs_resource", table_name="hipaa_audit_logs", schema="public")
    op.drop_index("idx_hipaa_audit_logs_user_id", table_name="hipaa_audit_logs", schema="public")
    op.drop_table("hipaa_audit_logs", schema="public")
