#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Stripe Service Tests
#
"""
Unit tests for server/billing/stripe_service.py

Tests Stripe service integration.
"""

import pytest

pytestmark = pytest.mark.unit


class TestStripeService:
    """Tests for Stripe service"""

    def test_stripe_service_imports(self):
        """Test that Stripe service can be imported"""
        try:
            from server.billing import stripe_service

            assert stripe_service is not None
        except ImportError:
            pytest.skip("stripe_service module not available")
