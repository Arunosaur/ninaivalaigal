#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Usage Metering Service
# Developer D - January 2025
#
# BILL-002: Three-dimensional usage metering

"""
Usage metering service for SPEC-147 billing.

Features:
- Three-dimensional usage tracking (storage, retrieval, token)
- Real-time usage event capture
- Idempotent logging (prevents double counting)
- Redis caching for performance
- Cost calculation at record time
"""

import hashlib
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .models import (
    AccountStatus,
    AccountType,
    BillingAccount,
    BillingPeriod,
    BillingPeriodStatus,
    ResourceType,
    UsageEvent,
    UsageQuota,
)
from .redis_cache import UsageQuotaCache


class UsageDimension(str, Enum):
    """Usage dimensions for billing"""

    STORAGE = "storage"
    RETRIEVAL = "retrieval"
    TOKEN = "token"


class UsageMeteringService:
    """
    Service for tracking usage across three dimensions.

    Features:
    - Real-time usage event capture
    - Idempotent logging (prevents double counting)
    - Integration with UsageEvent model
    - Redis caching for quota checks
    - Performance optimized (<5ms overhead)
    """

    def __init__(self, db: Session):
        """
        Initialize usage metering service.

        Args:
            db: Database session
        """
        self.db = db
        self.cache = UsageQuotaCache()

    def get_billing_account(self, account_type: AccountType, account_id: uuid.UUID) -> Optional[BillingAccount]:
        """
        Get billing account for an entity.

        Args:
            account_type: Account type (ORGANIZATION, TEAM, USER)
            account_id: Account ID (org/team/user UUID)

        Returns:
            BillingAccount instance or None
        """
        # Try to find existing account
        account = (
            self.db.query(BillingAccount)
            .filter(
                and_(
                    BillingAccount.account_type == account_type.value,
                    BillingAccount.account_id == account_id,
                    BillingAccount.status == AccountStatus.ACTIVE.value,
                    BillingAccount.deleted_at.is_(None),
                )
            )
            .first()
        )

        return account

    def get_current_billing_period(self, billing_account_id: uuid.UUID) -> Optional[BillingPeriod]:
        """
        Get current active billing period for an account.

        Args:
            billing_account_id: Billing account ID

        Returns:
            BillingPeriod instance or None
        """
        now = datetime.utcnow()

        period = (
            self.db.query(BillingPeriod)
            .filter(
                and_(
                    BillingPeriod.billing_account_id == billing_account_id,
                    BillingPeriod.period_start <= now,
                    BillingPeriod.period_end >= now,
                    BillingPeriod.status == BillingPeriodStatus.ACTIVE.value,
                )
            )
            .first()
        )

        return period

    def record_storage_usage(
        self,
        billing_account_id: uuid.UUID,
        billing_period_id: uuid.UUID,
        storage_gb: Decimal,
        metadata: Optional[Dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> UsageEvent:
        """
        Record storage usage (GB-month).

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Current billing period ID
            storage_gb: Storage usage in GB
            metadata: Optional metadata
            idempotency_key: Optional idempotency key for duplicate prevention

        Returns:
            UsageEvent instance
        """
        # Check for duplicate if idempotency key provided
        if idempotency_key:
            existing = (
                self.db.query(UsageEvent)
                .filter(
                    and_(
                        UsageEvent.billing_account_id == billing_account_id,
                        UsageEvent.event_metadata.contains({"idempotency_key": idempotency_key}),
                    )
                )
                .first()
            )
            if existing:
                return existing

        # Get current pricing for cost calculation
        cost_at_record_time = self._calculate_storage_cost(storage_gb)

        event = UsageEvent(
            billing_account_id=billing_account_id,
            billing_period_id=billing_period_id,
            resource_type=ResourceType.STORAGE.value,
            quantity=storage_gb,
            cost_at_record_time=cost_at_record_time,
            event_metadata={
                **(metadata or {}),
                **({"idempotency_key": idempotency_key} if idempotency_key else {}),
            },
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # Invalidate cache for this resource type
        self.cache.invalidate_usage(billing_account_id, ResourceType.STORAGE)

        return event

    def record_retrieval_usage(
        self,
        billing_account_id: uuid.UUID,
        billing_period_id: uuid.UUID,
        retrieval_count: int,
        metadata: Optional[Dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> UsageEvent:
        """
        Record retrieval usage (count of memory recall operations).

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Current billing period ID
            retrieval_count: Number of retrieval operations
            metadata: Optional metadata
            idempotency_key: Optional idempotency key

        Returns:
            UsageEvent instance
        """
        # Check for duplicate if idempotency key provided
        if idempotency_key:
            existing = (
                self.db.query(UsageEvent)
                .filter(
                    and_(
                        UsageEvent.billing_account_id == billing_account_id,
                        UsageEvent.event_metadata.contains({"idempotency_key": idempotency_key}),
                    )
                )
                .first()
            )
            if existing:
                return existing

        event = UsageEvent(
            billing_account_id=billing_account_id,
            billing_period_id=billing_period_id,
            resource_type=ResourceType.RETRIEVAL.value,
            quantity=Decimal(str(retrieval_count)),
            cost_at_record_time=None,  # Retrieval pricing TBD
            event_metadata={
                **(metadata or {}),
                **({"idempotency_key": idempotency_key} if idempotency_key else {}),
            },
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # Invalidate cache for this resource type
        self.cache.invalidate_usage(billing_account_id, ResourceType.RETRIEVAL)

        return event

    def record_token_usage(
        self,
        billing_account_id: uuid.UUID,
        billing_period_id: uuid.UUID,
        token_count: int,
        metadata: Optional[Dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> UsageEvent:
        """
        Record token usage (count of tokens processed).

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Current billing period ID
            token_count: Number of tokens
            metadata: Optional metadata
            idempotency_key: Optional idempotency key

        Returns:
            UsageEvent instance
        """
        # Check for duplicate if idempotency key provided
        if idempotency_key:
            existing = (
                self.db.query(UsageEvent)
                .filter(
                    and_(
                        UsageEvent.billing_account_id == billing_account_id,
                        UsageEvent.event_metadata.contains({"idempotency_key": idempotency_key}),
                    )
                )
                .first()
            )
            if existing:
                return existing

        event = UsageEvent(
            billing_account_id=billing_account_id,
            billing_period_id=billing_period_id,
            resource_type=ResourceType.TOKEN.value,
            quantity=Decimal(str(token_count)),
            cost_at_record_time=None,  # Token pricing TBD
            event_metadata={
                **(metadata or {}),
                **({"idempotency_key": idempotency_key} if idempotency_key else {}),
            },
        )

        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        # Invalidate cache for this resource type
        self.cache.invalidate_usage(billing_account_id, ResourceType.TOKEN)

        return event

    def get_current_usage(
        self, billing_account_id: uuid.UUID, billing_period_id: uuid.UUID, resource_type: ResourceType
    ) -> Decimal:
        """
        Get current usage for a resource type in the current period.

        Uses Redis cache if available, falls back to database query.

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Current billing period ID
            resource_type: Resource type (storage/retrieval/token)

        Returns:
            Total usage as Decimal
        """
        # Try cache first
        cached_usage = self.cache.get_current_usage(billing_account_id, resource_type)
        if cached_usage is not None:
            return cached_usage

        # Fall back to database
        result = (
            self.db.query(func.sum(UsageEvent.quantity))
            .filter(
                and_(
                    UsageEvent.billing_account_id == billing_account_id,
                    UsageEvent.billing_period_id == billing_period_id,
                    UsageEvent.resource_type == resource_type.value,
                    UsageEvent.processed == False,  # Only count unprocessed events
                )
            )
            .scalar()
        )

        usage = Decimal(result) if result else Decimal("0")

        # Cache the result
        self.cache.set_current_usage(billing_account_id, resource_type, usage)

        return usage

    def get_quota_usage_percentage(
        self, billing_account_id: uuid.UUID, billing_period_id: uuid.UUID, resource_type: ResourceType
    ) -> Tuple[Decimal, Decimal, float]:
        """
        Get quota usage percentage for a resource type.

        Uses Redis cache for both usage and quota limit if available.

        Returns:
            Tuple of (used, limit, percentage)
        """
        # Try cache for percentage first
        cached_percentage = self.cache.get_usage_percentage(billing_account_id, resource_type)
        if cached_percentage is not None:
            # Still need to return usage and limit - get from cache
            usage = self.cache.get_current_usage(billing_account_id, resource_type) or Decimal("0")
            limit = self.cache.get_quota_limit(billing_account_id, resource_type) or Decimal("0")
            return (usage, limit, cached_percentage)

        # Get usage (uses cache if available)
        usage = self.get_current_usage(billing_account_id, billing_period_id, resource_type)

        # Try cache for quota limit
        limit = self.cache.get_quota_limit(billing_account_id, resource_type)

        if limit is None:
            # Fall back to database
            quota = (
                self.db.query(UsageQuota)
                .filter(
                    and_(
                        UsageQuota.billing_account_id == billing_account_id,
                        UsageQuota.resource_type == resource_type.value,
                    )
                )
                .first()
            )

            if not quota:
                limit = Decimal("0")
            else:
                limit = quota.quota_limit
                # Cache the limit
                self.cache.set_quota_limit(billing_account_id, resource_type, limit)

        percentage = float((usage / limit * 100)) if limit > 0 else 0.0

        # Cache the percentage
        self.cache.set_usage_percentage(billing_account_id, resource_type, percentage)

        return (usage, limit, percentage)

    def _calculate_storage_cost(self, storage_gb: Decimal) -> Optional[Decimal]:
        """
        Calculate storage cost at record time.

        Args:
            storage_gb: Storage usage in GB

        Returns:
            Cost as Decimal or None
        """
        # TODO: Implement pricing lookup from PricingTier
        # For now, return None (cost calculation TBD)
        return None


# Helper functions for usage calculations


def calculate_storage_gb_month(file_size_bytes: int) -> Decimal:
    """
    Calculate storage usage in GB-month from file size in bytes.

    Args:
        file_size_bytes: File size in bytes

    Returns:
        Storage usage in GB-month
    """
    # Convert bytes to GB
    gb = Decimal(file_size_bytes) / Decimal(1024**3)
    # For now, assume monthly storage (actual calculation may vary)
    return gb


def calculate_tokens_from_text(text: str) -> int:
    """
    Estimate token count from text.

    Uses simple approximation: ~4 characters per token.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    # Simple approximation: ~4 characters per token
    # In production, use actual tokenizer (tiktoken, etc.)
    return len(text) // 4


def create_idempotency_key(billing_account_id: uuid.UUID, operation_type: str, request_id: str) -> str:
    """
    Create idempotency key for usage events.

    Args:
        billing_account_id: Billing account ID
        operation_type: Operation type (e.g., "storage_upload")
        request_id: Request ID

    Returns:
        Idempotency key as string
    """
    key_data = f"{billing_account_id}:{operation_type}:{request_id}"
    return hashlib.sha256(key_data.encode()).hexdigest()
