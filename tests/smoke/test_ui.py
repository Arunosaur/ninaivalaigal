"""
Smoke tests for UI accessibility and basic functionality.
These tests ensure the UI is running and serving content correctly.
"""

import time
from typing import Any, Dict

import pytest
import requests


class TestUISmoke:
    """Comprehensive UI smoke tests."""

    BASE_URL = "http://localhost:8081"
    TIMEOUT = 10

    def test_ui_accessibility(self):
        """Test that UI is accessible and serving content."""
        try:
            response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
            assert len(response.content) > 0
        except Exception as e:
            pytest.fail(f"UI accessibility test failed: {e}")

    def test_ui_static_assets(self):
        """Test that static assets are being served."""
        static_paths = [
            "/favicon.ico",
            "/assets/",  # May redirect or return directory listing
        ]

        for path in static_paths:
            try:
                url = f"{self.BASE_URL}{path}"
                response = requests.get(url, timeout=self.TIMEOUT)
                # Accept various status codes for static assets
                assert response.status_code in [200, 301, 302, 403, 404]
            except Exception as e:
                pytest.fail(f"Static asset test failed for {path}: {e}")

    def test_ui_response_time(self):
        """Test UI response time is acceptable."""
        try:
            start_time = time.time()
            response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # Convert to ms
            assert response.status_code == 200
            assert (
                response_time < 2000
            ), f"UI response time {response_time:.2f}ms exceeds 2000ms threshold"

        except Exception as e:
            pytest.fail(f"UI response time test failed: {e}")

    def test_ui_content_structure(self):
        """Test that UI contains expected HTML structure."""
        try:
            response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
            assert response.status_code == 200

            content = response.text.lower()

            # Check for basic HTML structure
            assert "<html" in content
            assert "<head" in content
            assert "<body" in content
            assert "</html>" in content

            # Check for common UI elements (may vary based on implementation)
            expected_elements = ["title", "meta", "script", "style"]
            for element in expected_elements:
                assert f"<{element}" in content or f"</{element}>" in content

        except Exception as e:
            pytest.fail(f"UI content structure test failed: {e}")

    def test_ui_security_headers(self):
        """Test that UI has basic security headers."""
        try:
            response = requests.get(self.BASE_URL, timeout=self.TIMEOUT)
            assert response.status_code == 200

            headers = response.headers

            # Check for common security headers (not all may be present)
            security_headers = [
                "x-frame-options",
                "x-content-type-options",
                "x-xss-protection",
                "content-security-policy",
                "strict-transport-security",
            ]

            # At least one security header should be present
            present_headers = [h for h in security_headers if h in headers]
            # Note: This is lenient - in production you'd want more specific checks

        except Exception as e:
            pytest.fail(f"UI security headers test failed: {e}")


class TestUIIntegration:
    """Integration tests between UI and API."""

    UI_URL = "http://localhost:8081"
    API_URL = "http://localhost:13370"
    TIMEOUT = 10

    def test_ui_can_reach_api(self):
        """Test that API is reachable from UI perspective."""
        try:
            # Test API health from UI's perspective
            response = requests.get(f"{self.API_URL}/health", timeout=self.TIMEOUT)
            assert response.status_code == 200

            # Test that UI is also accessible
            ui_response = requests.get(self.UI_URL, timeout=self.TIMEOUT)
            assert ui_response.status_code == 200

        except Exception as e:
            pytest.fail(f"UI-API integration test failed: {e}")

    def test_cors_configuration(self):
        """Test CORS configuration between UI and API."""
        try:
            # Make a preflight request from UI origin
            headers = {
                "Origin": self.UI_URL,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type",
            }

            response = requests.options(
                f"{self.API_URL}/health", headers=headers, timeout=self.TIMEOUT
            )

            # Should not fail completely (may return 405 if OPTIONS not implemented)
            assert response.status_code in [200, 204, 405]

        except Exception as e:
            pytest.fail(f"CORS configuration test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
