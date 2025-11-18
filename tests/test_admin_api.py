#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing Admin API Tests
# Developer D - January 2025

"""
Unit tests for SPEC-147 billing admin API endpoints.

Tests BILL-015: Billing Management API functionality.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

try:
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    TestClient = None


try:
    from server.billing.admin_api import router

    ADMIN_API_AVAILABLE = True
except ImportError:
    ADMIN_API_AVAILABLE = False
    router = None
from server.billing.models import (
    AccountStatus,
    AccountType,
    BillingAccount,
    BillingPeriod,
    BlockLevel,
    Invoice,
    InvoiceStatus,
    PlanTier,
    QuotaBlock,
    ResourceType,
    UsageEvent,
    UsageQuota,
)

pytestmark = pytest.mark.unit


@pytest.fixture
def sample_team_id():
    """Sample team ID for testing"""
    return uuid4()


@pytest.fixture
def billing_account(db_session, sample_team_id):
    """Create a test billing account"""
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
    """Create a test billing period"""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=30)
    period_end = now

    period = BillingPeriod(
        billing_account_id=billing_account.id,
        period_start=period_start,
        period_end=period_end,
        status="active",
    )
    db_session.add(period)
    db_session.commit()
    db_session.refresh(period)
    return period


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

                # Remove CHECK constraints that use char_length
                for constraint in list(table.constraints):
                    if hasattr(constraint, "sqltext"):
                        sqltext = str(constraint.sqltext)
                        if "char_length" in sqltext.lower():
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
def admin_client(db_session):
    """Create test client for admin API"""
    if not FASTAPI_AVAILABLE or not ADMIN_API_AVAILABLE:
        pytest.skip("FastAPI or admin API not available")

    try:
        from fastapi import FastAPI

        from server.database import get_db

        app = FastAPI()
        app.include_router(router)

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        return TestClient(app)
    except ImportError:
        pytest.skip("FastAPI not available")


class TestAccountManagement:
    """Tests for account management endpoints"""

    def test_list_billing_accounts(self, admin_client, db_session, billing_account):
        """Test listing billing accounts"""
        response = admin_client.get("/api/billing/admin/accounts")

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "accounts" in data
        assert isinstance(data["accounts"], list)

    def test_list_accounts_with_filters(self, admin_client, db_session, billing_account):
        """Test listing accounts with filters"""
        response = admin_client.get(
            "/api/billing/admin/accounts",
            params={"account_type": "team", "plan_tier": "pro", "status_filter": "active"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "accounts" in data

    def test_get_account_details(self, admin_client, db_session, billing_account, billing_period):
        """Test getting account details"""
        response = admin_client.get(f"/api/billing/admin/accounts/{billing_account.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(billing_account.id)
        assert "usage_summary" in data
        assert "active_blocks" in data

    def test_get_account_not_found(self, admin_client, db_session):
        """Test getting non-existent account"""
        fake_id = uuid4()
        response = admin_client.get(f"/api/billing/admin/accounts/{fake_id}")

        assert response.status_code == 404


class TestUsageMetrics:
    """Tests for usage metrics endpoints"""

    def test_get_usage_metrics(self, admin_client, db_session, billing_account, billing_period):
        """Test getting usage metrics"""
        # Create some usage events
        usage_event = UsageEvent(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            resource_type=ResourceType.STORAGE.value,
            quantity=Decimal("100"),
        )
        db_session.add(usage_event)
        db_session.commit()

        response = admin_client.get(f"/api/billing/admin/accounts/{billing_account.id}/usage")

        assert response.status_code == 200
        data = response.json()
        assert "usage_by_resource" in data
        assert ResourceType.STORAGE.value in data["usage_by_resource"]

    def test_get_usage_metrics_with_filters(self, admin_client, db_session, billing_account, billing_period):
        """Test getting usage metrics with filters"""
        response = admin_client.get(
            f"/api/billing/admin/accounts/{billing_account.id}/usage",
            params={
                "resource_type": "storage",
                "start_date": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "usage_by_resource" in data


class TestInvoiceHistory:
    """Tests for invoice history endpoints"""

    def test_get_invoice_history(self, admin_client, db_session, billing_account, billing_period):
        """Test getting invoice history"""
        # Create an invoice
        invoice = Invoice(
            billing_account_id=billing_account.id,
            billing_period_id=billing_period.id,
            invoice_number="INV-TEST-001",
            subtotal=Decimal("100.00"),
            total_amount=Decimal("100.00"),
            currency="USD",
            status=InvoiceStatus.ISSUED.value,
        )
        db_session.add(invoice)
        db_session.commit()

        response = admin_client.get(f"/api/billing/admin/accounts/{billing_account.id}/invoices")

        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data
        assert len(data["invoices"]) >= 1

    def test_get_invoice_history_with_status_filter(self, admin_client, db_session, billing_account, billing_period):
        """Test getting invoice history with status filter"""
        response = admin_client.get(
            f"/api/billing/admin/accounts/{billing_account.id}/invoices", params={"status_filter": "issued"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "invoices" in data


class TestQuotaManagement:
    """Tests for quota management endpoints"""

    def test_override_quota(self, admin_client, db_session, billing_account, billing_period):
        """Test overriding quota limit"""
        # Create a quota
        quota = UsageQuota(
            billing_account_id=billing_account.id,
            resource_type=ResourceType.STORAGE.value,
            quota_limit=Decimal("1000"),
            quota_used=Decimal("0"),
            overage_rate=Decimal("0.10"),
            period_start=billing_period.period_start,
            period_end=billing_period.period_end,
        )
        db_session.add(quota)
        db_session.commit()

        response = admin_client.post(
            f"/api/billing/admin/accounts/{billing_account.id}/quota/override",
            params={"resource_type": "storage", "new_limit": 5000.0},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quota_limit"] == 5000.0
        assert data["resource_type"] == "storage"

    def test_remove_quota_block(self, admin_client, db_session, billing_account):
        """Test removing quota block"""
        # Create a quota block
        block = QuotaBlock(
            billing_account_id=billing_account.id,
            resource_type=ResourceType.STORAGE.value,
            block_level=BlockLevel.SOFT.value,
            reason="Test block",
            is_active=True,
        )
        db_session.add(block)
        db_session.commit()

        response = admin_client.delete(f"/api/billing/admin/accounts/{billing_account.id}/quota/blocks/{block.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["removed"] is True

        # Verify block is deactivated
        db_session.refresh(block)
        assert block.is_active is False


class TestSystemMetrics:
    """Tests for system metrics endpoints"""

    def test_get_billing_overview(self, admin_client, db_session, billing_account):
        """Test getting billing overview"""
        response = admin_client.get("/api/billing/admin/metrics/overview")

        assert response.status_code == 200
        data = response.json()
        assert "total_accounts" in data
        assert "active_accounts" in data
        assert "accounts_by_tier" in data
        assert "active_quota_blocks" in data

    def test_get_usage_trends(self, admin_client, db_session, billing_account, billing_period):
        """Test getting usage trends"""
        # Create some usage events
        for i in range(5):
            usage_event = UsageEvent(
                billing_account_id=billing_account.id,
                billing_period_id=billing_period.id,
                resource_type=ResourceType.STORAGE.value,
                quantity=Decimal("10"),
            )
            db_session.add(usage_event)
        db_session.commit()

        response = admin_client.get("/api/billing/admin/metrics/trends", params={"days": 30})

        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
        assert ResourceType.STORAGE.value in data["trends"]

    def test_get_usage_trends_with_resource_filter(self, admin_client, db_session):
        """Test getting usage trends with resource filter"""
        response = admin_client.get(
            "/api/billing/admin/metrics/trends", params={"days": 30, "resource_type": "storage"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "trends" in data
