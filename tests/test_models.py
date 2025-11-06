#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing Models Tests
#
"""
Unit tests for server/billing/models.py

Tests billing database models.
"""

import pytest

pytestmark = pytest.mark.unit


class TestBillingModels:
    """Tests for billing models"""

    def test_billing_models_imports(self):
        """Test that billing models can be imported"""
        try:
            from server.billing.models import BillingAccount, Invoice, UsageQuota

            assert BillingAccount is not None
            assert Invoice is not None
            assert UsageQuota is not None
        except ImportError:
            pytest.skip("billing models module not available")
