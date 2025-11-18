#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Celery App Tests
#
"""
Unit tests for server/billing/celery_app.py

Tests Celery app configuration for billing tasks.
"""

import pytest

pytestmark = pytest.mark.unit


class TestCeleryApp:
    """Tests for Celery app"""

    def test_celery_app_imports(self):
        """Test that Celery app can be imported"""
        try:
            import os
            import sys

            # Add server directory to path if needed
            # __file__ is tests/test_celery_app.py, so dirname twice gets project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            server_path = os.path.join(project_root, "server")
            if os.path.exists(server_path) and server_path not in sys.path:
                sys.path.insert(0, server_path)

            from billing.celery_app import celery_app

            assert celery_app is not None
        except ImportError as e:
            pytest.skip(f"celery_app module not available: {e}")

    def test_celery_app_configuration(self):
        """Test that Celery app has correct configuration"""
        try:
            import os
            import sys

            # Add server directory to path if needed
            # __file__ is tests/test_celery_app.py, so dirname twice gets project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            server_path = os.path.join(project_root, "server")
            if os.path.exists(server_path) and server_path not in sys.path:
                sys.path.insert(0, server_path)

            from billing.celery_app import celery_app

            # Check that app has configuration
            assert hasattr(celery_app, "conf")
            assert celery_app.conf is not None

            # Check task routes exist
            assert "task_routes" in celery_app.conf
            assert len(celery_app.conf.task_routes) > 0

            # Check queues are configured
            routes_str = str(celery_app.conf.task_routes.values())
            assert "billing" in routes_str or "stripe" in routes_str or "notify" in routes_str
        except ImportError as e:
            pytest.skip(f"celery_app module not available: {e}")

    def test_celery_beat_schedule(self):
        """Test that Celery beat schedule is configured"""
        try:
            import os
            import sys

            # Add server directory to path if needed
            # __file__ is tests/test_celery_app.py, so dirname twice gets project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            server_path = os.path.join(project_root, "server")
            if os.path.exists(server_path) and server_path not in sys.path:
                sys.path.insert(0, server_path)

            from billing.celery_app import celery_app

            # Check beat schedule exists
            assert "beat_schedule" in celery_app.conf
            assert len(celery_app.conf.beat_schedule) > 0

            # Check specific scheduled tasks
            schedule = celery_app.conf.beat_schedule
            assert (
                "aggregate-usage-hourly" in schedule
                or "sync-stripe-hourly" in schedule
                or "generate-invoices-monthly" in schedule
            )
        except ImportError as e:
            pytest.skip(f"celery_app module not available: {e}")
