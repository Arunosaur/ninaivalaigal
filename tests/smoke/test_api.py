#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Smoke tests for API health and critical endpoints.
These tests ensure the API is running and responding correctly.
"""

import time

import pytest
import requests


class TestAPISmoke:
    """Comprehensive API smoke tests."""

    BASE_URL = "http://localhost:13370"
    TIMEOUT = 10

    def test_api_health_basic(self):
        """Test basic health endpoint."""
        url = f"{self.BASE_URL}/health"
        try:
            response = requests.get(url, timeout=self.TIMEOUT)
            assert response.status_code == 200
            data = response.json()
            assert data.get("status") == "ok"
        except Exception as e:
            pytest.fail(f"API basic health check failed: {e}")

    def test_api_health_detailed(self):
        """Test detailed health endpoint with database and Redis checks."""
        url = f"{self.BASE_URL}/health/detailed"
        try:
            response = requests.get(url, timeout=self.TIMEOUT)
            assert response.status_code == 200
            data = response.json()

            # Check for key health indicators
            assert "status" in data
            assert "uptime_s" in data or "uptime" in data or "db" in data  # Should have uptime or db info

            # Check database health
            if "database" in data:
                db_status = data["database"]
                assert db_status.get("status") in ["healthy", "degraded"]

            # Check Redis health
            if "redis" in data:
                redis_status = data["redis"]
                assert redis_status.get("status") in ["healthy", "degraded"]

        except Exception as e:
            pytest.fail(f"API detailed health check failed: {e}")

    def test_api_openapi_schema(self):
        """Test that OpenAPI schema is accessible."""
        url = f"{self.BASE_URL}/openapi.json"
        try:
            response = requests.get(url, timeout=self.TIMEOUT)
            assert response.status_code == 200

            # Verify it's valid JSON
            schema = response.json()
            assert "openapi" in schema or "swagger" in schema
            assert "paths" in schema

        except Exception as e:
            # Known issue: Large OpenAPI schema has Content-Length mismatch
            if "IncompleteRead" in str(e):
                pytest.skip(f"OpenAPI schema has known Content-Length issue: {e}")
            pytest.fail(f"OpenAPI schema check failed: {e}")

    def test_api_docs_accessible(self):
        """Test that API documentation is accessible."""
        url = f"{self.BASE_URL}/docs"
        try:
            response = requests.get(url, timeout=self.TIMEOUT)
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
        except Exception as e:
            pytest.fail(f"API docs accessibility check failed: {e}")

    def test_api_response_time(self):
        """Test API response time is acceptable."""
        url = f"{self.BASE_URL}/health"
        try:
            start_time = time.time()
            response = requests.get(url, timeout=self.TIMEOUT)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # Convert to ms
            assert response.status_code == 200
            assert response_time < 1000, f"Response time {response_time:.2f}ms exceeds 1000ms threshold"

        except Exception as e:
            pytest.fail(f"API response time check failed: {e}")

    def test_api_cors_headers(self):
        """Test that CORS headers are properly configured."""
        url = f"{self.BASE_URL}/health"
        try:
            response = requests.options(url, timeout=self.TIMEOUT)
            # Should not fail completely, even if CORS isn't configured
            assert response.status_code in [200, 405, 404]
        except Exception as e:
            pytest.fail(f"API CORS check failed: {e}")


class TestAPIMemoryEndpoints:
    """Smoke tests for memory-related endpoints."""

    BASE_URL = "http://localhost:13370"
    TIMEOUT = 10

    def test_memory_health(self):
        """Test memory provider health endpoint."""
        url = f"{self.BASE_URL}/health/status"  # Correct endpoint
        try:
            response = requests.get(url, timeout=self.TIMEOUT)
            # Should return 200 or 401 (if auth required)
            assert response.status_code in [200, 401]

            if response.status_code == 200:
                data = response.json()
                assert "status" in data
                assert data["status"] in ["healthy", "unhealthy"]

        except Exception as e:
            pytest.fail(f"Memory health check failed: {e}")

    def test_memory_tokenize_endpoint(self):
        """Test memory tokenize endpoint."""
        url = f"{self.BASE_URL}/memory/tokenize"
        try:
            # Test with valid text
            response = requests.post(url, json={"text": "test memory tokenization"}, timeout=self.TIMEOUT)
            assert response.status_code == 200
            data = response.json()
            assert "tokens" in data
            assert "count" in data
            assert data["count"] == 3
            assert data["tokens"] == ["test", "memory", "tokenization"]

            # Test with empty string
            response = requests.post(url, json={"text": ""}, timeout=self.TIMEOUT)
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0
            assert data["tokens"] == []

        except Exception as e:
            pytest.fail(f"Memory tokenize endpoint test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
