#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Celery Application Configuration
# Developer D - January 2025
#
# BILL-007: Celery Worker Architecture

"""
Celery application configuration for SPEC-147 billing system.

Provides async task processing for:
- Usage aggregation
- Stripe synchronization
- Invoice generation
- Quota notifications
- Payment transfer processing
"""

import os

from celery import Celery
from celery.schedules import crontab

# Get Redis URL from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

# Create Celery app
celery_app = Celery(
    "ninaivalaigal_billing",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "server.billing.celery_tasks",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task routing
    task_routes={
        "server.billing.celery_tasks.aggregate_usage_metrics": {"queue": "billing"},
        "server.billing.celery_tasks.sync_stripe_subscriptions": {"queue": "stripe"},
        "server.billing.celery_tasks.send_quota_warnings": {"queue": "notify"},
        "server.billing.celery_tasks.generate_monthly_invoices": {"queue": "billing"},
        "server.billing.celery_tasks.process_payment_transfers": {"queue": "billing"},
        "server.billing.celery_tasks.process_grace_periods": {"queue": "billing"},
        "server.billing.celery_tasks.archive_old_metrics": {"queue": "billing"},
        "server.billing.celery_tasks.retry_failed_payment": {"queue": "billing"},
        "server.billing.celery_tasks.generate_weekly_cost_summary": {"queue": "billing"},
    },
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    # Retry configuration
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
    # Result backend
    result_expires=3600,  # 1 hour
    # Beat schedule
    beat_schedule={
        "aggregate-usage-hourly": {
            "task": "server.billing.celery_tasks.aggregate_usage_metrics",
            "schedule": crontab(minute=0),  # Every hour at :00
            "options": {"queue": "billing"},
        },
        "sync-stripe-hourly": {
            "task": "server.billing.celery_tasks.sync_stripe_subscriptions",
            "schedule": crontab(minute=30),  # Every hour at :30
            "options": {"queue": "stripe"},
        },
        "generate-invoices-monthly": {
            "task": "server.billing.celery_tasks.generate_monthly_invoices",
            "schedule": crontab(hour=2, minute=0, day_of_month=1),  # 1st of month at 2 AM
            "options": {"queue": "billing"},
        },
        "process-grace-periods-daily": {
            "task": "server.billing.celery_tasks.process_grace_periods",
            "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
            "options": {"queue": "billing"},
        },
        "send-quota-warnings-daily": {
            "task": "server.billing.celery_tasks.send_quota_warnings",
            "schedule": crontab(hour=9, minute=0),  # Daily at 9 AM
            "options": {"queue": "notify"},
        },
        "archive-old-metrics-daily": {
            "task": "server.billing.celery_tasks.archive_old_metrics",
            "schedule": crontab(hour=4, minute=0),  # Daily at 4 AM (after invoice generation at 2 AM)
            "options": {"queue": "billing"},
        },
        "generate-weekly-cost-summary": {
            "task": "server.billing.celery_tasks.generate_weekly_cost_summary",
            "schedule": crontab(hour=8, minute=0, day_of_week=1),  # Every Monday at 8 AM
            "options": {"queue": "billing"},
        },
    },
    # Queue configuration
    task_default_queue="billing",
    task_default_exchange="billing",
    task_default_exchange_type="direct",
    task_default_routing_key="billing",
    # Worker configuration
    worker_hijack_root_logger=False,
    worker_log_format="[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    worker_task_log_format="[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    # Health checks
    worker_send_task_events=True,
    worker_timer_precision=1.0,
    # Graceful shutdown
    worker_disable_rate_limits=False,
    worker_enable_remote_control=True,
    # Memory leak prevention
    worker_max_memory_per_child=200000,  # 200MB per child process
)

# Import tasks after app configuration
from . import celery_tasks  # noqa: E402, F401
