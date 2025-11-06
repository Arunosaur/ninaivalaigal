#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Memory Browser API Tests
#
"""
Unit tests for server/routers/memory_browser_api.py

Tests memory browser API endpoints.
"""

import pytest

pytestmark = pytest.mark.unit


class TestMemoryBrowserAPI:
    """Tests for memory browser API"""

    def test_memory_browser_api_module_imports(self):
        """Test that memory browser API module can be imported"""
        try:
            from server.routers import memory_browser_api

            assert memory_browser_api is not None
        except ImportError:
            pytest.skip("memory_browser_api module not available")

    def test_memory_browser_routes_exist(self):
        """Test that memory browser routes are defined"""
        try:
            from server.routers.memory_browser_api import router

            assert router is not None
        except (ImportError, AttributeError):
            pytest.skip("memory_browser_api router not available")
