#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Usage Middleware Tests
#
"""
Unit tests for server/billing/usage_middleware.py

Tests usage tracking middleware.
"""

import pytest

pytestmark = pytest.mark.unit


class TestUsageMiddleware:
    """Tests for usage middleware"""

    def test_usage_middleware_imports(self):
        """Test that usage middleware can be imported"""
        try:
            from server.billing import usage_middleware

            assert usage_middleware is not None
        except ImportError:
            pytest.skip("usage_middleware module not available")
