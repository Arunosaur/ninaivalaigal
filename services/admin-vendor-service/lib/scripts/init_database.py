#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Initialize the ninaivalaigal database
Creates all tables based on SQLAlchemy models
"""

import os
import sys

# Add server to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.manager import DatabaseManager  # noqa: E402
from database.models import Base  # noqa: E402


def main():
    """Initialize database tables for ninaivalaigal platform."""
    # Get database URL from environment or use default for Colima dev
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://nina:dev_password_change_in_production@localhost:5442/ninaivalaigal_dev",
    )

    print("🔧 Initializing database...")
    print(f"   URL: {database_url.replace(':dev_password_change_in_production', ':****')}")

    try:
        # Create database manager (this calls create_tables automatically)
        DatabaseManager(database_url)

        print("✅ Database tables created successfully!")
        print(f"   Total tables: {len(Base.metadata.tables)}")
        print("\nTables created:")
        for table_name in sorted(Base.metadata.tables.keys()):
            print(f"   - {table_name}")

        return 0

    except Exception as e:
        print(f"❌ Failed to initialize database: {e}")
        import traceback  # noqa: E402

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
