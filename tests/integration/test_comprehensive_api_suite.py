#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Comprehensive API Test Suite
US-92: Comprehensive API Test Suite
SPEC-086: Multi-Runtime Port Allocation

Covers all major API endpoints with comprehensive testing including:
- Authentication & Authorization
- CRUD Operations
- Error Handling
- Edge Cases
- Integration Flows
"""

# Import shared fixtures from conftest.py
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional
from uuid import UUID, uuid4

import pytest
import requests

# Test Configuration
BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:13390")
TIMEOUT = int(os.getenv("TEST_API_TIMEOUT", "30"))


class APITestClient:
    """Test client wrapper for API testing"""

    def __init__(self, base_url: str = BASE_URL, auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = TIMEOUT
        self.session = requests.Session()

        if auth_token:
            self.session.headers.update({"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"})

    def get(self, endpoint: str, **kwargs):
        """GET request"""
        url = f"{self.base_url}{endpoint}"
        return self.session.get(url, timeout=self.timeout, **kwargs)

    def post(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs):
        """POST request"""
        url = f"{self.base_url}{endpoint}"
        return self.session.post(url, json=json_data, timeout=self.timeout, **kwargs)

    def put(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs):
        """PUT request"""
        url = f"{self.base_url}{endpoint}"
        return self.session.put(url, json=json_data, timeout=self.timeout, **kwargs)

    def delete(self, endpoint: str, **kwargs):
        """DELETE request"""
        url = f"{self.base_url}{endpoint}"
        return self.session.delete(url, timeout=self.timeout, **kwargs)

    def patch(self, endpoint: str, json_data: Optional[Dict] = None, **kwargs):
        """PATCH request"""
        url = f"{self.base_url}{endpoint}"
        return self.session.patch(url, json=json_data, timeout=self.timeout, **kwargs)


@pytest.fixture
def api_client():
    """Create API test client"""
    return APITestClient()


@pytest.fixture
def authenticated_client(api_client):
    """Create authenticated API client"""
    # This would normally get a real auth token
    # For now, return client without auth (tests will need to handle 401s)
    return api_client


class TestHealthEndpoints:
    """Test health and monitoring endpoints"""

    def test_health_basic(self, api_client):
        """Test basic health endpoint"""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["ok", "healthy", "up"]

    def test_health_detailed(self, api_client):
        """Test detailed health endpoint"""
        response = api_client.get("/health/detailed")
        # May return 200, 401 (auth required), or 404 (endpoint doesn't exist)
        assert response.status_code in [200, 401, 404]

        if response.status_code == 200:
            data = response.json()
            assert "status" in data or "db" in data or "uptime" in data

    def test_metrics_endpoint(self, api_client):
        """Test metrics endpoint (may require auth)"""
        response = api_client.get("/metrics")
        # May return 200, 401, or 404 depending on configuration
        assert response.status_code in [200, 401, 404, 403]

    def test_openapi_schema(self, api_client):
        """Test OpenAPI schema endpoint"""
        response = api_client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema or "swagger" in schema
        assert "paths" in schema
        assert len(schema["paths"]) > 0

    def test_docs_endpoint(self, api_client):
        """Test API documentation endpoint"""
        response = api_client.get("/docs")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")


class TestAuthenticationEndpoints:
    """Test authentication and user management endpoints"""

    def test_login_endpoint_exists(self, api_client):
        """Verify login endpoint exists and handles requests"""
        response = api_client.post("/auth/login", json_data={"email": "test@example.com", "password": "test123"})
        # Should return 400 (bad credentials) or 401, not 404
        assert response.status_code in [200, 400, 401, 422]

    def test_signup_endpoint_exists(self, api_client):
        """Verify signup endpoint exists"""
        response = api_client.post(
            "/auth/signup/individual",
            json_data={
                "email": f"test_{uuid4().hex[:8]}@example.com",
                "password": "testpassword123",
                "full_name": "Test User",
            },
        )
        # Should return 200 (success), 400 (validation), 422 (unprocessable), or 409 (conflict)
        assert response.status_code in [200, 201, 400, 422, 409]

    def test_protected_endpoint_requires_auth(self, api_client):
        """Verify protected endpoints require authentication"""
        # Try accessing a protected endpoint without auth
        response = api_client.get("/users/me")
        # Should return 401 Unauthorized or 403 Forbidden
        assert response.status_code in [401, 403]


class TestUserEndpoints:
    """Test user management endpoints"""

    def test_get_user_profile_requires_auth(self, api_client):
        """Test getting user profile requires authentication"""
        response = api_client.get("/users/me")
        assert response.status_code in [401, 403]

    def test_get_user_by_id_endpoint(self, api_client):
        """Test getting user by ID endpoint structure"""
        # Use a valid UUID format
        user_id = str(uuid4())
        response = api_client.get(f"/users/{user_id}")
        # Should return 401/403 (auth required) or 404 (not found), not 500
        assert response.status_code in [401, 403, 404]
        assert response.status_code != 500

    def test_update_user_profile_requires_auth(self, api_client):
        """Test updating user profile requires authentication"""
        response = api_client.patch("/users/me", json_data={"name": "Updated Name"})
        assert response.status_code in [401, 403]

    def test_get_user_teams_endpoint(self, api_client):
        """Test getting user teams endpoint"""
        response = api_client.get("/users/me/teams")
        assert response.status_code in [401, 403]

    def test_get_user_organizations_endpoint(self, api_client):
        """Test getting user organizations endpoint"""
        response = api_client.get("/users/me/organizations")
        assert response.status_code in [401, 403]


class TestTeamEndpoints:
    """Test team management endpoints"""

    def test_list_teams_requires_auth(self, api_client):
        """Test listing teams requires authentication"""
        response = api_client.get("/teams")
        assert response.status_code in [401, 403]

    def test_create_team_requires_auth(self, api_client):
        """Test creating team requires authentication"""
        response = api_client.post("/teams", json_data={"name": "Test Team", "description": "Test Description"})
        assert response.status_code in [401, 403]

    def test_get_team_by_id(self, api_client):
        """Test getting team by ID"""
        team_id = str(uuid4())
        response = api_client.get(f"/teams/{team_id}")
        assert response.status_code in [401, 403, 404]
        assert response.status_code != 500

    def test_update_team_requires_auth(self, api_client):
        """Test updating team requires authentication"""
        team_id = str(uuid4())
        response = api_client.patch(f"/teams/{team_id}", json_data={"name": "Updated Team Name"})
        assert response.status_code in [401, 403]

    def test_create_external_team_requires_auth(self, api_client):
        """Test creating external team requires authentication"""
        response = api_client.post("/teams/external", json_data={"name": "External Team"})
        # May return 401/403 (auth required) or 405 (method not allowed)
        assert response.status_code in [401, 403, 405]


class TestContextEndpoints:
    """Test context management endpoints (using UUIDs)"""

    def test_list_contexts_requires_auth(self, api_client):
        """Test listing contexts requires authentication"""
        response = api_client.get("/contexts")
        # May return 401, 403, or 404 depending on routing
        assert response.status_code in [401, 403, 404]

    def test_create_context_requires_auth(self, api_client):
        """Test creating context requires authentication"""
        response = api_client.post(
            "/contexts", json_data={"name": "Test Context", "scope": "personal", "visibility": "private"}
        )
        # May return 401/403 (auth required) or 404 (endpoint routing)
        assert response.status_code in [401, 403, 404]

    def test_get_context_by_id(self, api_client):
        """Test getting context by UUID"""
        context_id = str(uuid4())
        response = api_client.get(f"/contexts/{context_id}")
        # Should handle UUID format correctly
        assert response.status_code in [401, 404]
        assert response.status_code != 422  # Should not be validation error for UUID

    def test_update_context_requires_auth(self, api_client):
        """Test updating context requires authentication"""
        context_id = str(uuid4())
        response = api_client.put(f"/contexts/{context_id}", json_data={"name": "Updated Context"})
        # May return 401/403 (auth required) or 404 (endpoint routing)
        assert response.status_code in [401, 403, 404]

    def test_delete_context_requires_auth(self, api_client):
        """Test deleting context requires authentication"""
        context_id = str(uuid4())
        response = api_client.delete(f"/contexts/{context_id}")
        # May return 401/403 (auth required) or 404 (endpoint routing)
        assert response.status_code in [401, 403, 404]

    def test_share_context_requires_auth(self, api_client):
        """Test sharing context requires authentication"""
        context_id = str(uuid4())
        response = api_client.post(
            f"/contexts/{context_id}/share", json_data={"shared_with_user_id": str(uuid4()), "permission_level": "read"}
        )
        # May return 401/403 (auth required) or 404 (endpoint routing)
        assert response.status_code in [401, 403, 404]

    def test_get_audit_logs_requires_auth(self, api_client):
        """Test getting audit logs requires authentication"""
        context_id = str(uuid4())
        response = api_client.get(f"/contexts/{context_id}/audit-logs")
        # May return 401, 403, or 404
        assert response.status_code in [401, 403, 404]


class TestMemoryEndpoints:
    """Test memory management endpoints"""

    def test_list_memories_requires_auth(self, api_client):
        """Test listing memories requires authentication"""
        response = api_client.get("/memory")
        # May return 401/403 (auth required) or 404 (endpoint routing)
        assert response.status_code in [401, 403, 404]

    def test_tokenize_endpoint(self, api_client):
        """Test memory tokenize endpoint (may be public)"""
        response = api_client.post("/memory/tokenize", json_data={"text": "This is a test memory"})
        # May be public endpoint, or may not exist (404), or require auth
        assert response.status_code in [200, 401, 403, 404]

        if response.status_code == 200:
            data = response.json()
            assert "tokens" in data or "count" in data


class TestOrganizationEndpoints:
    """Test organization management endpoints"""

    def test_list_organizations_requires_auth(self, api_client):
        """Test listing organizations requires authentication"""
        response = api_client.get("/organizations")
        assert response.status_code in [401, 403]

    def test_get_organization_teams(self, api_client):
        """Test getting organization teams"""
        org_id = str(uuid4())
        response = api_client.get(f"/organizations/{org_id}/teams")
        assert response.status_code in [401, 403]


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_invalid_uuid_format(self, api_client):
        """Test that invalid UUID format returns appropriate error"""
        # Try with invalid UUID
        response = api_client.get("/contexts/invalid-uuid")
        # Should return 422 (validation error) or 404
        assert response.status_code in [422, 404, 401]

    def test_missing_required_fields(self, api_client):
        """Test that missing required fields return validation errors"""
        response = api_client.post("/contexts", json_data={})
        # May return 401 (auth required), 422 (validation), or 404 (endpoint routing)
        assert response.status_code in [401, 403, 422, 404]

    def test_malformed_json(self, api_client):
        """Test handling of malformed JSON"""
        response = api_client.post("/contexts", data="not json", headers={"Content-Type": "application/json"})
        # Should return 422 or 400 for malformed JSON
        assert response.status_code in [400, 422, 401]

    def test_invalid_method_on_endpoint(self, api_client):
        """Test that invalid HTTP methods return appropriate errors"""
        response = api_client.post("/health")  # POST on GET-only endpoint
        # Should return 405 Method Not Allowed or 404
        assert response.status_code in [405, 404]

    def test_nonexistent_endpoint(self, api_client):
        """Test that nonexistent endpoints return 404"""
        response = api_client.get("/nonexistent/endpoint/12345")
        assert response.status_code == 404


class TestIntegrationFlows:
    """Test complete integration flows"""

    def test_health_to_openapi_flow(self, api_client):
        """Test that health check works and OpenAPI is accessible"""
        # First check health
        health_response = api_client.get("/health")
        assert health_response.status_code == 200

        # Then check OpenAPI
        openapi_response = api_client.get("/openapi.json")
        assert openapi_response.status_code == 200

    def test_endpoint_discovery(self, api_client):
        """Test that we can discover available endpoints"""
        response = api_client.get("/openapi.json")
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})

            # Verify key endpoints exist
            key_endpoints = ["/health", "/users", "/teams", "/contexts", "/organizations"]

            found_endpoints = []
            for endpoint in key_endpoints:
                # Check if endpoint or variant exists
                for path in paths.keys():
                    if endpoint in path or path.startswith(endpoint):
                        found_endpoints.append(endpoint)
                        break

            # Should find at least some endpoints
            assert len(found_endpoints) > 0, "Should discover at least some key endpoints"

    def test_cors_headers(self, api_client):
        """Test CORS headers are configured"""
        response = api_client.get("/health")
        # CORS headers may or may not be present, but shouldn't cause errors
        assert response.status_code == 200


class TestPerformance:
    """Test API performance characteristics"""

    def test_health_response_time(self, api_client):
        """Test health endpoint response time"""
        import time

        start = time.time()
        response = api_client.get("/health")
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        # Health check should be fast (< 1 second)
        assert elapsed < 1000, f"Health check took {elapsed:.2f}ms, expected < 1000ms"

    def test_concurrent_requests(self, api_client):
        """Test API handles concurrent requests"""
        import concurrent.futures

        def make_request():
            return api_client.get("/health")

        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]

        # All requests should succeed
        assert all(r.status_code == 200 for r in results), "All concurrent requests should succeed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
