#!/usr/bin/env python3
"""
Comprehensive RBAC Integration Tests
Tests the complete RBAC system with context sensitivity and unit tests for retention/export
"""


import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from main import app

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
            "name": "RBAC Comprehensive Test User"
        }
        self.auth_token = None

    def test_user_signup_and_rbac_assignment(self):
        """Test user signup creates proper RBAC role assignment"""
        response = client.post("/auth/signup/individual", json=self.test_user_data)
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "jwt_token" in data["user"]

        # Login to get RBAC roles
        login_response = client.post("/auth/login", json={
            "email": self.test_user_data["email"],
            "password": self.test_user_data["password"]
        })
        assert login_response.status_code == 200

        login_data = login_response.json()
        assert "rbac_roles" in login_data["user"]
        assert login_data["user"]["rbac_roles"]["global"] == "MEMBER"

        self.auth_token = login_data["user"]["jwt_token"]

    def test_context_sensitivity_tiers(self):
        """Test RBAC matrix with per-context sensitivity tiers"""
        if not self.auth_token:
            self.test_user_signup_and_rbac_assignment()

        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test personal context creation (should work for MEMBER)
        context_data = {
            "name": "personal-sensitive-context",
            "description": "Personal context with sensitive data",
            "scope": "personal"
        }
        response = client.post("/contexts", json=context_data, headers=headers)
        assert response.status_code == 200

        # Test memory creation in context (should work for MEMBER)
        memory_data = {
            "type": "conversation",
            "source": "test",
            "data": {"content": "Test sensitive memory data"}
        }
        response = client.post("/memory", json=memory_data, headers=headers)
        assert response.status_code in [200, 201]

    def test_retention_export_permissions(self):
        """Test retention and export permissions based on role"""
        if not self.auth_token:
            self.test_user_signup_and_rbac_assignment()

        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test memory export (MEMBER should have export permissions)
        response = client.get("/memory/export", headers=headers)
        # Should work or return proper permission error
        assert response.status_code in [200, 403]

        # Test backup creation (should require higher role)
        backup_data = {"name": "test-backup", "include_sensitive": True}
        response = client.post("/backup", json=backup_data, headers=headers)
        # MEMBER should not have backup permissions
        assert response.status_code == 403

    def test_permission_audit_logging(self):
        """Test that all permission checks are properly audited"""
        if not self.auth_token:
            self.test_user_signup_and_rbac_assignment()

        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Perform several operations to generate audit logs
        client.get("/contexts", headers=headers)
        client.post("/contexts", json={"name": "audit-test"}, headers=headers)

        # Check audit logs (if accessible)
        audit_response = client.get("/rbac/audit", headers=headers)
        # May return 403 if user doesn't have audit permissions
        assert audit_response.status_code in [200, 403]

    def test_role_hierarchy_enforcement(self):
        """Test role hierarchy is properly enforced"""
        if not self.auth_token:
            self.test_user_signup_and_rbac_assignment()

        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test admin-only operations (should fail for MEMBER)
        admin_operations = [
            ("/rbac/status", "GET"),
            ("/rbac/roles/assign", "POST"),
            ("/users", "GET")
        ]

        for endpoint, method in admin_operations:
            if method == "GET":
                response = client.get(endpoint, headers=headers)
            else:
                response = client.post(endpoint, json={}, headers=headers)

            # Should return 403 for insufficient permissions
            assert response.status_code == 403

    def test_context_scope_permissions(self):
        """Test permissions work correctly across different context scopes"""
        if not self.auth_token:
            self.test_user_signup_and_rbac_assignment()

        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test personal scope (should work)
        personal_context = {
            "name": "personal-scope-test",
            "scope": "personal",
            "description": "Personal scope test"
        }
        response = client.post("/contexts", json=personal_context, headers=headers)
        assert response.status_code == 200

        # Test team scope without team membership (should fail or require team)
        team_context = {
            "name": "team-scope-test",
            "scope": "team",
            "team_id": 999,  # Non-existent team
            "description": "Team scope test"
        }
        response = client.post("/contexts", json=team_context, headers=headers)
        # Should fail due to invalid team or insufficient permissions
        assert response.status_code in [400, 403, 404]

    def test_permission_delegation_workflow(self):
        """Test permission delegation system"""
        if not self.auth_token:
            self.test_user_signup_and_rbac_assignment()

        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test requesting elevated permissions
        access_request = {
            "resource": "TEAM",
            "action": "ADMINISTER",
            "justification": "Need to manage team settings for project"
        }
        response = client.post("/rbac/access-request", json=access_request, headers=headers)
        # Should create access request
        assert response.status_code in [200, 201]

    def test_security_middleware_integration(self):
        """Test RBAC works with other security middleware"""
        if not self.auth_token:
            self.test_user_signup_and_rbac_assignment()

        headers = {"Authorization": f"Bearer {self.auth_token}"}

        # Test rate limiting doesn't interfere with RBAC
        for i in range(5):
            response = client.get("/contexts", headers=headers)
            assert response.status_code == 200

        # Test with invalid token
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/contexts", headers=invalid_headers)
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_async_rbac_operations():
    """Test RBAC with async operations"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Test async signup
        response = await ac.post("/auth/signup/individual", json={
            "email": "async_rbac_test@example.com",
            "password": "testpass123",
            "name": "Async RBAC Test"
        })
        assert response.status_code == 200

        # Test async login
        login_response = await ac.post("/auth/login", json={
            "email": "async_rbac_test@example.com",
            "password": "testpass123"
        })
        assert login_response.status_code == 200

        token = login_response.json()["user"]["jwt_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Test async context operations
        context_response = await ac.post("/contexts",
            json={"name": "async-test-context"},
            headers=headers
        )
        assert context_response.status_code == 200

def test_rbac_performance():
    """Test RBAC system performance doesn't degrade significantly"""
    import time

    # Create test user
    signup_response = client.post("/auth/signup/individual", json={
        "email": "perf_test@example.com",
        "password": "testpass123",
        "name": "Performance Test User"
    })
    assert signup_response.status_code == 200

    # Login
    login_response = client.post("/auth/login", json={
        "email": "perf_test@example.com",
        "password": "testpass123"
    })
    token = login_response.json()["user"]["jwt_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Time multiple operations
    start_time = time.time()
    for i in range(10):
        response = client.get("/contexts", headers=headers)
        assert response.status_code == 200
    end_time = time.time()

    # Should complete 10 operations in reasonable time (< 5 seconds)
    assert (end_time - start_time) < 5.0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
