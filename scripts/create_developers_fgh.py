#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create/Activate Developer F, G, H in Taiga.

Usage:
    python3 scripts/create_developers_fgh.py
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
    print("\n1️⃣  Authenticating...")
    response = requests.post(
        f"{API_ENDPOINT}/auth",
        json={"type": "normal", "username": USERNAME, "password": PASSWORD},
    )
    if response.status_code == 200:
        auth_token = response.json()["auth_token"]
        print("✅ Authenticated")
        return {"Authorization": f"Bearer {auth_token}"}
    else:
        print(f"❌ Authentication failed: {response.status_code}")
        sys.exit(1)


def find_user_by_username(headers, username):
    """Find user by username."""
    response = requests.get(f"{API_ENDPOINT}/users", headers=headers)
    if response.status_code == 200:
        users = response.json()
        for user in users:
            if user.get("username", "").lower() == username.lower():
                return user
    return None


def activate_user(headers, user_id):
    """Activate a user."""
    # Get current user data
    response = requests.get(f"{API_ENDPOINT}/users/{user_id}", headers=headers)
    if response.status_code == 200:
        user_data = response.json()
        user_data["is_active"] = True

        # Update user
        update_response = requests.patch(
            f"{API_ENDPOINT}/users/{user_id}",
            headers={**headers, "Content-Type": "application/json"},
            json=user_data,
        )
        return update_response.status_code == 200
    return False


def create_user(headers, username, full_name, email):
    """Create a new user."""
    # Taiga user creation endpoint
    user_data = {
        "username": username,
        "full_name": full_name,
        "email": email,
        "password": "changeme123",  # User should change on first login
        "is_active": True,
        "lang": "en",
        "timezone": "UTC",
    }

    # Note: User creation typically requires admin privileges
    # This might need to be done through the UI or requires special endpoint
    # For now, we'll try the standard endpoint
    response = requests.post(
        f"{API_ENDPOINT}/users",
        headers={**headers, "Content-Type": "application/json"},
        json=user_data,
    )

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"⚠️  User creation response: {response.status_code} - {response.text[:200]}")
        return None


def ensure_user_exists_and_active(headers, username, full_name, email_pattern):
    """Ensure user exists and is active."""
    print(f"\n📋 Processing {full_name} ({username})...")

    # Try different username formats
    possible_usernames = [
        username,
        username.replace(" ", "-"),
        username.replace("-", "_"),
        username.lower(),
        username.replace(" ", "-").lower(),
    ]

    user = None
    found_username = None

    for uname in possible_usernames:
        user = find_user_by_username(headers, uname)
        if user:
            found_username = uname
            break

    if user:
        user_id = user.get("id")
        is_active = user.get("is_active", False)
        current_username = user.get("username")
        current_email = user.get("email", "")

        print(f"   ✅ Found user: ID={user_id}, Username={current_username}, Active={is_active}")

        if not is_active:
            print(f"   🔄 Activating user...")
            if activate_user(headers, user_id):
                print(f"   ✅ User activated")
                return user_id
            else:
                print(f"   ❌ Failed to activate user")
                return None
        else:
            print(f"   ✅ User already active")
            return user_id
    else:
        print(f"   ⚠️  User not found. Attempting to create...")
        # Generate email if pattern provided
        if email_pattern:
            email = email_pattern.format(username=username.lower().replace(" ", "-"))
        else:
            email = f"{username.lower().replace(' ', '-')}@example.com"

        created_user = create_user(headers, username, full_name, email)
        if created_user:
            print(f"   ✅ User created: ID={created_user.get('id')}")
            return created_user.get("id")
        else:
            print(f"   ❌ Failed to create user. May need manual creation.")
            return None


def main():
    """Main function."""
    print("=" * 80)
    print("👥 Creating/Activating Developers F, G, H in Taiga")
    print("=" * 80)

    # Authenticate
    headers = authenticate()

    # Define developers
    developers = [
        {
            "username": "developer-f",
            "full_name": "Developer F",
            "email_pattern": "{username}@example.com",
        },
        {
            "username": "developer-g",
            "full_name": "Developer G",
            "email_pattern": "{username}@example.com",
        },
        {
            "username": "developer-h",
            "full_name": "Developer H",
            "email_pattern": "{username}@example.com",
        },
    ]

    # Process each developer
    results = {}
    for dev in developers:
        user_id = ensure_user_exists_and_active(headers, dev["username"], dev["full_name"], dev["email_pattern"])
        results[dev["username"]] = user_id

    # Summary
    print("\n" + "=" * 80)
    print("📊 Summary:")
    print("=" * 80)
    for dev in developers:
        user_id = results.get(dev["username"])
        status = "✅ Active" if user_id else "❌ Failed"
        print(f"  {dev['full_name']}: {status} (ID: {user_id if user_id else 'N/A'})")

    # Check if all succeeded
    all_success = all(results.values())
    if not all_success:
        print("\n⚠️  Some users may need to be created manually through Taiga UI")
        print("   Or check if user creation endpoint requires special permissions")

    print("=" * 80)


if __name__ == "__main__":
    main()




