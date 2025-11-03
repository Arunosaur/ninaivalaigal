#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Convert HIPAA ARRAY columns to JSONB

Revision ID: 0135_convert_hipaa_array_to_jsonb
Revises: 0134_add_team_governance_status
Create Date: 2025-11-02 18:00:00.000000

Fix schema mismatch: Migration 0128 created ARRAY columns but models use JSONB.
This migration converts:
- hipaa_audit_logs.phi_categories (ARRAY -> JSONB)
- hipaa_breach_incidents.phi_affected (ARRAY -> JSONB)
- hipaa_phi_detections.phi_categories (ARRAY -> JSONB)

JSONB is more flexible for storing nested/complex data structures.
"""

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "0135_convert_hipaa_array_to_jsonb"
down_revision = "0134_add_team_governance_status"
branch_labels = None
depends_on = None


def upgrade():
    """Convert ARRAY columns to JSONB"""

    # Convert hipaa_audit_logs.phi_categories from ARRAY to JSONB
    op.execute(
        text(
            """
            ALTER TABLE hipaa_audit_logs
            ALTER COLUMN phi_categories TYPE jsonb
            USING CASE
                WHEN phi_categories IS NULL THEN NULL
                ELSE to_jsonb(phi_categories)
            END
        """
        )
    )

    # Convert hipaa_breach_incidents.phi_affected from ARRAY to JSONB
    op.execute(
        text(
            """
            ALTER TABLE hipaa_breach_incidents
            ALTER COLUMN phi_affected TYPE jsonb
            USING CASE
                WHEN phi_affected IS NULL THEN NULL
                ELSE to_jsonb(phi_affected)
            END
        """
        )
    )

    # Convert hipaa_phi_detections.phi_categories from ARRAY to JSONB
    op.execute(
        text(
            """
            ALTER TABLE hipaa_phi_detections
            ALTER COLUMN phi_categories TYPE jsonb
            USING CASE
                WHEN phi_categories IS NULL THEN NULL
                ELSE to_jsonb(phi_categories)
            END
        """
        )
    )


def downgrade():
    """Convert JSONB columns back to ARRAY"""

    # Convert hipaa_audit_logs.phi_categories from JSONB to ARRAY
    op.execute(
        text(
            """
            ALTER TABLE hipaa_audit_logs
            ALTER COLUMN phi_categories TYPE text[]
            USING CASE
                WHEN phi_categories IS NULL THEN NULL
                WHEN jsonb_typeof(phi_categories) = 'array' THEN ARRAY(SELECT jsonb_array_elements_text(phi_categories))
                ELSE ARRAY[]::text[]
            END
        """
        )
    )

    # Convert hipaa_breach_incidents.phi_affected from JSONB to ARRAY
    op.execute(
        text(
            """
            ALTER TABLE hipaa_breach_incidents
            ALTER COLUMN phi_affected TYPE text[]
            USING CASE
                WHEN phi_affected IS NULL THEN NULL
                WHEN jsonb_typeof(phi_affected) = 'array' THEN ARRAY(SELECT jsonb_array_elements_text(phi_affected))
                ELSE ARRAY[]::text[]
            END
        """
        )
    )

    # Convert hipaa_phi_detections.phi_categories from JSONB to ARRAY
    op.execute(
        text(
            """
            ALTER TABLE hipaa_phi_detections
            ALTER COLUMN phi_categories TYPE text[]
            USING CASE
                WHEN phi_categories IS NULL THEN NULL
                WHEN jsonb_typeof(phi_categories) = 'array' THEN ARRAY(SELECT jsonb_array_elements_text(phi_categories))
                ELSE ARRAY[]::text[]
            END
        """
        )
    )
