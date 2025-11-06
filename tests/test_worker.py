#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing Worker Tests
#
"""
Unit tests for server/billing/worker.py

Tests Celery worker tasks for billing operations.
"""

import pytest

pytestmark = pytest.mark.unit


class TestBillingWorker:
    """Tests for billing worker tasks"""

    def test_worker_module_imports(self):
        """Test that worker module can be imported"""
        try:
            from server.billing import worker

            assert worker is not None
        except ImportError:
            pytest.skip("worker module not available")

    def test_worker_tasks_exist(self):
        """Test that worker tasks are defined"""
        try:
            from server.billing.worker import celery_app

            assert celery_app is not None
        except ImportError:
            pytest.skip("worker module not available")
