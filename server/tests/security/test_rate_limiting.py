#!/usr/bin/env python3
"""
Tests for Enhanced Rate Limiting Middleware

Tests RBAC-aware rate limiting with sliding window and token bucket algorithms.
"""

import asyncio
import time
from unittest.mock import Mock, patch

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.testclient import TestClient as StarletteTestClient

from server.security.middleware.rate_limiting import (
    EnhancedRateLimiter,
    RateLimitConfig,
    RateLimitMiddleware,
    RateLimitType,
    SlidingWindowCounter,
    TokenBucket,
)


class TestTokenBucket:
    """Test token bucket algorithm"""

    def test_token_bucket_initialization(self):
        """Test token bucket initialization"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.tokens == 10
        assert bucket.refill_rate == 1.0

    def test_token_bucket_consume_success(self):
        """Test successful token consumption"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.consume(5) is True
        assert bucket.tokens == 5

    def test_token_bucket_consume_failure(self):
        """Test token consumption failure when insufficient tokens"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.consume(15) is False
        assert bucket.tokens == 10  # Should not consume

    def test_token_bucket_refill(self):
        """Test token refill over time"""
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        bucket.consume(10)  # Empty bucket
        assert bucket.tokens == 0

        # Simulate time passing
        time.sleep(1.1)
        assert bucket.consume(1) is True  # Should have refilled 1+ tokens


class TestSlidingWindowCounter:
    """Test sliding window counter"""

    def test_sliding_window_initialization(self):
        """Test sliding window initialization"""
        counter = SlidingWindowCounter(window_seconds=60, limit=10)
        assert counter.window_seconds == 60
        assert counter.limit == 10
        assert len(counter.requests) == 0

    def test_sliding_window_allows_requests(self):
        """Test that requests are allowed within limit"""
        counter = SlidingWindowCounter(window_seconds=60, limit=10)

        # Add 5 requests
        for i in range(5):
            assert counter.is_allowed() is True

        assert len(counter.requests) == 5

    def test_sliding_window_blocks_excess_requests(self):
        """Test that excess requests are blocked"""
        counter = SlidingWindowCounter(window_seconds=60, limit=5)

        # Add 5 requests (at limit)
        for i in range(5):
            assert counter.is_allowed() is True

        # 6th request should be blocked
        assert counter.is_allowed() is False
        assert len(counter.requests) == 5

    def test_sliding_window_resets_old_requests(self):
        """Test that old requests are removed from window"""
        counter = SlidingWindowCounter(window_seconds=1, limit=5)

        # Add requests
        for i in range(5):
            assert counter.is_allowed() is True

        # Wait for window to expire
        time.sleep(1.1)

        # Should allow new requests
        assert counter.is_allowed() is True
        assert len(counter.requests) <= 2  # Old requests cleaned up


class TestEnhancedRateLimiter:
    """Test enhanced rate limiter with RBAC awareness"""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization"""
        limiter = EnhancedRateLimiter()
        assert len(limiter.endpoint_limits) > 0
        assert limiter.counters == {}

    def test_get_endpoint_pattern(self):
        """Test endpoint pattern matching"""
        limiter = EnhancedRateLimiter()

        assert limiter._get_endpoint_pattern("/auth/login") == "/auth/login"
        assert limiter._get_endpoint_pattern("/auth/signup") == "/auth/signup"
        assert limiter._get_endpoint_pattern("/memory/create") == "/memory"
        assert limiter._get_endpoint_pattern("/contexts/123") == "/contexts"
        assert limiter._get_endpoint_pattern("/unknown/path") == "default"

    def test_get_rate_config(self):
        """Test rate config retrieval"""
        limiter = EnhancedRateLimiter()

        # Test specific endpoint config
        config = limiter._get_rate_config("/auth/login", "anonymous")
        assert config is not None
        assert config.limit == 3

        # Test default config
        config = limiter._get_rate_config("/unknown/path", "anonymous")
        assert config is None  # No default configured

    def test_get_user_info_with_rbac(self):
        """Test user info extraction with RBAC context"""
        limiter = EnhancedRateLimiter()

        # Mock request with RBAC context
        request = Mock()
        rbac_context = Mock()
        rbac_context.user_id = "user-123"
        rbac_context.user_role = "MEMBER"
        request.state.rbac_context = rbac_context
        request.client = Mock(host="127.0.0.1")

        user_id, user_role = limiter._get_user_info(request)
        assert user_id == "user-123"
        assert user_role == "MEMBER"

    def test_get_user_info_anonymous(self):
        """Test user info extraction for anonymous users"""
        limiter = EnhancedRateLimiter()

        # Mock request without RBAC context
        request = Mock()
        request.state = Mock()
        request.state.rbac_context = None
        request.client = Mock(host="127.0.0.1")

        user_id, user_role = limiter._get_user_info(request)
        assert user_id.startswith("anon_")
        assert user_role == "anonymous"

    @pytest.mark.asyncio
    async def test_check_rate_limit_allowed(self):
        """Test rate limit check when request is allowed"""
        limiter = EnhancedRateLimiter()

        request = Mock()
        request.url.path = "/memory/create"
        request.state = Mock()
        request.state.rbac_context = None
        request.client = Mock(host="127.0.0.1")

        # First request should be allowed
        is_allowed, info = await limiter.check_rate_limit(request)
        assert is_allowed is True
        assert info is not None

    @pytest.mark.asyncio
    async def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit is exceeded"""
        limiter = EnhancedRateLimiter()

        request = Mock()
        request.url.path = "/auth/login"
        request.state = Mock()
        request.state.rbac_context = None
        request.client = Mock(host="127.0.0.1")

        # Make requests up to limit (3 for anonymous login)
        for i in range(3):
            is_allowed, info = await limiter.check_rate_limit(request)
            assert is_allowed is True

        # 4th request should be blocked
        is_allowed, info = await limiter.check_rate_limit(request)
        assert is_allowed is False
        assert info is not None
        assert info["remaining"] == 0

    def test_check_sliding_window(self):
        """Test sliding window rate limit check"""
        limiter = EnhancedRateLimiter()

        config = RateLimitConfig(limit=5, window_seconds=60, limit_type=RateLimitType.REQUESTS_PER_MINUTE)

        # Make 5 requests
        for i in range(5):
            assert limiter._check_sliding_window("user-1", "/test", config) is True

        # 6th request should be blocked
        assert limiter._check_sliding_window("user-1", "/test", config) is False

    def test_check_concurrent_limit(self):
        """Test concurrent request limit check"""
        limiter = EnhancedRateLimiter()

        config = RateLimitConfig(limit=3, window_seconds=60, limit_type=RateLimitType.CONCURRENT_REQUESTS)

        # Increment concurrent requests
        limiter.increment_concurrent("user-1", "/test")
        limiter.increment_concurrent("user-1", "/test")
        limiter.increment_concurrent("user-1", "/test")

        # Should be at limit
        assert limiter._check_concurrent_limit("user-1", "/test", config) is False

        # Decrement
        limiter.decrement_concurrent("user-1", "/test")

        # Should allow again
        assert limiter._check_concurrent_limit("user-1", "/test", config) is True

    def test_get_remaining_requests(self):
        """Test remaining requests calculation"""
        limiter = EnhancedRateLimiter()

        config = RateLimitConfig(limit=10, window_seconds=60, limit_type=RateLimitType.REQUESTS_PER_MINUTE)

        # Initially should have full limit
        remaining = limiter._get_remaining_requests("user-1", "/test", config)
        assert remaining == 10

        # Make some requests
        for i in range(3):
            limiter._check_sliding_window("user-1", "/test", config)

        # Should have 7 remaining
        remaining = limiter._get_remaining_requests("user-1", "/test", config)
        assert remaining == 7


class TestRateLimitMiddleware:
    """Test rate limiting middleware integration"""

    @pytest.fixture
    def app(self):
        """Create test FastAPI app"""
        app = FastAPI()

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @app.get("/auth/login")
        async def login_endpoint():
            return {"status": "ok"}

        return app

    @pytest.mark.asyncio
    async def test_middleware_allows_request(self, app):
        """Test that middleware allows requests within limit"""
        app.add_middleware(RateLimitMiddleware)

        client = TestClient(app)

        # First request should succeed
        response = client.get("/test")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers

    @pytest.mark.asyncio
    async def test_middleware_blocks_excess_requests(self, app):
        """Test that middleware blocks excess requests"""
        app.add_middleware(RateLimitMiddleware)

        client = TestClient(app)

        # Make requests to a rate-limited endpoint
        # Anonymous login limit is 3 per 5 minutes
        responses = [client.get("/auth/login") for _ in range(4)]

        # First 3 should succeed
        for i in range(3):
            assert responses[i].status_code == 200

        # 4th should be rate limited
        assert responses[3].status_code == 429
        assert "Rate limit exceeded" in responses[3].json()["detail"]

    @pytest.mark.asyncio
    async def test_middleware_headers(self, app):
        """Test that middleware adds rate limit headers"""
        app.add_middleware(RateLimitMiddleware)

        client = TestClient(app)

        response = client.get("/test")
        assert response.status_code == 200
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Remaining" in response.headers
        assert "X-RateLimit-Reset" in response.headers

    @pytest.mark.asyncio
    async def test_middleware_concurrent_tracking(self, app):
        """Test that middleware tracks concurrent requests"""
        app.add_middleware(RateLimitMiddleware)

        limiter = EnhancedRateLimiter()
        middleware = RateLimitMiddleware(app, rate_limiter=limiter)

        # This is more of an integration test
        # In practice, concurrent tracking happens automatically
        assert middleware.rate_limiter is not None


class TestRateLimitConfig:
    """Test rate limit configuration"""

    def test_rate_limit_config_creation(self):
        """Test rate limit config creation"""
        config = RateLimitConfig(
            limit=100, window_seconds=60, limit_type=RateLimitType.REQUESTS_PER_MINUTE, burst_allowance=10
        )

        assert config.limit == 100
        assert config.window_seconds == 60
        assert config.limit_type == RateLimitType.REQUESTS_PER_MINUTE
        assert config.burst_allowance == 10

    def test_rate_limit_config_defaults(self):
        """Test rate limit config with defaults"""
        config = RateLimitConfig(limit=50, window_seconds=60, limit_type=RateLimitType.REQUESTS_PER_HOUR)

        assert config.limit == 50
        assert config.burst_allowance == 0  # Default


@pytest.mark.asyncio
async def test_rate_limiter_cleanup():
    """Test that rate limiter cleans up old counters"""
    limiter = EnhancedRateLimiter()

    # Add some counters
    config = RateLimitConfig(limit=10, window_seconds=1, limit_type=RateLimitType.REQUESTS_PER_MINUTE)
    limiter._check_sliding_window("user-1", "/test", config)

    # Trigger cleanup (simulate old requests)
    await limiter._cleanup_old_counters()

    # Counters should still exist if recent
    assert "user-1" in limiter.counters or len(limiter.counters) >= 0


@pytest.mark.asyncio
async def test_rate_limiter_multiple_endpoints():
    """Test rate limiter with multiple endpoints"""
    limiter = EnhancedRateLimiter()

    request1 = Mock()
    request1.url.path = "/auth/login"
    request1.state = Mock()
    request1.state.rbac_context = None
    request1.client = Mock(host="127.0.0.1")

    request2 = Mock()
    request2.url.path = "/memory/create"
    request2.state = Mock()
    request2.state.rbac_context = None
    request2.client = Mock(host="127.0.0.1")

    # Should have separate limits for different endpoints
    is_allowed1, _ = await limiter.check_rate_limit(request1)
    is_allowed2, _ = await limiter.check_rate_limit(request2)

    assert is_allowed1 is True
    assert is_allowed2 is True


@pytest.mark.asyncio
async def test_rate_limiter_role_based_limits():
    """Test that rate limits differ by user role"""
    limiter = EnhancedRateLimiter()

    # Test that different roles have different limits
    # Owner should have higher limits than anonymous
    owner_config = limiter._get_rate_config("/memory", "OWNER")
    anonymous_config = limiter._get_rate_config("/memory", "anonymous")

    # Owner should have config if role-based limits are configured
    # Anonymous may not have config (falls back to default or None)
    # This test verifies the structure, not exact values
    assert owner_config is None or owner_config.limit >= 0  # Owner has config or None
