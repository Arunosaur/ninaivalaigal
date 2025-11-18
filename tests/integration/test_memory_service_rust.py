#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Integration tests for Memory Service (Rust)

Tests the Rust Memory Service endpoints:
- Health check
- Metrics
- JWT authentication
- CRUD operations
- Cache behavior
- Error handling

Requires:
- Memory Service running on port 13393 (or configured port)
- PostgreSQL database accessible
- Redis running
- Core API running for JWT token generation

Run with: pytest tests/integration/test_memory_service_rust.py -v
"""

import json
import time
from typing import Any, Dict, Optional
from uuid import uuid4

import pytest
import requests

# Mark all tests in this file as rust_integration
pytestmark = pytest.mark.rust_integration

# Configuration
from tests.config import CORE_API_BASE_URL, MEMORY_SERVICE_BASE_URL

MEMORY_SERVICE_URL = MEMORY_SERVICE_BASE_URL
CORE_API_URL = CORE_API_BASE_URL


class MemoryServiceClient:
    """Client for interacting with Memory Service"""

    def __init__(self, base_url: str, token: Optional[str] = None):
        self.base_url = base_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def get(self, path: str) -> requests.Response:
        """Make GET request"""
        return self.session.get(f"{self.base_url}{path}")

    def post(self, path: str, data: Dict[str, Any]) -> requests.Response:
        """Make POST request"""
        return self.session.post(f"{self.base_url}{path}", json=data, headers={"Content-Type": "application/json"})

    def health_check(self) -> requests.Response:
        """Check service health"""
        return self.get("/health")

    def get_metrics(self) -> requests.Response:
        """Get service metrics"""
        return self.get("/metrics")

    def list_memories(self) -> requests.Response:
        """List all memories"""
        return self.get("/api/v1/memories")

    def create_memory(self, content: str, metadata: Optional[Dict] = None) -> requests.Response:
        """Create a new memory"""
        data = {"content": content}
        if metadata:
            data["metadata"] = metadata
        return self.post("/api/v1/memories", data)

    def get_memory(self, memory_id: str) -> requests.Response:
        """Get a specific memory by ID"""
        return self.get(f"/api/v1/memories/{memory_id}")


def get_test_jwt_token() -> Optional[str]:
    """
    Get a test JWT token from Core API

    This requires Core API to be running and a test user to exist.
    For now, returns None if Core API is not available.
    """
    try:
        # Try to login with a test user
        login_data = {"email": "test@example.com", "password": "Test1234!"}
        response = requests.post(f"{CORE_API_URL}/auth/login", json=login_data, timeout=5)
        if response.status_code == 200:
            return response.json().get("access_token")
    except requests.RequestException:
        pass

    return None


@pytest.fixture(scope="module")
def client():
    """Create a Memory Service client"""
    token = get_test_jwt_token()
    return MemoryServiceClient(MEMORY_SERVICE_URL, token)


@pytest.fixture(scope="module")
def client_no_auth():
    """Create a Memory Service client without authentication"""
    return MemoryServiceClient(MEMORY_SERVICE_URL)


class TestHealthAndMetrics:
    """Tests for health check and metrics endpoints"""

    def test_health_check(self, client_no_auth):
        """Test health check endpoint"""
        response = client_no_auth.health_check()
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert data["service"] == "memory-service"
        assert "status" in data
        assert "database" in data
        assert "redis" in data
        assert data["status"] in ["healthy", "degraded"]

    def test_metrics_endpoint(self, client_no_auth):
        """Test metrics endpoint"""
        response = client_no_auth.get_metrics()
        assert response.status_code == 200

        data = response.json()
        assert "active_connections" in data
        assert "total_requests" in data
        assert "cache_hits" in data
        assert "cache_misses" in data


class TestAuthentication:
    """Tests for JWT authentication"""

    def test_list_memories_requires_auth(self, client_no_auth):
        """Test that listing memories requires authentication"""
        response = client_no_auth.list_memories()
        assert response.status_code == 401, "Should require authentication"

        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"] == "Authentication failed"

    def test_create_memory_requires_auth(self, client_no_auth):
        """Test that creating memories requires authentication"""
        response = client_no_auth.create_memory("Test content")
        assert response.status_code == 401, "Should require authentication"

    def test_get_memory_requires_auth(self, client_no_auth):
        """Test that getting a memory requires authentication"""
        memory_id = str(uuid4())
        response = client_no_auth.get_memory(memory_id)
        assert response.status_code == 401, "Should require authentication"

    def test_invalid_token(self, client_no_auth):
        """Test that invalid tokens are rejected"""
        invalid_client = MemoryServiceClient(MEMORY_SERVICE_URL, "invalid_token")
        response = invalid_client.list_memories()
        assert response.status_code == 401


class TestCRUDOperations:
    """Tests for CRUD operations (requires authentication)"""

    @pytest.mark.skipif(get_test_jwt_token() is None, reason="Requires valid JWT token from Core API")
    def test_list_memories_with_auth(self, client):
        """Test listing memories with valid authentication"""
        response = client.list_memories()
        assert response.status_code == 200

        # Should return a list (may be empty)
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.skipif(get_test_jwt_token() is None, reason="Requires valid JWT token from Core API")
    def test_create_memory_with_auth(self, client):
        """Test creating a memory with valid authentication"""
        test_content = f"Test memory {uuid4()}"
        response = client.create_memory(test_content, metadata={"test": True, "timestamp": time.time()})

        # Should return 200 or 201
        assert response.status_code in [200, 201], f"Expected 200/201, got {response.status_code}: {response.text}"

        data = response.json()
        assert "id" in data
        assert data["content"] == test_content
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.skipif(get_test_jwt_token() is None, reason="Requires valid JWT token from Core API")
    def test_get_memory_not_found(self, client):
        """Test getting a non-existent memory"""
        memory_id = str(uuid4())
        response = client.get_memory(memory_id)

        # Should return 404 for non-existent memory
        assert response.status_code == 404


class TestErrorHandling:
    """Tests for error handling"""

    def test_create_memory_invalid_json(self, client_no_auth):
        """Test creating memory with invalid JSON"""
        # Try to send invalid JSON
        response = requests.post(
            f"{MEMORY_SERVICE_URL}/api/v1/memories", data="invalid json", headers={"Content-Type": "application/json"}
        )
        # Should return 400 or 401 (401 if auth required)
        assert response.status_code in [400, 401]

    def test_create_memory_missing_content(self, client):
        """Test creating memory without content field"""
        if client.token is None:
            pytest.skip("Requires authentication")

        response = client.post("/api/v1/memories", {})
        # Should return 400 Bad Request
        assert response.status_code in [400, 422]


class TestCacheBehavior:
    """Tests for Redis cache behavior"""

    @pytest.mark.skipif(get_test_jwt_token() is None, reason="Requires valid JWT token from Core API")
    def test_cache_behavior(self, client):
        """Test that cache is working (if implemented)"""
        # This test would check:
        # 1. First request hits database
        # 2. Second request hits cache (faster)
        # 3. Cache invalidation on updates

        # For now, this is a placeholder
        # Actual implementation depends on cache being implemented
        pytest.skip("Cache behavior testing requires cache implementation")


class TestPerformance:
    """Performance tests"""

    def test_health_check_performance(self, client_no_auth):
        """Test that health check responds quickly"""
        start = time.time()
        response = client_no_auth.health_check()
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0, f"Health check took {elapsed}s, should be < 1s"


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v", "-s"])
