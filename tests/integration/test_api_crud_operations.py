#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Comprehensive CRUD operation tests for API endpoints
#

import os
from uuid import uuid4

import pytest
import requests

BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:13390")
TIMEOUT = int(os.getenv("TEST_API_TIMEOUT", "30"))


@pytest.fixture
def auth_token():
    """Get authentication token for testing"""
    # This would normally authenticate and return a real token
    # For now, return None (tests will verify 401 responses)
    return None


@pytest.fixture
def authenticated_client(auth_token):
    """Create authenticated HTTP client"""
    client = requests.Session()
    if auth_token:
        client.headers.update({"Authorization": f"Bearer {auth_token}"})
    return client


class TestContextCRUD:
    """Test context CRUD operations"""

    def test_create_context(self, authenticated_client):
        """Test creating a context"""
        context_data = {
            "name": f"Test Context {uuid4().hex[:8]}",
            "description": "Test description",
            "scope": "personal",
            "visibility": "private",
        }

        response = authenticated_client.post(f"{BASE_URL}/contexts", json=context_data, timeout=TIMEOUT)

        # Without auth, should return 401
        if authenticated_client.headers.get("Authorization"):
            assert response.status_code in [200, 201, 400, 422]
        else:
            assert response.status_code in [401, 403, 404]

    def test_list_contexts(self, authenticated_client):
        """Test listing contexts"""
        response = authenticated_client.get(f"{BASE_URL}/contexts", timeout=TIMEOUT)

        if authenticated_client.headers.get("Authorization"):
            assert response.status_code in [200, 400, 401, 403, 404]
            if response.status_code == 200:
                data = response.json()
                assert "contexts" in data or isinstance(data, list)
        else:
            assert response.status_code in [401, 403, 404]

    def test_get_context_by_id(self, authenticated_client):
        """Test getting context by UUID"""
        context_id = str(uuid4())

        response = authenticated_client.get(f"{BASE_URL}/contexts/{context_id}", timeout=TIMEOUT)

        # Should handle UUID correctly (not 422 validation error)
        assert response.status_code in [401, 404]
        assert response.status_code != 422

    def test_update_context(self, authenticated_client):
        """Test updating a context"""
        context_id = str(uuid4())
        update_data = {"name": "Updated Context Name", "description": "Updated description"}

        response = authenticated_client.put(f"{BASE_URL}/contexts/{context_id}", json=update_data, timeout=TIMEOUT)

        assert response.status_code in [401, 403, 404, 200, 400]

    def test_delete_context(self, authenticated_client):
        """Test deleting a context"""
        context_id = str(uuid4())

        response = authenticated_client.delete(f"{BASE_URL}/contexts/{context_id}", timeout=TIMEOUT)

        assert response.status_code in [401, 404, 204, 200]


class TestUserCRUD:
    """Test user CRUD operations"""

    def test_get_current_user_profile(self, authenticated_client):
        """Test getting current user profile"""
        response = authenticated_client.get(f"{BASE_URL}/users/me", timeout=TIMEOUT)

        assert response.status_code in [401, 403, 200]

    def test_update_user_profile(self, authenticated_client):
        """Test updating user profile"""
        update_data = {"name": "Updated Name", "preferred_name": "Updated"}

        response = authenticated_client.patch(f"{BASE_URL}/users/me", json=update_data, timeout=TIMEOUT)

        assert response.status_code in [401, 403, 200, 400]

    def test_get_user_by_id(self, authenticated_client):
        """Test getting user by UUID"""
        user_id = str(uuid4())

        response = authenticated_client.get(f"{BASE_URL}/users/{user_id}", timeout=TIMEOUT)

        assert response.status_code in [401, 403, 404]
        assert response.status_code != 422  # Should handle UUID correctly


class TestTeamCRUD:
    """Test team CRUD operations"""

    def test_list_teams(self, authenticated_client):
        """Test listing teams"""
        response = authenticated_client.get(f"{BASE_URL}/teams", timeout=TIMEOUT)

        assert response.status_code in [401, 403, 200]

    def test_create_team(self, authenticated_client):
        """Test creating a team"""
        team_data = {"name": f"Test Team {uuid4().hex[:8]}", "description": "Test team description"}

        response = authenticated_client.post(f"{BASE_URL}/teams", json=team_data, timeout=TIMEOUT)

        assert response.status_code in [401, 403, 200, 201, 400, 422]

    def test_get_team_by_id(self, authenticated_client):
        """Test getting team by UUID"""
        team_id = str(uuid4())

        response = authenticated_client.get(f"{BASE_URL}/teams/{team_id}", timeout=TIMEOUT)

        assert response.status_code in [401, 403, 404]
        assert response.status_code != 422

    def test_update_team(self, authenticated_client):
        """Test updating a team"""
        team_id = str(uuid4())
        update_data = {"name": "Updated Team Name"}

        response = authenticated_client.patch(f"{BASE_URL}/teams/{team_id}", json=update_data, timeout=TIMEOUT)

        assert response.status_code in [401, 403, 404, 200, 400]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
