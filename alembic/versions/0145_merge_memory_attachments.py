#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Merge memory attachments branch

Revision ID: 0144_merge_memory_attachments
Revises: 0142_spec147_part3, 0143_memory_attachments_schema
Create Date: 2025-11-05 08:45:00

Merge the memory attachments schema branch (0143) with the main SPEC-147 billing branch (0142).
This resolves the multiple heads issue in the Alembic migration chain.
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0145_merge_memory_attachments"
down_revision = ("0143_spec147_part3", "0144_memory_attachments")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Merge branches - no schema changes needed."""
    pass


def downgrade() -> None:
    """Merge branches - no schema changes needed."""
    pass
