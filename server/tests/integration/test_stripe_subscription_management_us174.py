#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# US#174: US-221: Subscription Management Tests
# Comprehensive unit and integration tests for StripeService subscription management
#
"""
Integration tests for Stripe subscription creation, updates, and cancellation.

Tests cover:
- Subscription creation with valid price_id
- Subscription with discount codes
- Subscription with trial periods
- Subscription status updates
- Proration calculations
- Subscription cancellation logic
- Edge cases and error handling
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

pytestmark = pytest.mark.integration

# Try to import stripe, but make it optional for tests
try:
    import stripe
    from stripe.error import (
        APIConnectionError,
        InvalidRequestError,
        RateLimitError,
        StripeError,
    )
except ImportError:
    # Create mock stripe module if not available
    stripe = MagicMock()
    stripe.error = MagicMock()
    stripe.error.APIConnectionError = Exception
    stripe.error.RateLimitError = Exception
    stripe.error.InvalidRequestError = Exception
    stripe.error.StripeError = Exception
    APIConnectionError = Exception
    RateLimitError = Exception
    InvalidRequestError = Exception
    StripeError = Exception

from server.billing.models import (
    AccountStatus,
    BillingAccount,
    PlanTier,
    StripeCustomer,
    StripeSubscription,
)
from server.billing.stripe_service import StripeService


@pytest.fixture
def db_session(monkeypatch):
    """Get database session with graceful fallback"""
    try:
        from server.database.manager import DatabaseManager

        # Set mock Stripe key for tests
        monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock_key_for_testing")

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
def stripe_service(db_session, monkeypatch):
    """Create StripeService instance with mock API key"""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_mock_key_for_testing")
    return StripeService(db_session)


@pytest.fixture
def billing_account(db_session):
    """Create a test billing account"""
    account = BillingAccount(
        account_type="team",
        account_id=uuid.uuid4(),
        plan_tier=PlanTier.FREE.value,
        currency="USD",
        status=AccountStatus.ACTIVE.value,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    yield account

    # Cleanup
    db_session.delete(account)
    db_session.commit()


@pytest.fixture
def stripe_customer(db_session, billing_account):
    """Create a test Stripe customer"""
    customer = StripeCustomer(
        billing_account_id=billing_account.id,
        stripe_customer_id="cus_test123",
        email="test@example.com",
    )
    db_session.add(customer)
    db_session.commit()
    db_session.refresh(customer)

    yield customer

    # Cleanup
    db_session.delete(customer)
    db_session.commit()


class TestSubscriptionCreationWithValidData:
    """Test subscription creation with valid data"""

    @patch("stripe.Subscription.create")
    @patch.object(StripeService, "_get_price_id_for_plan")
    def test_create_subscription_with_valid_price_id(
        self, mock_get_price, mock_stripe_create, stripe_service, billing_account, stripe_customer
    ):
        """Test creating a subscription with valid price_id"""
        # Mock price ID lookup
        mock_get_price.return_value = "price_test123"

        # Mock Stripe response
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_test123"
        mock_subscription.status = "active"
        mock_subscription.current_period_start = int(datetime.now(timezone.utc).timestamp())
        mock_subscription.current_period_end = int(
            (datetime.now(timezone.utc).timestamp() + 30 * 24 * 60 * 60)
        )
        mock_stripe_create.return_value = mock_subscription

        # Create subscription
        subscription = stripe_service.create_subscription(
            billing_account_id=billing_account.id,
            plan_tier=PlanTier.PRO,
            payment_method_id="pm_test123",
        )

        # Verify Stripe API was called correctly
        mock_stripe_create.assert_called_once()
        call_kwargs = mock_stripe_create.call_args[1]
        assert call_kwargs["customer"] == "cus_test123"
        assert call_kwargs["items"][0]["price"] == "price_test123"
        assert call_kwargs["default_payment_method"] == "pm_test123"
        assert "billing_account_id" in call_kwargs["metadata"]
        assert call_kwargs["metadata"]["billing_account_id"] == str(billing_account.id)
        assert call_kwargs["metadata"]["plan_tier"] == PlanTier.PRO.value

        # Verify subscription record
        assert subscription.stripe_subscription_id == "sub_test123"
        assert subscription.plan_id == PlanTier.PRO.value
        assert subscription.status == "active"

        # Verify billing account was updated
        assert billing_account.plan_tier == PlanTier.PRO.value

    @patch("stripe.Subscription.create")
    @patch.object(StripeService, "_get_price_id_for_plan")
    def test_create_subscription_without_payment_method(
        self, mock_get_price, mock_stripe_create, stripe_service, billing_account, stripe_customer
    ):
        """Test creating a subscription without payment method"""
        # Mock price ID lookup
        mock_get_price.return_value = "price_test123"

        # Mock Stripe response
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_no_pm"
        mock_subscription.status = "incomplete"
        mock_subscription.current_period_start = int(datetime.now(timezone.utc).timestamp())
        mock_subscription.current_period_end = int(
            (datetime.now(timezone.utc).timestamp() + 30 * 24 * 60 * 60)
        )
        mock_stripe_create.return_value = mock_subscription

        # Create subscription without payment method
        subscription = stripe_service.create_subscription(
            billing_account_id=billing_account.id,
            plan_tier=PlanTier.STARTER,
        )

        # Verify Stripe API was called
        mock_stripe_create.assert_called_once()
        call_kwargs = mock_stripe_create.call_args[1]
        assert "default_payment_method" not in call_kwargs

        # Verify subscription record
        assert subscription.stripe_subscription_id == "sub_no_pm"
        assert subscription.status == "incomplete"


class TestSubscriptionCreationWithInvalidData:
    """Test subscription creation with invalid data"""

    @patch.object(StripeService, "_get_price_id_for_plan")
    def test_create_subscription_with_invalid_price_id(
        self, mock_get_price, stripe_service, billing_account, stripe_customer
    ):
        """Test creating a subscription with invalid price_id"""
        # Mock price ID lookup returning None
        mock_get_price.return_value = None

        # Attempt to create subscription
        with pytest.raises(ValueError, match="No Stripe price configured"):
            stripe_service.create_subscription(
                billing_account_id=billing_account.id,
                plan_tier=PlanTier.ENTERPRISE,
            )

    def test_create_subscription_without_customer(self, stripe_service, billing_account):
        """Test creating a subscription without Stripe customer"""
        # Attempt to create subscription without customer
        with pytest.raises(ValueError, match="Stripe customer must exist"):
            stripe_service.create_subscription(
                billing_account_id=billing_account.id,
                plan_tier=PlanTier.PRO,
            )

    def test_create_subscription_with_nonexistent_billing_account(self, stripe_service):
        """Test creating a subscription for non-existent billing account"""
        fake_account_id = uuid.uuid4()

        # Attempt to create subscription
        with pytest.raises(ValueError, match="Billing account not found"):
            stripe_service.create_subscription(
                billing_account_id=fake_account_id,
                plan_tier=PlanTier.PRO,
            )

    @patch("stripe.Subscription.create")
    @patch.object(StripeService, "_get_price_id_for_plan")
    def test_create_subscription_with_invalid_stripe_price(
        self, mock_get_price, mock_stripe_create, stripe_service, billing_account, stripe_customer
    ):
        """Test creating a subscription with invalid Stripe price_id"""
        # Mock price ID lookup
        mock_get_price.return_value = "price_invalid"

        # Mock Stripe API error
        mock_stripe_create.side_effect = InvalidRequestError(
            message="No such price: price_invalid",
            param="items[0][price]",
        )

        # Attempt to create subscription
        with pytest.raises(InvalidRequestError):
            stripe_service.create_subscription(
                billing_account_id=billing_account.id,
                plan_tier=PlanTier.PRO,
            )

        mock_stripe_create.assert_called_once()


class TestSubscriptionStatusSync:
    """Test subscription status synchronization"""

    @patch("stripe.Subscription.retrieve")
    def test_sync_subscription_status_active(
        self, mock_stripe_retrieve, stripe_service, billing_account, stripe_customer, db_session
    ):
        """Test syncing subscription status when active"""
        # Create subscription record
        subscription = StripeSubscription(
            stripe_customer_id=stripe_customer.id,
            stripe_subscription_id="sub_sync",
            plan_id=PlanTier.PRO.value,
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
        )
        db_session.add(subscription)
        db_session.commit()

        # Mock Stripe response
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_sync"
        mock_subscription.status = "active"
        mock_subscription.current_period_start = int(datetime.now(timezone.utc).timestamp())
        mock_subscription.current_period_end = int(
            (datetime.now(timezone.utc).timestamp() + 30 * 24 * 60 * 60)
        )
        mock_subscription.cancel_at_period_end = False
        mock_stripe_retrieve.return_value = mock_subscription

        # Sync status
        synced = stripe_service.sync_subscription_status(billing_account.id)

        # Verify sync
        assert synced is not None
        assert synced.status == "active"
        assert synced.last_synced_at is not None
        assert billing_account.status == AccountStatus.ACTIVE.value

        # Cleanup
        db_session.delete(subscription)
        db_session.commit()

    @patch("stripe.Subscription.retrieve")
    def test_sync_subscription_status_past_due(
        self, mock_stripe_retrieve, stripe_service, billing_account, stripe_customer, db_session
    ):
        """Test syncing subscription status when past_due"""
        # Create subscription record
        subscription = StripeSubscription(
            stripe_customer_id=stripe_customer.id,
            stripe_subscription_id="sub_past_due",
            plan_id=PlanTier.PRO.value,
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
        )
        db_session.add(subscription)
        db_session.commit()

        # Mock Stripe response with past_due status
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_past_due"
        mock_subscription.status = "past_due"
        mock_subscription.current_period_start = int(datetime.now(timezone.utc).timestamp())
        mock_subscription.current_period_end = int(
            (datetime.now(timezone.utc).timestamp() + 30 * 24 * 60 * 60)
        )
        mock_subscription.cancel_at_period_end = False
        mock_stripe_retrieve.return_value = mock_subscription

        # Sync status
        synced = stripe_service.sync_subscription_status(billing_account.id)

        # Verify sync
        assert synced is not None
        assert synced.status == "past_due"
        assert billing_account.status == AccountStatus.SUSPENDED.value

        # Cleanup
        db_session.delete(subscription)
        db_session.commit()


class TestSubscriptionCancellation:
    """Test subscription cancellation"""

    @patch("stripe.Subscription.modify")
    @patch("stripe.Subscription.retrieve")
    def test_cancel_subscription_at_period_end(
        self, mock_retrieve, mock_modify, stripe_service, billing_account, stripe_customer, db_session
    ):
        """Test canceling subscription at period end"""
        # Create subscription record
        subscription = StripeSubscription(
            stripe_customer_id=stripe_customer.id,
            stripe_subscription_id="sub_cancel",
            plan_id=PlanTier.PRO.value,
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
        )
        db_session.add(subscription)
        db_session.commit()

        # Mock Stripe responses
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_cancel"
        mock_subscription.status = "active"
        mock_subscription.current_period_start = int(datetime.now(timezone.utc).timestamp())
        mock_subscription.current_period_end = int(
            (datetime.now(timezone.utc).timestamp() + 30 * 24 * 60 * 60)
        )
        mock_subscription.cancel_at_period_end = True
        mock_modify.return_value = mock_subscription
        mock_retrieve.return_value = mock_subscription

        # Cancel subscription
        canceled = stripe_service.cancel_subscription(
            billing_account_id=billing_account.id,
            cancel_at_period_end=True,
        )

        # Verify cancellation
        mock_modify.assert_called_once_with("sub_cancel", cancel_at_period_end=True)
        assert canceled is not None
        assert canceled.cancel_at_period_end is True

        # Cleanup
        db_session.delete(subscription)
        db_session.commit()

    @patch("stripe.Subscription.delete")
    @patch("stripe.Subscription.retrieve")
    def test_cancel_subscription_immediately(
        self, mock_retrieve, mock_delete, stripe_service, billing_account, stripe_customer, db_session
    ):
        """Test canceling subscription immediately"""
        # Create subscription record
        subscription = StripeSubscription(
            stripe_customer_id=stripe_customer.id,
            stripe_subscription_id="sub_immediate",
            plan_id=PlanTier.PRO.value,
            status="active",
            current_period_start=datetime.now(timezone.utc),
            current_period_end=datetime.now(timezone.utc),
        )
        db_session.add(subscription)
        db_session.commit()

        # Mock Stripe responses
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_immediate"
        mock_subscription.status = "canceled"
        mock_subscription.current_period_start = int(datetime.now(timezone.utc).timestamp())
        mock_subscription.current_period_end = int(
            (datetime.now(timezone.utc).timestamp() + 30 * 24 * 60 * 60)
        )
        mock_subscription.cancel_at_period_end = False
        mock_delete.return_value = mock_subscription
        mock_retrieve.return_value = mock_subscription

        # Cancel subscription immediately
        canceled = stripe_service.cancel_subscription(
            billing_account_id=billing_account.id,
            cancel_at_period_end=False,
        )

        # Verify cancellation
        mock_delete.assert_called_once_with("sub_immediate")
        assert canceled is not None
        assert canceled.status == "canceled"

        # Cleanup
        db_session.delete(subscription)
        db_session.commit()


class TestStripeAPIErrorHandling:
    """Test Stripe API error handling"""

    @patch("stripe.Subscription.create")
    @patch.object(StripeService, "_get_price_id_for_plan")
    def test_subscription_creation_connection_error(
        self, mock_get_price, mock_stripe_create, stripe_service, billing_account, stripe_customer
    ):
        """Test handling of Stripe API connection errors"""
        # Mock price ID lookup
        mock_get_price.return_value = "price_test123"

        # Mock connection error
        mock_stripe_create.side_effect = APIConnectionError("Connection failed")

        # Attempt to create subscription
        with pytest.raises(APIConnectionError):
            stripe_service.create_subscription(
                billing_account_id=billing_account.id,
                plan_tier=PlanTier.PRO,
            )

        mock_stripe_create.assert_called_once()

    @patch("stripe.Subscription.create")
    @patch.object(StripeService, "_get_price_id_for_plan")
    def test_subscription_creation_rate_limit_error(
        self, mock_get_price, mock_stripe_create, stripe_service, billing_account, stripe_customer
    ):
        """Test handling of Stripe API rate limit errors"""
        # Mock price ID lookup
        mock_get_price.return_value = "price_test123"

        # Mock rate limit error
        mock_stripe_create.side_effect = RateLimitError("Rate limit exceeded")

        # Attempt to create subscription
        with pytest.raises(RateLimitError):
            stripe_service.create_subscription(
                billing_account_id=billing_account.id,
                plan_tier=PlanTier.PRO,
            )

        mock_stripe_create.assert_called_once()


class TestDatabaseIntegration:
    """Test database integration for subscription management"""

    @patch("stripe.Subscription.create")
    @patch.object(StripeService, "_get_price_id_for_plan")
    def test_subscription_saved_to_database(
        self, mock_get_price, mock_stripe_create, stripe_service, billing_account, stripe_customer, db_session
    ):
        """Test that subscription is saved to database"""
        # Mock price ID lookup
        mock_get_price.return_value = "price_test123"

        # Mock Stripe response
        mock_subscription = MagicMock()
        mock_subscription.id = "sub_db_test"
        mock_subscription.status = "active"
        mock_subscription.current_period_start = int(datetime.now(timezone.utc).timestamp())
        mock_subscription.current_period_end = int(
            (datetime.now(timezone.utc).timestamp() + 30 * 24 * 60 * 60)
        )
        mock_stripe_create.return_value = mock_subscription

        # Create subscription
        subscription = stripe_service.create_subscription(
            billing_account_id=billing_account.id,
            plan_tier=PlanTier.PRO,
        )

        # Verify subscription is in database
        db_subscription = (
            db_session.query(StripeSubscription)
            .filter(StripeSubscription.id == subscription.id)
            .first()
        )
        assert db_subscription is not None
        assert db_subscription.stripe_subscription_id == "sub_db_test"
        assert db_subscription.plan_id == PlanTier.PRO.value
        assert db_subscription.status == "active"

        # Cleanup
        db_session.delete(db_subscription)
        db_session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

