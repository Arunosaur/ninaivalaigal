"""
Test SecurityBundle middleware functionality
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.security.middleware.security_bundle import (
    SecurityBundle,
    SecurityBundleMiddleware,
)
from server.security.redaction.detector_glue import detector_fn


@pytest.fixture
def app_with_bundle():
    """Create test FastAPI app with SecurityBundle"""
    app = FastAPI()

    @app.post("/test")
    async def test_endpoint(data: dict):
        return {"received": data}

    @app.post("/echo")
    async def echo_endpoint(request: dict):
        return {"received": request}

    @app.get("/secrets")
    async def secrets_endpoint():
        return {
            "openai_key": "sk-1234567890abcdef1234567890abcdef12345678",
            "message": "Hello world",
        }

    # Apply security bundle
    SecurityBundle.apply(app, detector_fn=detector_fn)

    return app


@pytest.fixture
def app_with_single_middleware():
    """Create test FastAPI app with SecurityBundleMiddleware"""
    app = FastAPI()

    @app.post("/test")
    async def test_endpoint(data: dict):
        return {"received": data}

    @app.get("/secrets")
    async def secrets_endpoint():
        return {"openai_key": "sk-1234567890abcdef1234567890abcdef12345678"}

    # Add single combined middleware
    app.add_middleware(SecurityBundleMiddleware, detector_fn=detector_fn)

    return app


@pytest.fixture
def client_bundle(app_with_bundle):
    """Create test client for bundle app"""
    return TestClient(app_with_bundle)


@pytest.fixture
def client_single(app_with_single_middleware):
    """Create test client for single middleware app"""
    return TestClient(app_with_single_middleware)


class TestSecurityBundle:
    def test_request_redaction_with_bundle(self, client_bundle):
        """Test request redaction works with SecurityBundle"""
        payload = {
            "message": "Here is my API key: sk-1234567890abcdef1234567890abcdef12345678",
            "user": "test@example.com",
        }

        response = client_bundle.post("/echo", json=payload)
        assert response.status_code == 200

        data = response.json()
        # The API key should be redacted
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in str(data)
        assert "REDACTED" in str(data)

    def test_response_redaction_with_bundle(self, client_bundle):
        """Test response redaction works with SecurityBundle"""
        response = client_bundle.get("/secrets")
        assert response.status_code == 200

        response_text = response.text
        # Secret should be redacted in response
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in response_text
        assert "REDACTED" in response_text

    def test_content_type_rejection(self, client_bundle):
        """Test content-type guard rejects binary content"""
        response = client_bundle.post(
            "/test",
            data=b"binary data with secret sk-1234567890abcdef1234567890abcdef12345678",
            headers={"Content-Type": "application/octet-stream"},
        )

        assert response.status_code == 415  # Unsupported Media Type

    def test_large_payload_rejection(self, client_bundle):
        """Test large payload rejection"""
        large_payload = {"data": "x" * (11 * 1024 * 1024)}  # 11MB > 10MB limit

        response = client_bundle.post("/test", json=large_payload)
        assert response.status_code == 413  # Payload Too Large

    def test_allowed_content_types_pass(self, client_bundle):
        """Test allowed content types pass through"""
        # JSON should be allowed
        response = client_bundle.post("/test", json={"message": "hello"})
        assert response.status_code == 200

        # Form data should be allowed
        response = client_bundle.post(
            "/test",
            data="message=hello",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert response.status_code == 200


class TestSecurityBundleMiddleware:
    def test_single_middleware_request_redaction(self, client_single):
        """Test request redaction with single middleware"""
        payload = {
            "secret": "sk-1234567890abcdef1234567890abcdef12345678",
            "normal": "data",
        }

        response = client_single.post("/test", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in str(data)

    def test_single_middleware_response_redaction(self, client_single):
        """Test response redaction with single middleware"""
        response = client_single.get("/secrets")
        assert response.status_code == 200

        response_text = response.text
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in response_text

    def test_single_middleware_content_type_guard(self, client_single):
        """Test content-type guard in single middleware"""
        response = client_single.post(
            "/test", data=b"binary data", headers={"Content-Type": "image/jpeg"}
        )

        assert response.status_code == 415


class TestAdvancedSecurityFeatures:
    def test_chunked_request_redaction(self, client_bundle):
        """Test redaction works with chunked requests"""
        # Simulate a large request that would be chunked
        large_text = "Normal text. " * 1000
        secret_text = f"{large_text} Secret: sk-1234567890abcdef1234567890abcdef12345678 {large_text}"

        payload = {"content": secret_text}
        response = client_bundle.post("/test", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in str(data)

    def test_boundary_split_secrets(self, client_bundle):
        """Test detection of secrets split across chunk boundaries"""
        # This would require more complex setup to truly test chunk boundaries
        # For now, test with a secret that could be split
        secret = "sk-1234567890abcdef1234567890abcdef12345678"
        part1 = secret[:24]  # "sk-1234567890abcdef12345"
        part2 = secret[24:]  # "67890abcdef12345678"

        payload = {"part1": part1, "part2": part2, "combined": secret}
        response = client_bundle.post("/test", json=payload)

        assert response.status_code == 200
        data = response.json()
        # The combined secret should be redacted
        assert secret not in str(data)

    def test_multiple_content_types_in_sequence(self, client_bundle):
        """Test handling multiple different content types"""
        # JSON request
        json_response = client_bundle.post("/test", json={"type": "json"})
        assert json_response.status_code == 200

        # Form data request
        form_response = client_bundle.post(
            "/test",
            data="type=form",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert form_response.status_code == 200

        # Binary request (should be rejected)
        binary_response = client_bundle.post(
            "/test", data=b"binary", headers={"Content-Type": "application/pdf"}
        )
        assert binary_response.status_code == 415

    def test_empty_and_malformed_requests(self, client_bundle):
        """Test handling of empty and malformed requests"""
        # Empty request
        empty_response = client_bundle.post("/test", json={})
        assert empty_response.status_code == 200

        # Request with no content-type
        no_type_response = client_bundle.post("/test", data="test")
        assert no_type_response.status_code == 200  # Should default to allowed

    def test_unicode_and_encoding_safety(self, client_bundle):
        """Test Unicode handling and encoding safety"""
        unicode_payload = {
            "message": "Hello 世界! Secret: sk-1234567890abcdef1234567890abcdef12345678",
            "emoji": "🔒🛡️🔐",
            "special": "àáâãäåæçèéêë",
        }

        response = client_bundle.post("/test", json=unicode_payload)
        assert response.status_code == 200

        data = response.json()
        # Secret should be redacted, Unicode should be preserved
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in str(data)
        assert "世界" in str(data)  # Unicode should be preserved
        assert "🔒" in str(data)  # Emojis should be preserved
