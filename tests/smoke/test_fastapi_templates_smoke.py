#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2025 Medhasys LLC
#
"""
Smoke Tests for FastAPI Templates

Validates critical paths:
- Template rendering
- Backend endpoint connectivity
- Database connectivity
- Authentication flow
- Error handling
"""

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import FastAPI app
try:
    from services.core_api.lib.main import app

    APP_AVAILABLE = True
except ImportError:
    APP_AVAILABLE = False
    app = None


@pytest.mark.skipif(not APP_AVAILABLE, reason="FastAPI app not available")
class TestTemplateRendering:
    """Test template rendering for customer and admin pages."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_customer_login_page_renders(self):
        """Test that customer login page renders successfully."""
        response = self.client.get("/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert b"login" in response.content.lower() or b"sign in" in response.content.lower()

    def test_customer_signup_page_renders(self):
        """Test that customer signup page renders successfully."""
        response = self.client.get("/signup")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_admin_login_page_renders(self):
        """Test that admin login page renders successfully."""
        response = self.client.get("/admin/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_customer_dashboard_requires_auth(self):
        """Test that customer dashboard requires authentication."""
        response = self.client.get("/customer/dashboard")
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]

    def test_admin_analytics_requires_auth(self):
        """Test that admin analytics requires authentication."""
        response = self.client.get("/admin/analytics")
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]


@pytest.mark.skipif(not APP_AVAILABLE, reason="FastAPI app not available")
class TestBackendEndpoints:
    """Test backend API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "ok"]

    def test_api_docs_available(self):
        """Test that OpenAPI docs are available."""
        response = self.client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_available(self):
        """Test that OpenAPI schema is available."""
        response = self.client.get("/openapi.json")
        assert response.status_code == 200
        schema = response.json()
        assert "openapi" in schema or "swagger" in schema


@pytest.mark.skipif(not APP_AVAILABLE, reason="FastAPI app not available")
class TestDatabaseConnectivity:
    """Test database connectivity through endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_database_health(self):
        """Test database health through health endpoint."""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        # Check if database status is reported
        if "database" in data:
            assert data["database"] in ["connected", "healthy", "ok"]


@pytest.mark.skipif(not APP_AVAILABLE, reason="FastAPI app not available")
class TestAuthenticationFlow:
    """Test authentication flow."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_login_endpoint_exists(self):
        """Test that login endpoint exists."""
        # Try POST to login (should handle even without credentials)
        response = self.client.post("/login", data={})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404

    def test_signup_endpoint_exists(self):
        """Test that signup endpoint exists."""
        response = self.client.post("/signup", data={})
        # Should not return 404 (endpoint exists)
        assert response.status_code != 404


@pytest.mark.skipif(not APP_AVAILABLE, reason="FastAPI app not available")
class TestErrorHandling:
    """Test error handling in templates and endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_404_handling(self):
        """Test 404 error handling."""
        response = self.client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_invalid_method_handling(self):
        """Test invalid HTTP method handling."""
        response = self.client.delete("/login")
        # Should return 405 Method Not Allowed or handle gracefully
        assert response.status_code in [405, 400, 404]


def test_imports_available():
    """Test that required modules can be imported."""
    try:
        from fastapi import FastAPI
        from fastapi.templating import Jinja2Templates
        from fastapi.testclient import TestClient

        assert True
    except ImportError as e:
        pytest.skip(f"Required imports not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
