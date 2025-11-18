#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""PostgreSQL Extensions - Foundation

Revision ID: 0001_extensions
Revises:
Create Date: 2025-10-10 22:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_extensions"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Install all required PostgreSQL extensions."""

    # Essential data type extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS citext;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Vector similarity (for embeddings) - pgvector
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # Graph database (Apache AGE)
    op.execute("CREATE EXTENSION IF NOT EXISTS age;")

    # Grant permissions for Apache AGE
    op.execute("GRANT USAGE ON SCHEMA ag_catalog TO PUBLIC;")


def downgrade() -> None:
    """Remove PostgreSQL extensions."""

    # Drop extensions in reverse order (respecting dependencies)
    op.execute("DROP EXTENSION IF EXISTS age CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS vector CASCADE;")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp" CASCADE;')
    op.execute("DROP EXTENSION IF EXISTS pgcrypto CASCADE;")
    op.execute("DROP EXTENSION IF EXISTS citext CASCADE;")
