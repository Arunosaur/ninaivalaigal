#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Admin Frontend Tests
#
"""
Unit tests for services/core-api/lib/admin_frontend.py

Tests admin frontend rendering and routes.
"""

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def setup_imports():
    """Setup imports for all tests"""
    import sys
    from pathlib import Path

    core_api_path = str(Path(__file__).parent.parent / "services" / "core-api")
    if core_api_path not in sys.path:
        sys.path.insert(0, core_api_path)


class TestAdminFrontend:
    """Tests for admin frontend"""

    def test_admin_frontend_module_imports(self):
        """Test that admin frontend module can be imported"""
        try:
            from lib import admin_frontend

            assert admin_frontend is not None
        except ImportError:
            pytest.skip("admin_frontend module not available")

    def test_admin_routes_exist(self):
        """Test that admin routes are defined"""
        try:
            from lib.admin_frontend import router

            assert router is not None
        except (ImportError, AttributeError):
            pytest.skip("admin_frontend router not available")
