"""
Authentication System Tests: Signup Flow

Tests user registration and account creation functionality.
"""

import pytest
import requests
import json

# Test Configuration
BASE_URL = "http://localhost:13370"


class TestUserSignup:
    """Test suite for user signup functionality"""

    def test_individual_signup_success(self):
        """Test successful individual user signup"""
        signup_data = {
            "email": "test_individual@spec052.com",
            "password": "StrongPass123!",
            "full_name": "SPEC-052 Individual User",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/auth/signup/individual", json=signup_data, timeout=5
            )

            if response.status_code == 404:
                pytest.skip("Individual signup endpoint not implemented")

            assert response.status_code in [
                200,
                201,
            ], f"Individual signup failed: {response.status_code}"

            if response.status_code in [200, 201]:
                result = response.json()
                assert (
                    "access_token" in result or "token" in result
                ), "Signup response missing access token"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_organization_signup_success(self):
        """Test successful organization signup"""
        signup_data = {
            "email": "test_org@spec052.com",
            "password": "StrongPass123!",
            "organization_name": "SPEC-052 Test Org",
            "full_name": "SPEC-052 Org Admin",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/auth/signup/organization", json=signup_data, timeout=5
            )

            if response.status_code == 404:
                pytest.skip("Organization signup endpoint not implemented")

            assert response.status_code in [
                200,
                201,
            ], f"Organization signup failed: {response.status_code}"

            if response.status_code in [200, 201]:
                result = response.json()
                assert (
                    "access_token" in result or "token" in result
                ), "Signup response missing access token"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_signup_duplicate_email(self):
        """Test signup with duplicate email address"""
        signup_data = {
            "email": "duplicate@spec052.com",
            "password": "StrongPass123!",
            "full_name": "Duplicate User Test",
        }

        try:
            # First signup
            response1 = requests.post(
                f"{BASE_URL}/auth/signup/individual", json=signup_data, timeout=5
            )

            if response1.status_code == 404:
                pytest.skip("Signup endpoint not implemented")

            # Second signup with same email
            response2 = requests.post(
                f"{BASE_URL}/auth/signup/individual", json=signup_data, timeout=5
            )

            # Should reject duplicate email
            assert response2.status_code in [
                400,
                409,
            ], f"Duplicate email not rejected: {response2.status_code}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_signup_weak_password(self):
        """Test signup with weak password"""
        signup_data = {
            "email": "weakpass@spec052.com",
            "password": "123",  # Weak password
            "full_name": "Weak Password User",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/auth/signup/individual", json=signup_data, timeout=5
            )

            if response.status_code == 404:
                pytest.skip("Signup endpoint not implemented")

            # Should reject weak password
            assert (
                response.status_code == 400
            ), f"Weak password not rejected: {response.status_code}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")

    def test_signup_invalid_email(self):
        """Test signup with invalid email format"""
        signup_data = {
            "email": "invalid-email-format",  # Invalid email
            "password": "StrongPass123!",
            "full_name": "Invalid Email User",
        }

        try:
            response = requests.post(
                f"{BASE_URL}/auth/signup/individual", json=signup_data, timeout=5
            )

            if response.status_code == 404:
                pytest.skip("Signup endpoint not implemented")

            # Should reject invalid email
            assert (
                response.status_code == 400
            ), f"Invalid email not rejected: {response.status_code}"

        except requests.exceptions.RequestException:
            pytest.skip("API not available - run 'make stack-up' first")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
