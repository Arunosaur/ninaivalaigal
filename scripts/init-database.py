#!/usr/bin/env python3
"""
Initialize database with all required tables
"""

import os
import sys

# Add server directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "server"))


def main():
    """Initialize database with all tables"""
    try:
        # Get database URL from environment
        database_url = os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ No database URL found. Set NINAIVALAIGAL_DATABASE_URL or DATABASE_URL")
            sys.exit(1)

        print(f"🔄 Initializing database: {database_url}")

        # Import here to avoid module issues
        from database import DatabaseManager

        # Create database manager and tables
        db = DatabaseManager(database_url)
        db.create_tables()

        print("✅ Database tables created successfully")

        # List all tables to verify
        from sqlalchemy import text

        with db.engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """
                )
            )
            tables = [row[0] for row in result]

        print(f"📊 Created {len(tables)} tables:")
        for table in tables:
            print(f"   • {table}")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
