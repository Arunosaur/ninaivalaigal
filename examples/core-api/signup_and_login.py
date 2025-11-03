#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
# examples/core-api/signup_and_login.py
"""
Example: Sign up a new user and login
"""
import requests

BASE_URL = "http://localhost:8000"

# Sign up
print("Creating new user...")
signup_response = requests.post(
    f"{BASE_URL}/auth/signup",
    json={"email": "demo@example.com", "password": "DemoPass123!", "name": "Demo User"},  # pragma: allowlist secret
)

if signup_response.status_code == 201:
    print("✅ User created successfully")
    print(signup_response.json())
else:
    print("❌ Signup failed:", signup_response.json())
    exit(1)

# Login
print("\nLogging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login", json={"email": "demo@example.com", "password": "DemoPass123!"}  # pragma: allowlist secret
)

if login_response.status_code == 200:
    print("✅ Login successful")
    token = login_response.json()["access_token"]
    print(f"Token: {token[:20]}...")
else:
    print("❌ Login failed:", login_response.json())
    exit(1)

# Get profile
print("\nGetting profile...")
profile_response = requests.get(f"{BASE_URL}/users/me", headers={"Authorization": f"Bearer {token}"})

if profile_response.status_code == 200:
    print("✅ Profile retrieved")
    print(profile_response.json())
else:
    print("❌ Failed to get profile:", profile_response.json())
