#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Usage Metering Service Tests
# Developer D - January 2025

"""
Unit tests for SPEC-147 usage metering service.

Tests three-dimensional usage tracking, Redis caching, and idempotency.
"""

import pytest

pytestmark = pytest.mark.unit
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from server.billing.models import (
    AccountStatus,
    BillingAccount,
    BillingPeriod,
    BillingPeriodStatus,
    PlanTier,
    ResourceType,
    UsageEvent,
    UsageQuota,
)
from server.billing.redis_cache import UsageQuotaCache
from server.billing.usage_metering import (
    AccountType,
    UsageDimension,
    UsageMeteringService,
    calculate_storage_gb_month,
    calculate_tokens_from_text,
    create_idempotency_key,
)


@pytest.fixture
def sample_team_id():
    """Sample team ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def billing_account(db_session, sample_team_id):
    """Create a billing account for testing"""
    account = BillingAccount(
        account_type=AccountType.TEAM.value,
        account_id=sample_team_id,
        plan_tier=PlanTier.PRO.value,
        currency="USD",
        status=AccountStatus.ACTIVE.value,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


@pytest.fixture(autouse=True)
def setup_tables(db_session):
    """Create billing tables before each test"""
    from sqlalchemy import event
    from sqlalchemy.dialects import postgresql, sqlite

    from server.billing.models import Base

    # Map PostgreSQL types to SQLite-compatible types
    @event.listens_for(Base.metadata, "before_create")
    def receive_before_create(target, connection, **kw):
        """Convert PostgreSQL-specific types and constraints for SQLite compatibility"""
        if connection.dialect.name == "sqlite":
            from sqlalchemy import String

            for table in target.tables.values():
                for column in table.columns:
                    # Replace JSONB with JSON
                    if isinstance(column.type, postgresql.JSONB):
                        column.type = sqlite.JSON()
                    # Replace INET with TEXT
                    elif isinstance(column.type, postgresql.INET):
                        column.type = String(255)
                    # Replace CHAR with String
                    elif isinstance(column.type, postgresql.CHAR):
                        column.type = String(column.type.length)

                # Remove constraints that use PostgreSQL-specific functions
                constraints_to_remove = []
                for constraint in list(table.constraints):
                    if hasattr(constraint, "sqltext"):
                        sqltext = str(constraint.sqltext)
                        # Remove constraints using PostgreSQL-specific functions
                        if any(func in sqltext.lower() for func in ["char_length", "gen_random_uuid"]):
                            constraints_to_remove.append(constraint)

                for constraint in constraints_to_remove:
                    table.constraints.remove(constraint)

    try:
        Base.metadata.create_all(bind=db_session.bind)
        yield
    finally:
        try:
            Base.metadata.drop_all(bind=db_session.bind)
        except Exception:
            pass


@pytest.fixture
def billing_period(db_session, billing_account):
    """Create a billing period for testing"""
    now = datetime.utcnow()
    period = BillingPeriod(
        billing_account_id=billing_account.id,
        period_start=now.replace(day=1),
        period_end=(now.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1),
        status=BillingPeriodStatus.ACTIVE.value,
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(period)
    return period


@pytest.fixture
def usage_quotas(db_session, billing_account):
    """Create usage quotas for all three dimensions"""
    now = datetime.utcnow()
    quotas = []

    for resource_type in [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]:
        quota = UsageQuota(
            billing_account_id=billing_account.id,
            resource_type=resource_type.value,
            quota_limit=Decimal("1000"),
            quota_used=Decimal("0"),
            period_start=now,
            period_end=now + timedelta(days=30),
        )
        db_session.add(quota)
        quotas.append(quota)

    db_session.commit()
    for quota in quotas:
        db_session.refresh(quota)
    return quotas


@pytest.fixture
def metering_service(db_session):
    """Create usage metering service"""
    return UsageMeteringService(db_session)


class TestStorageUsageTracking:
    """Tests for storage usage tracking"""

    def test_record_storage_usage(self, metering_service, billing_account, billing_period):
        """Test recording storage usage

        Note: UsageEvent.quantity uses Numeric(20, 0) which stores integers.
        For storage, we typically store GB as integers (rounded), or use a different
        column for decimal precision. For now, testing with integer value.
        """
        storage_gb = Decimal("10")  # Use integer to match Numeric(20, 0) column

        event = metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=storage_gb,
            metadata={"source": "test", "file": "test.pdf"},
        )

        assert event.id is not None
        assert event.resource_type == ResourceType.STORAGE.value
        assert event.quantity == storage_gb
        assert event.billing_account_id == billing_account.id
        assert event.billing_period_id == billing_period.id

    def test_storage_usage_idempotency(self, metering_service, billing_account, billing_period):
        """Test that idempotency keys prevent double counting"""
        idempotency_key = "test-key-123"
        storage_gb = Decimal("5.0")

        # Record first time
        event1 = metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=storage_gb,
            idempotency_key=idempotency_key,
        )

        # Record second time with same key
        event2 = metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=storage_gb,
            idempotency_key=idempotency_key,
        )

        # Should return same event
        assert event1.id == event2.id

        # Verify only one event exists
        events = metering_service.db.query(UsageEvent).filter(UsageEvent.billing_account_id == billing_account.id).all()
        assert len(events) == 1


class TestRetrievalUsageTracking:
    """Tests for retrieval usage tracking"""

    def test_record_retrieval_usage(self, metering_service, billing_account, billing_period):
        """Test recording retrieval usage"""
        event = metering_service.record_retrieval_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            retrieval_count=5,
            metadata={"endpoint": "/memory/search"},
        )

        assert event.id is not None
        assert event.resource_type == ResourceType.RETRIEVAL.value
        assert event.quantity == Decimal("5")

    def test_retrieval_usage_idempotency(self, metering_service, billing_account, billing_period):
        """Test idempotency for retrieval usage"""
        idempotency_key = "retrieval-key-456"

        event1 = metering_service.record_retrieval_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            retrieval_count=1,
            idempotency_key=idempotency_key,
        )

        event2 = metering_service.record_retrieval_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            retrieval_count=1,
            idempotency_key=idempotency_key,
        )

        assert event1.id == event2.id


class TestTokenUsageTracking:
    """Tests for token usage tracking"""

    def test_record_token_usage(self, metering_service, billing_account, billing_period):
        """Test recording token usage"""
        event = metering_service.record_token_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            token_count=1000,
            metadata={"model": "gpt-4"},
        )

        assert event.id is not None
        assert event.resource_type == ResourceType.TOKEN.value
        assert event.quantity == Decimal("1000")

    def test_token_usage_idempotency(self, metering_service, billing_account, billing_period):
        """Test idempotency for token usage"""
        idempotency_key = "token-key-789"

        event1 = metering_service.record_token_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            token_count=500,
            idempotency_key=idempotency_key,
        )

        event2 = metering_service.record_token_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            token_count=500,
            idempotency_key=idempotency_key,
        )

        assert event1.id == event2.id


class TestUsageQueries:
    """Tests for usage query methods"""

    def test_get_current_usage(self, metering_service, billing_account, billing_period):
        """Test getting current usage"""
        # Record some usage
        metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("10"),
        )

        metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("5"),
        )

        # Get current usage
        usage = metering_service.get_current_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            resource_type=ResourceType.STORAGE,
        )

        assert usage == Decimal("15")

    def test_get_quota_usage_percentage(self, metering_service, billing_account, billing_period, usage_quotas):
        """Test getting quota usage percentage"""
        # Record usage
        metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("250"),  # 25% of 1000 limit
        )

        # Get usage percentage
        used, limit, percentage = metering_service.get_quota_usage_percentage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            resource_type=ResourceType.STORAGE,
        )

        assert used == Decimal("250")
        assert limit == Decimal("1000")
        assert percentage == 25.0


class TestHelperFunctions:
    """Tests for helper functions"""

    def test_calculate_storage_gb_month(self):
        """Test storage GB-month calculation"""
        # 1 GB = 1024^3 bytes
        one_gb_bytes = 1024**3

        gb_month = calculate_storage_gb_month(one_gb_bytes)
        assert gb_month == Decimal("1.0")

    def test_calculate_tokens_from_text(self):
        """Test token calculation from text"""
        text = "This is a test sentence with multiple words."
        tokens = calculate_tokens_from_text(text)

        # Should estimate tokens (roughly 4 chars per token)
        assert tokens > 0
        assert tokens <= len(text)

    def test_create_idempotency_key(self):
        """Test idempotency key creation"""
        account_id = uuid.uuid4()
        key = create_idempotency_key(account_id, "storage_upload", "file-123")

        # Should be a SHA256 hash (64 hex characters)
        assert len(key) == 64
        assert all(c in "0123456789abcdef" for c in key)

        # Should be deterministic (same inputs produce same key)
        key2 = create_idempotency_key(account_id, "storage_upload", "file-123")
        assert key == key2

        # Different inputs should produce different keys
        key3 = create_idempotency_key(account_id, "storage_upload", "file-456")
        assert key != key3


class TestRedisCache:
    """Tests for Redis cache integration"""

    def test_cache_disabled_when_redis_unavailable(self):
        """Test that cache gracefully handles Redis unavailability"""
        cache = UsageQuotaCache(redis_client=None)

        # Should not raise exception
        usage = cache.get_current_usage(uuid.uuid4(), ResourceType.STORAGE)
        assert usage is None

    def test_cache_invalidation(self):
        """Test cache invalidation"""
        cache = UsageQuotaCache(redis_client=None)

        # Should not raise exception
        cache.invalidate_usage(uuid.uuid4(), ResourceType.STORAGE)
        cache.invalidate_usage(uuid.uuid4())  # All resource types
