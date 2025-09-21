#!/usr/bin/env python3
"""
Debug user authentication issues
Check password hashing and user creation
"""

import time

import bcrypt
import requests

BASE_URL = "http://localhost:8000"

def test_user_creation():
    """Test creating a new user with debug info"""
    print("🔍 Testing User Creation...")

    # Try creating a new unique user
    test_email = f"debug-user-{int(time.time())}@example.com"
    user_data = {
        "email": test_email,
        "password": "debugpass123",
        "name": "Debug User",
        "account_type": "individual"
    }

    print(f"Creating user: {test_email}")

    response = requests.post(f"{BASE_URL}/auth/signup/individual", json=user_data)

    if response.status_code == 200:
        result = response.json()
        print("✅ User created successfully!")
        print(f"   User ID: {result.get('user_id')}")

        # Try logging in immediately
        login_data = {
            "email": test_email,
            "password": "debugpass123"
        }

        login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data)

        if login_response.status_code == 200:
            login_result = login_response.json()
            print("✅ Login successful!")
            print(f"   Token: {login_result.get('user', {}).get('jwt_token', 'N/A')[:50]}...")
            return True
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"   Error: {login_response.text}")
            return False
    else:
        print(f"❌ User creation failed: {response.status_code}")
        print(f"   Error: {response.text}")
        return False

def test_existing_user_login():
    """Test login with known working user"""
    print("\n🔐 Testing Known Working User...")

    # Test with Krishna's account that we know works
    login_data = {
        "email": "krishna@example.com",
        "password": "test1234"
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)

    if response.status_code == 200:
        result = response.json()
        print("✅ Krishna login successful!")
        return True
    else:
        print(f"❌ Krishna login failed: {response.status_code}")
        return False

def test_durai_password_variations():
    """Test different password variations for durai@example.com"""
    print("\n🔍 Testing Durai Password Variations...")

    passwords_to_try = [
        "test1234",
        "password123",
        "durai123",
        "Test1234",
        "TEST1234",
        "admin123",
        "123456",
        ""
    ]

    for password in passwords_to_try:
        login_data = {
            "email": "durai@example.com",
            "password": password
        }

        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS with password: '{password}'")
            print(f"   Token: {result.get('user', {}).get('jwt_token', 'N/A')[:50]}...")
            return password
        else:
            print(f"❌ Failed with password: '{password}'")

    print("❌ No password worked for durai@example.com")
    return None

def check_password_hashing():
    """Check if password hashing is working correctly"""
    print("\n🔒 Testing Password Hashing...")

    test_password = "test1234"

    # Test bcrypt hashing
    hashed = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
    print(f"Original password: {test_password}")
    print(f"Bcrypt hash: {hashed.decode('utf-8')}")

    # Test verification
    is_valid = bcrypt.checkpw(test_password.encode('utf-8'), hashed)
    print(f"Hash verification: {is_valid}")

    return is_valid

def main():
    """Run all debug tests"""

    print("🐛 mem0 User Authentication Debug")
    print("=" * 50)

    # Test password hashing
    hash_ok = check_password_hashing()

    # Test known working user
    krishna_ok = test_existing_user_login()

    # Test durai password variations
    working_password = test_durai_password_variations()

    # Test creating new user
    new_user_ok = test_user_creation()

    print("\n" + "=" * 50)
    print("🎯 DEBUG RESULTS")
    print("=" * 50)

    print(f"Password Hashing: {'✅' if hash_ok else '❌'}")
    print(f"Krishna Login: {'✅' if krishna_ok else '❌'}")
    print(f"Durai Login: {'✅' if working_password else '❌'}")
    if working_password:
        print(f"  Working password: '{working_password}'")
    print(f"New User Creation: {'✅' if new_user_ok else '❌'}")

    if not working_password:
        print("\n💡 RECOMMENDATIONS:")
        print("1. Try creating durai@example.com again with a known password")
        print("2. Check if the user was created with a different password")
        print("3. Reset the user's password in the database")
        print("4. Create a new user with a different email")

if __name__ == "__main__":
    main()
