#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Complete V1 API Integration Tests

Tests all V1 endpoints to ensure they work correctly with versioning middleware.

Related: SPEC-088 API Versioning Strategy
"""

import pytest
from fastapi.testclient import TestClient


class TestV1Authentication:
    """Test V1 authentication endpoints."""

    def test_individual_signup(self, client: TestClient):
        """Test individual user signup."""
        response = client.post(
            "/api/v1/auth/signup/individual",
            json={"email": "test@example.com", "password": "SecurePass123!", "name": "Test User"},
        )

        assert response.status_code == 201
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "v1"

        data = response.json()
        assert data["success"] is True
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["verification_required"] is True

    def test_login(self, client: TestClient, test_user):
        """Test user login."""
        response = client.post(
            "/api/v1/auth/login", json={"email": test_user["email"], "password": test_user["password"]}
        )

        assert response.status_code == 200
        assert response.headers["X-API-Version"] == "v1"

        data = response.json()
        assert data["success"] is True
        assert "jwt_token" in data
        assert "expires_in" in data
        assert data["token_type"] == "Bearer"

    def test_get_current_user(self, client: TestClient, auth_headers):
        """Test get current user endpoint."""
        response = client.get("/api/v1/auth/me", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["X-API-Version"] == "v1"

        data = response.json()
        assert data["success"] is True
        assert "user" in data
        assert "user_id" in data["user"]
        assert "email" in data["user"]

    def test_refresh_token(self, client: TestClient, auth_headers):
        """Test token refresh."""
        response = client.post("/api/v1/auth/refresh", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "jwt_token" in data


class TestV1Users:
    """Test V1 user management endpoints."""

    def test_get_my_profile(self, client: TestClient, auth_headers):
        """Test get my profile."""
        response = client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["X-API-Version"] == "v1"

        data = response.json()
        assert data["success"] is True
        assert "user" in data
        assert "user_id" in data["user"]
        assert "email" in data["user"]

    def test_update_profile(self, client: TestClient, auth_headers):
        """Test update profile."""
        response = client.put("/api/v1/users/me", headers=auth_headers, json={"name": "Updated Name"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["name"] == "Updated Name"

    def test_get_user_by_id(self, client: TestClient, auth_headers, test_user):
        """Test get user by ID."""
        response = client.get(f"/api/v1/users/{test_user['user_id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user" in data


class TestV1Memory:
    """Test V1 memory endpoints."""

    def test_store_memory(self, client: TestClient, auth_headers):
        """Test store memory."""
        response = client.post(
            "/api/v1/memory",
            headers=auth_headers,
            json={"content": "Test memory content", "source": "manual", "data": {"context": "test", "tags": ["test"]}},
        )

        assert response.status_code == 201
        assert response.headers["X-API-Version"] == "v1"

        data = response.json()
        assert data["success"] is True
        assert "memory_id" in data
        return data["memory_id"]

    def test_get_memories(self, client: TestClient, auth_headers):
        """Test get memories with pagination."""
        response = client.get("/api/v1/memory?limit=10&skip=0", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memories" in data
        assert "pagination" in data
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["skip"] == 0

    def test_get_memory_by_id(self, client: TestClient, auth_headers, test_memory):
        """Test get specific memory."""
        response = client.get(f"/api/v1/memory/{test_memory['memory_id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "memory" in data
        assert data["memory"]["memory_id"] == test_memory["memory_id"]

    def test_search_memories(self, client: TestClient, auth_headers):
        """Test memory search."""
        response = client.post("/api/v1/memory/search?query=test&limit=10", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert "query" in data

    def test_delete_memory(self, client: TestClient, auth_headers, test_memory):
        """Test delete memory."""
        response = client.delete(f"/api/v1/memory/{test_memory['memory_id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestV1Teams:
    """Test V1 team endpoints."""

    def test_create_team(self, client: TestClient, auth_headers):
        """Test create team."""
        response = client.post(
            "/api/v1/teams",
            headers=auth_headers,
            json={"name": "Test Team", "description": "Test team description", "governance_type": "internal"},
        )

        assert response.status_code == 201
        assert response.headers["X-API-Version"] == "v1"

        data = response.json()
        assert data["success"] is True
        assert "team" in data
        assert data["team"]["name"] == "Test Team"
        return data["team"]["team_id"]

    def test_list_teams(self, client: TestClient, auth_headers):
        """Test list teams."""
        response = client.get("/api/v1/teams?skip=0&limit=10", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "teams" in data
        assert "pagination" in data

    def test_get_team(self, client: TestClient, auth_headers, test_team):
        """Test get team details."""
        response = client.get(f"/api/v1/teams/{test_team['team_id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "team" in data

    def test_update_team(self, client: TestClient, auth_headers, test_team):
        """Test update team."""
        response = client.put(
            f"/api/v1/teams/{test_team['team_id']}", headers=auth_headers, json={"name": "Updated Team Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_list_team_members(self, client: TestClient, auth_headers, test_team):
        """Test list team members."""
        response = client.get(f"/api/v1/teams/{test_team['team_id']}/members", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "members" in data


class TestV1Organizations:
    """Test V1 organization endpoints."""

    def test_create_organization(self, client: TestClient, auth_headers):
        """Test create organization."""
        response = client.post(
            "/api/v1/organizations",
            headers=auth_headers,
            json={"name": "Test Org", "industry": "Technology", "size": "11-50"},
        )

        assert response.status_code == 201
        assert response.headers["X-API-Version"] == "v1"

        data = response.json()
        assert data["success"] is True
        assert "organization" in data
        return data["organization"]["organization_id"]

    def test_list_organizations(self, client: TestClient, auth_headers):
        """Test list organizations."""
        response = client.get("/api/v1/organizations?skip=0&limit=10", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "organizations" in data

    def test_get_organization(self, client: TestClient, auth_headers, test_org):
        """Test get organization details."""
        response = client.get(f"/api/v1/organizations/{test_org['organization_id']}", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "organization" in data


class TestV1Versioning:
    """Test versioning middleware behavior."""

    def test_version_header_present(self, client: TestClient):
        """Test that version header is present."""
        response = client.get("/api/v1/test")
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "v1"

    def test_unsupported_version_returns_404(self, client: TestClient):
        """Test that unsupported versions return 404."""
        response = client.get("/api/v99/test")
        assert response.status_code == 404

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "VERSION_NOT_FOUND"

    def test_unversioned_endpoints_still_work(self, client: TestClient):
        """Test that unversioned endpoints still work."""
        response = client.get("/health")
        assert response.status_code == 200
        # Should not have version header

    def test_response_format_consistency(self, client: TestClient, auth_headers):
        """Test that all responses follow V1 format."""
        endpoints = [
            "/api/v1/users/me",
            "/api/v1/memory?limit=1",
            "/api/v1/teams?limit=1",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint, headers=auth_headers)
            assert response.status_code == 200

            data = response.json()
            assert "success" in data
            assert data["success"] is True


class TestV1ErrorHandling:
    """Test V1 error handling."""

    def test_unauthorized_returns_401(self, client: TestClient):
        """Test that unauthorized requests return 401."""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401

    def test_not_found_returns_404(self, client: TestClient, auth_headers):
        """Test that not found returns 404."""
        response = client.get("/api/v1/memory/00000000-0000-0000-0000-000000000000", headers=auth_headers)
        assert response.status_code == 404

    def test_validation_error_returns_422(self, client: TestClient):
        """Test that validation errors return 422."""
        response = client.post(
            "/api/v1/auth/signup/individual",
            json={"email": "invalid-email", "password": "short"},  # Invalid format  # Too short
        )
        assert response.status_code in [400, 422]


# Fixtures


@pytest.fixture
def test_user(client: TestClient):
    """Create a test user."""
    response = client.post(
        "/api/v1/auth/signup/individual",
        json={"email": "testuser@example.com", "password": "TestPass123!", "name": "Test User"},
    )
    data = response.json()
    return {"user_id": data["user"]["user_id"], "email": "testuser@example.com", "password": "TestPass123!"}


@pytest.fixture
def auth_headers(client: TestClient, test_user):
    """Get authentication headers."""
    response = client.post("/api/v1/auth/login", json={"email": test_user["email"], "password": test_user["password"]})
    data = response.json()
    token = data["jwt_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_memory(client: TestClient, auth_headers):
    """Create a test memory."""
    response = client.post(
        "/api/v1/memory",
        headers=auth_headers,
        json={"content": "Test memory", "source": "manual", "data": {"context": "test"}},
    )
    return response.json()


@pytest.fixture
def test_team(client: TestClient, auth_headers):
    """Create a test team."""
    response = client.post("/api/v1/teams", headers=auth_headers, json={"name": "Test Team", "description": "Test"})
    return response.json()["team"]


@pytest.fixture
def test_org(client: TestClient, auth_headers):
    """Create a test organization."""
    response = client.post(
        "/api/v1/organizations", headers=auth_headers, json={"name": "Test Org", "industry": "Technology"}
    )
    return response.json()["organization"]


if __name__ == "__main__":
    """
    Run tests.

    Usage:
        pytest tests/integration/test_v1_api_complete.py -v
    """
    pytest.main([__file__, "-v", "--tb=short"])
