#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Test API Versioning Middleware

Verifies that SPEC-088 versioning middleware is working correctly.
"""

import pytest
from fastapi.testclient import TestClient


def test_unversioned_endpoint_works(client: TestClient):
    """Test that unversioned endpoints still work."""
    response = client.get("/version-test")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Unversioned endpoint working"
    assert data["version"] == "unversioned"


def test_v1_endpoint_works(client: TestClient):
    """Test that v1 endpoints work and include version headers."""
    response = client.get("/api/v1/test")
    assert response.status_code == 200

    # Check response data
    data = response.json()
    assert data["message"] == "V1 endpoint working"
    assert data["version"] == "v1"
    assert data["middleware_working"] is True

    # Check version headers
    assert "X-API-Version" in response.headers
    assert response.headers["X-API-Version"] == "v1"


def test_v1_headers_endpoint(client: TestClient):
    """Test version headers are properly set."""
    response = client.get("/api/v1/headers")
    assert response.status_code == 200

    data = response.json()
    assert data["api_version"] == "v1"
    assert "headers" in data


def test_unsupported_version_returns_404(client: TestClient):
    """Test that unsupported versions return 404."""
    response = client.get("/api/v99/test")
    assert response.status_code == 404

    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VERSION_NOT_FOUND"
    assert "v99" in data["error"]["message"]
    assert "supported_versions" in data["error"]["details"]


def test_health_endpoint_unversioned(client: TestClient):
    """Test that health endpoints remain unversioned."""
    response = client.get("/health")
    assert response.status_code == 200
    # Health endpoint should not have version headers
    # (middleware skips non-/api/ paths)


def test_metrics_endpoint_unversioned(client: TestClient):
    """Test that metrics endpoints remain unversioned."""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Metrics endpoint should not have version headers


if __name__ == "__main__":
    """
    Run tests manually.

    Usage:
        python -m pytest tests/test_api_versioning_middleware.py -v
    """
    pytest.main([__file__, "-v"])
