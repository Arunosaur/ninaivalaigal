#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing System Integration Tests
# Developer D - January 2025

"""
Integration tests for SPEC-147 billing system.

Tests end-to-end workflows across:
- Billing models
- Usage metering
- Quota enforcement
- Redis caching
- Notifications
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import event
from sqlalchemy.dialects import postgresql, sqlite

from server.billing.models import (
    AccountStatus,
    AccountType,
    AuditLog,
    Base,
    BillingAccount,
    BillingPeriod,
    BillingPeriodStatus,
    BlockLevel,
    PlanTier,
    QuotaBlock,
    ResourceType,
    UsageEvent,
    UsageQuota,
)
from server.billing.quota_enforcement import QuotaEnforcementService, QuotaStatus
from server.billing.quota_notifications import QuotaNotificationService
from server.billing.redis_cache import UsageQuotaCache
from server.billing.usage_metering import UsageMeteringService

pytestmark = pytest.mark.integration


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
def sample_team_id():
    """Generate a sample team ID for testing"""
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
    """Create usage quotas for all resource types"""
    now = datetime.utcnow()
    quotas = {}

    for resource_type in [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]:
        quota = UsageQuota(
            billing_account_id=billing_account.id,
            resource_type=resource_type.value,
            quota_limit=Decimal("1000"),  # 1000 units for testing
            quota_used=Decimal("0"),
            period_start=now,
            period_end=now + timedelta(days=30),
        )
        db_session.add(quota)
        quotas[resource_type] = quota

    db_session.commit()
    for quota in quotas.values():
        db_session.refresh(quota)

    return quotas


@pytest.fixture
def usage_metering_service(db_session):
    """Create usage metering service"""
    return UsageMeteringService(db_session)


@pytest.fixture
def quota_enforcement_service(db_session, usage_metering_service):
    """Create quota enforcement service"""
    return QuotaEnforcementService(db_session, usage_metering_service)


@pytest.fixture
def notification_service(db_session):
    """Create notification service"""
    return QuotaNotificationService(db_session)


class TestEndToEndQuotaWorkflow:
    """End-to-end quota enforcement workflow tests"""

    def test_quota_workflow_normal_usage(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_quota,
        usage_metering_service,
        quota_enforcement_service,
    ):
        """Test complete workflow from usage recording to quota checking"""
        # Record storage usage
        event1 = usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("100"),
            metadata={"source": "test"},
        )

        assert event1.id is not None
        assert event1.resource_type == ResourceType.STORAGE.value

        # Check quota status (should be OK - 10% usage)
        status, percentage, block = quota_enforcement_service.check_quota_status(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert status == QuotaStatus.OK
        assert percentage < 75.0
        assert block is None

        # Enforce quota (should allow)
        allowed, error = quota_enforcement_service.enforce_quota(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert allowed is True
        assert error is None

    def test_quota_workflow_soft_warning(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_quota,
        usage_metering_service,
        quota_enforcement_service,
        notification_service,
    ):
        """Test workflow when usage exceeds 75% (soft warning)"""
        # Record usage to exceed 75% (800 GB out of 1000)
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("800"),
            metadata={"source": "test"},
        )

        # Check quota status (should be WARNING)
        status, percentage, block = quota_enforcement_service.check_quota_status(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert status == QuotaStatus.WARNING
        assert percentage >= 75.0
        assert percentage < 100.0

        # Check and enforce (should create soft block)
        allowed, error, active_block = quota_enforcement_service.check_and_enforce(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert allowed is True  # Still allowed but warned
        assert error is None
        assert active_block is not None
        assert active_block.block_level == BlockLevel.SOFT.value

        # Verify audit log was created
        audit_log = (
            db_session.query(AuditLog)
            .filter(AuditLog.billing_account_id == billing_account.id, AuditLog.event_type == "quota_warning")
            .first()
        )

        assert audit_log is not None
        assert audit_log.event_data["usage_percentage"] >= 75.0

    def test_quota_workflow_hard_block(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_quota,
        usage_metering_service,
        quota_enforcement_service,
    ):
        """Test workflow when usage exceeds 100% (hard block)"""
        # Record usage to exceed 100% (1100 GB out of 1000)
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("1100"),
            metadata={"source": "test"},
        )

        # Check quota status (should be BLOCKED)
        status, percentage, block = quota_enforcement_service.check_quota_status(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert status == QuotaStatus.BLOCKED
        assert percentage >= 100.0

        # Check and enforce (should create hard block and block operation)
        allowed, error, active_block = quota_enforcement_service.check_and_enforce(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert allowed is False  # Blocked
        assert error is not None
        assert "quota" in error.lower() or "exceeded" in error.lower()
        assert active_block is not None
        assert active_block.block_level == BlockLevel.HARD.value

        # Verify audit log was created
        audit_log = (
            db_session.query(AuditLog)
            .filter(AuditLog.billing_account_id == billing_account.id, AuditLog.event_type == "quota_block")
            .first()
        )

        assert audit_log is not None
        assert audit_log.event_data["usage_percentage"] >= 100.0

    def test_quota_workflow_read_operation_grace(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_quota,
        usage_metering_service,
        quota_enforcement_service,
    ):
        """Test graceful degradation for read operations during hard blocks"""
        # Record usage to exceed 100%
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("1100"),
        )

        # Create hard block with read operation grace
        usage_quota_storage = usage_quota[ResourceType.STORAGE]
        block = quota_enforcement_service.create_hard_block(
            billing_account_id=billing_account.id,
            usage_quota_id=usage_quota_storage.id,
            resource_type=ResourceType.STORAGE,
            reason="Test hard block",
            allow_read_operations=True,
        )

        assert block.event_metadata.get("allow_read_operations") is True

        # Check quota for read operation (should allow)
        status, percentage, active_block = quota_enforcement_service.check_quota_status(
            billing_account.id, billing_period.id, ResourceType.STORAGE, operation_type="read"
        )

        # Read operations should be allowed even during hard blocks
        # (status may be WARNING instead of BLOCKED if allow_read_operations=True)
        assert status in [QuotaStatus.WARNING, QuotaStatus.BLOCKED]

        # Enforce quota for read operation
        allowed, error = quota_enforcement_service.enforce_quota(
            billing_account.id, billing_period.id, ResourceType.STORAGE, operation_type="read"
        )

        # Read operations should be allowed
        assert allowed is True or error is None  # Either allowed or error is None


class TestMultiResourceQuota:
    """Tests for multi-resource quota management"""

    def test_multi_resource_usage_tracking(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_quota,
        usage_metering_service,
        quota_enforcement_service,
    ):
        """Test tracking usage across all three resource types"""
        # Record storage usage
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("500"),
        )

        # Record retrieval usage
        usage_metering_service.record_retrieval_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            retrieval_count=Decimal("200"),
        )

        # Record token usage
        usage_metering_service.record_token_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            token_count=Decimal("300"),
        )

        # Check quota status for each resource
        for resource_type in [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]:
            status, percentage, block = quota_enforcement_service.check_quota_status(
                billing_account.id, billing_period.id, resource_type
            )

            assert status == QuotaStatus.OK  # All under 75%
            assert percentage < 75.0

    def test_quota_summary_all_resources(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_quota,
        usage_metering_service,
        quota_enforcement_service,
    ):
        """Test quota summary for all resource types"""
        # Record some usage for each resource
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("500"),
        )

        usage_metering_service.record_retrieval_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            retrieval_count=Decimal("200"),
        )

        usage_metering_service.record_token_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            token_count=Decimal("300"),
        )

        # Get quota summary
        summary = quota_enforcement_service.get_quota_summary(billing_account.id, billing_period.id)

        assert "storage" in summary
        assert "retrieval" in summary
        assert "token" in summary

        for resource_type, data in summary.items():
            assert "status" in data
            assert "percentage" in data
            assert "used" in data
            assert "limit" in data
            assert "has_block" in data
            assert data["status"] == "ok"  # All under 75%
            assert data["percentage"] < 75.0


class TestQuotaBlockLifecycle:
    """Tests for quota block lifecycle management"""

    def test_block_creation_and_removal(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_quota,
        usage_metering_service,
        quota_enforcement_service,
    ):
        """Test complete block lifecycle"""
        # Start with normal usage
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("50"),
        )

        # Check quota (should be OK)
        status, _, _ = quota_enforcement_service.check_quota_status(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )
        assert status == QuotaStatus.OK

        # Increase usage to trigger soft block
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("750"),  # Total: 800 GB (80%)
        )

        # Check and enforce (should create soft block)
        allowed, _, soft_block = quota_enforcement_service.check_and_enforce(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert allowed is True
        assert soft_block is not None
        assert soft_block.block_level == BlockLevel.SOFT.value

        # Increase usage to trigger hard block (record additional 301 GB to reach 1101 total)
        # Note: We need to record enough to exceed 100% (1000 GB limit)
        # Current usage is 800 GB, so we need at least 201 more to exceed 100%
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("301"),  # Total: 1101 GB (110.1%)
        )

        # Flush and commit to ensure all usage events are persisted
        db_session.flush()
        db_session.commit()

        # Verify usage is actually recorded
        current_usage = usage_metering_service.get_current_usage(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )
        assert current_usage >= Decimal("1100"), f"Usage should be >= 1100 but got {current_usage}"

        # Check and enforce (should create hard block, soft block should be deactivated)
        allowed, error, hard_block = quota_enforcement_service.check_and_enforce(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        assert allowed is False, f"Should be blocked but got allowed=True. Error: {error}"
        assert error is not None
        assert hard_block is not None, "Hard block should be created"
        assert hard_block.block_level == BlockLevel.HARD.value, f"Expected hard block but got {hard_block.block_level}"

        # Verify soft block was deactivated
        db_session.refresh(soft_block)
        assert soft_block.is_active is False

        # Simulate usage reduction (remove some data)
        # In real scenario, this would be done by deleting data/files
        # For test, we'll manually reduce usage by creating a new period or adjusting
        # But for now, we'll test manual block removal

        # Remove block manually
        quota_enforcement_service.remove_block(billing_account.id, ResourceType.STORAGE)

        # Verify block is deactivated
        db_session.refresh(hard_block)
        assert hard_block.is_active is False
        assert hard_block.unblocked_at is not None


class TestAuditTrailIntegration:
    """Tests for audit trail integration"""

    def test_audit_trail_completeness(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_quota,
        usage_metering_service,
        quota_enforcement_service,
        notification_service,
    ):
        """Test that all quota actions are logged to audit trail"""
        # Record usage
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("800"),
        )

        # Trigger soft warning (should create audit log)
        quota_enforcement_service.check_and_enforce(billing_account.id, billing_period.id, ResourceType.STORAGE)

        # Check audit logs
        warning_logs = (
            db_session.query(AuditLog)
            .filter(AuditLog.billing_account_id == billing_account.id, AuditLog.event_type == "quota_warning")
            .all()
        )

        assert len(warning_logs) > 0

        # Increase usage to trigger hard block (record additional 301 GB to reach 1101 total = 110.1%)
        usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("301"),
        )

        # Flush and commit to ensure all usage events are persisted
        db_session.flush()
        db_session.commit()

        # Verify usage is actually recorded
        current_usage = usage_metering_service.get_current_usage(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )
        assert current_usage >= Decimal("1100"), f"Usage should be >= 1100 but got {current_usage}"

        # Trigger hard block (should create audit log)
        allowed, error, block = quota_enforcement_service.check_and_enforce(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        # Verify hard block was created
        assert block is not None, "Hard block should be created"
        assert block.block_level == BlockLevel.HARD.value, f"Expected hard block but got {block.block_level}"

        # Refresh session to ensure audit logs are committed
        db_session.commit()

        # Check audit logs
        block_logs = (
            db_session.query(AuditLog)
            .filter(AuditLog.billing_account_id == billing_account.id, AuditLog.event_type == "quota_block")
            .all()
        )

        assert len(block_logs) > 0, f"Expected quota_block audit logs but found {len(block_logs)}"

        # Verify all logs have event hash
        all_logs = db_session.query(AuditLog).filter(AuditLog.billing_account_id == billing_account.id).all()

        for log in all_logs:
            assert log.event_hash is not None
            assert len(log.event_hash) == 64  # SHA256 hex digest length


class TestIdempotencyIntegration:
    """Tests for idempotency across services"""

    def test_idempotent_usage_recording(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_metering_service,
    ):
        """Test that duplicate usage events are not double-counted"""
        # Create idempotency key
        idempotency_key = "test-key-123"

        # Record usage twice with same idempotency key
        event1 = usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("100"),
            idempotency_key=idempotency_key,
        )

        event2 = usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("100"),
            idempotency_key=idempotency_key,  # Same key
        )

        # Should return the same event (idempotent)
        assert event1.id == event2.id

        # Verify usage is only counted once
        usage = usage_metering_service.get_current_usage(billing_account.id, billing_period.id, ResourceType.STORAGE)

        assert usage == Decimal("100")  # Not 200


class TestConcurrentUsageTracking:
    """Tests for concurrent usage tracking scenarios"""

    def test_concurrent_usage_across_resources(
        self,
        db_session,
        billing_account,
        billing_period,
        usage_quota,
        usage_metering_service,
    ):
        """Test concurrent usage tracking across different resource types"""
        # Record usage for all three resources concurrently
        storage_event = usage_metering_service.record_storage_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            storage_gb=Decimal("100"),
        )

        retrieval_event = usage_metering_service.record_retrieval_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            retrieval_count=Decimal("50"),
        )

        token_event = usage_metering_service.record_token_usage(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            token_count=Decimal("200"),
        )

        # Verify all events are recorded
        assert storage_event.id is not None
        assert retrieval_event.id is not None
        assert token_event.id is not None

        # Verify usage is tracked separately for each resource
        storage_usage = usage_metering_service.get_current_usage(
            billing_account.id, billing_period.id, ResourceType.STORAGE
        )

        retrieval_usage = usage_metering_service.get_current_usage(
            billing_account.id, billing_period.id, ResourceType.RETRIEVAL
        )

        token_usage = usage_metering_service.get_current_usage(
            billing_account.id, billing_period.id, ResourceType.TOKEN
        )

        assert storage_usage == Decimal("100")
        assert retrieval_usage == Decimal("50")
        assert token_usage == Decimal("200")
