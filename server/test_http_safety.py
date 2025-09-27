"""
HTTP Safety Compliance Test Suite
Guards against Content-Length mismatches and other HTTP protocol violations
"""

import json

import pytest
from fastapi.testclient import TestClient
from http_safety_spec import HTTPSafetySpec
from main import app

client = TestClient(app)


class TestHTTPSafetyCompliance:
    """Test suite to ensure HTTP safety compliance"""

    def test_content_length_matches(self):
        """Test that Content-Length header matches actual response body"""
        response = client.get("/health")

        if "content-length" in response.headers:
            declared_length = int(response.headers["content-length"])
            actual_length = len(response.content)

            assert declared_length == actual_length, (
                f"Content-Length mismatch! Declared: {declared_length}, "
                f"Actual: {actual_length}, Response: {response.text}"
            )

    def test_json_responses_are_valid(self):
        """Test that all JSON responses are properly serialized"""
        response = client.get("/health")

        if response.headers.get("content-type", "").startswith("application/json"):
            try:
                json.loads(response.text)
            except json.JSONDecodeError as e:
                pytest.fail(f"Invalid JSON response: {e}, Response: {response.text}")

    def test_auth_endpoint_content_length(self):
        """Test that auth endpoints have correct Content-Length"""
        response = client.post(
            "/auth/login", json={"email": "test@ninaivalaigal.com", "password": "test"}
        )

        # Should not hang and should have correct Content-Length
        if "content-length" in response.headers:
            declared_length = int(response.headers["content-length"])
            actual_length = len(response.content)

            assert declared_length == actual_length, (
                f"Auth endpoint Content-Length mismatch! "
                f"Declared: {declared_length}, Actual: {actual_length}"
            )

    def test_no_truncated_responses(self):
        """Test that responses are not truncated"""
        response = client.get("/health")

        # Response should be complete
        assert response.status_code in [
            200,
            400,
            401,
            403,
            404,
            500,
        ], f"Unexpected status code: {response.status_code}"

        # Should have content
        assert len(response.content) > 0, "Response body is empty"

    def test_safe_response_creation(self):
        """Test the HTTPSafetySpec.create_safe_response method"""
        test_content = {"message": "test", "data": {"key": "value"}, "status": "ok"}

        response = HTTPSafetySpec.create_safe_response(test_content)

        # Should have correct Content-Length
        body_length = len(response.body)
        declared_length = int(response.headers["content-length"])

        assert body_length == declared_length, (
            f"Safe response Content-Length mismatch! "
            f"Body: {body_length}, Header: {declared_length}"
        )

    def test_diagnostics_endpoint(self):
        """Test that diagnostics endpoint works"""
        response = client.get("/diagnostics/http-safety")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_multiple_endpoints_for_content_length(self):
        """Test multiple endpoints to catch any Content-Length issues"""
        endpoints_to_test = [
            ("/health", "GET"),
            ("/health-simple", "GET"),
            ("/diagnostics/http-safety", "GET"),
        ]

        for endpoint, method in endpoints_to_test:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})

            # Check Content-Length if present
            if "content-length" in response.headers:
                declared_length = int(response.headers["content-length"])
                actual_length = len(response.content)

                assert declared_length == actual_length, (
                    f"Content-Length mismatch in {endpoint}! "
                    f"Declared: {declared_length}, Actual: {actual_length}"
                )


def test_content_length_matches(client):
    """Standalone test function for Content-Length validation"""
    response = client.get("/health")
    body_len = len(response.content)
    content_len_header = int(response.headers.get("content-length", 0))

    assert (
        body_len == content_len_header
    ), f"Mismatch in Content-Length! Actual: {body_len}, Header: {content_len_header}"


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running HTTP Safety Compliance Tests...")

    try:
        # Test health endpoint
        response = client.get("/health")
        print(f"✅ Health endpoint: {response.status_code}")

        # Test Content-Length
        if "content-length" in response.headers:
            declared = int(response.headers["content-length"])
            actual = len(response.content)
            if declared == actual:
                print(f"✅ Content-Length matches: {actual} bytes")
            else:
                print(
                    f"❌ Content-Length mismatch: declared={declared}, actual={actual}"
                )

        # Test diagnostics
        response = client.get("/diagnostics/http-safety")
        print(f"✅ Diagnostics endpoint: {response.status_code}")

        print("🎉 HTTP Safety tests completed!")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
