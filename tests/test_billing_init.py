#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing Package Init Tests
#
"""
Unit tests for server/billing/__init__.py

Tests that the billing package exports are correct and all modules can be imported.
"""

import pytest

pytestmark = pytest.mark.unit


def test_billing_package_imports():
    """Test that core billing package exports can be imported."""
    from server.billing import AccountType, BillingAccount, Invoice, UsageQuota

    assert AccountType is not None
    assert BillingAccount is not None
    assert UsageQuota is not None
    assert Invoice is not None


def test_billing_package_all_defined():
    """Test that billing package __all__ is properly defined."""
    import server.billing as billing_pkg

    assert hasattr(billing_pkg, "__all__")
    assert isinstance(billing_pkg.__all__, list)
    assert len(billing_pkg.__all__) > 0

    # Verify key exports are in __all__
    expected_exports = [
        "AccountType",
        "BillingAccount",
        "Invoice",
        "UsageQuota",
        "UsageMeteringService",
        "UsageQuotaCache",
    ]
    for export in expected_exports:
        assert export in billing_pkg.__all__, f"{export} should be in __all__"


def test_billing_enum_imports():
    """Test that billing enums can be imported."""
    from server.billing import (
        AccountStatus,
        AccountType,
        BlockLevel,
        InvoiceStatus,
        PlanTier,
        ResourceType,
        TransferStatus,
    )

    assert AccountStatus is not None
    assert AccountType is not None
    assert BlockLevel is not None
    assert InvoiceStatus is not None
    assert PlanTier is not None
    assert ResourceType is not None
    assert TransferStatus is not None


def test_billing_service_imports():
    """Test that billing services can be imported."""
    from server.billing import UsageMeteringService, UsageQuotaCache

    assert UsageMeteringService is not None
    assert UsageQuotaCache is not None


def test_billing_models_imports():
    """Test that billing models can be imported."""
    from server.billing import (
        BillingAccount,
        BillingEvent,
        BillingPeriod,
        CreditBalance,
        DiscountCode,
        Invoice,
        InvoiceLineItem,
        PaymentConfig,
        PaymentTransfer,
        PricingTier,
        QuotaBlock,
        StripeCustomer,
        StripeInvoice,
        StripeSubscription,
        UsageEvent,
        UsageQuota,
    )

    assert BillingAccount is not None
    assert BillingEvent is not None
    assert BillingPeriod is not None
    assert CreditBalance is not None
    assert DiscountCode is not None
    assert Invoice is not None
    assert InvoiceLineItem is not None
    assert PaymentConfig is not None
    assert PaymentTransfer is not None
    assert PricingTier is not None
    assert QuotaBlock is not None
    assert StripeCustomer is not None
    assert StripeInvoice is not None
    assert StripeSubscription is not None
    assert UsageEvent is not None
    assert UsageQuota is not None
