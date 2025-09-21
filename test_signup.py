#!/usr/bin/env python3
"""
Test script for mem0 signup and login functionality
Tests individual user signup, organization signup, and login
"""

import json

import requests

BASE_URL = "http://localhost:8000"


def test_individual_signup():
    """Test individual user signup"""
    print("🧪 Testing Individual User Signup...")

    signup_data = {
        "email": "john.doe@example.com",
        "password": "SecurePass123",
        "name": "John Doe",
        "account_type": "individual",
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/signup/individual", json=signup_data)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Individual signup successful!")
            print(f"User ID: {result.get('user', {}).get('user_id')}")
            print(f"Email: {result.get('user', {}).get('email')}")
            print(f"Account Type: {result.get('user', {}).get('account_type')}")
            return result.get("user", {}).get("jwt_token")
        else:
            print(f"❌ Individual signup failed: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error during individual signup: {e}")
        return None


def test_organization_signup():
    """Test organization signup"""
    print("\n🧪 Testing Organization Signup...")

    signup_data = {
        "user": {
            "email": "admin@acmecorp.com",
            "password": "AdminPass123",
            "name": "Jane Admin",
        },
        "organization": {
            "name": "Acme Corporation",
            "domain": "acmecorp.com",
            "size": "51-200",
            "industry": "Technology",
        },
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/signup/organization", json=signup_data
        )
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Organization signup successful!")
            print(f"User ID: {result.get('user_id')}")
            print(f"Organization ID: {result.get('organization_id')}")
            print(f"Role: {result.get('role')}")
            return result.get("jwt_token")
        else:
            print(f"❌ Organization signup failed: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error during organization signup: {e}")
        return None


def test_login(email, password):
    """Test user login"""
    print(f"\n🧪 Testing Login for {email}...")

    login_data = {"email": email, "password": password}

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Login successful!")
            print(f"User ID: {result.get('user', {}).get('user_id')}")
            print(f"Email: {result.get('user', {}).get('email')}")
            print(f"Account Type: {result.get('user', {}).get('account_type')}")
            return result.get("user", {}).get("jwt_token")
        else:
            print(f"❌ Login failed: {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error during login: {e}")
        return None


def test_protected_endpoint(token):
    """Test accessing protected endpoint with JWT token"""
    print("\n🧪 Testing Protected Endpoint Access...")

    headers = {"Authorization": f"Bearer {token}"}

    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ Protected endpoint access successful!")
            print(f"User Info: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Protected endpoint access failed: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error accessing protected endpoint: {e}")
        return False


def test_server_health():
    """Test if server is running"""
    print("🧪 Testing Server Health...")

    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Server is running!")
            return True
        else:
            print(f"❌ Server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Server is not accessible: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Mem0 Signup System Tests\n")

    # Test server health first
    if not test_server_health():
        print("❌ Server is not running. Please start the server first.")
        return

    # Test individual signup
    individual_token = test_individual_signup()

    # Test organization signup
    org_token = test_organization_signup()

    # Test login for individual user
    if individual_token:
        login_token = test_login("john.doe@example.com", "SecurePass123")
        if login_token:
            test_protected_endpoint(login_token)

    # Test login for organization admin
    if org_token:
        admin_login_token = test_login("admin@acmecorp.com", "AdminPass123")
        if admin_login_token:
            test_protected_endpoint(admin_login_token)

    print("\n🏁 Test Suite Complete!")


if __name__ == "__main__":
    main()
