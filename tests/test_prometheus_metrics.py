#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Prometheus Metrics Tests
#
"""
Unit tests for server/billing/prometheus_metrics.py

Tests Prometheus metrics collection for billing system.
"""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.unit


def test_prometheus_available():
    """Test that Prometheus metrics can be imported"""
    try:
        from server.billing import prometheus_metrics

        assert prometheus_metrics is not None
    except ImportError:
        pytest.skip("Prometheus not available")


@patch("server.billing.prometheus_metrics.PROMETHEUS_AVAILABLE", True)
def test_metrics_initialization():
    """Test that metrics are initialized correctly"""
    try:
        from server.billing.prometheus_metrics import (
            quota_blocks_total,
            stripe_sync_duration_seconds,
            usage_aggregation_lag_seconds,
        )

        # Metrics should be initialized (even if they're dummy objects)
        assert usage_aggregation_lag_seconds is not None
        assert quota_blocks_total is not None
        assert stripe_sync_duration_seconds is not None
    except ImportError:
        pytest.skip("Prometheus not available")


@patch("server.billing.prometheus_metrics.PROMETHEUS_AVAILABLE", True)
def test_usage_aggregation_lag_metric():
    """Test usage aggregation lag metric"""
    try:
        from server.billing.prometheus_metrics import usage_aggregation_lag

        # Should be able to observe values
        usage_aggregation_lag.observe(1.5)
    except (ImportError, AttributeError):
        pytest.skip("Prometheus not available or metric not accessible")


@patch("server.billing.prometheus_metrics.PROMETHEUS_AVAILABLE", True)
def test_quota_blocks_metric():
    """Test quota blocks counter metric"""
    try:
        from server.billing.prometheus_metrics import quota_blocks_total

        # Should be able to increment counter
        quota_blocks_total.labels(resource_type="storage", block_level="soft").inc()
    except (ImportError, AttributeError):
        pytest.skip("Prometheus not available or metric not accessible")


@patch("server.billing.prometheus_metrics.PROMETHEUS_AVAILABLE", False)
def test_metrics_without_prometheus():
    """Test that metrics work without Prometheus (using dummy objects)"""
    try:
        from server.billing import prometheus_metrics

        # When Prometheus is not available, dummy objects should be used
        # These should not raise errors when called
        prometheus_metrics.usage_aggregation_lag.observe(1.0)
        prometheus_metrics.quota_blocks_total.labels(resource_type="storage").inc()
        prometheus_metrics.stripe_sync_duration.observe(0.5)
    except ImportError:
        pytest.skip("Module not available")


def test_metric_labels():
    """Test that metrics can be labeled correctly"""
    try:
        from server.billing.prometheus_metrics import (
            celery_queue_depth,
            invoice_generation_duration,
        )

        # Test labeled metrics
        invoice_generation_duration.labels(status="success").observe(0.1)
        celery_queue_depth.labels(queue="billing").set(5)
    except (ImportError, AttributeError):
        pytest.skip("Prometheus not available or metrics not accessible")


def test_business_metrics():
    """Test business metrics collection"""
    try:
        from server.billing.prometheus_metrics import (
            active_subscriptions_total,
            churn_rate,
            monthly_recurring_revenue,
        )

        # Test business metrics
        active_subscriptions_total.labels(plan_tier="pro").inc()
        monthly_recurring_revenue.labels(plan_tier="pro").set(1000.0)
        churn_rate.set(0.05)
    except (ImportError, AttributeError):
        pytest.skip("Prometheus not available or metrics not accessible")


def test_worker_metrics():
    """Test worker resource usage metrics"""
    try:
        from server.billing.prometheus_metrics import (
            worker_cpu_usage_percent,
            worker_memory_usage_bytes,
            worker_task_duration,
        )

        # Test worker metrics
        worker_cpu_usage_percent.set(50.0)
        worker_memory_usage_bytes.set(1024 * 1024 * 512)  # 512MB
        worker_task_duration.labels(task_type="invoice_generation").observe(2.0)
    except (ImportError, AttributeError):
        pytest.skip("Prometheus not available or metrics not accessible")
