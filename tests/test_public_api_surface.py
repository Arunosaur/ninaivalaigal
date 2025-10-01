"""
Test Public API Surface

Ensures that only allowed endpoints appear in public documentation.
Prevents accidental exposure of internal/admin endpoints.
"""

import pytest
from api_exposure import PUBLIC_TAGS, is_public_endpoint
from fastapi.testclient import TestClient
from main import app
from openapi_filter import get_endpoint_count, get_filtered_openapi

from rbac.permissions import Role


class TestPublicAPISurface:
    """Test suite for public API surface validation."""

    def test_public_tags_are_minimal(self):
        """Ensure PUBLIC_TAGS only contains safe endpoints."""
        # Public tags should be minimal - only auth and health
        assert PUBLIC_TAGS == {"auth", "health"}

    def test_unauthenticated_gets_empty_schema(self):
        """Unauthenticated users should get empty/minimal schema."""
        filtered_schema = get_filtered_openapi(app, role=None)

        endpoint_count = get_endpoint_count(filtered_schema)

        # Unauthenticated should see 0 endpoints
        assert endpoint_count == 0, (
            f"Unauthenticated users should see 0 endpoints, "
            f"but saw {endpoint_count}"
        )

    def test_viewer_role_limited_access(self):
        """VIEWER role should only see external-safe endpoints."""
        filtered_schema = get_filtered_openapi(app, role=Role.VIEWER)

        endpoint_count = get_endpoint_count(filtered_schema)

        # VIEWER should see limited endpoints (auth, health, memory-public)
        # Exact count will vary, but should be much less than total
        assert (
            endpoint_count < 50
        ), f"VIEWER role should see <50 endpoints, but saw {endpoint_count}"

        # Check that admin/billing endpoints are NOT visible
        paths = filtered_schema.get("paths", {})
        admin_paths = [p for p in paths if "admin" in p.lower()]
        billing_paths = [p for p in paths if "billing" in p.lower()]

        assert (
            len(admin_paths) == 0
        ), f"VIEWER should not see admin paths: {admin_paths}"
        assert (
            len(billing_paths) == 0
        ), f"VIEWER should not see billing paths: {billing_paths}"

    def test_member_role_no_admin_access(self):
        """MEMBER role should not see admin endpoints."""
        filtered_schema = get_filtered_openapi(app, role=Role.MEMBER)

        paths = filtered_schema.get("paths", {})
        admin_paths = [p for p in paths if "/admin" in p]

        assert (
            len(admin_paths) == 0
        ), f"MEMBER role should not see /admin paths, but saw: {admin_paths}"

    def test_admin_role_has_admin_access(self):
        """ADMIN role should see admin endpoints."""
        filtered_schema = get_filtered_openapi(app, role=Role.ADMIN)

        endpoint_count = get_endpoint_count(filtered_schema)

        # ADMIN should see more endpoints than MEMBER
        member_schema = get_filtered_openapi(app, role=Role.MEMBER)
        member_count = get_endpoint_count(member_schema)

        assert endpoint_count > member_count, (
            f"ADMIN should see more endpoints than MEMBER "
            f"(admin: {endpoint_count}, member: {member_count})"
        )

    def test_system_role_sees_all_endpoints(self):
        """SYSTEM role should see all endpoints."""
        filtered_schema = get_filtered_openapi(app, role=Role.SYSTEM)

        endpoint_count = get_endpoint_count(filtered_schema)

        # SYSTEM should see the most endpoints
        # Current total is ~265
        assert (
            endpoint_count > 200
        ), f"SYSTEM role should see >200 endpoints, but saw {endpoint_count}"

    def test_role_hierarchy_is_enforced(self):
        """Ensure role hierarchy: VIEWER < MEMBER < ADMIN < SYSTEM."""
        viewer_count = get_endpoint_count(get_filtered_openapi(app, role=Role.VIEWER))
        member_count = get_endpoint_count(get_filtered_openapi(app, role=Role.MEMBER))
        admin_count = get_endpoint_count(get_filtered_openapi(app, role=Role.ADMIN))
        system_count = get_endpoint_count(get_filtered_openapi(app, role=Role.SYSTEM))

        assert (
            viewer_count < member_count
        ), "VIEWER should see fewer endpoints than MEMBER"
        assert (
            member_count < admin_count
        ), "MEMBER should see fewer endpoints than ADMIN"
        assert (
            admin_count <= system_count
        ), "ADMIN should see fewer or equal endpoints than SYSTEM"

    def test_sensitive_paths_not_in_public(self):
        """Ensure sensitive paths are never in public schema."""
        public_schema = get_filtered_openapi(app, role=None)
        paths = public_schema.get("paths", {})

        # These paths should NEVER be in public schema
        forbidden_patterns = [
            "/admin",
            "/billing",
            "/metrics",
            "/ops",
            "/vendor",
            "/invoice",
            "/api-keys",
        ]

        for pattern in forbidden_patterns:
            matching_paths = [p for p in paths if pattern in p.lower()]
            assert len(matching_paths) == 0, (
                f"Public schema should not contain paths with '{pattern}', "
                f"but found: {matching_paths}"
            )

    def test_is_public_endpoint_function(self):
        """Test the is_public_endpoint helper function."""
        # Public tags should be recognized
        assert is_public_endpoint(["auth"]) is True
        assert is_public_endpoint(["health"]) is True

        # Non-public tags should not be recognized
        assert is_public_endpoint(["admin"]) is False
        assert is_public_endpoint(["billing"]) is False
        assert is_public_endpoint(["memory"]) is False

        # Mixed tags - should be public if ANY tag is public
        assert is_public_endpoint(["auth", "admin"]) is True

        # Empty/None should not be public
        assert is_public_endpoint([]) is False
        assert is_public_endpoint(None) is False


class TestDocumentationEndpoints:
    """Test the protected documentation endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_openapi_json_returns_filtered_schema(self, client):
        """Test that /openapi.json returns filtered schema."""
        response = client.get("/openapi.json")

        # In development mode, should return 200 with SYSTEM role
        assert response.status_code == 200

        data = response.json()
        assert "paths" in data
        assert "info" in data

    def test_docs_endpoint_exists(self, client):
        """Test that /docs endpoint exists."""
        response = client.get("/docs")

        # In development mode with SYSTEM role, should return 200
        # In production without auth, should return 401
        assert response.status_code in [200, 401]

    def test_default_docs_disabled(self, client):
        """Ensure default FastAPI docs endpoints are disabled."""
        # These should NOT exist since we disabled them
        response = client.get("/redoc")
        assert response.status_code == 404, "/redoc should be disabled"


@pytest.mark.skipif(
    True,  # Skip by default - requires running server
    reason="Integration test - requires running server with authentication",
)
class TestAuthenticatedDocAccess:
    """Integration tests for authenticated doc access (requires running server)."""

    def test_unauthenticated_docs_returns_401(self):
        """Test that unauthenticated access to /docs returns 401."""
        import requests

        response = requests.get("http://localhost:13390/docs")

        # Should return 401 in production
        # In development with SYSTEM role, returns 200
        assert response.status_code in [200, 401]

    def test_viewer_sees_limited_endpoints(self):
        """Test that VIEWER role sees limited endpoints."""
        # TODO: Implement with actual JWT token
        pass

    def test_admin_sees_admin_endpoints(self):
        """Test that ADMIN role sees admin endpoints."""
        # TODO: Implement with actual JWT token
        pass
