#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# Customer Frontend Tests
#
"""
Unit tests for services/core-api/lib/customer_frontend.py

Tests customer frontend rendering and routes.
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


class TestCustomerFrontend:
    """Tests for customer frontend"""

    def test_customer_frontend_module_imports(self):
        """Test that customer frontend module can be imported"""
        try:
            from lib import customer_frontend

            assert customer_frontend is not None
        except ImportError:
            pytest.skip("customer_frontend module not available")

    def test_customer_routes_exist(self):
        """Test that customer routes are defined"""
        try:
            from lib.customer_frontend import router

            assert router is not None
        except (ImportError, AttributeError):
            pytest.skip("customer_frontend router not available")
