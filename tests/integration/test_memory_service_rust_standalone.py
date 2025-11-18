#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Standalone integration tests for Memory Service (Rust)
Runs without requiring conftest or fixtures
"""

import time
from uuid import uuid4

import pytest
import requests

# Mark all tests in this file as rust_integration
pytestmark = pytest.mark.rust_integration

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.config import MEMORY_SERVICE_BASE_URL

MEMORY_SERVICE_URL = MEMORY_SERVICE_BASE_URL


def test_health_check():
    """Test health check endpoint"""
    print("Testing health check endpoint...")
    response = requests.get(f"{MEMORY_SERVICE_URL}/health", timeout=5)

    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

    data = response.json()
    assert data.get("service") == "memory-service" or data.get("service") is not None
    assert "status" in data
    print(f"✓ Health check passed: {data.get('status')}")
    return True


def test_metrics_endpoint():
    """Test metrics endpoint"""
    print("Testing metrics endpoint...")
    response = requests.get(f"{MEMORY_SERVICE_URL}/metrics", timeout=5)

    # Metrics might require auth or might be open - check both cases
    if response.status_code == 200:
        data = response.json()
        print(f"✓ Metrics endpoint accessible (200): {data}")
        return True
    elif response.status_code == 401:
        print("⚠ Metrics endpoint requires authentication (401)")
        # This is acceptable if metrics are protected
        return True
    else:
        print(f"✗ Unexpected status code: {response.status_code}")
        return False


def test_list_memories_requires_auth():
    """Test that listing memories requires authentication"""
    print("Testing list memories auth requirement...")
    response = requests.get(f"{MEMORY_SERVICE_URL}/api/v1/memories", timeout=5)

    assert response.status_code == 401, f"Should require auth (401), got {response.status_code}"
    print("✓ List memories correctly requires authentication")
    return True


def test_create_memory_requires_auth():
    """Test that creating memories requires authentication"""
    print("Testing create memory auth requirement...")
    response = requests.post(f"{MEMORY_SERVICE_URL}/api/v1/memories", json={"content": "Test"}, timeout=5)

    assert response.status_code == 401, f"Should require auth (401), got {response.status_code}"
    print("✓ Create memory correctly requires authentication")
    return True


def test_get_memory_requires_auth():
    """Test that getting a memory requires authentication"""
    print("Testing get memory auth requirement...")
    memory_id = str(uuid4())
    response = requests.get(f"{MEMORY_SERVICE_URL}/api/v1/memories/{memory_id}", timeout=5)

    assert response.status_code == 401, f"Should require auth (401), got {response.status_code}"
    print("✓ Get memory correctly requires authentication")
    return True


def test_invalid_token():
    """Test that invalid tokens are rejected"""
    print("Testing invalid token rejection...")
    response = requests.get(
        f"{MEMORY_SERVICE_URL}/api/v1/memories", headers={"Authorization": "Bearer invalid_token"}, timeout=5
    )

    assert response.status_code == 401, f"Should reject invalid token (401), got {response.status_code}"
    print("✓ Invalid token correctly rejected")
    return True


def test_create_memory_invalid_json():
    """Test creating memory with invalid JSON"""
    print("Testing invalid JSON handling...")
    response = requests.post(
        f"{MEMORY_SERVICE_URL}/api/v1/memories",
        data="invalid json",
        headers={"Content-Type": "application/json"},
        timeout=5,
    )

    # Should return 400 or 401 (401 if auth checked first)
    assert response.status_code in [400, 401], f"Expected 400 or 401, got {response.status_code}"
    print("✓ Invalid JSON correctly handled")
    return True


def test_health_check_performance():
    """Test that health check responds quickly"""
    print("Testing health check performance...")
    start = time.time()
    response = requests.get(f"{MEMORY_SERVICE_URL}/health", timeout=5)
    elapsed = time.time() - start

    assert response.status_code == 200
    assert elapsed < 1.0, f"Health check took {elapsed}s, should be < 1s"
    print(f"✓ Health check performance: {elapsed:.3f}s")
    return True


def main():
    """Run all tests"""
    print("=" * 70)
    print("Memory Service Integration Tests - Standalone")
    print("=" * 70)
    print()

    tests = [
        ("Health Check", test_health_check),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("List Memories Auth", test_list_memories_requires_auth),
        ("Create Memory Auth", test_create_memory_requires_auth),
        ("Get Memory Auth", test_get_memory_requires_auth),
        ("Invalid Token", test_invalid_token),
        ("Invalid JSON", test_create_memory_invalid_json),
        ("Health Performance", test_health_check_performance),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"✗ {name} failed")
        except Exception as e:
            failed += 1
            print(f"✗ {name} failed with error: {e}")
        print()

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    if failed == 0:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
