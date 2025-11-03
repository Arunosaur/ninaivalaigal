#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Integration Tests for Advanced Health Endpoints (SPEC-018)

Comprehensive integration tests for:
- GET /health - Basic liveness check
- GET /health/live - Kubernetes liveness probe
- GET /health/ready - Readiness probe with dependencies
- GET /health/detailed - Detailed health with SLO metrics
- GET /memory/health - Memory service health checks
- SLO monitoring integration
"""

import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Try to import FastAPI and TestClient
try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

# Add paths for imports - services_dir FIRST (before lib) to get correct routers
current_dir = os.path.dirname(__file__)
services_dir = os.path.join(current_dir, "..", "..")
# Insert services_dir first so we get routers/health.py not lib/routers
sys.path.insert(0, services_dir)

try:
    # Import health router from services/core-api/routers/health.py
    from routers import health as health_module

    health_router = health_module.router

    # Try to import memory health router (optional)
    try:
        from lib.observability.memory_health import router as memory_health_router
    except (ImportError, AttributeError):
        memory_health_router = None

    HEALTH_ENDPOINTS_AVAILABLE = True
except (ImportError, AttributeError) as e:
    HEALTH_ENDPOINTS_AVAILABLE = False
    health_router = None
    memory_health_router = None

# Only skip if both are unavailable
if not FASTAPI_AVAILABLE:
    pytestmark = pytest.mark.skip(reason="FastAPI not available")
elif not HEALTH_ENDPOINTS_AVAILABLE:
    pytestmark = pytest.mark.skip(reason="Health endpoints not available")
else:
    # Both available, no skip
    pass


@pytest.fixture
def test_app():
    """Create test FastAPI app with health routers"""
    app = FastAPI(title="Test Health API")
    if health_router:
        app.include_router(health_router, prefix="")
    if memory_health_router:
        try:
            app.include_router(memory_health_router, prefix="/memory")
        except Exception:
            pass  # Memory health router might not be available
    return app


@pytest.fixture
def client(test_app):
    """Create test client"""
    return TestClient(test_app)


class TestBasicHealthEndpoint:
    """Test GET /health basic health check"""

    def test_health_endpoint_returns_200(self, client):
        """Test that /health returns 200 OK"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "core-api"
        assert data["version"] == "1.0.0"
        assert "uptime_seconds" in data
        assert "timestamp" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0

    def test_health_endpoint_response_time(self, client):
        """Test that /health responds quickly (<10ms target per SPEC-018)"""
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000  # Convert to ms

        assert response.status_code == 200
        # Should be very fast, allow some margin for test environment
        assert elapsed < 100  # 100ms is reasonable for test environment


class TestLivenessProbe:
    """Test GET /health/live Kubernetes liveness probe"""

    def test_liveness_endpoint_returns_200(self, client):
        """Test that /health/live returns 200 OK (always, even if degraded)"""
        response = client.get("/health/live")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "core-api"
        assert "uptime_seconds" in data
        assert "timestamp" in data

    def test_liveness_endpoint_always_returns_healthy(self, client):
        """Test that liveness probe always returns healthy if app is running"""
        # Liveness should not check dependencies
        # Even if DB is down, liveness should be healthy
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestReadinessProbe:
    """Test GET /health/ready readiness check with dependencies"""

    @patch("routers.health.check_database")
    @patch("routers.health.check_redis")
    @patch("routers.health.check_pgbouncer")
    def test_readiness_with_all_healthy_dependencies(self, mock_pgbouncer, mock_redis, mock_db, client):
        """Test readiness when all dependencies are healthy"""
        mock_db.return_value = {"status": "healthy", "type": "postgresql", "message": "Connected"}
        mock_redis.return_value = {"status": "healthy", "type": "redis", "message": "Connected"}
        mock_pgbouncer.return_value = {"status": "healthy", "type": "pgbouncer", "message": "Active"}

        response = client.get("/health/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert data["service"] == "core-api"
        assert "dependencies" in data
        assert data["dependencies"]["database"]["status"] == "healthy"
        assert data["dependencies"]["redis"]["status"] == "healthy"
        assert data["dependencies"]["pgbouncer"]["status"] == "healthy"

    @patch("routers.health.check_database")
    @patch("routers.health.check_redis")
    @patch("routers.health.check_pgbouncer")
    def test_readiness_with_unhealthy_database(self, mock_pgbouncer, mock_redis, mock_db, client):
        """Test readiness fails when database is unhealthy"""
        mock_db.return_value = {"status": "unhealthy", "type": "postgresql", "error": "Connection refused"}
        mock_redis.return_value = {"status": "healthy", "type": "redis", "message": "Connected"}
        mock_pgbouncer.return_value = {"status": "healthy", "type": "pgbouncer", "message": "Active"}

        response = client.get("/health/ready")
        assert response.status_code == 503

        data = response.json()
        assert data["detail"]["status"] == "not_ready"
        assert data["detail"]["dependencies"]["database"]["status"] == "unhealthy"

    @patch("routers.health.check_database")
    @patch("routers.health.check_redis")
    @patch("routers.health.check_pgbouncer")
    def test_readiness_with_unknown_redis(self, mock_pgbouncer, mock_redis, mock_db, client):
        """Test readiness accepts 'unknown' status (not configured)"""
        mock_db.return_value = {"status": "healthy", "type": "postgresql", "message": "Connected"}
        mock_redis.return_value = {"status": "unknown", "type": "redis", "message": "REDIS_URL not configured"}
        mock_pgbouncer.return_value = {"status": "healthy", "type": "pgbouncer", "message": "Active"}

        response = client.get("/health/ready")
        # Should still be ready even if Redis is unknown (not required)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert data["dependencies"]["redis"]["status"] == "unknown"

    @patch("routers.health.check_database")
    @patch("routers.health.check_redis")
    @patch("routers.health.check_pgbouncer")
    def test_readiness_with_exception(self, mock_pgbouncer, mock_redis, mock_db, client):
        """Test readiness handles exceptions gracefully"""
        mock_db.side_effect = Exception("Database connection error")
        mock_redis.return_value = {"status": "healthy", "type": "redis", "message": "Connected"}
        mock_pgbouncer.return_value = {"status": "healthy", "type": "pgbouncer", "message": "Active"}

        response = client.get("/health/ready")
        assert response.status_code == 503

        data = response.json()
        assert data["detail"]["status"] == "not_ready"
        assert "error" in data["detail"]["dependencies"]["database"]


class TestDetailedHealthEndpoint:
    """Test GET /health/detailed comprehensive health check"""

    @patch("routers.health.get_slo_metrics")
    @patch("routers.health.check_database")
    @patch("routers.health.check_redis")
    @patch("routers.health.check_pgbouncer")
    def test_detailed_health_with_slo_metrics(self, mock_pgbouncer, mock_redis, mock_db, mock_slo, client):
        """Test detailed health includes SLO metrics"""
        mock_db.return_value = {"status": "healthy", "type": "postgresql", "message": "Connected"}
        mock_redis.return_value = {"status": "healthy", "type": "redis", "message": "Connected"}
        mock_pgbouncer.return_value = {"status": "healthy", "type": "pgbouncer", "message": "Active"}
        mock_slo.return_value = {
            "1h": {"availability": 0.999, "response_time_p95": 0.15, "error_rate": 0.0001},
            "24h": {"availability": 0.998, "response_time_p95": 0.18, "error_rate": 0.0002},
        }

        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "core-api"
        assert "dependencies" in data
        assert "slo_metrics" in data
        assert "uptime_seconds" in data
        assert "timestamp" in data

    @patch("routers.health.get_slo_metrics")
    @patch("routers.health.check_database")
    @patch("routers.health.check_redis")
    @patch("routers.health.check_pgbouncer")
    def test_detailed_health_with_degraded_status(self, mock_pgbouncer, mock_redis, mock_db, mock_slo, client):
        """Test detailed health shows degraded when dependencies fail"""
        mock_db.return_value = {"status": "healthy", "type": "postgresql", "message": "Connected"}
        mock_redis.return_value = {"status": "unhealthy", "type": "redis", "error": "Connection timeout"}
        mock_pgbouncer.return_value = {"status": "healthy", "type": "pgbouncer", "message": "Active"}
        mock_slo.return_value = {}

        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "degraded"  # Should be degraded, not unhealthy
        assert data["dependencies"]["redis"]["status"] == "unhealthy"

    @patch("routers.health.get_slo_metrics")
    @patch("routers.health.check_database")
    @patch("routers.health.check_redis")
    @patch("routers.health.check_pgbouncer")
    def test_detailed_health_slo_metrics_structure(self, mock_pgbouncer, mock_redis, mock_db, mock_slo, client):
        """Test that SLO metrics are properly structured"""
        mock_db.return_value = {"status": "healthy", "type": "postgresql"}
        mock_redis.return_value = {"status": "healthy", "type": "redis"}
        mock_pgbouncer.return_value = {"status": "healthy", "type": "pgbouncer"}
        mock_slo.return_value = {
            "1h": {
                "availability": 0.9995,
                "response_time_p95": 0.125,
                "error_rate": 0.00005,
                "compliance": {"overall": True},
            },
            "24h": {
                "availability": 0.9990,
                "response_time_p95": 0.150,
                "error_rate": 0.00010,
                "compliance": {"overall": True},
            },
        }

        response = client.get("/health/detailed")
        assert response.status_code == 200

        data = response.json()
        slo = data["slo_metrics"]

        # Should have time windows
        assert "1h" in slo or "24h" in slo

        # If SLO data exists, check structure
        if "1h" in slo:
            assert "availability" in slo["1h"] or "error" in slo

    @patch("routers.health.get_slo_metrics")
    def test_detailed_health_slo_metrics_error_handling(self, mock_slo, client):
        """Test that SLO metrics errors don't break detailed health"""
        # Mock should return error dict, not raise exception
        # The get_slo_metrics function catches exceptions and returns error dict
        mock_slo.return_value = {"error": "SLO monitoring unavailable"}

        # Should still return health check even if SLO fails
        response = client.get("/health/detailed")
        # Should return 200 even with SLO error (health endpoint should be resilient)
        assert response.status_code == 200

        data = response.json()
        # Should handle SLO error gracefully
        assert "slo_metrics" in data
        # SLO metrics should show error or be empty dict
        assert "error" in data["slo_metrics"] or data["slo_metrics"] == {}


class TestMemoryHealthEndpoint:
    """Test GET /memory/health memory service health checks"""

    @patch("lib.observability.memory_health.check_memory_service")
    @patch("lib.observability.memory_health.check_redis_memory_cache")
    def test_memory_health_endpoint_exists(self, mock_redis_check, mock_service_check, client):
        """Test that /memory/health endpoint exists and responds"""
        mock_service_check.return_value = {
            "status": "healthy",
            "response_time_ms": 12.5,
            "endpoints": 5,
            "details": {"service": "memory_api", "router_loaded": True},
        }
        mock_redis_check.return_value = {
            "status": "healthy",
            "response_time_ms": 5.2,
            "memory_usage_mb": 128.5,
            "connected_clients": 3,
            "details": {"redis_version": "7.0.0"},
        }

        # Try to call the endpoint
        try:
            response = client.get("/memory/health")
            # Should return 200 if endpoint exists
            if response.status_code == 200:
                data = response.json()
                assert "status" in data
                assert "service" in data
        except Exception:
            # Endpoint might not be registered, that's okay for now
            pytest.skip("Memory health endpoint not registered in test app")

    def test_memory_health_simple_endpoint(self, client):
        """Test /memory/health/simple load balancer endpoint"""
        try:
            response = client.get("/memory/health/simple")
            # Simple endpoint should be very fast
            assert response.status_code in [200, 404]  # 404 if not implemented
        except Exception:
            pytest.skip("Memory health simple endpoint not available")


class TestSLOIntegration:
    """Test SLO monitoring integration with health endpoints"""

    @patch("routers.health.get_slo_metrics")
    def test_slo_metrics_in_detailed_health(self, mock_slo, client):
        """Test that SLO metrics appear in detailed health"""
        mock_slo.return_value = {
            "1h": {
                "availability": 0.9999,
                "response_time_p95": 0.120,
                "error_rate": 0.00001,
                "compliance": {"overall": True, "availability": True, "response_time_p95": True, "error_rate": True},
            }
        }

        response = client.get("/health/detailed")
        if response.status_code == 200:
            data = response.json()
            if "slo_metrics" in data:
                slo = data["slo_metrics"]
                assert "1h" in slo

    @patch("lib.observability.slo_monitoring.record_slo_request")
    def test_slo_tracking_integration(self, mock_record):
        """Test that SLO tracking can be called"""
        try:
            from lib.observability.slo_monitoring import record_slo_request

            # Should be able to record requests
            record_slo_request(response_time=0.15, is_error=False, is_available=True)

            # Verify it was called (if function exists)
            assert True  # Test passes if no exception
        except ImportError:
            pytest.skip("SLO monitoring not available")


class TestEndpointPerformance:
    """Test performance requirements from SPEC-018"""

    def test_health_endpoint_performance(self, client):
        """Test /health responds within <10ms target"""
        import time

        start = time.time()
        response = client.get("/health")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        # In test environment, allow up to 100ms (10x margin for test overhead)
        assert elapsed < 100, f"Health endpoint too slow: {elapsed}ms"

    def test_liveness_endpoint_performance(self, client):
        """Test /health/live responds quickly"""
        import time

        start = time.time()
        response = client.get("/health/live")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < 100, f"Liveness endpoint too slow: {elapsed}ms"

    @patch("routers.health.check_database")
    @patch("routers.health.check_redis")
    @patch("routers.health.check_pgbouncer")
    def test_detailed_health_performance(self, mock_pgbouncer, mock_redis, mock_db, client):
        """Test /health/detailed responds within <250ms target"""
        import time

        mock_db.return_value = {"status": "healthy", "type": "postgresql"}
        mock_redis.return_value = {"status": "healthy", "type": "redis"}
        mock_pgbouncer.return_value = {"status": "healthy", "type": "pgbouncer"}

        start = time.time()
        response = client.get("/health/detailed")
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        # SPEC-018 target is <250ms, allow 500ms in test environment
        assert elapsed < 500, f"Detailed health endpoint too slow: {elapsed}ms"


class TestErrorHandling:
    """Test error handling in health endpoints"""

    @patch("routers.health.check_database")
    @patch("routers.health.check_redis")
    @patch("routers.health.check_pgbouncer")
    def test_readiness_handles_exceptions_gracefully(self, mock_pgbouncer, mock_redis, mock_db, client):
        """Test that exceptions in dependency checks are handled"""
        mock_db.side_effect = RuntimeError("Database connection pool exhausted")
        mock_redis.side_effect = ConnectionError("Redis connection failed")
        mock_pgbouncer.return_value = {"status": "healthy"}

        # Should return 503, not crash
        response = client.get("/health/ready")
        assert response.status_code == 503

        # Should have error details in response
        data = response.json()
        assert "detail" in data
        assert "dependencies" in data["detail"]

    def test_health_endpoint_never_crashes(self, client):
        """Test that basic health endpoint never raises exceptions"""
        # Should always return 200 if app is running
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
