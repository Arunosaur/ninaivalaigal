#!/usr/bin/env python3
"""
Cross-platform testing script for mem0
Tests CLI, shell integration, and server functionality
"""

import json
import subprocess
import sys
import time


def run_command(cmd, cwd=None):
    """Run command and return result"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=cwd
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e), "returncode": -1}


def test_cli_functionality():
    """Test CLI commands"""
    print("🧪 Testing CLI functionality...")

    # Test context creation
    result = run_command("./client/mem0 context start cross-platform-test")
    if not result["success"]:
        print(f"❌ Context creation failed: {result['stderr']}")
        return False
    print("✅ Context creation successful")

    # Test memory storage
    result = run_command(
        './client/mem0 remember "Cross-platform test memory" --context cross-platform-test'
    )
    if not result["success"]:
        print(f"❌ Memory storage failed: {result['stderr']}")
        return False
    print("✅ Memory storage successful")

    # Test memory recall
    result = run_command("./client/mem0 recall --context cross-platform-test")
    if not result["success"]:
        print(f"❌ Memory recall failed: {result['stderr']}")
        return False

    try:
        memory_data = json.loads(result["stdout"])
        if memory_data and "Cross-platform test memory" in str(memory_data):
            print("✅ Memory recall successful")
            return True
        else:
            print("❌ Memory recall returned unexpected data")
            return False
    except json.JSONDecodeError:
        print("❌ Memory recall returned invalid JSON")
        return False


def test_fastapi_server():
    """Test FastAPI server endpoints"""
    print("🧪 Testing FastAPI server...")

    # Test contexts endpoint
    result = run_command('curl -s -X GET "http://127.0.0.1:13370/contexts"')
    if not result["success"]:
        print(f"❌ FastAPI contexts endpoint failed: {result['stderr']}")
        return False

    try:
        contexts_data = json.loads(result["stdout"])
        if "contexts" in contexts_data:
            print("✅ FastAPI contexts endpoint working")
        else:
            print("❌ FastAPI contexts endpoint returned unexpected format")
            return False
    except json.JSONDecodeError:
        print("❌ FastAPI contexts endpoint returned invalid JSON")
        return False

    # Test memory endpoint
    result = run_command(
        'curl -s -X GET "http://127.0.0.1:13370/memory?context=cross-platform-test"'
    )
    if not result["success"]:
        print(f"❌ FastAPI memory endpoint failed: {result['stderr']}")
        return False

    try:
        memory_data = json.loads(result["stdout"])
        if isinstance(memory_data, list):
            print("✅ FastAPI memory endpoint working")
            return True
        else:
            print("❌ FastAPI memory endpoint returned unexpected format")
            return False
    except json.JSONDecodeError:
        print("❌ FastAPI memory endpoint returned invalid JSON")
        return False


def test_mcp_server():
    """Test MCP server functionality"""
    print("🧪 Testing MCP server...")

    result = run_command("cd server && python test_mcp.py")
    if not result["success"]:
        print(f"❌ MCP server test failed: {result['stderr']}")
        return False

    if "MCP server tools test completed!" in result["stdout"]:
        print("✅ MCP server functionality working")
        return True
    else:
        print("❌ MCP server test did not complete successfully")
        return False


def test_database_connection():
    """Test database connectivity"""
    print("🧪 Testing database connection...")

    result = run_command(
        "cd server && python -c \"from database import DatabaseManager; from main import load_config; db = DatabaseManager(load_config()); session = db.get_session(); print('Database connected'); session.close()\""
    )
    if not result["success"]:
        print(f"❌ Database connection failed: {result['stderr']}")
        return False

    if "Database connected" in result["stdout"]:
        print("✅ Database connection working")
        return True
    else:
        print("❌ Database connection test failed")
        return False


def main():
    """Run all cross-platform tests"""
    print("🚀 Starting cross-platform tests for mem0...")
    print("=" * 50)

    tests = [
        ("Database Connection", test_database_connection),
        ("CLI Functionality", test_cli_functionality),
        ("FastAPI Server", test_fastapi_server),
        ("MCP Server", test_mcp_server),
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        results[test_name] = test_func()
        time.sleep(1)  # Brief pause between tests

    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if not passed:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! mem0 is working correctly across platforms.")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED. Please check the output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
