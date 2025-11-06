#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing Models Package
# Developer D - January 2025

"""
SPEC-147 Billing Models Package

Unified polymorphic billing architecture supporting Organizations, Teams, and Users.
"""

# Export all SPEC-147 billing models
from .models import (  # Enums; Core Models
    AccountStatus,
    AccountType,
    AuditLog,
    BillingAccount,
    BillingEvent,
    BillingPeriod,
    BillingPeriodStatus,
    BlockLevel,
    CreditBalance,
    DiscountApplication,
    DiscountCode,
    Invoice,
    InvoiceLineItem,
    InvoiceStatus,
    PaymentConfig,
    PaymentTransfer,
    PlanTier,
    PricingTier,
    QuotaBlock,
    ResourceType,
    StripeCustomer,
    StripeInvoice,
    StripeSubscription,
    TransferStatus,
    UsageEvent,
    UsageQuota,
)

# Export Redis cache
from .redis_cache import UsageQuotaCache

# Export usage metering services
from .usage_metering import (
    UsageDimension,
    UsageMeteringService,
    calculate_storage_gb_month,
    calculate_tokens_from_text,
    create_idempotency_key,
)

# Export middleware (optional - only if FastAPI available)
try:
    from .usage_middleware import UsageMeteringMiddleware

    MIDDLEWARE_AVAILABLE = True
except ImportError:
    # FastAPI not available - middleware not needed for model-only imports
    UsageMeteringMiddleware = None  # type: ignore
    MIDDLEWARE_AVAILABLE = False

__all__ = [
    # Enums
    "AccountType",
    "AccountStatus",
    "PlanTier",
    "ResourceType",
    "BlockLevel",
    "TransferStatus",
    "InvoiceStatus",
    "BillingPeriodStatus",
    # Core Models
    "BillingAccount",
    "PricingTier",
    "UsageQuota",
    "BillingPeriod",
    "UsageEvent",
    "QuotaBlock",
    "PaymentConfig",
    "PaymentTransfer",
    "Invoice",
    "InvoiceLineItem",
    "CreditBalance",
    "DiscountCode",
    "DiscountApplication",
    "StripeCustomer",
    "StripeSubscription",
    "StripeInvoice",
    "AuditLog",
    "BillingEvent",
    # Usage Metering
    "UsageMeteringService",
    "UsageDimension",
    "calculate_storage_gb_month",
    "calculate_tokens_from_text",
    "create_idempotency_key",
    # Redis Cache
    "UsageQuotaCache",
    # Middleware (optional)
    "UsageMeteringMiddleware",
    # Quota Enforcement
    "QuotaEnforcementService",
    "QuotaStatus",
    # Quota Notifications
    "QuotaNotificationService",
    # Stripe Integration
    "StripeService",
    # Payment Transfer
    "PaymentTransferService",
    # Celery
    "celery_app",
    # Prometheus Metrics
    "prometheus_metrics",
    # Leader Election
    "LeaderElection",
    "LeaderElectionBeatScheduler",
    # Distributed Locking
    "DistributedLock",
    "with_idempotency_lock",
    # Archival
    "MetricsArchivalService",
]
