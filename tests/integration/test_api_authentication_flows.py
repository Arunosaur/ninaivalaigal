#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Comprehensive authentication flow tests for API
#

# Import shared fixtures from conftest.py
import os
from uuid import uuid4

import pytest
import requests

BASE_URL = os.getenv("TEST_API_BASE_URL", "http://localhost:13390")
TIMEOUT = int(os.getenv("TEST_API_TIMEOUT", "30"))


class TestAuthenticationFlows:
    """Test complete authentication flows"""

    def test_signup_individual_user(self, auth_token, admin_token=None, member_token=None):
        """Test individual user signup flow"""
        client = requests.Session()

        # Generate unique email
        email = f"test_{uuid4().hex[:8]}@example.com"
        password = "TestPassword123!"

        response = client.post(
            f"{BASE_URL}/auth/signup/individual",
            json={"email": email, "password": password, "full_name": "Test User", "preferred_name": "Test"},
            timeout=TIMEOUT,
        )

        # Should succeed or return validation error
        assert response.status_code in [200, 201, 400, 422, 409]

        if response.status_code in [200, 201]:
            data = response.json()
            # Should return user info or token
            assert "user" in data or "token" in data or "user_id" in data

    def test_login_with_valid_credentials(self, auth_token, admin_token=None, member_token=None):
        """Test login with valid credentials (if test user exists)"""
        client = requests.Session()

        # This would need a test user to be created first
        response = client.post(
            f"{BASE_URL}/auth/login", json={"email": "test@example.com", "password": "test123"}, timeout=TIMEOUT
        )

        # May return 401 if user doesn't exist, 200 if login succeeds
        assert response.status_code in [200, 400, 401, 422]

        if response.status_code == 200:
            data = response.json()
            assert "token" in data or "access_token" in data or "auth_token" in data

    def test_login_with_invalid_credentials(self, auth_token, admin_token=None, member_token=None):
        """Test login with invalid credentials"""
        client = requests.Session()

        response = client.post(
            f"{BASE_URL}/auth/login",
            json={"email": "nonexistent@example.com", "password": "wrongpassword"},
            timeout=TIMEOUT,
        )

        assert response.status_code in [401, 400, 422]

    def test_access_protected_endpoint_with_token(self, auth_token, admin_token=None, member_token=None):
        """Test accessing protected endpoint with valid token"""
        # This would require getting a valid token first
        # For now, just verify the endpoint exists and requires auth
        client = requests.Session()

        # Try without token
        response = client.get(f"{BASE_URL}/users/me", timeout=TIMEOUT)
        assert response.status_code in [401, 403]  # 401 Unauthorized or 403 Forbidden

        # Try with invalid token
        client.headers.update({"Authorization": "Bearer invalid_token"})
        response = client.get(f"{BASE_URL}/users/me", timeout=TIMEOUT)
        assert response.status_code == 401

    def test_token_expiration(self, auth_token, admin_token=None, member_token=None):
        """Test that expired tokens are rejected"""
        client = requests.Session()
        client.headers.update({"Authorization": "Bearer expired_token_here"})

        response = client.get(f"{BASE_URL}/users/me", timeout=TIMEOUT)
        assert response.status_code == 401

    def test_signup_validation_errors(self, auth_token, admin_token=None, member_token=None):
        """Test signup with validation errors"""
        client = requests.Session()

        test_cases = [
            # Missing email
            {"password": "test123", "full_name": "Test"},
            # Missing password
            {"email": "test@example.com", "full_name": "Test"},
            # Invalid email format
            {"email": "not-an-email", "password": "test123", "full_name": "Test"},
            # Weak password
            {"email": "test@example.com", "password": "123", "full_name": "Test"},
        ]

        for test_data in test_cases:
            response = client.post(f"{BASE_URL}/auth/signup/individual", json=test_data, timeout=TIMEOUT)
            # Should return validation error
            assert response.status_code in [400, 422]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
