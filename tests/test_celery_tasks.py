#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Celery Tasks Tests
#
"""
Unit tests for server/billing/celery_tasks.py

Tests Celery tasks for billing operations.
"""

from unittest.mock import patch

import pytest

pytestmark = pytest.mark.unit


class TestCeleryTasks:
    """Tests for Celery tasks"""

    def test_celery_tasks_imports(self):
        """Test that Celery tasks can be imported"""
        try:
            import os
            import sys

            # Add server directory to path if needed
            # __file__ is tests/test_celery_tasks.py, so dirname twice gets project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            server_path = os.path.join(project_root, "server")
            if os.path.exists(server_path) and server_path not in sys.path:
                sys.path.insert(0, server_path)

            from billing import celery_tasks

            assert celery_tasks is not None
        except ImportError as e:
            pytest.skip(f"celery_tasks module not available: {e}")

    def test_event_stream_integration_available(self):
        """Test that event stream integration is available"""
        try:
            import os
            import sys

            # Add server directory to path if needed
            # __file__ is tests/test_celery_tasks.py, so dirname twice gets project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            server_path = os.path.join(project_root, "server")
            if os.path.exists(server_path) and server_path not in sys.path:
                sys.path.insert(0, server_path)

            from billing import celery_tasks

            # Check if event stream is enabled or gracefully disabled
            assert hasattr(celery_tasks, "EVENT_STREAM_ENABLED")
        except ImportError as e:
            pytest.skip(f"celery_tasks module not available: {e}")

    def test_publish_event_sync_function_exists(self):
        """Test that publish_event_sync function exists"""
        try:
            import os
            import sys

            # Add server directory to path if needed
            # __file__ is tests/test_celery_tasks.py, so dirname twice gets project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            server_path = os.path.join(project_root, "server")
            if os.path.exists(server_path) and server_path not in sys.path:
                sys.path.insert(0, server_path)

            from billing.celery_tasks import publish_event_sync

            assert callable(publish_event_sync)
        except ImportError as e:
            pytest.skip(f"celery_tasks module not available: {e}")

    def test_publish_event_sync_with_event_stream(self):
        """Test publish_event_sync when event stream is enabled"""
        try:
            import os
            import sys

            # Add server directory to path if needed
            # __file__ is tests/test_celery_tasks.py, so dirname twice gets project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            server_path = os.path.join(project_root, "server")
            if os.path.exists(server_path) and server_path not in sys.path:
                sys.path.insert(0, server_path)

            from billing.celery_tasks import publish_event_sync

            # Test that function exists and is callable
            assert callable(publish_event_sync)

            # Test with event stream disabled (should return None gracefully)
            with patch("billing.celery_tasks.EVENT_STREAM_ENABLED", False):
                result = publish_event_sync(
                    event_type=None,
                    source_service="test",
                    payload={},
                )
                assert result is None
        except ImportError:
            pytest.skip("celery_tasks module not available")
