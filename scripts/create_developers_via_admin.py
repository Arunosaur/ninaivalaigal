#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Attempt to create developers via various methods.
Since Taiga API doesn't support user creation, this script provides
instructions and attempts alternative methods.

Usage:
    python3 scripts/create_developers_via_admin.py
"""

import os
import sys

import requests

TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"
USERNAME = os.getenv("TAIGA_USERNAME", "admin")
PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")


def authenticate():
    """Authenticate and get auth token."""
    response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if response.status_code == 200:
        return {"Authorization": f"Bearer {response.json()['auth_token']}"}
    return None


def check_if_user_exists(headers, username):
    """Check if user already exists."""
    response = requests.get(f"{API_ENDPOINT}/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("username", "").lower() == username.lower():
                return user
    return None


def main():
    """Main function."""
    print("=" * 80)
    print("👥 Creating Developers F, G, H in Taiga")
    print("=" * 80)

    # Authenticate
    print("\n1️⃣  Authenticating...")
    headers = authenticate()
    if not headers:
        print("❌ Authentication failed")
        sys.exit(1)
    print("✅ Authenticated")

    developers = [
        {"username": "developer-f", "full_name": "Developer F", "email": "developer-f@example.com"},
        {"username": "developer-g", "full_name": "Developer G", "email": "developer-g@example.com"},
        {"username": "developer-h", "full_name": "Developer H", "email": "developer-h@example.com"},
    ]

    # Check existing users
    print("\n2️⃣  Checking existing users...")
    existing = {}
    for dev in developers:
        user = check_if_user_exists(headers, dev["username"])
        if user:
            existing[dev["username"]] = user
            status = "Active" if user.get("is_active") else "Inactive"
            print(f"   ✅ {dev['username']} exists (ID: {user.get('id')}, Status: {status})")
        else:
            print(f"   ❌ {dev['username']} does not exist")

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    print(f"Existing users: {len(existing)}/{len(developers)}")

    for dev in developers:
        if dev["username"] in existing:
            user = existing[dev["username"]]
            print(f"  ✅ {dev['full_name']}: Exists (ID: {user.get('id')}, Active: {user.get('is_active')})")
        else:
            print(f"  ❌ {dev['full_name']}: Needs creation")

    print("\n" + "=" * 80)
    print("⚠️  IMPORTANT: Taiga API Limitations")
    print("=" * 80)
    print("The Taiga REST API does not support user creation programmatically.")
    print("Users must be created through the Taiga admin UI.")
    print("\nTo create the missing developers:")
    print(f"1. Navigate to: {TAIGA_URL}/admin/users/user/")
    print("2. Click 'Add user'")
    print("3. Create each developer with:")
    print("   - Username: developer-f, developer-g, developer-h")
    print("   - Email: developer-f@example.com, etc.")
    print("   - Full name: Developer F, Developer G, Developer H")
    print("   - Active: ✅ (checked)")
    print("   - Password: changeme123 (users should change on first login)")
    print("\nAfter creating users, run:")
    print("  python3 scripts/assign_spec055_stories_to_developers.py")
    print("=" * 80)


if __name__ == "__main__":
    main()




