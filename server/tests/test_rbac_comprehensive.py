#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Comprehensive RBAC Integration Tests
Tests the complete RBAC system with context sensitivity and unit tests for retention/export
"""


import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app
from auth import AUTH_COOKIE_NAME

# Test client setup
client = TestClient(app)


class TestRBACComprehensive:
    """Comprehensive RBAC system tests"""

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup test data"""
        self.test_user_data = {
            "email": "rbac_comprehensive_test@example.com",
            "password": "testpass123",
            "name": "RBAC Comprehensive Test User",
        }
        self.session_cookies = None

    def _ensure_authenticated(self):
        """Ensure the shared test client has an authenticated session."""

        if self.session_cookies is None:
            self.test_user_signup_and_rbac_assignment()

        if self.session_cookies is not None:
            client.cookies.update(self.session_cookies)

    @pytest.mark.unit
    def test_user_signup_and_rbac_assignment(self):
        """Test user signup creates proper RBAC role assignment"""
        response = client.post("/auth/signup/individual", json=self.test_user_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True

        # Login to get RBAC roles
        login_response = client.post(
            "/auth/login",
            json={
                "email": self.test_user_data["email"],
                "password": self.test_user_data["password"],
            },
        )
        assert login_response.status_code == 200

        login_data = login_response.json()
        assert "user" in login_data
        assert "session" in login_data
        assert login_data["session"]["token_delivery"] == "cookie"
        assert login_data["user"]["rbac_roles"]["global"] == "MEMBER"

        cookie_token = login_response.cookies.get(AUTH_COOKIE_NAME)
        assert cookie_token, "Expected authentication cookie to be set"
        self.session_cookies = login_response.cookies

    @pytest.mark.unit
    def test_context_sensitivity_tiers(self):
        """Test RBAC matrix with per-context sensitivity tiers"""
        self._ensure_authenticated()

        # Test personal context creation (should work for MEMBER)
        context_data = {
            "name": "personal-sensitive-context",
            "description": "Personal context with sensitive data",
            "scope": "personal",
        }
        response = client.post("/contexts", json=context_data)
        assert response.status_code == 200

        # Test memory creation in context (should work for MEMBER)
        memory_data = {
            "type": "conversation",
            "source": "test",
            "data": {"content": "Test sensitive memory data"},
        }
        response = client.post("/memory", json=memory_data)
        assert response.status_code in [200, 201]

    @pytest.mark.unit
    def test_retention_export_permissions(self):
        """Test retention and export permissions based on role"""
        self._ensure_authenticated()

        # Test memory export (MEMBER should have export permissions)
        response = client.get("/memory/export")
        # Should work or return proper permission error
        assert response.status_code in [200, 403]

        # Test backup creation (should require higher role)
        backup_data = {"name": "test-backup", "include_sensitive": True}
        response = client.post("/backup", json=backup_data)
        # MEMBER should not have backup permissions
        assert response.status_code == 403

    @pytest.mark.unit
    def test_permission_audit_logging(self):
        """Test that all permission checks are properly audited"""
        self._ensure_authenticated()

        # Perform several operations to generate audit logs
        client.get("/contexts")
        client.post("/contexts", json={"name": "audit-test"})

        # Check audit logs (if accessible)
        audit_response = client.get("/rbac/audit")
        # May return 403 if user doesn't have audit permissions
        assert audit_response.status_code in [200, 403]

    @pytest.mark.unit
    def test_role_hierarchy_enforcement(self):
        """Test role hierarchy is properly enforced"""
        self._ensure_authenticated()

        # Test admin-only operations (should fail for MEMBER)
        admin_operations = [
            ("/rbac/status", "GET"),
            ("/rbac/roles/assign", "POST"),
            ("/users", "GET"),
        ]

        for endpoint, method in admin_operations:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint, json={})

            # Should return 403 for insufficient permissions
            assert response.status_code == 403

    @pytest.mark.unit
    def test_context_scope_permissions(self):
        """Test permissions work correctly across different context scopes"""
        self._ensure_authenticated()

        # Test personal scope (should work)
        personal_context = {
            "name": "personal-scope-test",
            "scope": "personal",
            "description": "Personal scope test",
        }
        response = client.post("/contexts", json=personal_context)
        assert response.status_code == 200

        # Test team scope without team membership (should fail or require team)
        team_context = {
            "name": "team-scope-test",
            "scope": "team",
            "team_id": 999,  # Non-existent team
            "description": "Team scope test",
        }
        response = client.post("/contexts", json=team_context)
        # Should fail due to invalid team or insufficient permissions
        assert response.status_code in [400, 403, 404]

    @pytest.mark.unit
    def test_permission_delegation_workflow(self):
        """Test permission delegation system"""
        self._ensure_authenticated()

        # Test requesting elevated permissions
        access_request = {
            "resource": "TEAM",
            "action": "ADMINISTER",
            "justification": "Need to manage team settings for project",
        }
        response = client.post("/rbac/access-request", json=access_request)
        # Should create access request
        assert response.status_code in [200, 201]

    @pytest.mark.unit
    def test_security_middleware_integration(self):
        """Test RBAC works with other security middleware"""
        self._ensure_authenticated()

        # Test rate limiting doesn't interfere with RBAC
        for _i in range(5):
            response = client.get("/contexts")
            assert response.status_code == 200

        # Test with invalid session (cleared cookies)
        saved_cookies = client.cookies.copy()
        client.cookies.clear()
        response = client.get("/contexts")
        assert response.status_code in [401, 403]
        client.cookies.update(saved_cookies)


@pytest.mark.unit
@pytest.mark.asyncio
async def test_async_rbac_operations():
    """Test RBAC with async operations"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test async signup
        response = await ac.post(
            "/auth/signup/individual",
            json={
                "email": "async_rbac_test@example.com",
                "password": "testpass123",
                "name": "Async RBAC Test",
            },
        )
        assert response.status_code == 200

        # Test async login
        login_response = await ac.post(
            "/auth/login",
            json={"email": "async_rbac_test@example.com", "password": "testpass123"},
        )
        assert login_response.status_code == 200

        assert login_response.cookies.get(AUTH_COOKIE_NAME)
        ac.cookies.update(login_response.cookies)

        # Test async context operations
        context_response = await ac.post("/contexts", json={"name": "async-test-context"})
        assert context_response.status_code == 200


@pytest.mark.unit
def test_rbac_performance():
    """Test RBAC system performance doesn't degrade significantly"""
    import time

    # Create test user
    signup_response = client.post(
        "/auth/signup/individual",
        json={
            "email": "perf_test@example.com",
            "password": "testpass123",
            "name": "Performance Test User",
        },
    )
    assert signup_response.status_code == 200

    # Login
    login_response = client.post(
        "/auth/login",
        json={"email": "perf_test@example.com", "password": "testpass123"},
    )
    assert login_response.cookies.get(AUTH_COOKIE_NAME)
    client.cookies.update(login_response.cookies)

    # Time multiple operations
    start_time = time.time()
    for _i in range(10):
        response = client.get("/contexts")
        assert response.status_code == 200
    end_time = time.time()

    # Should complete 10 operations in reasonable time (< 5 seconds)
    assert (end_time - start_time) < 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
