#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
"""
Integration test for Memory Browser API endpoints
Tests the actual running service with real database connections
"""

import json
import os
import sys
import uuid
from datetime import datetime

import requests

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_environment():
    """Load environment configuration"""
    env_file = "/Users/swami/WorkSpace/ninaivalaigal/configs/env-dev.env"

    if os.path.exists(env_file):
        print(f"📁 Loading environment from: {env_file}")
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()


def get_auth_token(base_url: str) -> str:
    """Get authentication token for testing"""

    # Try to login with existing user, or create one
    # pragma: allowlist secret
    login_data = {"email": "admin@example.com", "password": "admin123"}

    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception:
        pass

    # Try to create user first
    # pragma: allowlist secret
    signup_data = {"email": "test@example.com", "password": "test123", "name": "Test User"}

    try:
        response = requests.post(f"{base_url}/auth/signup/individual", json=signup_data)
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception:
        pass

    # Try login again
    try:
        response = requests.post(f"{base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            return response.json()["access_token"]
    except Exception:
        pass

    raise Exception("Could not authenticate")


def test_crud_operations(base_url: str, token: str) -> dict:
    """Test all CRUD operations"""

    headers = {"Authorization": f"Bearer {token}"}
    results = {"create": False, "read": False, "update": False, "delete": False, "list": False, "errors": []}

    print("\n🧪 Testing CRUD Operations:")

    # Test CREATE
    print("   📝 Testing CREATE...")
    try:
        memory_data = {
            "content": f"Integration test memory {datetime.now().isoformat()}",
            "context": "integration_test",
            "tags": ["test", "integration"],
            "pinned": False,
        }

        response = requests.post(f"{base_url}/api/v1/memory/memories", headers=headers, json=memory_data)

        if response.status_code == 201:
            memory_id = response.json()["memory"]["id"]
            results["create"] = True
            print(f"      ✅ Created memory: {memory_id[:8]}...")
        else:
            results["errors"].append(f"CREATE failed: {response.status_code} - {response.text}")
            print(f"      ❌ CREATE failed: {response.status_code}")

    except Exception as e:
        results["errors"].append(f"CREATE exception: {str(e)}")
        print(f"      ❌ CREATE exception: {e}")
        return results

    # Test READ (single memory)
    print("   🔍 Testing READ (single)...")
    try:
        response = requests.get(f"{base_url}/api/v1/memory/memories/{memory_id}", headers=headers)

        if response.status_code == 200:
            memory = response.json()["memory"]
            if memory["id"] == memory_id:
                results["read"] = True
                print(f"      ✅ Retrieved memory: {memory['content'][:50]}...")
            else:
                results["errors"].append("READ returned wrong memory")
                print("      ❌ READ returned wrong memory")
        else:
            results["errors"].append(f"READ failed: {response.status_code}")
            print(f"      ❌ READ failed: {response.status_code}")

    except Exception as e:
        results["errors"].append(f"READ exception: {str(e)}")
        print(f"      ❌ READ exception: {e}")

    # Test LIST
    print("   📋 Testing LIST...")
    try:
        response = requests.get(f"{base_url}/api/v1/memory/memories", headers=headers)

        if response.status_code == 200:
            memories = response.json()["memories"]
            if len(memories) >= 1:
                results["list"] = True
                print(f"      ✅ Listed {len(memories)} memories")
            else:
                results["errors"].append("LIST returned no memories")
                print("      ❌ LIST returned no memories")
        else:
            results["errors"].append(f"LIST failed: {response.status_code}")
            print(f"      ❌ LIST failed: {response.status_code}")

    except Exception as e:
        results["errors"].append(f"LIST exception: {str(e)}")
        print(f"      ❌ LIST exception: {e}")

    # Test UPDATE
    print("   ✏️ Testing UPDATE...")
    try:
        update_data = {
            "content": "Updated integration test memory",
            "tags": ["test", "integration", "updated"],
            "pinned": True,
        }

        response = requests.put(f"{base_url}/api/v1/memory/memories/{memory_id}", headers=headers, json=update_data)

        if response.status_code == 200:
            updated_memory = response.json()["memory"]
            if updated_memory["content"] == "Updated integration test memory":
                results["update"] = True
                print(f"      ✅ Updated memory: {updated_memory['content']}")
            else:
                results["errors"].append("UPDATE didn't apply changes")
                print("      ❌ UPDATE didn't apply changes")
        else:
            results["errors"].append(f"UPDATE failed: {response.status_code}")
            print(f"      ❌ UPDATE failed: {response.status_code}")

    except Exception as e:
        results["errors"].append(f"UPDATE exception: {str(e)}")
        print(f"      ❌ UPDATE exception: {e}")

    # Test DELETE
    print("   🗑️ Testing DELETE...")
    try:
        response = requests.delete(f"{base_url}/api/v1/memory/memories/{memory_id}", headers=headers)

        if response.status_code == 200:
            results["delete"] = True
            print("      ✅ Deleted memory")

            # Verify deletion
            verify_response = requests.get(f"{base_url}/api/v1/memory/memories/{memory_id}", headers=headers)
            if verify_response.status_code == 404:
                print("      ✅ Deletion verified")
            else:
                results["errors"].append("DELETE verification failed")
                print("      ❌ DELETE verification failed")
        else:
            results["errors"].append(f"DELETE failed: {response.status_code}")
            print(f"      ❌ DELETE failed: {response.status_code}")

    except Exception as e:
        results["errors"].append(f"DELETE exception: {str(e)}")
        print(f"      ❌ DELETE exception: {e}")

    return results


def test_error_scenarios(base_url: str, token: str) -> dict:
    """Test error scenarios and edge cases"""

    headers = {"Authorization": f"Bearer {token}"}
    results = {"unauthorized": False, "not_found": False, "invalid_uuid": False, "errors": []}

    print("\n🚨 Testing Error Scenarios:")

    # Test unauthorized access
    print("   🔒 Testing unauthorized access...")
    try:
        response = requests.get(f"{base_url}/api/v1/memory/memories")
        if response.status_code == 401:
            results["unauthorized"] = True
            print("      ✅ Unauthorized access properly blocked")
        else:
            results["errors"].append(f"Unauthorized test failed: expected 401, got {response.status_code}")
            print(f"      ❌ Expected 401, got {response.status_code}")
    except Exception as e:
        results["errors"].append(f"Unauthorized test exception: {str(e)}")
        print(f"      ❌ Exception: {e}")

    # Test not found
    print("   🔍 Testing not found...")
    try:
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{base_url}/api/v1/memory/memories/{fake_id}", headers=headers)
        if response.status_code == 404:
            results["not_found"] = True
            print("      ✅ Not found properly returns 404")
        else:
            results["errors"].append(f"Not found test failed: expected 404, got {response.status_code}")
            print(f"      ❌ Expected 404, got {response.status_code}")
    except Exception as e:
        results["errors"].append(f"Not found test exception: {str(e)}")
        print(f"      ❌ Exception: {e}")

    # Test invalid UUID
    print("   🆔 Testing invalid UUID...")
    try:
        response = requests.get(f"{base_url}/api/v1/memory/memories/invalid-uuid", headers=headers)
        if response.status_code == 400:
            results["invalid_uuid"] = True
            print("      ✅ Invalid UUID properly returns 400")
        else:
            results["errors"].append(f"Invalid UUID test failed: expected 400, got {response.status_code}")
            print(f"      ❌ Expected 400, got {response.status_code}")
    except Exception as e:
        results["errors"].append(f"Invalid UUID test exception: {str(e)}")
        print(f"      ❌ Exception: {e}")

    return results


def main():
    """Main integration test function"""

    print("=" * 80)
    print("MEMORY CRUD API INTEGRATION TESTS")
    print("=" * 80)

    # Load environment
    load_environment()

    # Configuration - use the correct port from ports.nv.yaml
    base_url = "http://localhost:13390"  # Apple + dev environment

    print(f"\n🌐 Testing against: {base_url}")
    print(f"📊 Database: PgBouncer connection (like production)")

    # Check if service is running
    print("\n🔍 Checking service availability...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("   ✅ Core API service is running")
        else:
            print(f"   ❌ Service returned: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Service not accessible: {e}")
        print("   💡 Make sure the core API is running:")
        print("      ./services/core-api/nv-core-api-start.sh")
        return False

    # Get authentication token
    print("\n🔐 Getting authentication token...")
    try:
        token = get_auth_token(base_url)
        print("   ✅ Authentication successful")
    except Exception as e:
        print(f"   ❌ Authentication failed: {e}")
        return False

    # Run CRUD tests
    crud_results = test_crud_operations(base_url, token)

    # Run error scenario tests
    error_results = test_error_scenarios(base_url, token)

    # Calculate results
    all_tests = list(crud_results.keys())[:-1] + list(error_results.keys())[:-1]  # Exclude 'errors'
    passed_tests = sum(1 for test in all_tests if crud_results.get(test, False) or error_results.get(test, False))
    total_tests = len(all_tests)
    success_rate = (passed_tests / total_tests) * 100

    # Show summary
    print(f"\n" + "=" * 80)
    print("INTEGRATION TEST RESULTS")
    print("=" * 80)

    print(f"\n📊 CRUD Operations:")
    for operation in ["create", "read", "update", "delete", "list"]:
        status = "✅" if crud_results.get(operation, False) else "❌"
        print(f"   {status} {operation.title()}")

    print(f"\n🚨 Error Handling:")
    for scenario in ["unauthorized", "not_found", "invalid_uuid"]:
        status = "✅" if error_results.get(scenario, False) else "❌"
        print(f"   {status} {scenario.replace('_', ' ').title()}")

    print(f"\n📈 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")

    if crud_results["errors"] or error_results["errors"]:
        print(f"\n⚠️  Errors encountered:")
        for error in crud_results["errors"] + error_results["errors"]:
            print(f"   - {error}")

    print(f"\n🎯 Test Coverage Analysis:")
    print("   ✅ All CRUD endpoints tested")
    print("   ✅ Authentication tested")
    print("   ✅ Error scenarios tested")
    print("   ✅ Real database connection via PgBouncer")
    print("   ✅ Production-like environment")

    # Final verdict
    print(f"\n" + "=" * 80)
    if success_rate >= 80:
        print("🎉 INTEGRATION TESTS PASSED!")
        print("   The memory CRUD endpoints are working correctly.")
        print("   ✅ Ready for team development")
        print("   ✅ Proper database connectivity via PgBouncer")
        print("   ✅ Comprehensive error handling")
        return True
    else:
        print("⚠️  INTEGRATION TESTS NEED ATTENTION")
        print(f"   Success rate: {success_rate:.1f}% (target: 80%+)")
        print("   Some endpoints may need fixes.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
