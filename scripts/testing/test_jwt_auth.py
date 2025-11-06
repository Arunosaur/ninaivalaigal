#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Test JWT authentication flow for context ownership
"""

import asyncio
import os
import sys

sys.path.append("/Users/asrajag/Workspace/mem0/server")

# Set environment variables for testing
# pragma: allowlist secret
os.environ["NINAIVALAIGAL_USER_TOKEN"] = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo4LCJlbWFpbCI6ImR1cmFpQGV4YW1wbGUuY29tIiwiYWNjb3VudF90eXBlIjoiaW5kaXZpZHVhbCIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNzU3ODc5NjI5fQ.FQulmDLPK2WaBLuW-NIZ5TsKutnqP4E7iMKigVKoWaI"
)
os.environ["NINAIVALAIGAL_USER_ID"] = "8"
# pragma: allowlist secret
os.environ["NINAIVALAIGAL_DATABASE_URL"] = (
    "postgresql://nina:dev_password_change_in_production@localhost:5432/ninaivalaigal_dev"
)

from database import DatabaseManager  # noqa: E402

from auth import load_config  # noqa: E402
from mcp_server import context_start, get_user_from_jwt  # noqa: E402


async def test_jwt_authentication():
    """Test complete JWT authentication flow"""
    print("🧪 Testing JWT Authentication Flow")
    print("=" * 50)

    # 1. Test JWT token decoding
    print("\n1. Testing JWT token decoding...")
    user_id = get_user_from_jwt()
    print(f"   JWT-derived user_id: {user_id}")

    # 2. Test context creation with JWT user
    print("\n2. Testing context_start with JWT authentication...")
    result = await context_start("CIP Analysis")
    print(f"   Result: {result}")

    # 3. Debug the create_context call directly
    print("\n3. Testing create_context directly...")
    config = load_config()
    if isinstance(config, dict):
        database_url = (
            config.get("database_url") or os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv("DATABASE_URL")
        )
    else:
        database_url = config or os.getenv("NINAIVALAIGAL_DATABASE_URL") or os.getenv("DATABASE_URL")

    if not database_url:
        # Build from environment variables as last resort
        host = os.getenv("PGBOUNCER_HOST") or os.getenv("POSTGRES_HOST", "localhost")
        user = os.getenv("NINA_DB_USER") or os.getenv("POSTGRES_USER", "nina")
        password = os.getenv("NINA_DB_PASSWORD") or os.getenv("POSTGRES_PASSWORD", "dev_password_change_in_production")
        db_name = os.getenv("NINA_DB_NAME") or os.getenv("POSTGRES_DB", "ninaivalaigal_dev")
        port = os.getenv("PGBOUNCER_PORT") or os.getenv("PGBOUNCER_TX_PORT", "6432")
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    db = DatabaseManager(database_url)

    # Call create_context directly with user_id
    print(f"   Calling create_context('CIP Analysis', user_id={user_id})")
    context = db.create_context("CIP Analysis", user_id=user_id)
    print(f"   Returned context: {context}")

    # Check database state
    session = db.get_session()
    try:
        from database import RecordingContext  # noqa: E402

        context = session.query(RecordingContext).filter_by(name="CIP Analysis").first()
        if context:
            print(f"   Context found: {context.name}")
            print(f"   Owner ID: {context.owner_id}")
            print(f"   Is Active: {context.is_active}")
            print(f"   Created: {context.created_at}")

            if context.owner_id == user_id:
                print("   ✅ SUCCESS: Context ownership matches JWT user_id!")
            else:
                print(f"   ❌ FAILED: Expected owner_id={user_id}, got {context.owner_id}")
        else:
            print("   ❌ FAILED: Context not found")
    finally:
        session.close()

    print("\n" + "=" * 50)
    print("JWT Authentication Test Complete")


if __name__ == "__main__":
    asyncio.run(test_jwt_authentication())
