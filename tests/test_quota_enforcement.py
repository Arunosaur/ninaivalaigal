#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Quota Enforcement Tests
# Developer D - January 2025

"""
Unit tests for SPEC-147 quota enforcement system.

Tests soft/hard blocking, notifications, and graceful degradation.
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import DDL, event
from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session

from server.billing.models import (
    AccountStatus,
    AuditLog,
    Base,
    BillingAccount,
    BillingPeriod,
    BillingPeriodStatus,
    BlockLevel,
    PlanTier,
    QuotaBlock,
    ResourceType,
    UsageQuota,
)
from server.billing.quota_enforcement import QuotaEnforcementService, QuotaStatus
from server.billing.quota_notifications import QuotaNotificationService
from server.billing.usage_metering import UsageMeteringService

pytestmark = pytest.mark.unit


@pytest.fixture
def sample_team_id():
    """Generate a sample team ID for testing"""
    return uuid.uuid4()


@pytest.fixture
def billing_account(db_session, sample_team_id):
    """Create a billing account for testing"""
    account = BillingAccount(
        account_type="team",
        account_id=sample_team_id,
        plan_tier=PlanTier.PRO.value,
        currency="USD",
        status=AccountStatus.ACTIVE.value,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)
    return account


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
def usage_quota(db_session, billing_account):
    """Create a usage quota for testing"""
    now = datetime.utcnow()
    quota = UsageQuota(
        billing_account_id=billing_account.id,
        resource_type=ResourceType.STORAGE.value,
        quota_limit=Decimal("1000"),
        quota_used=Decimal("0"),
        period_start=now,
        period_end=now + timedelta(days=30),
    )
    db_session.add(quota)
    db_session.commit()
    db_session.refresh(quota)
    return quota


@pytest.fixture(autouse=True)
def setup_tables(db_session):
    """Create billing tables before each test"""

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
        # Create all billing tables
        Base.metadata.create_all(bind=db_session.bind)
        yield
    finally:
        # Cleanup after test
        try:
            Base.metadata.drop_all(bind=db_session.bind)
        except Exception:
            pass  # Ignore cleanup errors


@pytest.fixture
def enforcement_service(db_session):
    """Create quota enforcement service"""
    usage_metering = UsageMeteringService(db_session)
    return QuotaEnforcementService(db_session, usage_metering)


class TestQuotaStatus:
    """Tests for quota status checking"""

    def test_quota_status_ok(self, enforcement_service, billing_account, billing_period, usage_quota):
        """Test quota status when usage is OK"""
        status, percentage, block = enforcement_service.check_quota_status(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert status == QuotaStatus.OK
        assert percentage < 75.0
        assert block is None

    def test_quota_status_warning(self, enforcement_service, billing_account, billing_period, usage_quota, db_session):
        """Test quota status when usage exceeds 75%"""
        # Record usage to exceed 75%
        usage_metering = UsageMeteringService(db_session)
        usage_metering.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("800"),  # 80% of 1000 limit
        )

        status, percentage, block = enforcement_service.check_quota_status(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert status == QuotaStatus.WARNING
        assert percentage >= 75.0
        assert percentage < 100.0

    def test_quota_status_blocked(self, enforcement_service, billing_account, billing_period, usage_quota, db_session):
        """Test quota status when usage exceeds 100%"""
        # Record usage to exceed 100%
        usage_metering = UsageMeteringService(db_session)
        usage_metering.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("1100"),  # 110% of 1000 limit
        )

        status, percentage, block = enforcement_service.check_quota_status(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert status == QuotaStatus.BLOCKED
        assert percentage >= 100.0


class TestQuotaEnforcement:
    """Tests for quota enforcement"""

    def test_enforce_quota_ok(self, enforcement_service, billing_account, billing_period):
        """Test quota enforcement when usage is OK"""
        allowed, error = enforcement_service.enforce_quota(billing_account.id, billing_period.id, ResourceType.STORAGE)

        assert allowed is True
        assert error is None

    def test_enforce_quota_blocked(self, enforcement_service, billing_account, billing_period, usage_quota, db_session):
        """Test quota enforcement when usage exceeds 100%"""
        # Record usage to exceed 100%
        usage_metering = UsageMeteringService(db_session)
        usage_metering.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("1100"),
        )

        allowed, error = enforcement_service.enforce_quota(billing_account.id, billing_period.id, ResourceType.STORAGE)

        assert allowed is False
        assert error is not None
        assert "quota" in error.lower() or "exceeded" in error.lower()


class TestQuotaBlocks:
    """Tests for quota block creation"""

    def test_create_soft_block(self, enforcement_service, billing_account, usage_quota):
        """Test creating a soft quota block"""
        block = enforcement_service.create_soft_block(
            billing_account_id=billing_account.id,
            usage_quota_id=usage_quota.id,
            resource_type=ResourceType.STORAGE,
            reason="Usage exceeded 75%",
        )

        assert block.id is not None
        assert block.block_level == BlockLevel.SOFT.value
        assert block.is_active is True
        assert block.reason == "Usage exceeded 75%"

    def test_create_hard_block(self, enforcement_service, billing_account, usage_quota):
        """Test creating a hard quota block"""
        block = enforcement_service.create_hard_block(
            billing_account_id=billing_account.id,
            usage_quota_id=usage_quota.id,
            resource_type=ResourceType.STORAGE,
            reason="Usage exceeded 100%",
            allow_read_operations=True,
        )

        assert block.id is not None
        assert block.block_level == BlockLevel.HARD.value
        assert block.is_active is True
        assert block.event_metadata.get("allow_read_operations") is True

    def test_remove_block(self, enforcement_service, billing_account, usage_quota):
        """Test removing quota blocks"""
        # Create a block
        block = enforcement_service.create_soft_block(
            billing_account_id=billing_account.id,
            usage_quota_id=usage_quota.id,
            resource_type=ResourceType.STORAGE,
            reason="Test block",
        )

        assert block.is_active is True

        # Remove block
        enforcement_service.remove_block(billing_account.id, ResourceType.STORAGE)

        # Verify block is deactivated
        db_session = enforcement_service.db
        db_session.commit()  # Ensure changes are committed
        updated_block = db_session.query(QuotaBlock).filter(QuotaBlock.id == block.id).first()

        assert updated_block is not None
        assert updated_block.is_active is False
        assert updated_block.unblocked_at is not None


class TestQuotaNotifications:
    """Tests for quota notifications"""

    def test_send_soft_warning(self, db_session, billing_account):
        """Test sending soft warning notification"""
        notification_service = QuotaNotificationService(db_session)

        notification_service.send_soft_warning(
            billing_account_id=billing_account.id,
            resource_type=ResourceType.STORAGE,
            usage_percentage=80.0,
            used=800.0,
            limit=1000.0,
        )

        # Verify audit log was created
        audit_log = (
            db_session.query(AuditLog)
            .filter(AuditLog.billing_account_id == billing_account.id, AuditLog.event_type == "quota_warning")
            .first()
        )

        assert audit_log is not None
        assert audit_log.event_data["usage_percentage"] == 80.0

    def test_send_hard_block_notification(self, db_session, billing_account):
        """Test sending hard block notification"""
        notification_service = QuotaNotificationService(db_session)

        notification_service.send_hard_block_notification(
            billing_account_id=billing_account.id,
            resource_type=ResourceType.STORAGE,
            usage_percentage=110.0,
            block_reason="Quota exceeded 100%",
        )

        # Verify audit log was created
        audit_log = (
            db_session.query(AuditLog)
            .filter(AuditLog.billing_account_id == billing_account.id, AuditLog.event_type == "quota_block")
            .first()
        )

        assert audit_log is not None
        assert audit_log.event_data["usage_percentage"] == 110.0


class TestQuotaSummary:
    """Tests for quota summary"""

    def test_get_quota_summary(self, enforcement_service, billing_account, billing_period):
        """Test getting quota summary for all resource types"""
        summary = enforcement_service.get_quota_summary(billing_account.id, billing_period.id)

        assert "storage" in summary
        assert "retrieval" in summary
        assert "token" in summary

        for resource_type, data in summary.items():
            assert "status" in data
            assert "percentage" in data
            assert "used" in data
            assert "limit" in data
            assert "has_block" in data
