"""
Authentication Test Fixtures and Configuration

Provides shared fixtures and configuration for authentication tests.
"""

import pytest
import requests
from fastapi.testclient import TestClient
import os
import sys

# Add project root to Python path for imports
project_root = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Test Configuration
BASE_URL = "http://localhost:13370"
TEST_TIMEOUT = 5


@pytest.fixture
def api_base_url():
    """Provide the base URL for API testing"""
    return BASE_URL


@pytest.fixture
def test_headers():
    """Provide basic test headers"""
    return {"Content-Type": "application/json", "Accept": "application/json"}


@pytest.fixture
def auth_headers():
    """Provide headers with test authorization token"""
    return {
        "Authorization": "Bearer test_token_placeholder",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@pytest.fixture
def admin_headers():
    """Provide headers with admin authorization token"""
    return {
        "Authorization": "Bearer admin_token_placeholder",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@pytest.fixture
def readonly_headers():
    """Provide headers with read-only authorization token"""
    return {
        "Authorization": "Bearer readonly_token_placeholder",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@pytest.fixture
def test_user_data():
    """Provide test user data for signup/login tests"""
    return {
        "email": "testuser@spec052.com",
        "password": "StrongTestPass123!",
        "full_name": "SPEC-052 Test User",
    }


@pytest.fixture
def test_org_data():
    """Provide test organization data for organization signup tests"""
    return {
        "email": "orgadmin@spec052.com",
        "password": "StrongOrgPass123!",
        "full_name": "SPEC-052 Org Admin",
        "organization_name": "SPEC-052 Test Organization",
    }


@pytest.fixture
def invalid_credentials():
    """Provide invalid credentials for negative testing"""
    return {"email": "invalid@example.com", "password": "WrongPassword123!"}


@pytest.fixture
def malicious_payloads():
    """Provide malicious payloads for security testing"""
    return {
        "sql_injection": {
            "email": "admin'; DROP TABLE users; --",
            "password": "password",
        },
        "xss_payload": {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "full_name": "<script>alert('xss')</script>",
            "organization_name": "<img src=x onerror=alert('xss')>",
        },
        "oversized_data": {
            "email": "test@example.com",
            "password": "StrongPass123!",
            "full_name": "A" * 10000,  # 10KB name
            "bio": "B" * 100000,  # 100KB bio
        },
    }


@pytest.fixture
def api_client():
    """Provide a simple API client for making requests"""

    class APIClient:
        def __init__(self, base_url=BASE_URL):
            self.base_url = base_url
            self.timeout = TEST_TIMEOUT

        def get(self, endpoint, headers=None, params=None):
            return requests.get(
                f"{self.base_url}{endpoint}",
                headers=headers,
                params=params,
                timeout=self.timeout,
            )

        def post(self, endpoint, json=None, data=None, headers=None):
            return requests.post(
                f"{self.base_url}{endpoint}",
                json=json,
                data=data,
                headers=headers,
                timeout=self.timeout,
            )

        def put(self, endpoint, json=None, headers=None):
            return requests.put(
                f"{self.base_url}{endpoint}",
                json=json,
                headers=headers,
                timeout=self.timeout,
            )

        def delete(self, endpoint, headers=None):
            return requests.delete(
                f"{self.base_url}{endpoint}", headers=headers, timeout=self.timeout
            )

    return APIClient()


@pytest.fixture
def check_api_availability():
    """Check if API is available before running tests"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


@pytest.fixture(autouse=True)
def skip_if_api_unavailable(check_api_availability):
    """Automatically skip tests if API is not available"""
    if not check_api_availability:
        pytest.skip("API not available - run 'make stack-up' first")


# Test data generators
def generate_test_email(prefix="test"):
    """Generate unique test email addresses"""
    import time

    timestamp = int(time.time())
    return f"{prefix}_{timestamp}@spec052.com"


def generate_strong_password():
    """Generate a strong test password"""
    import random
    import string

    # Ensure password meets strength requirements
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(random.choice(chars) for _ in range(12))

    # Ensure it has required character types
    return f"Test{password}123!"


# Utility functions for tests
def is_valid_jwt_format(token):
    """Check if token has valid JWT format (3 parts separated by dots)"""
    if not token or not isinstance(token, str):
        return False

    parts = token.split(".")
    return len(parts) == 3


def extract_error_message(response):
    """Extract error message from API response"""
    try:
        if response.headers.get("content-type", "").startswith("application/json"):
            data = response.json()
            return data.get(
                "detail", data.get("message", data.get("error", "Unknown error"))
            )
        else:
            return response.text
    except:
        return f"HTTP {response.status_code}"


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "auth: mark test as authentication-related")
    config.addinivalue_line("markers", "security: mark test as security-related")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names"""
    for item in items:
        # Add markers based on test file names
        if "test_negative_cases" in item.nodeid:
            item.add_marker(pytest.mark.security)
        if "test_rate_limiting" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        if any(
            word in item.nodeid for word in ["test_signup", "test_login", "test_token"]
        ):
            item.add_marker(pytest.mark.auth)


# Custom assertions
def assert_valid_token_response(response):
    """Assert that response contains a valid token"""
    assert response.status_code in [
        200,
        201,
    ], f"Token response failed: {response.status_code}"

    data = response.json()
    assert "access_token" in data or "token" in data, "Response missing access token"

    token = data.get("access_token") or data.get("token")
    assert is_valid_jwt_format(token), f"Invalid JWT format: {token}"


def assert_error_response(response, expected_status_codes):
    """Assert that response is an error with expected status code"""
    if not isinstance(expected_status_codes, (list, tuple)):
        expected_status_codes = [expected_status_codes]

    assert (
        response.status_code in expected_status_codes
    ), f"Expected status {expected_status_codes}, got {response.status_code}: {extract_error_message(response)}"
