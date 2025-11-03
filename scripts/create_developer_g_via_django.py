#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Create Developer G in Taiga via Django shell.
This script runs Django commands to create the user if Taiga is running.
"""

import subprocess
import sys

TAIGA_CONTAINER = "taiga-docker-taiga-back-1"


def check_taiga_running():
    """Check if Taiga container is running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={TAIGA_CONTAINER}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return TAIGA_CONTAINER in result.stdout
    except Exception:
        return False


def create_developer_g():
    """Create Developer G via Django shell."""
    django_command = """
from taiga.users.models import User
from django.contrib.auth import get_user_model

User = get_user_model()

# Check if user already exists
if User.objects.filter(username='developer-g').exists():
    user = User.objects.get(username='developer-g')
    print(f'User developer-g already exists (ID: {user.id})')
    if not user.is_active:
        user.is_active = True
        user.save()
        print('User activated')
    else:
        print('User is already active')
else:
    # Create new user
    user = User.objects.create_user(
        username='developer-g',
        email='developer-g@example.com',
        full_name='Developer G',
        password='changeme123',
        is_active=True
    )
    print(f'User developer-g created (ID: {user.id})')
"""

    try:
        cmd = ["docker", "exec", "-i", TAIGA_CONTAINER, "python", "manage.py", "shell"]

        print("Creating Developer G via Django shell...")
        result = subprocess.run(
            cmd,
            input=django_command,
            text=True,
            capture_output=True,
            check=False,
        )

        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr, file=sys.stderr)

        return result.returncode == 0
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    print("=" * 80)
    print("CREATING DEVELOPER G IN TAIGA VIA DJANGO SHELL")
    print("=" * 80)
    print()

    # Check if Taiga is running
    print("1️⃣  Checking if Taiga container is running...")
    if not check_taiga_running():
        print("❌ Taiga container not found or not running")
        print(f"   Expected container: {TAIGA_CONTAINER}")
        print()
        print("Please:")
        print("1. Start Taiga first: cd taiga-docker && docker-compose up -d")
        print("2. Or create Developer G manually via Taiga admin UI:")
        print("   http://localhost:9000/admin/users/user/add/")
        sys.exit(1)
    print("✅ Taiga container is running")
    print()

    # Create user
    print("2️⃣  Creating Developer G...")
    if create_developer_g():
        print("✅ Developer G created/verified")
    else:
        print("❌ Failed to create Developer G")
        print()
        print("Please create manually via:")
        print("http://localhost:9000/admin/users/user/add/")
        sys.exit(1)

    print()
    print("=" * 80)
    print("SUCCESS")
    print("=" * 80)
    print()
    print("Developer G should now be available in Taiga.")
    print("You can now reassign US#558 from admin to Developer G.")


if __name__ == "__main__":
    main()
