#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Merge migration heads

Revision ID: 0136_merge_heads
Revises: 0135_add_team_lead_user, 0135_convert_hipaa_array_to_jsonb
Create Date: 2025-11-02 05:17:00.000000

Merge two parallel migration branches.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0136_merge_heads"
down_revision = ("0135_add_team_lead_user", "0135_convert_hipaa_array_to_jsonb")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge branches - no changes needed."""
    pass


def downgrade() -> None:
    """Merge branches - no changes needed."""
    pass
