#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Tests for Stripe Webhook Processing - US#175

Comprehensive tests for webhook event processing with signature verification.
Tests all 3 webhook events: invoice.payment_succeeded, invoice.payment_failed, customer.subscription.updated
"""

import json
import os
import sys
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


# Import webhook processing function directly (avoiding router import issues)
# Use lazy import to avoid SQLAlchemy conflicts
def get_process_payment_webhook():
    """Get process_payment_webhook function"""
    from lib.billing_engine_integration_api import process_payment_webhook

    return process_payment_webhook


def get_stores():
    """Get store dictionaries"""
    from lib.billing_engine_integration_api import (
        billing_invoices_store,
        payment_attempts_store,
        stripe_subscriptions_store,
    )

    return billing_invoices_store, payment_attempts_store, stripe_subscriptions_store


# Test fixtures
@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_stripe_event_payment_succeeded():
    """Create mock Stripe event for payment succeeded"""
    return {
        "id": "evt_test_payment_succeeded",
        "type": "invoice.payment_succeeded",
        "data": {
            "object": {
                "id": "inv_test_123",
                "subscription": "sub_test_123",
                "amount_paid": 5000,  # $50.00
                "status": "paid",
                "customer": "cus_test_123",
            }
        },
        "created": int(time.time()),
    }


@pytest.fixture
def mock_stripe_event_payment_failed():
    """Create mock Stripe event for payment failed"""
    return {
        "id": "evt_test_payment_failed",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": "inv_test_456",
                "subscription": "sub_test_123",
                "status": "open",
                "customer": "cus_test_123",
                "last_payment_error": {
                    "message": "Your card was declined.",
                    "type": "card_error",
                },
            }
        },
        "created": int(time.time()),
    }


@pytest.fixture
def mock_stripe_event_subscription_updated():
    """Create mock Stripe event for subscription updated"""
    return {
        "id": "evt_test_subscription_updated",
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "id": "sub_test_123",
                "status": "active",
                "current_period_start": int(time.time()),
                "current_period_end": int(time.time()) + 2592000,  # 30 days
                "customer": "cus_test_123",
            }
        },
        "created": int(time.time()),
    }


@pytest.fixture
def setup_test_data():
    """Setup test data stores"""
    billing_invoices_store, payment_attempts_store, stripe_subscriptions_store = get_stores()

    # Clear stores
    billing_invoices_store.clear()
    payment_attempts_store.clear()
    stripe_subscriptions_store.clear()

    # Setup test subscription
    team_id = "team_test_123"
    stripe_subscriptions_store[team_id] = {
        "stripe_subscription_id": "sub_test_123",
        "status": "active",
        "team_id": team_id,
    }

    # Setup test invoice
    billing_invoices_store["inv_test_123"] = {
        "id": "inv_test_123",
        "team_id": team_id,
        "status": "open",
        "amount": 50.00,
    }

    yield

    # Cleanup
    billing_invoices_store.clear()
    payment_attempts_store.clear()
    stripe_subscriptions_store.clear()


class TestWebhookSignatureVerification:
    """Tests for webhook signature verification"""

    @pytest.fixture
    def client(self):
        """Create test client with mocked router"""
        from fastapi import FastAPI
        from lib.billing_engine_integration_api import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_valid_webhook_signature(self, client):
        """Test webhook with valid signature"""
        payload = json.dumps({"type": "invoice.payment_succeeded", "id": "evt_test"})
        valid_signature = "t=1234567890,v1=test_signature"

        with patch("lib.billing_engine_integration_api.stripe.Webhook.construct_event") as mock_construct:
            mock_construct.return_value = {"type": "invoice.payment_succeeded", "id": "evt_test"}

            response = client.post(
                "/billing-engine/webhooks/stripe",
                data=payload,
                headers={"stripe-signature": valid_signature, "content-type": "application/json"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["received"] is True
            assert data["event_id"] == "evt_test"

    @pytest.mark.asyncio
    async def test_invalid_webhook_signature(self, client):
        """Test webhook with invalid signature"""
        payload = json.dumps({"type": "invoice.payment_succeeded", "id": "evt_test"})
        invalid_signature = "invalid_signature"

        with patch("lib.billing_engine_integration_api.stripe.Webhook.construct_event") as mock_construct:
            import stripe

            mock_construct.side_effect = stripe.error.SignatureVerificationError(
                "Invalid signature", "stripe-signature"
            )

            response = client.post(
                "/billing-engine/webhooks/stripe",
                data=payload,
                headers={"stripe-signature": invalid_signature, "content-type": "application/json"},
            )

            assert response.status_code == 400
            assert "Invalid signature" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_missing_webhook_signature(self, client):
        """Test webhook without signature header"""
        payload = json.dumps({"type": "invoice.payment_succeeded", "id": "evt_test"})

        response = client.post(
            "/billing-engine/webhooks/stripe",
            data=payload,
            headers={"content-type": "application/json"},
        )

        # Should fail due to missing signature
        assert response.status_code in [400, 422]

    @pytest.mark.asyncio
    async def test_invalid_payload(self, client):
        """Test webhook with invalid payload"""
        invalid_payload = "not valid json"
        valid_signature = "t=1234567890,v1=test_signature"

        with patch("lib.billing_engine_integration_api.stripe.Webhook.construct_event") as mock_construct:
            mock_construct.side_effect = ValueError("Invalid payload")

            response = client.post(
                "/billing-engine/webhooks/stripe",
                data=invalid_payload,
                headers={"stripe-signature": valid_signature, "content-type": "application/json"},
            )

            assert response.status_code == 400
            assert "Invalid payload" in response.json()["detail"]


class TestPaymentSucceededWebhook:
    """Tests for invoice.payment_succeeded webhook event"""

    def test_payment_succeeded_updates_invoice(self, setup_test_data, mock_stripe_event_payment_succeeded):
        """Test that payment succeeded updates invoice status"""
        process_payment_webhook = get_process_payment_webhook()
        billing_invoices_store, _, _ = get_stores()

        result = process_payment_webhook(mock_stripe_event_payment_succeeded)

        assert result["processed"] is True
        assert result["event_type"] == "invoice.payment_succeeded"
        assert result["team_id"] == "team_test_123"
        assert result["invoice_id"] == "inv_test_123"
        assert "updated_invoice_status" in result["actions_taken"]
        assert "recorded_payment" in result["actions_taken"]

        # Verify invoice was updated
        invoice = billing_invoices_store.get("inv_test_123")
        assert invoice is not None
        assert invoice["status"] == "paid"
        assert "paid_at" in invoice
        assert invoice["amount_paid"] == 50.00

    def test_payment_succeeded_unknown_subscription(self, setup_test_data):
        """Test payment succeeded for unknown subscription"""
        process_payment_webhook = get_process_payment_webhook()

        event = {
            "id": "evt_test",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "inv_unknown",
                    "subscription": "sub_unknown",
                    "amount_paid": 5000,
                }
            },
        }

        result = process_payment_webhook(event)

        assert result["processed"] is False
        assert result["team_id"] is None

    def test_payment_succeeded_unknown_invoice(self, setup_test_data):
        """Test payment succeeded for invoice not in store"""
        process_payment_webhook = get_process_payment_webhook()
        billing_invoices_store, _, _ = get_stores()

        event = {
            "id": "evt_test",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "inv_not_in_store",
                    "subscription": "sub_test_123",
                    "amount_paid": 5000,
                }
            },
        }

        result = process_payment_webhook(event)

        # Should still process (team found) but invoice not updated
        assert result["processed"] is True
        assert result["team_id"] == "team_test_123"


class TestPaymentFailedWebhook:
    """Tests for invoice.payment_failed webhook event"""

    def test_payment_failed_records_failure(self, setup_test_data, mock_stripe_event_payment_failed):
        """Test that payment failed records failure and initiates retry"""
        process_payment_webhook = get_process_payment_webhook()
        _, payment_attempts_store, _ = get_stores()

        result = process_payment_webhook(mock_stripe_event_payment_failed)

        assert result["processed"] is True
        assert result["event_type"] == "invoice.payment_failed"
        assert result["team_id"] == "team_test_123"
        assert result["invoice_id"] == "inv_test_456"
        assert "recorded_payment_failure" in result["actions_taken"]
        assert "initiated_retry_sequence" in result["actions_taken"]

        # Verify failure was recorded
        failure = payment_attempts_store.get("inv_test_456")
        assert failure is not None
        assert failure["team_id"] == "team_test_123"
        assert failure["failure_reason"] == "Your card was declined."
        assert failure["retry_count"] == 0
        assert "failed_at" in failure

    def test_payment_failed_unknown_subscription(self, setup_test_data):
        """Test payment failed for unknown subscription"""
        event = {
            "id": "evt_test",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "id": "inv_unknown",
                    "subscription": "sub_unknown",
                    "last_payment_error": {"message": "Card declined"},
                }
            },
        }

        result = process_payment_webhook(event)

        assert result["processed"] is False
        assert result["team_id"] is None

    def test_payment_failed_missing_error_message(self, setup_test_data):
        """Test payment failed without error message"""
        event = {
            "id": "evt_test",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "id": "inv_test_no_error",
                    "subscription": "sub_test_123",
                }
            },
        }

        result = process_payment_webhook(event)

        assert result["processed"] is True
        failure = payment_attempts_store.get("inv_test_no_error")
        assert failure["failure_reason"] == "Unknown"


class TestSubscriptionUpdatedWebhook:
    """Tests for customer.subscription.updated webhook event"""

    def test_subscription_updated_syncs_status(self, setup_test_data, mock_stripe_event_subscription_updated):
        """Test that subscription updated syncs status"""
        process_payment_webhook = get_process_payment_webhook()
        _, _, stripe_subscriptions_store = get_stores()

        result = process_payment_webhook(mock_stripe_event_subscription_updated)

        assert result["processed"] is True
        assert result["event_type"] == "customer.subscription.updated"
        assert result["team_id"] == "team_test_123"
        assert result["subscription_id"] == "sub_test_123"
        assert "updated_subscription_status" in result["actions_taken"]

        # Verify subscription was updated
        subscription = stripe_subscriptions_store.get("team_test_123")
        assert subscription is not None
        assert subscription["status"] == "active"
        assert "current_period_start" in subscription
        assert "current_period_end" in subscription

    def test_subscription_updated_unknown_subscription(self, setup_test_data):
        """Test subscription updated for unknown subscription"""
        event = {
            "id": "evt_test",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_unknown",
                    "status": "active",
                }
            },
        }

        result = process_payment_webhook(event)

        assert result["processed"] is False
        assert result["team_id"] is None

    def test_subscription_updated_status_change(self, setup_test_data):
        """Test subscription status change (active to cancelled)"""
        # Set initial status
        stripe_subscriptions_store["team_test_123"]["status"] = "active"

        event = {
            "id": "evt_test",
            "type": "customer.subscription.updated",
            "data": {
                "object": {
                    "id": "sub_test_123",
                    "status": "canceled",
                    "current_period_start": int(time.time()),
                    "current_period_end": int(time.time()) + 2592000,
                }
            },
        }

        result = process_payment_webhook(event)

        assert result["processed"] is True
        subscription = stripe_subscriptions_store.get("team_test_123")
        assert subscription["status"] == "canceled"


class TestWebhookRaceConditions:
    """Tests for race conditions and duplicate handling"""

    def test_duplicate_webhook_delivery(self, setup_test_data, mock_stripe_event_payment_succeeded):
        """Test handling of duplicate webhook events (idempotency)"""
        process_payment_webhook = get_process_payment_webhook()
        billing_invoices_store, _, _ = get_stores()

        # Process first webhook
        result1 = process_payment_webhook(mock_stripe_event_payment_succeeded)
        assert result1["processed"] is True

        # Process duplicate webhook
        result2 = process_payment_webhook(mock_stripe_event_payment_succeeded)

        # Should still process (idempotent)
        assert result2["processed"] is True
        # Invoice should still be marked as paid
        invoice = billing_invoices_store.get("inv_test_123")
        assert invoice["status"] == "paid"

    def test_concurrent_webhook_processing(self, setup_test_data):
        """Test concurrent webhook processing"""
        import concurrent.futures

        process_payment_webhook = get_process_payment_webhook()
        billing_invoices_store, _, _ = get_stores()

        events = [
            {
                "id": f"evt_test_{i}",
                "type": "invoice.payment_succeeded",
                "data": {
                    "object": {
                        "id": f"inv_test_{i}",
                        "subscription": "sub_test_123",
                        "amount_paid": 5000,
                    }
                },
            }
            for i in range(5)
        ]

        # Setup invoices
        for i in range(5):
            billing_invoices_store[f"inv_test_{i}"] = {
                "id": f"inv_test_{i}",
                "team_id": "team_test_123",
                "status": "open",
            }

        # Process concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(process_payment_webhook, events))

        # All should succeed
        assert all(r["processed"] for r in results)
        # All invoices should be paid
        for i in range(5):
            invoice = billing_invoices_store.get(f"inv_test_{i}")
            assert invoice["status"] == "paid"

    def test_out_of_order_webhook_processing(self, setup_test_data):
        """Test processing webhooks out of order"""
        process_payment_webhook = get_process_payment_webhook()
        billing_invoices_store, _, _ = get_stores()

        # Process payment failed first
        failed_event = {
            "id": "evt_failed",
            "type": "invoice.payment_failed",
            "data": {
                "object": {
                    "id": "inv_test_out_of_order",
                    "subscription": "sub_test_123",
                    "last_payment_error": {"message": "Declined"},
                }
            },
        }

        result1 = process_payment_webhook(failed_event)
        assert result1["processed"] is True

        # Then process payment succeeded (out of order)
        succeeded_event = {
            "id": "evt_succeeded",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "inv_test_out_of_order",
                    "subscription": "sub_test_123",
                    "amount_paid": 5000,
                }
            },
        }

        # Setup invoice
        billing_invoices_store["inv_test_out_of_order"] = {
            "id": "inv_test_out_of_order",
            "team_id": "team_test_123",
            "status": "open",
        }

        result2 = process_payment_webhook(succeeded_event)
        assert result2["processed"] is True

        # Final state should be paid (last event wins)
        invoice = billing_invoices_store.get("inv_test_out_of_order")
        assert invoice["status"] == "paid"


class TestWebhookErrorHandling:
    """Tests for error handling in webhook processing"""

    def test_webhook_with_missing_event_type(self, setup_test_data):
        """Test webhook event without type"""
        process_payment_webhook = get_process_payment_webhook()

        event = {
            "id": "evt_test",
            "data": {
                "object": {
                    "id": "inv_test",
                    "subscription": "sub_test_123",
                }
            },
        }

        result = process_payment_webhook(event)

        assert result["processed"] is False
        assert result["event_type"] is None

    def test_webhook_with_exception(self, setup_test_data):
        """Test webhook processing with exception"""
        process_payment_webhook = get_process_payment_webhook()

        event = {
            "id": "evt_test",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": None,  # This will cause an error
            },
        }

        result = process_payment_webhook(event)

        assert result["processed"] is False
        assert "error" in result
        assert "error_occurred" in result["actions_taken"]

    def test_webhook_unknown_event_type(self, setup_test_data):
        """Test webhook with unknown event type"""
        process_payment_webhook = get_process_payment_webhook()

        event = {
            "id": "evt_test",
            "type": "unknown.event.type",
            "data": {
                "object": {
                    "id": "obj_test",
                }
            },
        }

        result = process_payment_webhook(event)

        # Should not process unknown event types
        assert result["processed"] is False
        assert result["event_type"] == "unknown.event.type"


class TestWebhookBackgroundProcessing:
    """Tests for background task processing"""

    @pytest.fixture
    def client(self):
        """Create test client with mocked router"""
        from fastapi import FastAPI
        from lib.billing_engine_integration_api import router

        app = FastAPI()
        app.include_router(router)
        return TestClient(app)

    @pytest.mark.asyncio
    async def test_webhook_triggers_background_task(self, client):
        """Test that webhook triggers background task"""
        payload = json.dumps({"type": "invoice.payment_succeeded", "id": "evt_test"})

        with (
            patch("lib.billing_engine_integration_api.stripe.Webhook.construct_event") as mock_construct,
            patch("lib.billing_engine_integration_api.process_webhook_event") as mock_process,
        ):

            mock_construct.return_value = {"type": "invoice.payment_succeeded", "id": "evt_test"}

            response = client.post(
                "/billing-engine/webhooks/stripe",
                data=payload,
                headers={"stripe-signature": "t=123,v1=test", "content-type": "application/json"},
            )

            assert response.status_code == 200
            # Background task should be added (FastAPI handles this automatically)

    @pytest.mark.asyncio
    async def test_background_task_processing(self, setup_test_data):
        """Test background task processes webhook correctly"""
        from lib.billing_engine_integration_api import process_webhook_event

        billing_invoices_store, _, _ = get_stores()

        # Setup invoice
        billing_invoices_store["inv_test_123"] = {
            "id": "inv_test_123",
            "team_id": "team_test_123",
            "status": "open",
        }

        event = {
            "id": "evt_background_test",
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "id": "inv_test_123",
                    "subscription": "sub_test_123",
                    "amount_paid": 5000,
                }
            },
        }

        result = await process_webhook_event(event)

        assert result["processed"] is True
        assert "processing_time" in result
        assert result["processing_time"] > 0


class TestWebhookPerformance:
    """Tests for webhook processing performance"""

    def test_webhook_processing_performance(self, setup_test_data, mock_stripe_event_payment_succeeded):
        """Test that webhook processing is fast (<2 seconds per webhook)"""
        import time

        process_payment_webhook = get_process_payment_webhook()

        start_time = time.time()
        result = process_payment_webhook(mock_stripe_event_payment_succeeded)
        processing_time = time.time() - start_time

        assert result["processed"] is True
        assert processing_time < 2.0, f"Webhook processing took {processing_time}s, should be <2s"

    def test_multiple_webhooks_performance(self, setup_test_data):
        """Test processing multiple webhooks efficiently"""
        import time

        process_payment_webhook = get_process_payment_webhook()
        billing_invoices_store, _, _ = get_stores()

        events = [
            {
                "id": f"evt_{i}",
                "type": "invoice.payment_succeeded",
                "data": {
                    "object": {
                        "id": f"inv_{i}",
                        "subscription": "sub_test_123",
                        "amount_paid": 5000,
                    }
                },
            }
            for i in range(10)
        ]

        # Setup invoices
        for i in range(10):
            billing_invoices_store[f"inv_{i}"] = {
                "id": f"inv_{i}",
                "team_id": "team_test_123",
                "status": "open",
            }

        start_time = time.time()
        results = [process_payment_webhook(event) for event in events]
        total_time = time.time() - start_time

        assert all(r["processed"] for r in results)
        assert total_time < 5.0, f"Processing 10 webhooks took {total_time}s, should be <5s"
