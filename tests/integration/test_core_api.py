# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC

import uuid

import pytest
import requests

from tests.config import CORE_API_BASE_URL


@pytest.mark.integration
class TestAuthFlow:
    """Test complete authentication flow"""

    def test_signup_creates_user(self):
        """User can sign up with valid data"""
        email = f"newuser-{uuid.uuid4().hex[:8]}@test.com"
        response = requests.post(
            f"{CORE_API_BASE_URL}/auth/signup",
            json={"email": email, "password": "SecurePass123!", "name": "New User"},  # pragma: allowlist secret
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["user"]["email"] == email
        assert data["user"]["name"] == "New User"
        assert "id" in data["user"]

    def test_signup_rejects_duplicate_email(self):
        """Cannot sign up with existing email"""
        email = f"duplicate-{uuid.uuid4().hex[:8]}@test.com"
        # First signup
        requests.post(
            f"{CORE_API_BASE_URL}/auth/signup",
            json={"email": email, "password": "Pass123!", "name": "First User"},  # pragma: allowlist secret
        )

        # Duplicate signup
        response = requests.post(
            f"{CORE_API_BASE_URL}/auth/signup",
            json={"email": email, "password": "Pass123!", "name": "Second User"},  # pragma: allowlist secret
        )

        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_login_returns_token(self):
        """User can login with correct credentials"""
        email = f"login-{uuid.uuid4().hex[:8]}@test.com"
        # First signup
        requests.post(
            f"{CORE_API_BASE_URL}/auth/signup",
            json={"email": email, "password": "LoginPass123!", "name": "Login User"},  # pragma: allowlist secret
        )

        # Login
        response = requests.post(
            f"{CORE_API_BASE_URL}/auth/login",
            json={"email": email, "password": "LoginPass123!"},  # pragma: allowlist secret
        )

        assert response.status_code == 200
        data = response.json()
        assert "jwt_token" in data
        assert data["token_type"] == "Bearer"

    def test_login_rejects_wrong_password(self):
        """Login fails with incorrect password"""
        # First signup
        requests.post(
            f"{CORE_API_BASE_URL}/auth/signup",
            json={
                "email": "wrongpass@test.com",
                "password": "CorrectPass123!",  # pragma: allowlist secret
                "name": "User",
            },
        )

        # Login with wrong password
        response = requests.post(
            f"{CORE_API_BASE_URL}/auth/login",
            json={"email": "wrongpass@test.com", "password": "WrongPass123!"},  # pragma: allowlist secret
        )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()


@pytest.mark.integration
class TestUserManagement:
    """Test user management endpoints"""

    @pytest.fixture
    def auth_token(self):
        """Get auth token for authenticated requests"""
        # Signup
        requests.post(
            f"{CORE_API_BASE_URL}/auth/signup",
            json={
                "email": "authuser@test.com",
                "password": "AuthPass123!",  # pragma: allowlist secret
                "name": "Auth User",
            },
        )

        # Login
        response = requests.post(
            f"{CORE_API_BASE_URL}/auth/login",
            json={"email": "authuser@test.com", "password": "AuthPass123!"},  # pragma: allowlist secret
        )

        return response.json()["jwt_token"]

    @pytest.mark.skip(reason="User profile endpoints not yet implemented")
    def test_get_current_user(self, auth_token):
        """Get current user profile"""
        response = requests.get(f"{CORE_API_BASE_URL}/users/me", headers={"Authorization": f"Bearer {auth_token}"})

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "authuser@test.com"
        assert data["name"] == "Auth User"

    @pytest.mark.skip(reason="User profile endpoints not yet implemented")
    def test_update_user_profile(self, auth_token):
        """Update user profile"""
        response = requests.patch(
            f"{CORE_API_BASE_URL}/users/me",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"name": "Updated Name"},
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Updated Name"


@pytest.mark.integration
class TestTeamManagement:
    """Test team management endpoints"""

    @pytest.fixture
    def auth_token(self):
        """Get auth token"""
        requests.post(
            f"{CORE_API_BASE_URL}/auth/signup",
            json={
                "email": "teamuser@test.com",
                "password": "TeamPass123!",  # pragma: allowlist secret
                "name": "Team User",
            },
        )

        response = requests.post(
            f"{CORE_API_BASE_URL}/auth/login",
            json={"email": "teamuser@test.com", "password": "TeamPass123!"},  # pragma: allowlist secret
        )

        return response.json()["jwt_token"]

    @pytest.mark.skip(reason="Team management endpoints not yet implemented")
    def test_create_team(self, auth_token):
        """Create a new team"""
        response = requests.post(
            f"{CORE_API_BASE_URL}/teams", headers={"Authorization": f"Bearer {auth_token}"}, json={"name": "My Team"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My Team"
        assert "id" in data

    @pytest.mark.skip(reason="Team management endpoints not yet implemented")
    def test_list_teams(self, auth_token):
        """List user's teams"""
        # Create team
        requests.post(
            f"{CORE_API_BASE_URL}/teams", headers={"Authorization": f"Bearer {auth_token}"}, json={"name": "Team 1"}
        )

        # List teams
        response = requests.get(f"{CORE_API_BASE_URL}/teams", headers={"Authorization": f"Bearer {auth_token}"})

        assert response.status_code == 200
        teams = response.json()
        assert len(teams) >= 1
        assert any(t["name"] == "Team 1" for t in teams)
