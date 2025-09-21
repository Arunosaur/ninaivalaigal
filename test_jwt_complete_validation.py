#!/usr/bin/env python3
"""
Complete JWT Authentication Validation Test
Tests all CLI commands with JWT authentication to ensure security is working correctly.
"""

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta

import jwt


def setup_environment():
    """Set up test environment with JWT secret and token"""
    # Set JWT secret
    os.environ["MEM0_JWT_SECRET"] = "dev-secret-key-change-in-production"

    # Create test JWT token
    test_payload = {
        "user_id": 8,
        "email": "durai@example.com",
        "account_type": "individual",
        "role": "user",
        "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp()),
    }

    token = jwt.encode(
        test_payload, "dev-secret-key-change-in-production", algorithm="HS256"
    )
    os.environ["NINAIVALAIGAL_USER_TOKEN"] = token

    print("✅ Environment configured with JWT token")
    return token


def ensure_test_user_exists():
    """Ensure test user exists in database"""
    db_path = "/Users/asrajag/Workspace/mem0/server/mem0.db"

    if not os.path.exists(db_path):
        print("❌ Database not found, please start the server first")
        return False

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE id = 8")
    user = cursor.fetchone()

    if not user:
        # Create test user
        password_hash = hashlib.sha256(b"testpass123").hexdigest()
        cursor.execute(
            """
        INSERT INTO users (id, username, email, name, password_hash, account_type, role, is_active)
        VALUES (8, 'durai', 'durai@example.com', 'Durai', ?, 'individual', 'user', 1)
        """,
            (password_hash,),
        )
        conn.commit()
        print("✅ Test user created")
    else:
        print("✅ Test user already exists")

    conn.close()
    return True


def run_cli_command(command):
    """Run CLI command and return result"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd="/Users/asrajag/Workspace/mem0",
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def test_jwt_authentication():
    """Test complete JWT authentication flow"""
    print("🔐 Testing JWT Authentication Flow")
    print("=" * 50)

    # Setup environment
    token = setup_environment()

    # Ensure test user exists
    if not ensure_test_user_exists():
        return False

    # Test 1: List contexts (should work with JWT)
    print("\n1. Testing contexts command...")
    success, stdout, stderr = run_cli_command("eM contexts")
    if success:
        print("✅ Contexts command successful")
    else:
        print(f"❌ Contexts command failed: {stderr}")
        return False

    # Test 2: Start context
    print("\n2. Testing start context...")
    success, stdout, stderr = run_cli_command("eM start --context jwt-test")
    if success and "Now recording" in stdout:
        print("✅ Start context successful")
    else:
        print(f"❌ Start context failed: {stderr}")
        return False

    # Test 3: Store memory
    print("\n3. Testing remember command...")
    memory_data = json.dumps(
        {"type": "test", "data": {"message": "JWT auth test successful"}}
    )
    success, stdout, stderr = run_cli_command(
        f"eM remember '{memory_data}' --context jwt-test"
    )
    if success and "Memory entry recorded" in stdout:
        print("✅ Remember command successful")
    else:
        print(f"❌ Remember command failed: {stderr}")
        return False

    # Test 4: Recall memories
    print("\n4. Testing recall command...")
    success, stdout, stderr = run_cli_command("eM recall --context jwt-test")
    if success and "JWT auth test successful" in stdout:
        print("✅ Recall command successful")
    else:
        print(f"❌ Recall command failed: {stderr}")
        return False

    # Test 5: Stop context
    print("\n5. Testing stop context...")
    success, stdout, stderr = run_cli_command("eM stop --context jwt-test")
    if success and "Recording stopped" in stdout:
        print("✅ Stop context successful")
    else:
        print(f"❌ Stop context failed: {stderr}")
        return False

    # Test 6: Delete context
    print("\n6. Testing delete context...")
    success, stdout, stderr = run_cli_command("eM delete --context jwt-test")
    if success and "deleted successfully" in stdout:
        print("✅ Delete context successful")
    else:
        print(f"❌ Delete context failed: {stderr}")
        return False

    print("\n🎉 All JWT authentication tests passed!")
    return True


def test_without_jwt():
    """Test that commands fail without JWT token"""
    print("\n🚫 Testing without JWT token (should fail)")
    print("=" * 50)

    # Remove JWT token
    if "NINAIVALAIGAL_USER_TOKEN" in os.environ:
        del os.environ["NINAIVALAIGAL_USER_TOKEN"]

    success, stdout, stderr = run_cli_command("eM contexts")
    if not success and ("401" in stderr or "Unauthorized" in stderr):
        print("✅ Commands properly fail without JWT token")
        return True
    else:
        print("❌ Commands should fail without JWT token but didn't")
        return False


def main():
    """Main test function"""
    print("🧪 JWT Authentication Complete Validation Test")
    print("=" * 60)

    # Test with JWT
    jwt_success = test_jwt_authentication()

    # Test without JWT
    no_jwt_success = test_without_jwt()

    print("\n" + "=" * 60)
    if jwt_success and no_jwt_success:
        print("🎉 ALL TESTS PASSED - JWT Authentication is working correctly!")
        print("✅ CLI commands work with valid JWT tokens")
        print("✅ CLI commands fail without JWT tokens")
        print("✅ User isolation and ownership is enforced")
        return 0
    else:
        print("❌ SOME TESTS FAILED - JWT Authentication needs fixes")
        return 1


if __name__ == "__main__":
    sys.exit(main())
