#!/usr/bin/env python
"""
Seed Initial Staff Accounts - SPEC-085

Creates initial admin account for platform access.
Run this after database migration to bootstrap staff management.

Usage:
    conda activate nina
    python scripts/seed_initial_staff.py

Or use Makefile:
    make seed-staff
"""

import os
import sys
from pathlib import Path

# Add server directory to path
server_path = Path(__file__).parent.parent / "server"
sys.path.insert(0, str(server_path))

import bcrypt
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def seed_initial_staff():
    """Seed initial staff accounts"""

    # Get database URL from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://nina:dev_password_change_in_production@localhost:5432/ninaivalaigal_dev",
    )

    print(f"🔌 Connecting to database...")
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if staff table exists
        check_table = text(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'staff'
            );
        """
        )

        table_exists = session.execute(check_table).scalar()

        if not table_exists:
            print("❌ Staff table does not exist. Run migrations first:")
            print("   alembic upgrade head")
            return False

        # Check if any staff already exist
        check_staff = text("SELECT COUNT(*) FROM staff")
        staff_count = session.execute(check_staff).scalar()

        if staff_count > 0:
            print(f"ℹ️  Staff table already has {staff_count} accounts. Skipping seed.")
            print("   Use the admin console to create additional staff.")
            return True

        print("🌱 Seeding initial staff accounts...")

        # Initial admin account
        admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@ninaivalaigal.com")
        admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "ChangeMe123!@#")
        admin_name = os.getenv("INITIAL_ADMIN_NAME", "Platform Administrator")

        password_hash = hash_password(admin_password)

        insert_admin = text(
            """
            INSERT INTO staff (email, name, password_hash, role, department, is_active)
            VALUES (:email, :name, :password_hash, :role, :department, :is_active)
            RETURNING id, email, role
        """
        )

        result = session.execute(
            insert_admin,
            {
                "email": admin_email,
                "name": admin_name,
                "password_hash": password_hash,
                "role": "admin",
                "department": "Platform Operations",
                "is_active": True,
            },
        )

        admin = result.fetchone()
        session.commit()

        print("✅ Initial staff accounts created successfully!")
        print("")
        print("=" * 60)
        print("🔐 INITIAL ADMIN CREDENTIALS")
        print("=" * 60)
        print(f"Email:    {admin_email}")
        print(f"Password: {admin_password}")
        print(f"Role:     {admin[2]}")
        print("=" * 60)
        print("")
        print("⚠️  IMPORTANT SECURITY NOTES:")
        print("1. Change this password immediately after first login")
        print("2. Do not commit these credentials to version control")
        print("3. Use environment variables for production:")
        print("   - INITIAL_ADMIN_EMAIL")
        print("   - INITIAL_ADMIN_PASSWORD")
        print("   - INITIAL_ADMIN_NAME")
        print("")
        print("🌐 Access the admin console at:")
        print("   http://localhost:8181/staff-login.html")
        print("")

        return True

    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding staff: {e}")
        return False
    finally:
        session.close()


if __name__ == "__main__":
    print("🚀 Ninaivalaigal - Initial Staff Seed Script")
    print("")

    success = seed_initial_staff()

    if success:
        print("✅ Seed completed successfully!")
        sys.exit(0)
    else:
        print("❌ Seed failed!")
        sys.exit(1)
