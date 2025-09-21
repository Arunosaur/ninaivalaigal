"""Tests for metrics label guard with bounded cardinality validation."""

import time

import pytest

from server.observability.metrics_label_guard import (
    ALL_REASON_BUCKETS,
    CORE_ROUTE_TEMPLATES,
    CardinalityTracker,
    MetricsLabelGuard,
    MetricsLabelGuardConfig,
    validate_metric_labels,
    validate_metric_labels_legacy,
)


class TestCardinalityTracker:
    """Test cardinality tracking functionality."""

    def test_tracker_initialization(self):
        """Test tracker initializes with empty sets."""
        tracker = CardinalityTracker()

        assert len(tracker.route_templates) == 0
        assert len(tracker.reason_buckets) == 0
        assert len(tracker.user_buckets) == 0
        assert len(tracker.label_combinations) == 0
        assert len(tracker.violations) == 0

    def test_window_reset(self):
        """Test tracking window reset functionality."""
        tracker = CardinalityTracker()

        # Add some data
        tracker.route_templates.add("/test")
        tracker.reason_buckets.add("test_reason")
        tracker.violations.append({"test": "violation"})

        # Reset window
        tracker.reset_window()

        assert len(tracker.route_templates) == 0
        assert len(tracker.reason_buckets) == 0
        assert len(tracker.violations) == 0

    def test_should_reset_window(self):
        """Test window reset timing logic."""
        tracker = CardinalityTracker()

        # Fresh window should not reset
        assert not tracker.should_reset_window(3600)

        # Simulate old window
        tracker.window_start = time.time() - 7200  # 2 hours ago
        assert tracker.should_reset_window(3600)  # 1 hour window


class TestMetricsLabelGuardConfig:
    """Test configuration for metrics label guard."""

    def test_default_config(self):
        """Test default configuration values."""
        config = MetricsLabelGuardConfig()

        assert config.max_route_templates == 100
        assert config.max_reason_buckets == 50
        assert config.max_user_buckets == 1000
        assert config.max_label_length == 128
        assert config.strict_mode is True
        assert config.enable_cardinality_tracking is True
        assert len(config.allowed_route_templates) > 0
        assert len(config.allowed_reason_buckets) > 0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = MetricsLabelGuardConfig(
            max_route_templates=50,
            max_reason_buckets=25,
            strict_mode=False
        )

        assert config.max_route_templates == 50
        assert config.max_reason_buckets == 25
        assert config.strict_mode is False


class TestMetricsLabelGuard:
    """Test comprehensive metrics label validation."""

    def test_guard_initialization(self):
        """Test guard initializes with proper config."""
        guard = MetricsLabelGuard()

        assert guard.config is not None
        assert guard.tracker is not None
        assert guard._route_template_pattern is not None

    def test_valid_labels_pass(self):
        """Test valid labels pass validation."""
        guard = MetricsLabelGuard()

        labels = {
            "route": "/memories/{id}",
            "reason": "jwt_invalid",
            "user_id": "user123"
        }

        result = guard.validate_labels(labels, "test_metric")

        assert result["valid"] is True
        assert len(result["violations"]) == 0
        assert "route" in result["sanitized_labels"]
        assert "reason" in result["sanitized_labels"]
        assert "user_id" in result["sanitized_labels"]

    def test_invalid_route_template_fails(self):
        """Test invalid route template fails validation."""
        config = MetricsLabelGuardConfig(strict_mode=False)  # Use permissive mode for testing
        guard = MetricsLabelGuard(config)

        labels = {
            "route": "/invalid/concrete/path/123",
            "reason": "jwt_invalid"
        }

        result = guard.validate_labels(labels, "test_metric")

        assert result["valid"] is False
        assert any(v["type"] == "label_validation_failed" for v in result["violations"])
        assert any("not in allowlist" in v["message"] for v in result["violations"])

    def test_invalid_reason_bucket_fails(self):
        """Test invalid reason bucket fails validation."""
        config = MetricsLabelGuardConfig(strict_mode=False)  # Use permissive mode for testing
        guard = MetricsLabelGuard(config)

        labels = {
            "route": "/memories/{id}",
            "reason": "invalid_reason_bucket"
        }

        result = guard.validate_labels(labels, "test_metric")

        assert result["valid"] is False
        assert any(v["type"] == "label_validation_failed" for v in result["violations"])
        assert any("not in allowlist" in v["message"] for v in result["violations"])

    def test_label_length_validation(self):
        """Test label length validation."""
        config = MetricsLabelGuardConfig(max_label_length=10, strict_mode=False)
        guard = MetricsLabelGuard(config)

        labels = {
            "route": "/healthz",  # Use shorter route that fits in 10 chars
            "reason": "timeout",  # Use shorter reason that fits in 10 chars
            "custom_label": "this_is_a_very_long_label_value_that_exceeds_limit"
        }

        result = guard.validate_labels(labels, "test_metric")

        assert result["valid"] is False
        assert any("exceeds maximum length" in v["message"] for v in result["violations"])

    def test_user_id_anonymization(self):
        """Test user ID gets anonymized for metrics."""
        guard = MetricsLabelGuard()

        labels = {
            "route": "/memories/{id}",
            "user_id": "sensitive_user_id_12345"
        }

        result = guard.validate_labels(labels, "test_metric")

        assert result["valid"] is True
        anonymized_user = result["sanitized_labels"]["user_id"]
        assert anonymized_user.startswith("user_")
        assert anonymized_user != "sensitive_user_id_12345"

    def test_route_template_normalization(self):
        """Test route template normalization."""
        guard = MetricsLabelGuard()

        test_cases = [
            ("memories/{id}", "/memories/{id}"),  # Add leading slash
            ("/memories/{id}/", "/memories/{id}"),  # Remove trailing slash
            ("/memories/{id}?param=value", "/memories/{id}")  # Remove query params
        ]

        for input_route, expected in test_cases:
            normalized = guard._normalize_route_template(input_route)
            assert normalized == expected

    def test_cardinality_bounds_enforcement(self):
        """Test cardinality bounds are enforced."""
        config = MetricsLabelGuardConfig(
            max_route_templates=2,
            max_reason_buckets=2,
            strict_mode=False  # Don't raise exceptions for this test
        )
        guard = MetricsLabelGuard(config)

        # Add labels within bounds
        result1 = guard.validate_labels({"route": "/memories/{id}"}, "metric1")
        assert result1["valid"] is True

        result2 = guard.validate_labels({"route": "/contexts/{id}/memories"}, "metric2")
        assert result2["valid"] is True

        # Add third route template - should exceed bounds
        result3 = guard.validate_labels({"route": "/users/{id}/contexts"}, "metric3")
        assert result3["valid"] is False
        assert any(v["type"] == "route_cardinality_exceeded" for v in result3["violations"])

    def test_strict_mode_raises_exceptions(self):
        """Test strict mode raises exceptions on violations."""
        config = MetricsLabelGuardConfig(strict_mode=True)
        guard = MetricsLabelGuard(config)

        labels = {
            "route": "/invalid/route",
            "reason": "jwt_invalid"
        }

        with pytest.raises(ValueError, match="not in allowlist"):
            guard.validate_labels(labels, "test_metric")

    def test_permissive_mode_returns_violations(self):
        """Test permissive mode returns violations without raising."""
        config = MetricsLabelGuardConfig(strict_mode=False)
        guard = MetricsLabelGuard(config)

        labels = {
            "route": "/invalid/route",
            "reason": "jwt_invalid"
        }

        result = guard.validate_labels(labels, "test_metric")

        assert result["valid"] is False
        assert len(result["violations"]) > 0
        # Should not raise exception

    def test_cardinality_stats_tracking(self):
        """Test cardinality statistics tracking."""
        guard = MetricsLabelGuard()

        # Add some labels
        guard.validate_labels({"route": "/memories/{id}", "reason": "jwt_invalid"}, "metric1")
        guard.validate_labels({"route": "/contexts/{id}/memories", "reason": "rbac_denied"}, "metric2")

        stats = guard.get_cardinality_stats()

        assert "cardinality" in stats
        assert "limits" in stats
        assert stats["cardinality"]["route_templates"] == 2
        assert stats["cardinality"]["reason_buckets"] == 2
        assert stats["cardinality"]["total_combinations"] == 2


class TestConvenienceFunctions:
    """Test convenience functions for label validation."""

    def test_validate_metric_labels_success(self):
        """Test successful label validation returns sanitized labels."""
        labels = {
            "route": "/memories/{id}",
            "reason": "jwt_invalid"
        }

        sanitized = validate_metric_labels(labels, "test_metric")

        assert "route" in sanitized
        assert "reason" in sanitized
        assert sanitized["route"] == "/memories/{id}"
        assert sanitized["reason"] == "jwt_invalid"

    def test_validate_metric_labels_failure(self):
        """Test failed label validation raises ValueError."""
        labels = {
            "route": "/invalid/route",
            "reason": "jwt_invalid"
        }

        with pytest.raises(ValueError, match="not in allowlist"):
            validate_metric_labels(labels, "test_metric")

    def test_legacy_compatibility_function(self):
        """Test legacy compatibility function works."""
        # Valid labels should pass
        valid_labels = {
            "route": "/memories/{id}",
            "reason": "jwt_invalid"
        }

        # Should not raise
        validate_metric_labels_legacy(valid_labels)

        # Invalid route should raise with legacy message
        invalid_route_labels = {
            "route": "/invalid/route"
        }

        with pytest.raises(ValueError, match="route label must be a known template"):
            validate_metric_labels_legacy(invalid_route_labels)

        # Invalid reason should raise with legacy message
        invalid_reason_labels = {
            "route": "/memories/{id}",
            "reason": "invalid_reason"
        }

        with pytest.raises(ValueError, match="invalid reason label"):
            validate_metric_labels_legacy(invalid_reason_labels)


class TestAllowedTemplatesAndBuckets:
    """Test allowed templates and reason buckets."""

    def test_core_route_templates_defined(self):
        """Test core route templates are properly defined."""
        assert len(CORE_ROUTE_TEMPLATES) > 0
        assert "/memories/{id}" in CORE_ROUTE_TEMPLATES
        assert "/contexts/{id}/memories" in CORE_ROUTE_TEMPLATES
        assert "/healthz" in CORE_ROUTE_TEMPLATES

    def test_all_reason_buckets_defined(self):
        """Test all reason buckets are properly defined."""
        assert len(ALL_REASON_BUCKETS) > 0
        assert "jwt_invalid" in ALL_REASON_BUCKETS
        assert "rbac_denied" in ALL_REASON_BUCKETS
        assert "multipart_rejected" in ALL_REASON_BUCKETS
        assert "timeout" in ALL_REASON_BUCKETS
        assert "validation_failed" in ALL_REASON_BUCKETS

    def test_route_template_patterns(self):
        """Test route template patterns are valid."""
        guard = MetricsLabelGuard()

        valid_patterns = [
            "/memories/{id}",
            "/contexts/{id}/memories",
            "/users/{user_id}/contexts/{context_id}",
            "/admin/users",
            "/healthz/config"
        ]

        for pattern in valid_patterns:
            assert guard._route_template_pattern.match(pattern), f"Pattern {pattern} should be valid"

        invalid_patterns = [
            "memories/{id}",  # Missing leading slash
            "/memories/{id}/}",  # Malformed template
            "/memories/{{id}}",  # Double braces
            "/memories/{id with spaces}"  # Spaces in template
        ]

        for pattern in invalid_patterns:
            assert not guard._route_template_pattern.match(pattern), f"Pattern {pattern} should be invalid"


class TestThreadSafety:
    """Test thread safety of cardinality tracking."""

    def test_concurrent_label_validation(self):
        """Test concurrent label validation is thread-safe."""
        import concurrent.futures

        guard = MetricsLabelGuard()
        results = []

        def validate_labels_worker(worker_id):
            labels = {
                "route": "/memories/{id}",
                "reason": "jwt_invalid",
                "user_id": f"user_{worker_id}"
            }
            result = guard.validate_labels(labels, f"metric_{worker_id}")
            return result["valid"]

        # Run concurrent validations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(validate_labels_worker, i) for i in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]

        # All validations should succeed
        assert all(results)

        # Check cardinality tracking worked correctly
        stats = guard.get_cardinality_stats()
        assert stats["cardinality"]["route_templates"] == 1  # Same route for all
        assert stats["cardinality"]["reason_buckets"] == 1   # Same reason for all
        assert stats["cardinality"]["user_buckets"] == 50    # Different users


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
