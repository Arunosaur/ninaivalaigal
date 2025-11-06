#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
"""
Tests for SLO Compliance Endpoint (US#141)

Tests the /health/slo-compliance endpoint:
- Availability SLO (99.9% uptime, 30-day window)
- Response time SLO (P95 < 200ms, 24-hour window)
- Error rate SLO (< 0.1%, 24-hour window)
- Time window support (1h, 24h, 7d)
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from fastapi import FastAPI
from routers.health import router, slo_compliance_check

app = FastAPI()
app.include_router(router)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


class TestSLOComplianceEndpoint:
    """Test suite for /health/slo-compliance endpoint"""

    def test_slo_compliance_endpoint_exists(self, client):
        """Test that /health/slo-compliance endpoint exists"""
        # Mock the SLO status function to avoid dependencies
        with patch("lib.observability.slo_monitoring.get_slo_status") as mock_get_slo_status:
            mock_get_slo_status.return_value = {
                "window": "1h",
                "targets": {
                    "availability": 0.999,
                    "response_time_p95": 0.2,
                    "error_rate": 0.001,
                },
                "current": {
                    "availability": 0.9995,
                    "response_time_p95": 0.15,
                    "error_rate": 0.0005,
                },
                "compliance": {
                    "availability": True,
                    "response_time_p95": True,
                    "error_rate": True,
                    "overall": True,
                },
                "overall_status": "healthy",
                "timestamp": "2025-01-15T10:00:00",
            }

            response = client.get("/health/slo-compliance")

            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "window" in data
            assert "targets" in data
            assert "current" in data
            assert "compliance" in data
            assert "overall_compliant" in data
            assert "timestamp" in data

    def test_slo_compliance_with_different_windows(self, client):
        """Test SLO compliance endpoint with different time windows"""
        windows = ["1h", "24h", "7d"]

        for window in windows:
            with patch("lib.observability.slo_monitoring.get_slo_status") as mock_get_slo_status:
                mock_get_slo_status.return_value = {
                    "window": window,
                    "targets": {
                        "availability": 0.999,
                        "response_time_p95": 0.2,
                        "error_rate": 0.001,
                    },
                    "current": {
                        "availability": 0.9995,
                        "response_time_p95": 0.15,
                        "error_rate": 0.0005,
                    },
                    "compliance": {
                        "availability": True,
                        "response_time_p95": True,
                        "error_rate": True,
                        "overall": True,
                    },
                    "overall_status": "healthy",
                    "timestamp": "2025-01-15T10:00:00",
                }

                response = client.get(f"/health/slo-compliance?window={window}")

                assert response.status_code == 200
                data = response.json()
                assert data["window"] == window

    def test_slo_compliance_invalid_window(self, client):
        """Test SLO compliance endpoint with invalid window"""
        response = client.get("/health/slo-compliance?window=invalid")

        # Should return 422 validation error
        assert response.status_code == 422

    def test_slo_compliance_healthy_status(self, client):
        """Test SLO compliance when all SLOs are met"""
        with patch("lib.observability.slo_monitoring.get_slo_status") as mock_get_slo_status:
            mock_get_slo_status.return_value = {
                "window": "1h",
                "targets": {
                    "availability": 0.999,
                    "response_time_p95": 0.2,
                    "error_rate": 0.001,
                },
                "current": {
                    "availability": 0.9995,  # Above target
                    "response_time_p95": 0.15,  # Below target
                    "error_rate": 0.0005,  # Below target
                },
                "compliance": {
                    "availability": True,
                    "response_time_p95": True,
                    "error_rate": True,
                    "overall": True,
                },
                "overall_status": "healthy",
                "timestamp": "2025-01-15T10:00:00",
            }

            response = client.get("/health/slo-compliance")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["overall_compliant"] is True
            assert data["compliance"]["availability"] is True
            assert data["compliance"]["response_time_p95"] is True
            assert data["compliance"]["error_rate"] is True

    def test_slo_compliance_degraded_status(self, client):
        """Test SLO compliance when SLOs are violated"""
        with patch("lib.observability.slo_monitoring.get_slo_status") as mock_get_slo_status:
            mock_get_slo_status.return_value = {
                "window": "1h",
                "targets": {
                    "availability": 0.999,
                    "response_time_p95": 0.2,
                    "error_rate": 0.001,
                },
                "current": {
                    "availability": 0.998,  # Below target
                    "response_time_p95": 0.25,  # Above target
                    "error_rate": 0.002,  # Above target
                },
                "compliance": {
                    "availability": False,
                    "response_time_p95": False,
                    "error_rate": False,
                    "overall": False,
                },
                "overall_status": "degraded",
                "timestamp": "2025-01-15T10:00:00",
            }

            response = client.get("/health/slo-compliance")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["overall_compliant"] is False
            assert data["compliance"]["availability"] is False
            assert data["compliance"]["response_time_p95"] is False
            assert data["compliance"]["error_rate"] is False

    def test_slo_compliance_partial_violation(self, client):
        """Test SLO compliance when some SLOs are violated"""
        with patch("lib.observability.slo_monitoring.get_slo_status") as mock_get_slo_status:
            mock_get_slo_status.return_value = {
                "window": "1h",
                "targets": {
                    "availability": 0.999,
                    "response_time_p95": 0.2,
                    "error_rate": 0.001,
                },
                "current": {
                    "availability": 0.9995,  # Above target
                    "response_time_p95": 0.25,  # Above target (violation)
                    "error_rate": 0.0005,  # Below target
                },
                "compliance": {
                    "availability": True,
                    "response_time_p95": False,  # Violated
                    "error_rate": True,
                    "overall": False,
                },
                "overall_status": "degraded",
                "timestamp": "2025-01-15T10:00:00",
            }

            response = client.get("/health/slo-compliance")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["overall_compliant"] is False
            assert data["compliance"]["availability"] is True
            assert data["compliance"]["response_time_p95"] is False
            assert data["compliance"]["error_rate"] is True

    def test_slo_compliance_error_handling(self, client):
        """Test SLO compliance endpoint error handling"""
        with patch("lib.observability.slo_monitoring.get_slo_status") as mock_get_slo_status:
            mock_get_slo_status.return_value = {
                "window": "1h",
                "overall_status": "error",
                "error": "Failed to calculate SLO metrics",
                "timestamp": "2025-01-15T10:00:00",
            }

            response = client.get("/health/slo-compliance")

            assert response.status_code == 500
            detail = response.json()["detail"]
            assert "Failed to calculate SLO metrics" in detail or "error" in detail.lower()

    def test_slo_compliance_default_window(self, client):
        """Test SLO compliance endpoint uses default window (1h)"""
        with patch("lib.observability.slo_monitoring.get_slo_status") as mock_get_slo_status:
            mock_get_slo_status.return_value = {
                "window": "1h",
                "targets": {},
                "current": {},
                "compliance": {"overall": True},
                "overall_status": "healthy",
                "timestamp": "2025-01-15T10:00:00",
            }

            response = client.get("/health/slo-compliance")

            assert response.status_code == 200
            # Verify default window was used
            mock_get_slo_status.assert_called_once_with("1h")

    def test_slo_compliance_response_structure(self, client):
        """Test SLO compliance response structure"""
        with patch("lib.observability.slo_monitoring.get_slo_status") as mock_get_slo_status:
            mock_get_slo_status.return_value = {
                "window": "24h",
                "targets": {
                    "availability": 0.999,
                    "response_time_p95": 0.2,
                    "error_rate": 0.001,
                },
                "current": {
                    "availability": 0.9995,
                    "response_time_p95": 0.15,
                    "error_rate": 0.0005,
                },
                "compliance": {
                    "availability": True,
                    "response_time_p95": True,
                    "error_rate": True,
                    "overall": True,
                },
                "overall_status": "healthy",
                "timestamp": "2025-01-15T10:00:00",
            }

            response = client.get("/health/slo-compliance?window=24h")

            assert response.status_code == 200
            data = response.json()

            # Verify all required fields
            assert "status" in data
            assert "window" in data
            assert "targets" in data
            assert "current" in data
            assert "compliance" in data
            assert "overall_compliant" in data
            assert "timestamp" in data

            # Verify targets structure
            assert "availability" in data["targets"]
            assert "response_time_p95" in data["targets"]
            assert "error_rate" in data["targets"]

            # Verify current metrics structure
            assert "availability" in data["current"]
            assert "response_time_p95" in data["current"]
            assert "error_rate" in data["current"]

            # Verify compliance structure
            assert "availability" in data["compliance"]
            assert "response_time_p95" in data["compliance"]
            assert "error_rate" in data["compliance"]
            assert "overall" in data["compliance"]
