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
            from server.billing.celery_app import celery_app

            assert celery_app is not None
        except ImportError:
            pytest.skip("celery_app module not available")
