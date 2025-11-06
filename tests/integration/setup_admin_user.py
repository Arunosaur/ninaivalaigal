#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""
Setup script to create a test admin user for integration testing

This script creates a test admin user with admin role for running
admin organization integration tests.

Usage:
    python3 tests/integration/setup_admin_user.py
"""

import os
import sys

import psycopg2
import requests
from psycopg2.extras import RealDictCursor

# Configuration
BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:13390")
ADMIN_EMAIL = "admin@ninaivalaigal.com"
# pragma: allowlist secret
ADMIN_PASSWORD = "admin123"
ADMIN_NAME = "Test Admin User"

# Database configuration (from environment or defaults)
DATABASE_URL = os.getenv(
    # pragma: allowlist secret
    "DATABASE_URL",
    "postgresql://nina:dev_password_change_in_production@localhost:6432/ninaivalaigal_dev",
)


def get_db_connection():
    """Get database connection"""
    try:
        # Parse DATABASE_URL
        import urllib.parse

        parsed = urllib.parse.urlparse(DATABASE_URL)
        conn = psycopg2.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            database=parsed.path.lstrip("/") if parsed.path else "ninaivalaigal_dev",
            user=parsed.username or "nina",
            password=parsed.password or "dev_password_change_in_production",
        )
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None


def create_admin_user_via_api():
    """Try to create admin user via API"""
    signup_url = f"{BASE_URL}/auth/signup/individual"
    signup_data = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "name": ADMIN_NAME, "account_type": "individual"}

    try:
        response = requests.post(signup_url, json=signup_data, timeout=5)
        if response.status_code in [200, 201]:
            print(f"✅ User created via API: {ADMIN_EMAIL}")
            return True
        elif response.status_code == 400:
            data = response.json()
            if "already exists" in str(data.get("detail", "")).lower():
                print(f"ℹ️  User already exists: {ADMIN_EMAIL}")
                return True
    except Exception as e:
        print(f"⚠️  API signup failed: {e}")

    return False


def update_user_role_to_admin(user_id: str):
    """Update user role to admin in database"""
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database - skipping role update")
        return False

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Update user role to admin
            cur.execute("UPDATE users SET role = 'admin', is_system_admin = true WHERE id = %s", (user_id,))
            conn.commit()

            if cur.rowcount > 0:
                print(f"✅ Updated user {user_id} to admin role")
                return True
            else:
                print(f"⚠️  User {user_id} not found in database")
                return False
    except Exception as e:
        print(f"❌ Error updating user role: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def get_user_id_from_db(email: str):
    """Get user ID from database by email"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT id FROM users WHERE email = %s", (email,))
            result = cur.fetchone()
            if result:
                return str(result["id"])
            return None
    except Exception as e:
        print(f"❌ Error getting user ID: {e}")
        return None
    finally:
        conn.close()


def main():
    print("=" * 70)
    print("Setting up test admin user for integration tests")
    print("=" * 70)
    print()

    # Step 1: Create user via API
    print("Step 1: Creating user via API...")
    user_created = create_admin_user_via_api()

    if not user_created:
        print("❌ Failed to create user via API")
        return 1

    # Step 2: Get user ID
    print()
    print("Step 2: Getting user ID from database...")
    user_id = get_user_id_from_db(ADMIN_EMAIL)

    if not user_id:
        print("❌ User not found in database")
        return 1

    print(f"✅ Found user ID: {user_id}")

    # Step 3: Update role to admin
    print()
    print("Step 3: Updating user role to admin...")
    role_updated = update_user_role_to_admin(user_id)

    if not role_updated:
        print("❌ Failed to update user role")
        return 1

    print()
    print("=" * 70)
    print("✅ Test admin user setup complete!")
    print("=" * 70)
    print(f"Email: {ADMIN_EMAIL}")
    print(f"Password: {ADMIN_PASSWORD}")
    print(f"Role: admin")
    print()
    print("You can now run integration tests:")
    print("  pytest tests/integration/test_admin_organizations.py -v -m integration")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
