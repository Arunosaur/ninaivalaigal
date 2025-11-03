#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
# Verification script for Developers F, G, H
# This script checks if the developers exist and provides instructions for creation
#
# Usage:
#     python3 scripts/create_developers_fgh_guide.py

import os
import sys

import requests

# Configuration
TAIGA_URL = os.getenv("TAIGA_URL", "http://localhost:9000")
API_ENDPOINT = f"{TAIGA_URL}/api/v1"

# Get credentials from environment
TAIGA_USERNAME = os.getenv("TAIGA_USERNAME", "admin")
TAIGA_PASSWORD = os.getenv("TAIGA_PASSWORD", "admin123")


def authenticate():
    """Authenticate with Taiga and return auth token."""
    auth_url = f"{API_ENDPOINT}/auth"
    auth_data = {"username": TAIGA_USERNAME, "password": TAIGA_PASSWORD, "type": "normal"}

    try:
        response = requests.post(auth_url, json=auth_data)
        if response.status_code == 200:
            return response.json().get("auth_token")
        else:
            print(f"❌ Authentication failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None


def check_developers(auth_token):
    """Check if Developers F, G, H exist."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    url = f"{API_ENDPOINT}/users"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            all_users = response.json()

            developers = {
                "Developer F": None,
                "Developer G": None,
                "Developer H": None,
            }

            for user in all_users:
                username = user.get("username", "").lower()
                full_name = user.get("full_name", "").lower()

                if "developer-f" in username or ("developer" in username and "f" in username):
                    developers["Developer F"] = user
                elif "developer-g" in username or ("developer" in username and "g" in username):
                    developers["Developer G"] = user
                elif "developer-h" in username or ("developer" in username and "h" in username):
                    developers["Developer H"] = user

            return developers
        return None
    except Exception as e:
        print(f"❌ Error checking developers: {e}")
        return None


def print_instructions():
    """Print manual creation instructions."""
    print("\n" + "=" * 70)
    print("📋 MANUAL CREATION INSTRUCTIONS")
    print("=" * 70)
    print(
        """
The Taiga API does not support programmatic user creation.
You must create these developers manually via the Django admin interface.

Step 1: Open Django Admin
   URL: http://localhost:9000/admin/users/user/

Step 2: Create Each Developer
   Click "Add user" for each developer:

   Developer F:
   - Username: developer-f
   - Full name: Developer F
   - Email: developer-f@example.com
   - Password: changeme123
   - ✅ Active (IMPORTANT - check this box!)
   - Save

   Developer G:
   - Username: developer-g
   - Full name: Developer G
   - Email: developer-g@example.com
   - Password: changeme123
   - ✅ Active (IMPORTANT - check this box!)
   - Save

   Developer H:
   - Username: developer-h
   - Full name: Developer H
   - Email: developer-h@example.com
   - Password: changeme123
   - ✅ Active (IMPORTANT - check this box!)
   - Save

Step 3: Verify Creation
   After creating, run this script again to verify:
   python3 scripts/create_developers_fgh_guide.py

    """
    )


def main():
    """Main execution."""
    print("🔍 Checking for Developers F, G, H in Taiga...")
    print("=" * 70)

    # Authenticate
    auth_token = authenticate()
    if not auth_token:
        print("❌ Authentication failed")
        print_instructions()
        sys.exit(1)

    # Check developers
    developers = check_developers(auth_token)
    if developers is None:
        print("❌ Failed to check developers")
        print_instructions()
        sys.exit(1)

    # Report status
    all_exist = True
    for dev_name, dev_data in developers.items():
        if dev_data:
            print(f"✅ {dev_name}: EXISTS")
            print(f"   Username: {dev_data.get('username')}")
            print(f"   Full Name: {dev_data.get('full_name')}")
            print(f"   Email: {dev_data.get('email')}")
            print(f"   ID: {dev_data.get('id')}")
            print(f"   Active: {dev_data.get('is_active', False)}")
            print()
        else:
            print(f"❌ {dev_name}: NOT FOUND")
            print()
            all_exist = False

    if all_exist:
        print("✅ All developers exist!")
        sys.exit(0)
    else:
        print("⚠️  Some developers are missing. Follow the instructions below.")
        print_instructions()
        sys.exit(1)


if __name__ == "__main__":
    main()
