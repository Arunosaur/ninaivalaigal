"""
Integration tests for security middleware
"""


import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from server.rbac.permissions import Role
from server.security.audit import SecurityEventType, security_alert_manager
from server.security.middleware.rate_limiting import (
    EnhancedRateLimiter,
    RateLimitMiddleware,
)
from server.security.middleware.redaction_middleware import RedactionMiddleware
from server.security.middleware.security_headers import (
    DevelopmentSecurityHeaders,
    SecurityHeadersMiddleware,
)
from server.security_integration import SecurityManager, configure_security


class TestSecurityHeadersMiddleware:
    """Test security headers middleware"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = FastAPI()
        self.app.add_middleware(SecurityHeadersMiddleware)

        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        self.client = TestClient(self.app)

    def test_security_headers_added(self):
        """Test that security headers are added to responses"""
        response = self.client.get("/test")

        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"

        assert "Strict-Transport-Security" in response.headers
        assert "max-age=" in response.headers["Strict-Transport-Security"]

        assert "Content-Security-Policy" in response.headers

    def test_development_headers(self):
        """Test development mode headers"""
        dev_app = FastAPI()
        dev_app.add_middleware(DevelopmentSecurityHeaders)

        @dev_app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        dev_client = TestClient(dev_app)
        response = dev_client.get("/test")

        # Development mode should have relaxed CSP
        csp = response.headers.get("Content-Security-Policy", "")
        assert "'unsafe-inline'" in csp or "'unsafe-eval'" in csp


class TestRedactionMiddleware:
    """Test redaction middleware"""

    def setup_method(self):
        """Set up test fixtures"""
        self.app = FastAPI()

        # Mock RBAC context
        async def mock_rbac_middleware(request: Request, call_next):
            from server.rbac_middleware import RBACContext
            request.state.rbac_context = RBACContext(
                user_id=123,
                user_role=Role.MEMBER,
                organization_id=1,
                team_id=1,
                permissions=set()
            )
            return await call_next(request)

        self.app.middleware("http")(mock_rbac_middleware)
        self.app.add_middleware(RedactionMiddleware, enabled=True)

        @self.app.post("/test")
        async def test_endpoint(data: dict):
            return {"received": data, "secret": "sk-test123"}

        self.client = TestClient(self.app)

    def test_request_redaction(self):
        """Test redaction of request data"""
        test_data = {
            "message": "Hello",
            "api_key": "sk-1234567890abcdef1234567890abcdef12345678",
            "email": "user@example.com"
        }

        response = self.client.post("/test", json=test_data)

        # Should get successful response
        assert response.status_code == 200

        # Response should not contain original secrets
        response_text = response.text
        assert "sk-1234567890abcdef" not in response_text

    def test_response_redaction(self):
        """Test redaction of response data"""
        response = self.client.post("/test", json={"message": "test"})

        assert response.status_code == 200
        response_data = response.json()

        # Response should have redacted the secret
        assert "sk-test123" not in str(response_data)

    def test_middleware_disabled(self):
        """Test middleware when disabled"""
        disabled_app = FastAPI()
        disabled_app.add_middleware(RedactionMiddleware, enabled=False)

        @disabled_app.post("/test")
        async def test_endpoint(data: dict):
            return {"received": data}

        disabled_client = TestClient(disabled_app)

        test_data = {"api_key": "sk-test123"}
        response = disabled_client.post("/test", json=test_data)

        # When disabled, should pass through without redaction
        assert response.status_code == 200


class TestRateLimitingMiddleware:
    """Test rate limiting middleware"""

    def setup_method(self):
        """Set up test fixtures"""
        self.rate_limiter = EnhancedRateLimiter()
        self.app = FastAPI()

        # Mock RBAC context
        async def mock_rbac_middleware(request: Request, call_next):
            from server.rbac_middleware import RBACContext
            request.state.rbac_context = RBACContext(
                user_id=123,
                user_role=Role.MEMBER,
                organization_id=1,
                team_id=1,
                permissions=set()
            )
            return await call_next(request)

        self.app.middleware("http")(mock_rbac_middleware)
        self.app.add_middleware(RateLimitMiddleware, rate_limiter=self.rate_limiter)

        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "test"}

        self.client = TestClient(self.app)

    def test_rate_limiting_allows_normal_requests(self):
        """Test that normal requests are allowed"""
        response = self.client.get("/test")
        assert response.status_code == 200

    def test_rate_limiting_blocks_excessive_requests(self):
        """Test that excessive requests are blocked"""
        # Make many requests quickly
        responses = []
        for i in range(150):  # Exceed typical rate limit
            response = self.client.get("/test")
            responses.append(response)

        # Should have some 429 responses
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes, "Should block excessive requests with 429"

    def test_rate_limiting_headers(self):
        """Test that rate limiting headers are added"""
        response = self.client.get("/test")

        # Should include rate limiting headers
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers


class TestSecurityIntegration:
    """Test complete security integration"""

    def setup_method(self):
        """Set up test fixtures"""
        self.security_manager = SecurityManager()
        self.app = FastAPI()

        # Configure security
        configure_security(self.app, development_mode=True)

        @self.app.post("/memory")
        async def store_memory(data: dict):
            return {"stored": data}

        @self.app.get("/admin/action")
        async def admin_action():
            return {"action": "completed"}

        self.client = TestClient(self.app)

    def test_security_status(self):
        """Test security status reporting"""
        status = self.security_manager.get_security_status()

        assert "security_enabled" in status
        assert "redaction_enabled" in status
        assert "rate_limiting_enabled" in status
        assert "security_headers_enabled" in status

    @pytest.mark.asyncio
    async def test_redact_text_function(self):
        """Test text redaction function"""
        from server.security.redaction.config import ContextSensitivity
        from server.security_integration import redact_text

        text = "API key: sk-1234567890abcdef1234567890abcdef12345678"
        redacted = await redact_text(text, ContextSensitivity.INTERNAL)

        assert "sk-1234567890abcdef" not in redacted
        assert "[REDACTED" in redacted or "***" in redacted

    @pytest.mark.asyncio
    async def test_cross_org_access_check(self):
        """Test cross-organization access checking"""
        from server.rbac.permissions import Role
        from server.rbac_middleware import RBACContext
        from server.security_integration import check_cross_org_access

        # Create RBAC context
        rbac_context = RBACContext(
            user_id=123,
            user_role=Role.MEMBER,
            organization_id=1,
            team_id=1,
            permissions=set()
        )

        # Test same org access (should be allowed)
        allowed = await check_cross_org_access(rbac_context, 1)
        assert allowed == True

        # Test different org access (should be blocked)
        blocked = await check_cross_org_access(rbac_context, 2)
        assert blocked == False


class TestSecurityAlerting:
    """Test security alerting system"""

    @pytest.mark.asyncio
    async def test_failed_login_alert(self):
        """Test failed login alerting"""
        initial_events = len(security_alert_manager.recent_events)

        await security_alert_manager.log_security_event(
            SecurityEventType.FAILED_LOGIN,
            metadata={"ip_address": "192.168.1.100"}
        )

        assert len(security_alert_manager.recent_events) > initial_events

    @pytest.mark.asyncio
    async def test_high_entropy_detection_alert(self):
        """Test high entropy detection alerting"""
        initial_events = len(security_alert_manager.recent_events)

        await security_alert_manager.log_security_event(
            SecurityEventType.HIGH_ENTROPY_DETECTION,
            user_id=123,
            metadata={"entropy_score": 4.8, "secret_type": "api_key"}
        )

        assert len(security_alert_manager.recent_events) > initial_events

    @pytest.mark.asyncio
    async def test_cross_org_attempt_alert(self):
        """Test cross-org access attempt alerting"""
        initial_alerts = len(security_alert_manager.active_alerts)

        await security_alert_manager.log_security_event(
            SecurityEventType.CROSS_ORG_ATTEMPT,
            user_id=123,
            metadata={"user_org_id": 1, "target_org_id": 2}
        )

        # Cross-org attempts should trigger immediate alerts
        assert len(security_alert_manager.active_alerts) > initial_alerts

    def test_security_statistics(self):
        """Test security statistics generation"""
        stats = security_alert_manager.get_security_statistics(24)

        assert "total_events" in stats
        assert "events_by_type" in stats
        assert "unique_users_involved" in stats
        assert "active_alerts" in stats
        assert "time_period_hours" in stats
        assert stats["time_period_hours"] == 24


class TestEndToEndSecurity:
    """End-to-end security testing"""

    def setup_method(self):
        """Set up complete application with security"""
        self.app = FastAPI()

        # Add all security middleware
        configure_security(self.app, development_mode=False)

        # Add test endpoints
        @self.app.post("/api/memory")
        async def store_memory(request: Request, data: dict):
            return {"message": "Memory stored", "data": data}

        @self.app.get("/api/admin/users")
        async def get_users(request: Request):
            return {"users": [{"id": 1, "email": "admin@example.com"}]}

        self.client = TestClient(self.app)

    def test_complete_security_pipeline(self):
        """Test complete security pipeline with real request"""
        # Request with sensitive data
        sensitive_data = {
            "content": "Here's the API key: sk-1234567890abcdef1234567890abcdef12345678",
            "user_email": "user@company.com",
            "phone": "+1-555-123-4567"
        }

        response = self.client.post("/api/memory", json=sensitive_data)

        # Should get successful response
        assert response.status_code in [200, 401, 403]  # May fail auth, but shouldn't crash

        # Response should have security headers
        assert "X-Content-Type-Options" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_security_headers_on_all_responses(self):
        """Test that security headers are added to all responses"""
        # Test different endpoints
        endpoints = ["/api/memory", "/api/admin/users"]

        for endpoint in endpoints:
            response = self.client.get(endpoint)

            # All responses should have security headers
            assert "X-Content-Type-Options" in response.headers
            assert "X-Frame-Options" in response.headers
            assert "Strict-Transport-Security" in response.headers


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
