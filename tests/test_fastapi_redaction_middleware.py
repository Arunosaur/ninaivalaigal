"""
Test FastAPI redaction middleware functionality
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.security.middleware.fastapi_redaction import RedactionASGIMiddleware
from server.security.redaction.detector_glue import detector_fn


@pytest.fixture
def app():
    """Create test FastAPI app with redaction middleware"""
    app = FastAPI()

    @app.post("/test")
    async def test_endpoint(data: dict):
        return {"received": data}

    @app.post("/echo")
    async def echo_endpoint(request: dict):
        return {"received": request}

    # Add redaction middleware
    app.add_middleware(RedactionASGIMiddleware, detector_fn=detector_fn, overlap=64)

    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return TestClient(app)


class TestFastAPIRedactionMiddleware:
    def test_basic_secret_redaction(self, client):
        """Test basic secret redaction in request body"""
        payload = {
            "message": "Here is my API key: sk-1234567890abcdef1234567890abcdef12345678",
            "user": "test@example.com",
        }

        response = client.post("/echo", json=payload)
        assert response.status_code == 200

        data = response.json()
        # The API key should be redacted
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in str(data)
        assert "[REDACTED" in str(data) or "REDACTED" in str(data)

    def test_aws_key_redaction(self, client):
        """Test AWS access key redaction"""
        payload = {
            "config": {"aws_access_key": "AKIAIOSFODNN7EXAMPLE", "region": "us-east-1"}
        }

        response = client.post("/test", json=payload)
        assert response.status_code == 200

        data = response.json()
        # AWS key should be redacted
        assert "AKIAIOSFODNN7EXAMPLE" not in str(data)

    def test_github_token_redaction(self, client):
        """Test GitHub token redaction"""
        payload = {
            "github_token": "ghp_1234567890abcdef1234567890abcdef12345678",
            "repo": "test/repo",
        }

        response = client.post("/echo", json=payload)
        assert response.status_code == 200

        data = response.json()
        # GitHub token should be redacted
        assert "ghp_1234567890abcdef1234567890abcdef12345678" not in str(data)

    def test_multiple_secrets_redaction(self, client):
        """Test redaction of multiple different secret types"""
        payload = {
            "openai": "sk-1234567890abcdef1234567890abcdef12345678",
            "aws": "AKIAIOSFODNN7EXAMPLE",
            "github": "ghp_1234567890abcdef1234567890abcdef12345678",
            "email": "user@example.com",
            "phone": "555-123-4567",
        }

        response = client.post("/test", json=payload)
        assert response.status_code == 200

        data = response.json()
        response_str = str(data)

        # All secrets should be redacted
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in response_str
        assert "AKIAIOSFODNN7EXAMPLE" not in response_str
        assert "ghp_1234567890abcdef1234567890abcdef12345678" not in response_str
        assert "555-123-4567" not in response_str

    def test_no_secrets_passthrough(self, client):
        """Test that normal data passes through unchanged"""
        payload = {
            "message": "Hello world",
            "count": 42,
            "active": True,
            "tags": ["test", "demo"],
        }

        response = client.post("/echo", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Normal data should pass through
        assert data["received"]["message"] == "Hello world"
        assert data["received"]["count"] == 42
        assert data["received"]["active"] is True

    def test_large_payload_redaction(self, client):
        """Test redaction with large payloads"""
        large_text = "Normal text. " * 1000
        secret_text = f"{large_text} Secret: sk-1234567890abcdef1234567890abcdef12345678 {large_text}"

        payload = {"content": secret_text}

        response = client.post("/test", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Secret should be redacted even in large payload
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in str(data)

    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON"""
        # Send raw text instead of JSON
        response = client.post(
            "/test",
            data="This contains a secret: sk-1234567890abcdef1234567890abcdef12345678",
            headers={"Content-Type": "text/plain"},
        )

        # Should handle gracefully (may return error but shouldn't crash)
        assert response.status_code in [200, 422, 400]  # Various valid responses

    def test_empty_payload(self, client):
        """Test handling of empty payloads"""
        response = client.post("/test", json={})
        assert response.status_code == 200

        data = response.json()
        assert data["received"] == {}

    def test_nested_secret_redaction(self, client):
        """Test redaction in deeply nested structures"""
        payload = {
            "level1": {
                "level2": {
                    "level3": {
                        "secret": "sk-1234567890abcdef1234567890abcdef12345678",
                        "normal": "data",
                    }
                }
            }
        }

        response = client.post("/echo", json=payload)
        assert response.status_code == 200

        data = response.json()
        # Nested secret should be redacted
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in str(data)
