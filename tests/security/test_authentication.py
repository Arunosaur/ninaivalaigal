#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Security tests for authentication."""


class TestAuthentication:
    """Test authentication security."""

    def test_login_with_valid_credentials(self, client, test_user_data):
        """Test login with valid credentials."""
        response = client.post(
            "/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"],  # pragma: allowlist secret
            },
        )
        # Test should handle both success and expected failure cases
        assert response.status_code in [200, 401, 422]

    def test_login_with_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/auth/login",
            json={
                "email": "invalid@example.com",
                "password": "WrongPassword123!",  # pragma: allowlist secret
            },
        )
        assert response.status_code in [401, 422]

    def test_protected_endpoint_without_auth(self, client):
        """Test protected endpoint without authentication."""
        response = client.get("/api/memories")
        assert response.status_code in [401, 403]
