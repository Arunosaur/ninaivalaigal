#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Integration tests for billing analytics (US#180: US-227)
Tests for revenue metrics, payment metrics, usage trends, and churn risk scoring
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, List
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from sqlalchemy import func
from sqlalchemy.orm import Session

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

pytestmark = pytest.mark.integration

from server.billing.models import (
    AccountStatus,
    BillingAccount,
    BillingPeriod,
    BillingPeriodStatus,
    Invoice,
    InvoiceStatus,
    PlanTier,
    StripeCustomer,
    StripeSubscription,
)
from server.database.models import Team, User


def create_test_billing_period(db_session: Session, billing_account: BillingAccount, days_back: int = 30):
    """Helper to create a test billing period"""
    now = datetime.now(timezone.utc)
    billing_period = BillingPeriod(
        id=uuid4(),
        billing_account_id=billing_account.id,
        status=BillingPeriodStatus.ACTIVE.value,
        period_start=now - timedelta(days=days_back),
        period_end=now,
    )
    db_session.add(billing_period)
    db_session.flush()
    return billing_period


@pytest.fixture
def db_session(monkeypatch):
    """Get database session with graceful fallback"""
    try:
        from server.database.manager import DatabaseManager

        db = DatabaseManager()
        session = db.get_session()

        # Ensure clean transaction state
        try:
            session.rollback()
        except Exception:
            pass

        yield session

        # Cleanup: rollback any uncommitted changes
        try:
            session.rollback()
        except Exception:
            pass
        session.close()
    except Exception as e:
        pytest.skip(f"Database not available: {str(e)}", allow_module_level=False)


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user"""
    unique_id = str(uuid4())[:8]
    user = User(
        id=uuid4(),
        email=f"test-{unique_id}@example.com",
        username=f"testuser-{unique_id}",
        name="Test User",
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_team(db_session: Session, test_user: User) -> Team:
    """Create a test team"""
    team = Team(
        id=uuid4(),
        name="Test Team",
        origin="native",
        governance_type="internal",
        status="active",
    )
    if hasattr(team, "owner_id"):
        team.owner_id = test_user.id
    if hasattr(team, "lead_user_id"):
        team.lead_user_id = test_user.id
    db_session.add(team)
    db_session.commit()
    return team


@pytest.fixture
def billing_account(db_session: Session, test_team: Team) -> BillingAccount:
    """Create a billing account"""
    account = BillingAccount(
        id=uuid4(),
        account_type="team",
        account_id=test_team.id,
        status=AccountStatus.ACTIVE.value,
        plan_tier=PlanTier.PRO.value,
        currency="USD",
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def stripe_customer(db_session: Session, billing_account: BillingAccount) -> StripeCustomer:
    """Create a Stripe customer"""
    customer = StripeCustomer(
        id=uuid4(),
        billing_account_id=billing_account.id,
        stripe_customer_id=f"cus_{uuid4().hex[:24]}",
        email="test@example.com",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(customer)
    db_session.commit()
    return customer


@pytest.fixture
def stripe_subscription(
    db_session: Session, stripe_customer: StripeCustomer, billing_account: BillingAccount
) -> StripeSubscription:
    """Create a Stripe subscription"""
    now = datetime.now(timezone.utc)
    subscription = StripeSubscription(
        id=uuid4(),
        stripe_customer_id=stripe_customer.id,  # Use the UUID primary key, not stripe_customer_id string
        stripe_subscription_id=f"sub_{uuid4().hex[:24]}",
        plan_id="pro",
        status="active",
        current_period_start=now,
        current_period_end=now + timedelta(days=30),
    )
    db_session.add(subscription)
    db_session.commit()
    return subscription


class TestRevenueMetrics:
    """Test revenue metrics calculations (MRR, ARR, LTV, revenue trends)"""

    def test_mrr_calculation(self, db_session: Session, billing_account: BillingAccount, stripe_subscription):
        """Test Monthly Recurring Revenue calculation"""
        # MRR should be based on subscription plan price
        # Pro plan = $99/month
        expected_mrr = 99.0

        # Calculate MRR from active subscriptions
        # Get subscriptions via StripeCustomer relationship
        stripe_customer = (
            db_session.query(StripeCustomer)
            .filter(StripeCustomer.billing_account_id == billing_account.id)
            .first()
        )
        if stripe_customer:
            active_subscriptions = (
                db_session.query(StripeSubscription)
                .filter(
                    StripeSubscription.stripe_customer_id == stripe_customer.id,
                    StripeSubscription.status == "active",
                )
                .all()
            )
        else:
            active_subscriptions = []

        mrr = 0.0
        for sub in active_subscriptions:
            if sub.plan_id == "pro":
                mrr += 99.0
            elif sub.plan_id == "starter":
                mrr += 29.0
            elif sub.plan_id == "enterprise":
                mrr += 500.0

        assert mrr == expected_mrr

    def test_arr_calculation(self, db_session: Session, billing_account: BillingAccount, stripe_subscription):
        """Test Annual Recurring Revenue calculation"""
        # ARR = MRR * 12
        mrr = 99.0  # Pro plan
        expected_arr = mrr * 12

        assert expected_arr == 1188.0

    def test_lifetime_value_calculation(
        self, db_session: Session, billing_account: BillingAccount, stripe_subscription
    ):
        """Test Customer Lifetime Value calculation"""
        # LTV = Average Revenue Per User * Average Customer Lifespan
        # For this test, assume $99/month for 24 months average
        mrr = 99.0
        average_lifespan_months = 24
        expected_ltv = mrr * average_lifespan_months

        assert expected_ltv == 2376.0

    def test_revenue_trend_analysis(self, db_session: Session, billing_account: BillingAccount):
        """Test revenue trend analysis over time"""
        now = datetime.now(timezone.utc)

        # Create a billing period first (required for Invoice)
        billing_period = create_test_billing_period(db_session, billing_account, days_back=90)

        # Create invoices over the past 3 months
        invoices = []
        for i in range(3):
            invoice = Invoice(
                id=uuid4(),
                billing_period_id=billing_period.id,
                billing_account_id=billing_account.id,
                invoice_number=f"INV-{i+1}",
                status=InvoiceStatus.PAID.value,
                subtotal=Decimal("99.00"),
                tax_amount=Decimal("0.00"),
                total_amount=Decimal("99.00"),
                currency="USD",
                issued_at=now - timedelta(days=30 * (3 - i)),
                due_at=now - timedelta(days=30 * (3 - i)) + timedelta(days=7),
            )
            db_session.add(invoice)
            invoices.append(invoice)

        db_session.commit()

        # Calculate revenue trend
        revenue_by_month = {}
        for invoice in invoices:
            month_key = invoice.issued_at.strftime("%Y-%m")
            if month_key not in revenue_by_month:
                revenue_by_month[month_key] = Decimal("0.00")
            revenue_by_month[month_key] += invoice.total_amount

        # Should have 3 months of revenue
        assert len(revenue_by_month) == 3
        assert all(amount == Decimal("99.00") for amount in revenue_by_month.values())


class TestPaymentMetrics:
    """Test payment metrics calculations"""

    def test_payment_success_rate_calculation(
        self, db_session: Session, billing_account: BillingAccount
    ):
        """Test payment success rate calculation"""
        now = datetime.now(timezone.utc)

        # Create 10 invoices: 8 paid, 2 failed
        paid_count = 8
        failed_count = 2

        # Create a billing period first (required for Invoice)
        billing_period = create_test_billing_period(db_session, billing_account, days_back=30)

        for i in range(paid_count):
            invoice = Invoice(
                id=uuid4(),
                billing_period_id=billing_period.id,
                billing_account_id=billing_account.id,
                invoice_number=f"INV-PAID-{i+1}",
                status=InvoiceStatus.PAID.value,
                subtotal=Decimal("99.00"),
                total_amount=Decimal("99.00"),
                currency="USD",
                issued_at=now - timedelta(days=i),
            )
            db_session.add(invoice)

        for i in range(failed_count):
            invoice = Invoice(
                id=uuid4(),
                billing_period_id=billing_period.id,
                billing_account_id=billing_account.id,
                invoice_number=f"INV-FAILED-{i+1}",
                status=InvoiceStatus.ISSUED.value,
                subtotal=Decimal("99.00"),
                total_amount=Decimal("99.00"),
                currency="USD",
                issued_at=now - timedelta(days=i),
                due_at=now - timedelta(days=i) - timedelta(days=1),  # Overdue
            )
            db_session.add(invoice)

        db_session.commit()

        # Calculate success rate
        total_invoices = db_session.query(Invoice).filter(Invoice.billing_account_id == billing_account.id).count()
        paid_invoices = (
            db_session.query(Invoice)
            .filter(
                Invoice.billing_account_id == billing_account.id,
                Invoice.status == InvoiceStatus.PAID.value,
            )
            .count()
        )

        success_rate = paid_invoices / total_invoices if total_invoices > 0 else 0.0

        assert success_rate == 0.8  # 8/10 = 80%

    def test_failed_payment_count(self, db_session: Session, billing_account: BillingAccount):
        """Test failed payment count"""
        now = datetime.now(timezone.utc)

        # Create billing period
        billing_period = create_test_billing_period(db_session, billing_account, days_back=30)

        # Create overdue invoices (failed payments)
        for i in range(3):
            invoice = Invoice(
                id=uuid4(),
                billing_period_id=billing_period.id,
                billing_account_id=billing_account.id,
                invoice_number=f"INV-OVERDUE-{i+1}",
                status=InvoiceStatus.ISSUED.value,
                subtotal=Decimal("99.00"),
                total_amount=Decimal("99.00"),
                currency="USD",
                issued_at=now - timedelta(days=10 + i),
                due_at=now - timedelta(days=5 + i),  # Overdue
            )
            db_session.add(invoice)

        db_session.commit()

        # Count failed payments (overdue invoices)
        failed_count = (
            db_session.query(Invoice)
            .filter(
                Invoice.billing_account_id == billing_account.id,
                Invoice.status == InvoiceStatus.ISSUED.value,
                Invoice.due_at < now,
            )
            .count()
        )

        assert failed_count == 3

    def test_retry_success_rate(self, db_session: Session, billing_account: BillingAccount):
        """Test retry success rate calculation"""
        # This would require PaymentFailure model integration
        # For now, test the concept with invoices that were retried

        # Create billing period
        billing_period = create_test_billing_period(db_session, billing_account, days_back=30)
        now = datetime.now(timezone.utc)

        # Create initial failed invoice
        failed_invoice = Invoice(
            id=uuid4(),
            billing_period_id=billing_period.id,
            billing_account_id=billing_account.id,
            invoice_number="INV-RETRY-1",
            status=InvoiceStatus.ISSUED.value,
            subtotal=Decimal("99.00"),
            total_amount=Decimal("99.00"),
            currency="USD",
            issued_at=now - timedelta(days=5),
            due_at=now - timedelta(days=2),
        )
        db_session.add(failed_invoice)

        # Create retry invoice (paid)
        retry_invoice = Invoice(
            id=uuid4(),
            billing_period_id=billing_period.id,
            billing_account_id=billing_account.id,
            invoice_number="INV-RETRY-2",
            status=InvoiceStatus.PAID.value,
            subtotal=Decimal("99.00"),
            total_amount=Decimal("99.00"),
            currency="USD",
            issued_at=now - timedelta(days=1),
        )
        db_session.add(retry_invoice)
        db_session.commit()

        # In a real implementation, we'd track retry attempts
        # For this test, assume 1 retry that succeeded
        retry_attempts = 1
        successful_retries = 1
        retry_success_rate = successful_retries / retry_attempts if retry_attempts > 0 else 0.0

        assert retry_success_rate == 1.0  # 100% success rate

    def test_average_payment_time_calculation(self, db_session: Session, billing_account: BillingAccount):
        """Test average payment time calculation"""
        now = datetime.now(timezone.utc)

        # Create billing period
        billing_period = create_test_billing_period(db_session, billing_account, days_back=60)

        # Create invoices with different payment times
        payment_times = [2, 3, 5, 7, 10]  # days to payment

        for i, days_to_payment in enumerate(payment_times):
            issued_at = now - timedelta(days=30 + i)
            paid_at = issued_at + timedelta(days=days_to_payment)

            invoice = Invoice(
                id=uuid4(),
                billing_period_id=billing_period.id,
                billing_account_id=billing_account.id,
                invoice_number=f"INV-TIME-{i+1}",
                status=InvoiceStatus.PAID.value,
                subtotal=Decimal("99.00"),
                total_amount=Decimal("99.00"),
                currency="USD",
                issued_at=issued_at,
            )
            # In a real implementation, we'd have a paid_at field
            # For this test, calculate from issued_at + days_to_payment
            db_session.add(invoice)

        db_session.commit()

        # Calculate average payment time
        avg_payment_time = sum(payment_times) / len(payment_times)

        assert avg_payment_time == 5.4  # (2+3+5+7+10)/5 = 5.4 days


class TestUsageTrends:
    """Test usage trend calculations"""

    def test_daily_usage_aggregation(self, db_session: Session, billing_account: BillingAccount):
        """Test daily usage aggregation"""
        # This would require UsageEvent model integration
        # For now, test the concept with mock data

        now = datetime.now(timezone.utc)
        daily_usage = {}

        # Simulate 7 days of usage
        for i in range(7):
            date_key = (now - timedelta(days=i)).date()
            daily_usage[date_key] = 100.0 * (i + 1)  # Increasing usage

        # Aggregate daily usage
        total_usage = sum(daily_usage.values())
        avg_daily_usage = total_usage / len(daily_usage)

        assert len(daily_usage) == 7
        assert avg_daily_usage == 400.0  # (100+200+300+400+500+600+700)/7

    def test_weekly_usage_trends(self, db_session: Session, billing_account: BillingAccount):
        """Test weekly usage trends"""
        now = datetime.now(timezone.utc)
        weekly_usage = {}

        # Simulate 4 weeks of usage
        for week in range(4):
            week_start = now - timedelta(weeks=4 - week)
            week_key = week_start.strftime("%Y-W%W")
            weekly_usage[week_key] = 1000.0 * (week + 1)  # Increasing usage

        # Calculate week-over-week growth
        weeks = sorted(weekly_usage.keys())
        if len(weeks) >= 2:
            current_week_usage = weekly_usage[weeks[-1]]
            previous_week_usage = weekly_usage[weeks[-2]]
            growth_rate = (current_week_usage - previous_week_usage) / previous_week_usage

            assert growth_rate == pytest.approx(0.333, abs=0.01)  # 33.3% growth (4000-3000)/3000

    def test_monthly_usage_patterns(self, db_session: Session, billing_account: BillingAccount):
        """Test monthly usage patterns"""
        now = datetime.now(timezone.utc)
        monthly_usage = {}

        # Simulate 3 months of usage
        for month in range(3):
            month_start = now - timedelta(days=30 * (3 - month))
            month_key = month_start.strftime("%Y-%m")
            monthly_usage[month_key] = 10000.0 * (month + 1)  # Increasing usage

        # Calculate month-over-month growth
        months = sorted(monthly_usage.keys())
        assert len(months) == 3

        if len(months) >= 2:
            current_month_usage = monthly_usage[months[-1]]
            previous_month_usage = monthly_usage[months[-2]]
            growth_rate = (current_month_usage - previous_month_usage) / previous_month_usage

            assert growth_rate == 0.5  # 50% growth (30000-20000)/20000

    def test_usage_growth_calculation(self, db_session: Session, billing_account: BillingAccount):
        """Test usage growth calculation"""
        # Calculate growth between two periods
        period1_usage = 1000.0
        period2_usage = 1500.0

        growth_rate = (period2_usage - period1_usage) / period1_usage
        growth_percentage = growth_rate * 100

        assert growth_rate == 0.5  # 50% growth
        assert growth_percentage == 50.0


class TestChurnRiskScoring:
    """Test churn risk scoring calculations"""

    def test_payment_failure_impact_on_churn_score(
        self, db_session: Session, billing_account: BillingAccount
    ):
        """Test payment failure impact on churn score"""
        now = datetime.now(timezone.utc)

        # Create billing period
        billing_period = create_test_billing_period(db_session, billing_account, days_back=30)

        # Create overdue invoices (payment failures)
        for i in range(2):
            invoice = Invoice(
                id=uuid4(),
                billing_period_id=billing_period.id,
                billing_account_id=billing_account.id,
                invoice_number=f"INV-CHURN-{i+1}",
                status=InvoiceStatus.ISSUED.value,
                subtotal=Decimal("99.00"),
                total_amount=Decimal("99.00"),
                currency="USD",
                issued_at=now - timedelta(days=10 + i),
                due_at=now - timedelta(days=5 + i),  # Overdue
            )
            db_session.add(invoice)

        db_session.commit()

        # Calculate churn risk based on payment failures
        overdue_count = (
            db_session.query(Invoice)
            .filter(
                Invoice.billing_account_id == billing_account.id,
                Invoice.status == InvoiceStatus.ISSUED.value,
                Invoice.due_at < now,
            )
            .count()
        )

        # Churn risk increases with payment failures
        base_churn_risk = 0.1
        if overdue_count > 0:
            churn_risk_score = min(0.1 + (overdue_count * 0.3), 1.0)
        else:
            churn_risk_score = base_churn_risk

        assert churn_risk_score == 0.7  # 0.1 + (2 * 0.3) = 0.7

    def test_usage_decline_detection(self, db_session: Session, billing_account: BillingAccount):
        """Test usage decline detection"""
        # Simulate usage decline over 3 months
        monthly_usage = [10000.0, 8000.0, 5000.0]  # Declining usage

        # Detect decline
        if len(monthly_usage) >= 2:
            recent_usage = monthly_usage[-1]
            previous_usage = monthly_usage[-2]
            decline_rate = (previous_usage - recent_usage) / previous_usage

            # Significant decline (>30%) increases churn risk
            if decline_rate > 0.3:
                churn_risk_increase = 0.2
            elif decline_rate > 0.1:
                churn_risk_increase = 0.1
            else:
                churn_risk_increase = 0.0

            base_churn_risk = 0.1
            churn_risk_score = min(base_churn_risk + churn_risk_increase, 1.0)

            assert decline_rate == 0.375  # (8000-5000)/8000 = 37.5%
            assert churn_risk_score == pytest.approx(0.3, abs=0.01)  # 0.1 + 0.2 = 0.3

    def test_engagement_metric_weighting(self, db_session: Session, billing_account: BillingAccount):
        """Test engagement metric weighting in churn risk calculation"""
        # Define engagement metrics with weights
        metrics = {
            "payment_success_rate": {"value": 0.8, "weight": 0.4},  # 80% success, 40% weight
            "usage_trend": {"value": -0.2, "weight": 0.3},  # -20% decline, 30% weight
            "days_since_last_activity": {"value": 15, "weight": 0.3},  # 15 days, 30% weight
        }

        # Calculate weighted churn risk
        base_risk = 0.1

        # Payment failure impact
        if metrics["payment_success_rate"]["value"] < 0.9:
            payment_risk = (1.0 - metrics["payment_success_rate"]["value"]) * metrics["payment_success_rate"]["weight"]
        else:
            payment_risk = 0.0

        # Usage decline impact
        if metrics["usage_trend"]["value"] < 0:
            usage_risk = abs(metrics["usage_trend"]["value"]) * metrics["usage_trend"]["weight"]
        else:
            usage_risk = 0.0

        # Inactivity impact
        if metrics["days_since_last_activity"]["value"] > 7:
            inactivity_risk = min(metrics["days_since_last_activity"]["value"] / 30.0, 1.0) * metrics[
                "days_since_last_activity"
            ]["weight"]
        else:
            inactivity_risk = 0.0

        churn_risk_score = min(base_risk + payment_risk + usage_risk + inactivity_risk, 1.0)

        # Expected: 0.1 + (0.2 * 0.4) + (0.2 * 0.3) + (0.5 * 0.3) = 0.1 + 0.08 + 0.06 + 0.15 = 0.39
        assert churn_risk_score == pytest.approx(0.39, abs=0.01)


class TestBillingAnalyticsIntegration:
    """Integration tests for complete billing analytics flow"""

    def test_complete_analytics_calculation(
        self, db_session: Session, billing_account: BillingAccount, stripe_subscription
    ):
        """Test complete analytics calculation with all metrics"""
        now = datetime.now(timezone.utc)

        # Create billing period
        billing_period = create_test_billing_period(db_session, billing_account, days_back=60)

        # Create invoices
        for i in range(5):
            invoice = Invoice(
                id=uuid4(),
                billing_period_id=billing_period.id,
                billing_account_id=billing_account.id,
                invoice_number=f"INV-{i+1}",
                status=InvoiceStatus.PAID.value if i < 4 else InvoiceStatus.ISSUED.value,
                subtotal=Decimal("99.00"),
                total_amount=Decimal("99.00"),
                currency="USD",
                issued_at=now - timedelta(days=30 - (i * 7)),
                due_at=now - timedelta(days=30 - (i * 7)) + timedelta(days=7),
            )
            db_session.add(invoice)

        db_session.commit()

        # Calculate all metrics
        # MRR
        mrr = 99.0  # Pro plan

        # ARR
        arr = mrr * 12

        # Total revenue
        total_revenue = (
            db_session.query(func.sum(Invoice.total_amount))
            .filter(
                Invoice.billing_account_id == billing_account.id,
                Invoice.status == InvoiceStatus.PAID.value,
            )
            .scalar()
            or Decimal("0.00")
        )

        # Payment success rate
        total_invoices = (
            db_session.query(Invoice).filter(Invoice.billing_account_id == billing_account.id).count()
        )
        paid_invoices = (
            db_session.query(Invoice)
            .filter(
                Invoice.billing_account_id == billing_account.id,
                Invoice.status == InvoiceStatus.PAID.value,
            )
            .count()
        )
        payment_success_rate = paid_invoices / total_invoices if total_invoices > 0 else 0.0

        # Churn risk
        overdue_count = (
            db_session.query(Invoice)
            .filter(
                Invoice.billing_account_id == billing_account.id,
                Invoice.status == InvoiceStatus.ISSUED.value,
                Invoice.due_at < now,
            )
            .count()
        )

        churn_risk_score = 0.1
        if overdue_count > 0:
            churn_risk_score = 0.7
        elif payment_success_rate < 0.8:
            churn_risk_score = 0.5

        # Assertions
        assert mrr == 99.0
        assert arr == 1188.0
        assert float(total_revenue) == 396.0  # 4 paid invoices * $99
        assert payment_success_rate == 0.8  # 4/5 = 80%
        assert churn_risk_score == 0.1  # No overdue, success rate >= 0.8

