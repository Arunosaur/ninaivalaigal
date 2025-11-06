#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Prometheus Metrics
# Developer D - January 2025
#
# BILL-010: Prometheus Metrics & Monitoring

"""
Prometheus metrics for SPEC-147 billing system.

Provides metrics for:
- Usage aggregation lag
- Quota block metrics
- Stripe sync metrics
- Invoice generation metrics
- Celery queue depth
- Worker resource usage
- Business metrics
"""

try:
    from prometheus_client import Counter, Gauge, Histogram, Summary

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

    # Create dummy classes for when Prometheus is not available
    class Counter:
        def __init__(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

    class Histogram:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

    class Gauge:
        def __init__(self, *args, **kwargs):
            pass

        def set(self, *args, **kwargs):
            pass

        def inc(self, *args, **kwargs):
            pass

        def dec(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self

    class Summary:
        def __init__(self, *args, **kwargs):
            pass

        def observe(self, *args, **kwargs):
            pass

        def labels(self, *args, **kwargs):
            return self


# Usage Metrics
usage_aggregation_lag = Histogram(
    "billing_usage_aggregation_lag_seconds",
    "Time lag for usage aggregation",
    ["resource_type"],
    buckets=[1, 5, 10, 30, 60, 300, 600, 3600],
)

usage_events_total = Counter(
    "billing_usage_events_total", "Total usage events recorded", ["resource_type", "account_type"]
)

usage_quantity = Summary("billing_usage_quantity", "Usage quantity recorded", ["resource_type"])

# Quota Metrics
quota_blocks_total = Counter(
    "billing_quota_blocks_total", "Total quota blocks created", ["block_level", "resource_type"]
)

quota_blocks_active = Gauge("billing_quota_blocks_active", "Active quota blocks", ["block_level", "resource_type"])

quota_usage_percentage = Gauge(
    "billing_quota_usage_percentage", "Quota usage percentage", ["billing_account_id", "resource_type"]
)

# Stripe Metrics
stripe_sync_duration = Histogram(
    "billing_stripe_sync_duration_seconds", "Stripe sync duration", ["sync_type"], buckets=[1, 5, 10, 30, 60, 300]
)

stripe_sync_errors_total = Counter(
    "billing_stripe_sync_errors_total", "Stripe sync errors", ["error_type", "sync_type"]
)

stripe_sync_success_total = Counter("billing_stripe_sync_success_total", "Stripe sync successes", ["sync_type"])

# Invoice Metrics
invoice_generation_duration = Histogram(
    "billing_invoice_generation_duration_seconds", "Invoice generation duration", buckets=[1, 5, 10, 30, 60, 300]
)

invoice_generation_total = Counter("billing_invoice_generation_total", "Total invoices generated", ["status"])

invoice_amount = Summary("billing_invoice_amount", "Invoice amounts", ["currency"])

# Celery Queue Metrics
celery_queue_depth = Gauge("billing_celery_queue_depth", "Celery queue depth", ["queue_name"])

celery_task_duration = Histogram(
    "billing_celery_task_duration_seconds",
    "Celery task duration",
    ["task_name", "queue_name"],
    buckets=[1, 5, 10, 30, 60, 300, 600],
)

celery_task_errors_total = Counter(
    "billing_celery_task_errors_total", "Celery task errors", ["task_name", "queue_name", "error_type"]
)

celery_task_success_total = Counter(
    "billing_celery_task_success_total", "Celery task successes", ["task_name", "queue_name"]
)

# Worker Metrics
worker_memory_usage = Gauge("billing_worker_memory_usage_bytes", "Worker memory usage", ["worker_name"])

worker_cpu_usage = Gauge("billing_worker_cpu_usage_percent", "Worker CPU usage", ["worker_name"])

# Business Metrics
billing_accounts_total = Gauge(
    "billing_accounts_total", "Total billing accounts", ["account_type", "plan_tier", "status"]
)

active_billing_periods = Gauge("billing_active_periods_total", "Active billing periods")

revenue_total = Summary("billing_revenue_total", "Total revenue", ["currency"])

# Payment Transfer Metrics
payment_transfers_total = Counter(
    "billing_payment_transfers_total", "Payment transfers processed", ["status", "reason"]
)

grace_periods_active = Gauge("billing_grace_periods_active", "Active grace periods")

grace_period_days_remaining = Gauge(
    "billing_grace_period_days_remaining", "Days remaining in grace period", ["billing_account_id"]
)


def record_usage_event(resource_type: str, account_type: str, quantity: float):
    """Record usage event metrics"""
    if PROMETHEUS_AVAILABLE:
        usage_events_total.labels(resource_type=resource_type, account_type=account_type).inc()
        usage_quantity.labels(resource_type=resource_type).observe(quantity)


def record_quota_block(block_level: str, resource_type: str):
    """Record quota block creation"""
    if PROMETHEUS_AVAILABLE:
        quota_blocks_total.labels(block_level=block_level, resource_type=resource_type).inc()
        quota_blocks_active.labels(block_level=block_level, resource_type=resource_type).inc()


def remove_quota_block(block_level: str, resource_type: str):
    """Record quota block removal"""
    if PROMETHEUS_AVAILABLE:
        quota_blocks_active.labels(block_level=block_level, resource_type=resource_type).dec()


def record_stripe_sync(sync_type: str, duration: float, success: bool, error_type: str = None):
    """Record Stripe sync metrics"""
    if PROMETHEUS_AVAILABLE:
        stripe_sync_duration.labels(sync_type=sync_type).observe(duration)
        if success:
            stripe_sync_success_total.labels(sync_type=sync_type).inc()
        else:
            stripe_sync_errors_total.labels(error_type=error_type or "unknown", sync_type=sync_type).inc()


def record_invoice_generation(duration: float, status: str, amount: float = None, currency: str = "USD"):
    """Record invoice generation metrics"""
    if PROMETHEUS_AVAILABLE:
        invoice_generation_duration.observe(duration)
        invoice_generation_total.labels(status=status).inc()
        if amount is not None:
            invoice_amount.labels(currency=currency).observe(amount)


def record_celery_task(task_name: str, queue_name: str, duration: float, success: bool, error_type: str = None):
    """Record Celery task metrics"""
    if PROMETHEUS_AVAILABLE:
        celery_task_duration.labels(task_name=task_name, queue_name=queue_name).observe(duration)
        if success:
            celery_task_success_total.labels(task_name=task_name, queue_name=queue_name).inc()
        else:
            celery_task_errors_total.labels(
                task_name=task_name, queue_name=queue_name, error_type=error_type or "unknown"
            ).inc()


def update_queue_depth(queue_name: str, depth: int):
    """Update Celery queue depth"""
    if PROMETHEUS_AVAILABLE:
        celery_queue_depth.labels(queue_name=queue_name).set(depth)


def update_billing_accounts_metric(account_type: str, plan_tier: str, status: str, count: int):
    """Update billing accounts metric"""
    if PROMETHEUS_AVAILABLE:
        billing_accounts_total.labels(account_type=account_type, plan_tier=plan_tier, status=status).set(count)


def record_payment_transfer(status: str, reason: str):
    """Record payment transfer metrics"""
    if PROMETHEUS_AVAILABLE:
        payment_transfers_total.labels(status=status, reason=reason).inc()
