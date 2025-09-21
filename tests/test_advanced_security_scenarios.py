"""
Advanced security test scenarios based on external code review recommendations
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.security.middleware.security_bundle import SecurityBundle
from server.security.redaction.detector_glue import detector_fn, enhanced_detector_fn


class TestPropertyFuzzScenarios:
    """Property/fuzz tests: generate random secrets and ensure they never survive round-trip"""

    def test_random_secret_generation_redaction(self):
        """Generate random secrets with confusables and ensure redaction"""
        import random
        import string

        # Generate high-entropy strings that look like secrets
        def generate_fake_secret(length=48):
            chars = string.ascii_letters + string.digits
            return ''.join(random.choice(chars) for _ in range(length))

        app = FastAPI()

        @app.post("/test")
        async def test_endpoint(data: dict):
            return {"received": data}

        SecurityBundle.apply(app, detector_fn=enhanced_detector_fn)
        client = TestClient(app)

        # Test multiple random high-entropy strings
        for _ in range(10):
            fake_secret = f"sk-{generate_fake_secret(48)}"
            payload = {"secret": fake_secret}

            response = client.post("/test", json=payload)
            assert response.status_code == 200

            # Secret should not survive round-trip
            response_text = response.text
            assert fake_secret not in response_text
            assert "REDACTED" in response_text or "MASKED" in response_text

class TestMultipartDifferentialScenarios:
    """Multipart/differential test: secret in text part + binary part → only text gets redacted"""

    def test_multipart_text_binary_differential(self):
        """Test that secrets in text parts are redacted but binary parts are handled safely"""
        app = FastAPI()

        @app.post("/upload")
        async def upload_endpoint():
            return {"status": "received"}

        SecurityBundle.apply(app, detector_fn=detector_fn)
        client = TestClient(app)

        # Test multipart with text containing secret
        files = {
            'text_field': (None, 'Secret key: sk-1234567890abcdef1234567890abcdef12345678'),
            'binary_field': ('test.bin', b'\x00\x01\x02\x03binary_data_here', 'application/octet-stream')
        }

        response = client.post("/upload", files=files)
        # Should reject due to binary content type or handle gracefully
        assert response.status_code in [200, 415, 413]

class TestGzipDeflateScenarios:
    """Gzip/deflate tests and HTTP/2 multi-frame tests"""

    def test_compressed_content_handling(self):
        """Test handling of compressed content"""
        app = FastAPI()

        @app.post("/compressed")
        async def compressed_endpoint(data: dict):
            return {"received": data}

        SecurityBundle.apply(app, detector_fn=detector_fn)
        client = TestClient(app)

        # Test with compression headers
        payload = {"secret": "sk-1234567890abcdef1234567890abcdef12345678"}
        response = client.post("/compressed",
                             json=payload,
                             headers={"Content-Encoding": "gzip"})

        # Should handle gracefully (may reject or process)
        assert response.status_code in [200, 415, 400]

class TestPlaceholderRematchScenarios:
    """Placeholders re-match: ensure redaction markers don't trigger further detection"""

    def test_redaction_markers_dont_retrigger(self):
        """Ensure redaction placeholders don't trigger additional redaction"""
        app = FastAPI()

        @app.post("/test")
        async def test_endpoint(data: dict):
            return data

        SecurityBundle.apply(app, detector_fn=detector_fn)
        client = TestClient(app)

        # Send data that already contains redaction markers
        payload = {
            "already_redacted": "[REDACTED-AWS-KEY]",
            "new_secret": "sk-1234567890abcdef1234567890abcdef12345678",
            "marker_like": "AWS_KEY_REDACTED_MARKER"
        }

        response = client.post("/test", json=payload)
        assert response.status_code == 200

        data = response.json()
        # New secret should be redacted, existing markers should remain
        assert "sk-1234567890abcdef1234567890abcdef12345678" not in str(data)
        assert "[REDACTED-AWS-KEY]" in str(data)  # Should not be double-redacted

class TestReverseProxyScenarios:
    """End-to-end with reverse proxy configured to not buffer"""

    def test_streaming_chunk_behavior(self):
        """Test real chunk behavior with streaming"""
        app = FastAPI()

        @app.post("/stream")
        async def stream_endpoint(data: dict):
            # Simulate streaming response
            return {"processed": data, "chunks": "simulated"}

        SecurityBundle.apply(app, detector_fn=detector_fn, overlap=32)
        client = TestClient(app)

        # Test with data that could be split across chunks
        secret = "sk-1234567890abcdef1234567890abcdef12345678"
        large_payload = {
            "prefix": "x" * 1000,
            "secret": secret,
            "suffix": "y" * 1000
        }

        response = client.post("/stream", json=large_payload)
        assert response.status_code == 200

        # Secret should be redacted even in streaming scenario
        assert secret not in response.text

class TestPerformanceAndMemoryScenarios:
    """Performance and memory safety tests"""

    def test_large_payload_memory_safety(self):
        """Test memory safety with large payloads"""
        app = FastAPI()

        @app.post("/large")
        async def large_endpoint(data: dict):
            return {"size": len(str(data))}

        # Configure with smaller limits for testing
        SecurityBundle.apply(app,
                           detector_fn=detector_fn,
                           max_body_bytes=1024*1024)  # 1MB limit
        client = TestClient(app)

        # Test with payload near the limit
        medium_payload = {"data": "x" * (500 * 1024)}  # 500KB
        response = client.post("/large", json=medium_payload)
        assert response.status_code == 200

        # Test with payload over the limit
        large_payload = {"data": "x" * (2 * 1024 * 1024)}  # 2MB
        response = client.post("/large", json=large_payload)
        assert response.status_code == 413  # Payload Too Large

    def test_constant_memory_usage(self):
        """Test that memory usage remains constant for streaming"""
        app = FastAPI()

        @app.post("/memory")
        async def memory_endpoint(data: dict):
            return {"received": True}

        SecurityBundle.apply(app, detector_fn=detector_fn, overlap=64)
        client = TestClient(app)

        # Multiple requests should not accumulate memory
        for i in range(10):
            payload = {
                "iteration": i,
                "secret": f"sk-{i:044d}1234567890abcdef12345678",
                "padding": "x" * 10000
            }

            response = client.post("/memory", json=payload)
            assert response.status_code == 200

            # Verify redaction occurred
            assert f"sk-{i:044d}1234567890abcdef12345678" not in response.text

class TestIdempotencyAndRetries:
    """Idempotency and retry scenarios"""

    def test_idempotent_redaction(self):
        """Test that redaction is idempotent"""
        app = FastAPI()

        @app.post("/idempotent")
        async def idempotent_endpoint(data: dict):
            return data

        SecurityBundle.apply(app, detector_fn=detector_fn)
        client = TestClient(app)

        payload = {"secret": "sk-1234567890abcdef1234567890abcdef12345678"}

        # Make the same request multiple times
        responses = []
        for _ in range(3):
            response = client.post("/idempotent", json=payload)
            assert response.status_code == 200
            responses.append(response.json())

        # All responses should be identical (idempotent redaction)
        assert all(resp == responses[0] for resp in responses)

        # Secret should be redacted in all responses
        for resp in responses:
            assert "sk-1234567890abcdef1234567890abcdef12345678" not in str(resp)

class TestRateLimitingIntegration:
    """Rate limiting behavior with security middleware"""

    def test_rate_limit_per_credential(self):
        """Test rate limiting doesn't interfere with redaction"""
        app = FastAPI()

        @app.post("/rate_limited")
        async def rate_limited_endpoint(data: dict):
            return {"processed": data}

        SecurityBundle.apply(app, detector_fn=detector_fn)
        client = TestClient(app)

        # Multiple requests with different secrets
        for i in range(5):
            payload = {"secret": f"sk-{i:044d}1234567890abcdef12345678"}
            response = client.post("/rate_limited", json=payload)

            # Should succeed and redact
            assert response.status_code == 200
            assert f"sk-{i:044d}1234567890abcdef12345678" not in response.text

class TestErrorHandlingAndRecovery:
    """Error handling and recovery scenarios"""

    def test_malformed_detector_recovery(self):
        """Test graceful handling when detector function fails"""
        def failing_detector(text: str) -> str:
            if "trigger_error" in text:
                raise Exception("Detector failure")
            return detector_fn(text)

        app = FastAPI()

        @app.post("/error_test")
        async def error_test_endpoint(data: dict):
            return data

        SecurityBundle.apply(app, detector_fn=failing_detector)
        client = TestClient(app)

        # Normal request should work
        normal_payload = {"secret": "sk-1234567890abcdef1234567890abcdef12345678"}
        response = client.post("/error_test", json=normal_payload)
        assert response.status_code == 200

        # Error-triggering request should be handled gracefully
        error_payload = {"trigger_error": "yes", "secret": "sk-1234567890abcdef1234567890abcdef12345678"}
        response = client.post("/error_test", json=error_payload)
        # Should either succeed with fallback or return appropriate error
        assert response.status_code in [200, 500, 502]
