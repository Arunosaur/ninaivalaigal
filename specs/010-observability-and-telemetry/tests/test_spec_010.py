"""
SPEC-010: Observability & Telemetry Tests

Tests for health endpoints, metrics, and structured logging.
"""

import os
import time

import httpx
import pytest

API_BASE = os.environ.get("API_BASE", "http://127.0.0.1:13370")

def test_basic_health():
    """Test basic health endpoint returns 200 with correct status"""
    response = httpx.get(f"{API_BASE}/health", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_detailed_health():
    """Test detailed health endpoint includes required fields"""
    response = httpx.get(f"{API_BASE}/health/detailed", timeout=5)
    assert response.status_code == 200
    data = response.json()

    # Required fields
    assert "status" in data
    assert "uptime_s" in data
    assert "db" in data
    assert isinstance(data["uptime_s"], int)
    assert data["uptime_s"] >= 0

    # Database status
    assert "connected" in data["db"]
    assert isinstance(data["db"]["connected"], bool)

def test_metrics_endpoint():
    """Test Prometheus metrics endpoint"""
    response = httpx.get(f"{API_BASE}/metrics", timeout=5)
    assert response.status_code == 200

    # Check content type
    assert "text/plain" in response.headers.get("content-type", "")

    # Check for expected metrics
    content = response.text
    assert "http_requests_total" in content
    assert "http_request_duration_seconds" in content
    assert "app_uptime_seconds" in content

def test_health_latency_slo():
    """Test health endpoint meets SLO requirements (< 250ms)"""
    start_time = time.perf_counter()
    response = httpx.get(f"{API_BASE}/health", timeout=5)
    end_time = time.perf_counter()

    latency_ms = (end_time - start_time) * 1000

    assert response.status_code == 200
    assert latency_ms < 250, f"Health endpoint took {latency_ms:.1f}ms, exceeds 250ms SLO"

def test_metrics_after_requests():
    """Test that metrics are updated after making requests"""
    # Make a few requests to generate metrics
    for _ in range(3):
        httpx.get(f"{API_BASE}/health", timeout=5)

    # Check metrics
    response = httpx.get(f"{API_BASE}/metrics", timeout=5)
    assert response.status_code == 200

    content = response.text
    # Should have recorded our health check requests
    assert 'http_requests_total{' in content
    assert 'method="GET"' in content
    assert 'code="200"' in content

@pytest.mark.skip(reason="Requires request ID header implementation")
def test_request_id_tracking():
    """Test request ID is tracked in responses"""
    custom_id = "test-request-123"
    response = httpx.get(
        f"{API_BASE}/health",
        headers={"X-Request-ID": custom_id},
        timeout=5
    )

    assert response.status_code == 200
    # In a full implementation, we might return the request ID in response headers
