#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Manual UI Testing Script for mem0 Signup System
Creates dummy data and provides test scenarios
"""

import time

import requests

BASE_URL = "http://localhost:8000"


def test_server_health():
    """Check if server is running"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and healthy")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        return False


def create_test_individual_user():
    """Create a test individual user"""
    user_data = {
        "email": "john.developer@example.com",
        "password": "password123",
        "name": "John Developer",
        "account_type": "individual",
    }

    print("\n🧪 Testing Individual User Signup...")
    print(f"Creating user: {user_data['name']} ({user_data['email']})")

    try:
        response = requests.post(f"{BASE_URL}/auth/signup/individual", json=user_data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            print("✅ Individual user created successfully!")
            print(f"   User ID: {result.get('user_id')}")
            print(f"   JWT Token: {result.get('access_token', 'N/A')[:50]}...")
            return result
        else:
            print(f"❌ Individual signup failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during individual signup: {e}")
        return None


def create_test_organization():
    """Create a test organization with admin user"""
    org_data = {
        "user": {
            "email": "sarah.admin@acmecorp.com",
            "password": "admin123",
            "name": "Sarah Admin",
        },
        "organization": {
            "name": "Acme Corporation",
            "domain": "acmecorp.com",
            "size": "11-50",
            "industry": "Technology",
        },
    }

    print("\n🏢 Testing Organization Signup...")
    print(f"Creating organization: {org_data['organization']['name']}")
    print(f"Admin user: {org_data['user']['name']} ({org_data['user']['email']})")

    try:
        response = requests.post(f"{BASE_URL}/auth/signup/organization", json=org_data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            print("✅ Organization created successfully!")
            print(f"   Organization ID: {result.get('organization_id')}")
            print(f"   Admin User ID: {result.get('user_id')}")
            print(f"   JWT Token: {result.get('access_token', 'N/A')[:50]}...")
            return result
        else:
            print(f"❌ Organization signup failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during organization signup: {e}")
        return None


def test_login(email, password):
    """Test login functionality"""
    login_data = {"email": email, "password": password}

    print(f"\n🔐 Testing Login for {email}...")

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, timeout=10)

        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"   User: {result.get('user', {}).get('name')}")
            print(f"   Account Type: {result.get('user', {}).get('account_type')}")
            print(f"   JWT Token: {result.get('access_token', 'N/A')[:50]}...")
            return result
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Network error during login: {e}")
        return None


def print_ui_test_instructions():
    """Print manual UI testing instructions"""
    print("\n" + "=" * 60)
    print("🎯 MANUAL UI TESTING INSTRUCTIONS")
    print("=" * 60)

    print("\n1. 📝 SIGNUP PAGE TESTING:")
    print(f"   Open: {BASE_URL}/")
    print("   Test Cases:")
    print("   • Individual Account:")
    print("     - Name: John Developer")
    print("     - Email: john.dev@example.com")
    print("     - Password: password123")
    print("   • Organization Account:")
    print("     - Admin Name: Sarah Admin")
    print("     - Admin Email: sarah@acmecorp.com")
    print("     - Password: admin123")
    print("     - Org Name: Acme Corporation")
    print("     - Domain: acmecorp.com")

    print("\n2. 🔐 LOGIN PAGE TESTING:")
    print(f"   Open: {BASE_URL}/login")
    print("   Test with the accounts you just created")

    print("\n3. 🧪 ERROR TESTING:")
    print("   • Try duplicate emails")
    print("   • Try weak passwords")
    print("   • Try invalid email formats")
    print("   • Try empty fields")

    print("\n4. 📱 RESPONSIVE TESTING:")
    print("   • Test on mobile screen sizes")
    print("   • Test form validation")
    print("   • Test loading states")


def main():
    """Main testing function"""
    print("🚀 mem0 UI Testing Suite")
    print("=" * 40)

    # Check server health
    if not test_server_health():
        print("\n❌ Server is not running. Please start it first:")
        print("   cd /Users/asrajag/Workspace/mem0/server")
        print("   uvicorn main:app --reload --port 8000")
        return

    # Create test data via API
    individual_result = create_test_individual_user()
    time.sleep(1)  # Brief pause between requests

    org_result = create_test_organization()
    time.sleep(1)

    # Test login for created users
    if individual_result:
        test_login("john.developer@example.com", "password123")
        time.sleep(1)

    if org_result:
        test_login("sarah.admin@acmecorp.com", "admin123")

    # Print UI testing instructions
    print_ui_test_instructions()

    print("\n" + "=" * 60)
    print("✅ API testing complete! Now test the UI manually in your browser.")
    print("=" * 60)


if __name__ == "__main__":
    main()
