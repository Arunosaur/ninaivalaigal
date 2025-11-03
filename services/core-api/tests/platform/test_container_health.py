#!/usr/bin/env python3
# SPDX-License-Identifier: Elastic-2.0
# Copyright (c) 2025 Medhasys LLC
"""
Integration tests for Container Health Monitoring (SPEC-051)

Tests the container health monitoring system, circuit breakers,
and performance baselines.
"""

import asyncio

# Import the monitoring components
import sys
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

CORE_API_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(CORE_API_DIR / "lib"))

from observability.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_breaker_registry,
)
from observability.container_health import (
    ContainerHealthMonitor,
    ContainerStatus,
    ServiceType,
    get_container_health_monitor,
)
from observability.performance_baselines import (
    PerformanceBaselineManager,
    get_baseline_manager,
)


class TestContainerHealthMonitor:
    """Test container health monitoring system"""

    @pytest.fixture
    def monitor(self):
        """Create a fresh monitor instance"""
        return ContainerHealthMonitor()

    @pytest.mark.asyncio
    async def test_check_http_service_healthy(self, monitor):
        """Test checking a healthy HTTP service"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "healthy", "uptime_seconds": 3600}

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            health = await monitor.check_http_service(ServiceType.CORE_API, "http://localhost:8000/health")

            assert health.service == ServiceType.CORE_API
            assert health.status == ContainerStatus.HEALTHY
            assert health.response_time_ms is not None
            assert health.uptime_seconds == 3600

    @pytest.mark.asyncio
    async def test_check_http_service_unhealthy(self, monitor):
        """Test checking an unhealthy HTTP service"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection refused")
            )

            health = await monitor.check_http_service(ServiceType.CORE_API, "http://localhost:8000/health")

            assert health.service == ServiceType.CORE_API
            assert health.status == ContainerStatus.UNHEALTHY
            assert health.error == "Connection refused"

    @pytest.mark.asyncio
    async def test_check_http_service_timeout(self, monitor):
        """Test checking a service that times out"""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            health = await monitor.check_http_service(ServiceType.CORE_API, "http://localhost:8000/health")

            assert health.service == ServiceType.CORE_API
            assert health.status == ContainerStatus.UNHEALTHY
            assert health.error == "Timeout"

    @pytest.mark.asyncio
    async def test_validate_dependencies(self, monitor):
        """Test dependency validation"""
        # Add some mock health data
        monitor.health_cache[ServiceType.POSTGRES] = Mock(status=ContainerStatus.HEALTHY)
        monitor.health_cache[ServiceType.REDIS] = Mock(status=ContainerStatus.UNHEALTHY)

        dependencies = await monitor.validate_dependencies()

        # Core API depends on Postgres, PgBouncer, and Redis
        assert ServiceType.CORE_API in dependencies
        core_api_deps = dependencies[ServiceType.CORE_API]

        assert core_api_deps["postgres"] == ContainerStatus.HEALTHY
        assert core_api_deps["redis"] == ContainerStatus.UNHEALTHY

    @pytest.mark.asyncio
    async def test_get_platform_health(self, monitor):
        """Test getting overall platform health"""
        with patch.object(monitor, "check_all_services") as mock_check:
            # Mock healthy services
            mock_check.return_value = {
                ServiceType.CORE_API: Mock(
                    service=ServiceType.CORE_API,
                    status=ContainerStatus.HEALTHY,
                    to_dict=lambda: {"service": "core-api", "status": "healthy"},
                ),
                ServiceType.REDIS: Mock(
                    service=ServiceType.REDIS,
                    status=ContainerStatus.HEALTHY,
                    to_dict=lambda: {"service": "redis", "status": "healthy"},
                ),
            }

            platform_health = await monitor.get_platform_health()

            assert platform_health["overall_status"] == "healthy"
            assert "services" in platform_health
            assert "dependencies" in platform_health
            assert "summary" in platform_health
            assert platform_health["summary"]["total_services"] == 2


class TestCircuitBreaker:
    """Test circuit breaker pattern"""

    @pytest.fixture
    def breaker(self):
        """Create a fresh circuit breaker"""
        return CircuitBreaker(name="test-service", failure_threshold=3, recovery_timeout=5, success_threshold=2)

    @pytest.mark.asyncio
    async def test_circuit_closed_success(self, breaker):
        """Test successful call with closed circuit"""

        async def success_func():
            return "success"

        result = await breaker.call(success_func)

        assert result == "success"
        assert breaker.state == CircuitState.CLOSED
        assert breaker.failure_count == 0

    @pytest.mark.asyncio
    async def test_circuit_opens_after_failures(self, breaker):
        """Test circuit opens after threshold failures"""

        async def failing_func():
            raise Exception("Service failed")

        # Trigger failures up to threshold
        for i in range(3):
            with pytest.raises(Exception):
                await breaker.call(failing_func)

        assert breaker.state == CircuitState.OPEN
        assert breaker.failure_count == 3

    @pytest.mark.asyncio
    async def test_circuit_rejects_when_open(self, breaker):
        """Test circuit rejects calls when open"""
        # Force circuit open
        breaker.state = CircuitState.OPEN

        async def any_func():
            return "should not execute"

        with pytest.raises(CircuitBreakerError) as exc:
            await breaker.call(any_func)

        assert "OPEN" in str(exc.value)

    @pytest.mark.asyncio
    async def test_circuit_half_open_recovery(self, breaker):
        """Test circuit recovery through half-open state"""
        import time
        from datetime import datetime, timedelta

        # Force circuit open with old failure time
        breaker.state = CircuitState.OPEN
        breaker.last_failure_time = datetime.utcnow() - timedelta(seconds=10)

        async def success_func():
            return "success"

        # First call should transition to half-open
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.HALF_OPEN

        # Second successful call should close circuit
        result = await breaker.call(success_func)
        assert result == "success"
        assert breaker.state == CircuitState.CLOSED

    def test_get_status(self, breaker):
        """Test getting circuit breaker status"""
        status = breaker.get_status()

        assert status["name"] == "test-service"
        assert status["state"] == CircuitState.CLOSED.value
        assert "failure_count" in status
        assert "failure_threshold" in status


class TestCircuitBreakerRegistry:
    """Test circuit breaker registry"""

    @pytest.fixture
    def registry(self):
        """Create a fresh registry"""
        return CircuitBreakerRegistry()

    def test_register_breaker(self, registry):
        """Test registering a circuit breaker"""
        breaker = registry.register("test-service")

        assert breaker is not None
        assert breaker.name == "test-service"
        assert registry.get("test-service") == breaker

    def test_register_duplicate(self, registry):
        """Test registering duplicate returns existing"""
        breaker1 = registry.register("test-service")
        breaker2 = registry.register("test-service")

        assert breaker1 is breaker2

    def test_get_all_status(self, registry):
        """Test getting status of all breakers"""
        registry.register("service-1")
        registry.register("service-2")

        all_status = registry.get_all_status()

        assert len(all_status) == 2
        assert "service-1" in all_status
        assert "service-2" in all_status

    def test_reset_all(self, registry):
        """Test resetting all circuit breakers"""
        breaker1 = registry.register("service-1")
        breaker2 = registry.register("service-2")

        # Force breakers open
        breaker1.state = CircuitState.OPEN
        breaker2.state = CircuitState.OPEN

        registry.reset_all()

        assert breaker1.state == CircuitState.CLOSED
        assert breaker2.state == CircuitState.CLOSED


class TestPerformanceBaselines:
    """Test performance baseline system"""

    @pytest.fixture
    def manager(self, tmp_path):
        """Create a baseline manager with temp file"""
        baseline_file = tmp_path / "test_baselines.json"
        return PerformanceBaselineManager(baseline_file=baseline_file)

    def test_establish_baseline(self, manager):
        """Test establishing a performance baseline"""
        manager.establish_baseline(service="test-service", metric="response_time_ms", baseline_value=50.0, unit="ms")

        baselines = manager.get_service_baselines("test-service")

        assert "response_time_ms" in baselines
        assert baselines["response_time_ms"]["baseline_value"] == 50.0
        assert baselines["response_time_ms"]["unit"] == "ms"

    def test_check_metric_normal(self, manager):
        """Test checking metric within normal range"""
        manager.establish_baseline(service="test-service", metric="response_time_ms", baseline_value=50.0, unit="ms")

        result = manager.check_metric("test-service", "response_time_ms", 45.0)

        assert result["status"] == "normal"
        assert result["value"] == 45.0
        assert result["baseline"] == 50.0

    def test_check_metric_warning(self, manager):
        """Test checking metric in warning range"""
        manager.establish_baseline(
            service="test-service",
            metric="response_time_ms",
            baseline_value=50.0,
            unit="ms",
            warning_multiplier=1.5,
            critical_multiplier=2.0,
        )

        # 80ms is above warning threshold (75ms) but below critical (100ms)
        result = manager.check_metric("test-service", "response_time_ms", 80.0)

        assert result["status"] == "warning"
        assert result["threshold_warning"] == 75.0

    def test_check_metric_critical(self, manager):
        """Test checking metric in critical range"""
        manager.establish_baseline(
            service="test-service",
            metric="response_time_ms",
            baseline_value=50.0,
            unit="ms",
            warning_multiplier=1.5,
            critical_multiplier=2.0,
        )

        # 120ms is above critical threshold (100ms)
        result = manager.check_metric("test-service", "response_time_ms", 120.0)

        assert result["status"] == "critical"
        assert result["threshold_critical"] == 100.0

    def test_check_metric_no_baseline(self, manager):
        """Test checking metric without established baseline"""
        result = manager.check_metric("unknown-service", "response_time_ms", 50.0)

        assert result["status"] == "unknown"
        assert "No baseline" in result["message"]

    def test_persistence(self, manager, tmp_path):
        """Test baseline persistence to file"""
        manager.establish_baseline(service="test-service", metric="response_time_ms", baseline_value=50.0, unit="ms")

        # Create new manager with same file
        new_manager = PerformanceBaselineManager(baseline_file=manager.baseline_file)

        baselines = new_manager.get_service_baselines("test-service")
        assert "response_time_ms" in baselines
        assert baselines["response_time_ms"]["baseline_value"] == 50.0


@pytest.mark.integration
class TestContainerHealthAPI:
    """Integration tests for container health API endpoints"""

    @pytest.mark.asyncio
    async def test_health_containers_endpoint(self):
        """Test GET /platform/health/containers endpoint"""
        # This would require a running server
        # For now, just verify the endpoint exists
        from api.container_health_api import router

        routes = [route.path for route in router.routes]
        assert "/platform/health/containers" in routes

    @pytest.mark.asyncio
    async def test_health_summary_endpoint(self):
        """Test GET /platform/health/summary endpoint"""
        from api.container_health_api import router

        routes = [route.path for route in router.routes]
        assert "/platform/health/summary" in routes
