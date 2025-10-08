"""
Integration tests for multipart security monitoring system.

Tests the complete monitoring pipeline from rejection events to Prometheus metrics
and alert rule validation.
"""

import time
from unittest.mock import patch

import pytest

from server.health.multipart_config import (
    get_multipart_config_health,
    validate_multipart_boot_config,
)
from server.security.feature_flags import (
    emergency_rollback,
    get_all_flags,
    get_feature_flag_health,
    set_flag,
)
from server.security.monitoring.grafana_metrics import (
    _metrics_collector,
    get_all_metrics,
    get_prometheus_metrics,
    record_multipart_processing,
    record_multipart_rejection,
)


class TestMultipartMonitoring:
    """Test multipart security monitoring integration."""

    def setup_method(self):
        """Reset metrics before each test."""
        _metrics_collector.metrics.clear()
        _metrics_collector.metric_history.clear()

    def test_rejection_metrics_recording(self):
        """Test that multipart rejections are properly recorded."""
        # Record various rejection types
        record_multipart_rejection("archive_blocked", "/api/upload", "tenant-123")
        record_multipart_rejection("invalid_encoding", "/api/files", "tenant-456")
        record_multipart_rejection("magic_byte_detected", "/api/upload", "tenant-123")

        metrics = get_all_metrics()

        # Verify metrics are recorded with proper labels
        assert (
            "multipart_reject_total{endpoint=/api/upload,reason=archive_blocked,tenant=tenant-123}"
            in metrics
        )
        assert (
            "multipart_reject_total{endpoint=/api/files,reason=invalid_encoding,tenant=tenant-456}"
            in metrics
        )
        assert (
            "multipart_reject_total{endpoint=/api/upload,reason=magic_byte_detected,tenant=tenant-123}"
            in metrics
        )

        # Verify counts
        assert (
            metrics[
                "multipart_reject_total{endpoint=/api/upload,reason=archive_blocked,tenant=tenant-123}"
            ]
            == 1
        )
        assert (
            metrics[
                "multipart_reject_total{endpoint=/api/files,reason=invalid_encoding,tenant=tenant-456}"
            ]
            == 1
        )

    def test_processing_metrics_recording(self):
        """Test that multipart processing metrics are recorded."""
        # Record processing statistics
        record_multipart_processing(
            parts_count=5, bytes_count=1024000, duration_seconds=0.003
        )
        record_multipart_processing(
            parts_count=2, bytes_count=512000, duration_seconds=0.001
        )

        metrics = get_all_metrics()

        # Verify processing metrics
        assert metrics["multipart_parts_total"] == 7
        assert metrics["multipart_bytes_total"] == 1536000
        assert metrics["multipart_processing_duration_seconds_count"] == 2
        assert metrics["multipart_processing_duration_seconds_sum"] == 0.004

    def test_prometheus_format_export(self):
        """Test Prometheus format export includes all required metrics."""
        # Generate test data
        record_multipart_rejection("archive_blocked", "/api/upload", "tenant-1")
        record_multipart_rejection("invalid_encoding", "/api/files", "tenant-2")
        record_multipart_processing(3, 768000, 0.002)

        prometheus_output = get_prometheus_metrics()

        # Verify Prometheus format
        assert (
            "# HELP multipart_reject_total Total multipart rejections with reason"
            in prometheus_output
        )
        assert "# TYPE multipart_reject_total counter" in prometheus_output
        assert (
            "multipart_reject_total{endpoint=/api/upload,reason=archive_blocked,tenant=tenant-1} 1"
            in prometheus_output
        )

        assert (
            "# HELP multipart_parts_total Total multipart parts received"
            in prometheus_output
        )
        assert "multipart_parts_total 3" in prometheus_output

        assert (
            "# HELP multipart_processing_duration_seconds Multipart processing duration"
            in prometheus_output
        )
        assert "multipart_processing_duration_seconds_count 1" in prometheus_output

    def test_alert_threshold_simulation(self):
        """Test alert threshold conditions with simulated traffic."""
        # Simulate spike in rejections (>50 in 10 minutes)
        for i in range(55):
            record_multipart_rejection(
                "archive_blocked", f"/api/endpoint-{i%3}", f"tenant-{i%10}"
            )

        metrics = get_all_metrics()

        # Count total rejections
        total_rejections = sum(
            value
            for key, value in metrics.items()
            if key.startswith("multipart_reject_total")
        )

        assert total_rejections == 55

        # Verify we would trigger the alert (>50 rejections)
        assert total_rejections > 50

        # Simulate archive-specific alert (>10 archive blocks)
        archive_rejections = sum(
            value for key, value in metrics.items() if "reason=archive_blocked" in key
        )

        assert archive_rejections == 55  # All were archive_blocked
        assert archive_rejections > 10  # Would trigger archive-specific alert

    def test_feature_flag_integration(self):
        """Test feature flag system integration with monitoring."""
        # Test flag changes
        assert set_flag("archive_checks_enabled", False, "test_user")
        assert set_flag("magic_byte_detection_enabled", False, "test_user")

        # Get flag health status
        flag_health = get_feature_flag_health()

        assert flag_health["total_flags"] > 0
        assert flag_health["disabled_flags"] >= 2
        assert not flag_health["critical_flags_status"]["archive_checks"]

        # Test recent changes tracking
        assert len(flag_health["recent_changes"]) >= 2

        # Verify flags appear in recent changes
        recent_flags = [change["flag"] for change in flag_health["recent_changes"]]
        assert "archive_checks_enabled" in recent_flags
        assert "magic_byte_detection_enabled" in recent_flags

    def test_emergency_rollback_procedure(self):
        """Test emergency rollback functionality."""
        # Perform emergency rollback
        results = emergency_rollback("test_incident")

        # Verify rollback results
        assert results["archive_checks_enabled"] == True  # Successfully disabled
        assert results["magic_byte_detection_enabled"] == True  # Successfully disabled
        assert (
            results["compression_ratio_checks_enabled"] == True
        )  # Successfully disabled

        # Verify flags are actually disabled
        flags = get_all_flags()
        assert not flags["archive_checks_enabled"]["enabled"]
        assert not flags["magic_byte_detection_enabled"]["enabled"]
        assert not flags["compression_ratio_checks_enabled"]["enabled"]

        # Verify critical flags remain enabled (not in rollback)
        assert flags["rbac_enforcement_enabled"]["enabled"]
        assert flags["log_scrubbing_enabled"]["enabled"]

    def test_health_endpoint_integration(self):
        """Test /healthz/config endpoint integration."""
        # Set some flags for testing
        set_flag("archive_checks_enabled", False, "health_test")

        # Get health status
        health_status = get_multipart_config_health()

        # Verify structure
        assert "status" in health_status
        assert "limits" in health_status
        assert "security_features" in health_status
        assert "rejection_reasons" in health_status
        assert "feature_flags" in health_status

        # Verify feature flag integration
        feature_flags = health_status["feature_flags"]
        assert "total_flags" in feature_flags
        assert "critical_flags_status" in feature_flags
        assert not feature_flags["critical_flags_status"]["archive_checks"]

        # Verify rejection reasons match expected values
        expected_reasons = [
            "engine_error",
            "policy_denied",
            "magic_mismatch",
            "part_too_large",
            "too_many_parts",
            "invalid_encoding",
            "archive_blocked",
        ]
        assert all(
            reason in health_status["rejection_reasons"] for reason in expected_reasons
        )

    def test_boot_validation(self):
        """Test boot-time configuration validation."""
        validation_result = validate_multipart_boot_config()

        # Should be valid in test environment
        assert validation_result["valid"]
        assert isinstance(validation_result["errors"], list)
        assert isinstance(validation_result["warnings"], list)
        assert isinstance(validation_result["actionable_messages"], list)

    def test_canary_monitoring_scenario(self):
        """Test canary deployment monitoring scenario."""
        # Simulate canary deployment with elevated rejections

        # Normal baseline traffic
        for i in range(10):
            record_multipart_processing(2, 100000, 0.001)

        # Canary deployment starts showing issues
        for i in range(8):  # Just under the 10 threshold
            record_multipart_rejection(
                "archive_blocked", "/api/upload", f"canary-tenant-{i}"
            )

        metrics = get_all_metrics()

        # Should not trigger alert yet (8 < 10)
        archive_blocks = sum(
            value for key, value in metrics.items() if "reason=archive_blocked" in key
        )
        assert archive_blocks == 8
        assert archive_blocks < 10  # Below alert threshold

        # Add 3 more to trigger alert
        for i in range(3):
            record_multipart_rejection(
                "archive_blocked", "/api/upload", f"canary-tenant-{i+8}"
            )

        metrics = get_all_metrics()
        archive_blocks = sum(
            value for key, value in metrics.items() if "reason=archive_blocked" in key
        )
        assert archive_blocks == 11
        assert archive_blocks > 10  # Would trigger canary alert

    def test_performance_monitoring(self):
        """Test performance monitoring for P95 latency targets."""
        # Record various processing times
        processing_times = [
            0.001,
            0.002,
            0.003,
            0.004,
            0.008,
            0.012,
            0.015,
        ]  # Some above 5ms target

        for duration in processing_times:
            record_multipart_processing(1, 50000, duration)

        metrics = get_all_metrics()

        # Verify histogram metrics
        assert metrics["multipart_processing_duration_seconds_count"] == len(
            processing_times
        )
        assert metrics["multipart_processing_duration_seconds_sum"] == sum(
            processing_times
        )

        # Calculate average (not P95, but validates data collection)
        avg_duration = (
            metrics["multipart_processing_duration_seconds_sum"]
            / metrics["multipart_processing_duration_seconds_count"]
        )
        assert avg_duration > 0.005  # Above 5ms target, would trigger performance alert

    @patch("server.security.feature_flags.logger")
    def test_audit_logging(self, mock_logger):
        """Test that flag changes are properly audit logged."""
        # Change a critical flag
        set_flag("rbac_enforcement_enabled", False, "security_test")

        # Verify audit log was called
        mock_logger.warning.assert_called()

        # Check log message contains required information
        log_call = mock_logger.warning.call_args[0][0]
        assert "rbac_enforcement_enabled" in log_call
        assert "True → False" in log_call
        assert "security_test" in log_call

    def test_metrics_thread_safety(self):
        """Test metrics collection under concurrent access."""
        import threading

        def record_metrics():
            for i in range(50):
                record_multipart_rejection(
                    "archive_blocked", "/api/test", f"thread-tenant-{i}"
                )
                time.sleep(0.001)  # Small delay to simulate real processing

        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=record_metrics)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        metrics = get_all_metrics()

        # Should have recorded all metrics without corruption
        total_rejections = sum(
            value
            for key, value in metrics.items()
            if key.startswith("multipart_reject_total")
        )

        assert total_rejections == 150  # 3 threads * 50 records each


class TestAlertRuleValidation:
    """Test alert rule configurations match expected format."""

    def test_prometheus_alert_syntax(self):
        """Test that alert rules use correct Prometheus syntax."""
        # This would typically be validated against actual Prometheus
        # For now, we test the metric names match what we generate

        expected_metrics = [
            "multipart_reject_total",
            "multipart_parts_total",
            "multipart_bytes_total",
            "multipart_processing_duration_seconds",
            "security_middleware_health",
            "rbac_access_denied_total",
        ]

        # Record test data for each metric
        record_multipart_rejection("test", "/test", "test")
        record_multipart_processing(1, 1000, 0.001)

        prometheus_output = get_prometheus_metrics()

        # Verify all expected metrics appear in output
        for metric in expected_metrics[:4]:  # Test the ones we can generate
            assert (
                f"# TYPE {metric}" in prometheus_output or metric in prometheus_output
            )

    def test_alert_label_consistency(self):
        """Test that alert labels match metric label structure."""
        # Record rejection with specific labels
        record_multipart_rejection(
            "archive_blocked", "/api/upload", "production-tenant"
        )

        metrics = get_all_metrics()

        # Find the metric key
        metric_key = None
        for key in metrics.keys():
            if "multipart_reject_total" in key and "archive_blocked" in key:
                metric_key = key
                break

        assert metric_key is not None

        # Verify label structure matches alert expectations
        assert "reason=archive_blocked" in metric_key
        assert "endpoint=/api/upload" in metric_key
        assert "tenant=production-tenant" in metric_key


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
