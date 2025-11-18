#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Stripe Integration Service
# Developer D - January 2025
#
# BILL-004: Stripe subscription management and status sync

"""
Stripe integration service for SPEC-147 billing.

Features:
- Stripe customer creation
- Subscription management
- Webhook handling
- Payment method management
- Subscription lifecycle handling
"""

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import stripe

    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False
    stripe = None  # type: ignore

from sqlalchemy.orm import Session

from .models import (
    AccountStatus,
    BillingAccount,
    PlanTier,
    StripeCustomer,
    StripeInvoice,
    StripeSubscription,
)


class StripeService:
    """
    Service for Stripe integration.

    Features:
    - Customer creation and management
    - Subscription lifecycle management
    - Webhook event handling
    - Payment method management
    - Status synchronization
    """

    def __init__(self, db: Session, api_key: Optional[str] = None):
        """
        Initialize Stripe service.

        Args:
            db: Database session
            api_key: Stripe API key (optional, uses env var if not provided)
        """
        self.db = db

        if not STRIPE_AVAILABLE:
            raise ImportError("stripe package not available. Install with: pip install stripe")

        # Initialize Stripe API key
        self.api_key = api_key or os.getenv("STRIPE_SECRET_KEY")
        if not self.api_key:
            raise ValueError("Stripe API key not provided. Set STRIPE_SECRET_KEY environment variable.")

        stripe.api_key = self.api_key

    def create_customer(
        self,
        billing_account_id: uuid.UUID,
        email: str,
        name: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> StripeCustomer:
        """
        Create Stripe customer for billing account.

        Args:
            billing_account_id: Billing account ID
            email: Customer email
            name: Customer name (optional)
            metadata: Additional metadata (optional)

        Returns:
            StripeCustomer instance
        """
        # Check if customer already exists
        existing = self.db.query(StripeCustomer).filter(StripeCustomer.billing_account_id == billing_account_id).first()

        if existing:
            return existing

        # Create Stripe customer
        stripe_customer_data = stripe.Customer.create(
            email=email,
            name=name,
            metadata={
                **(metadata or {}),
                "billing_account_id": str(billing_account_id),
            },
        )

        # Create local record
        stripe_customer = StripeCustomer(
            billing_account_id=billing_account_id,
            stripe_customer_id=stripe_customer_data.id,
            email=email,
            metadata=metadata or {},
        )

        self.db.add(stripe_customer)
        self.db.commit()
        self.db.refresh(stripe_customer)

        return stripe_customer

    def create_subscription(
        self,
        billing_account_id: uuid.UUID,
        plan_tier: PlanTier,
        payment_method_id: Optional[str] = None,
        billing_cycle_anchor: Optional[int] = None,
        trial_days: Optional[int] = None,
    ) -> StripeSubscription:
        """
        Create Stripe subscription for billing account.

        Args:
            billing_account_id: Billing account ID
            plan_tier: Plan tier (FREE, STARTER, PRO, ENTERPRISE)
            payment_method_id: Stripe payment method ID (optional)
            billing_cycle_anchor: Unix timestamp for billing cycle anchor (optional, US#164)
            trial_days: Trial period in days (optional, US#164)

        Returns:
            StripeSubscription instance
        """
        # Get billing account
        billing_account = self.db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()

        if not billing_account:
            raise ValueError(f"Billing account not found: {billing_account_id}")

        # Get or create Stripe customer
        stripe_customer_record = (
            self.db.query(StripeCustomer).filter(StripeCustomer.billing_account_id == billing_account_id).first()
        )

        if not stripe_customer_record:
            # Create customer (requires email - would need to get from user/org/team)
            raise ValueError("Stripe customer must exist before creating subscription")

        # Get Stripe price ID for plan tier
        price_id = self._get_price_id_for_plan(plan_tier)
        if not price_id:
            raise ValueError(f"No Stripe price configured for plan tier: {plan_tier.value}")

        # Create Stripe subscription (US#164: with billing cycle anchor and trial support)
        subscription_data = {
            "customer": stripe_customer_record.stripe_customer_id,
            "items": [{"price": price_id}],
            "metadata": {
                "billing_account_id": str(billing_account_id),
                "plan_tier": plan_tier.value,
            },
        }

        # Set billing cycle anchor (US#164)
        if billing_cycle_anchor:
            subscription_data["billing_cycle_anchor"] = billing_cycle_anchor
        # Otherwise Stripe will set it to current time

        # Set trial period (US#164)
        if trial_days:
            subscription_data["trial_period_days"] = trial_days

        if payment_method_id:
            subscription_data["default_payment_method"] = payment_method_id

        stripe_subscription = stripe.Subscription.create(**subscription_data)

        # Create local subscription record
        subscription = StripeSubscription(
            stripe_customer_id=stripe_customer_record.id,
            stripe_subscription_id=stripe_subscription.id,
            plan_id=plan_tier.value,
            status=stripe_subscription.status,
            current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
            current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end),
        )

        self.db.add(subscription)

        # Update billing account plan tier
        billing_account.plan_tier = plan_tier.value
        self.db.commit()
        self.db.refresh(subscription)

        return subscription

    def sync_subscription_status(self, billing_account_id: uuid.UUID) -> Optional[StripeSubscription]:
        """
        Sync subscription status from Stripe (US#164: enhanced with past_due handling).

        Args:
            billing_account_id: Billing account ID

        Returns:
            Updated StripeSubscription instance or None
        """
        # Find subscription via StripeCustomer (US#164: fix query)
        stripe_customer = (
            self.db.query(StripeCustomer).filter(StripeCustomer.billing_account_id == billing_account_id).first()
        )

        if not stripe_customer:
            return None

        subscription = (
            self.db.query(StripeSubscription)
            .filter(StripeSubscription.stripe_customer_id == stripe_customer.id)
            .first()
        )

        if not subscription:
            return None

        # Fetch latest from Stripe
        stripe_subscription = stripe.Subscription.retrieve(subscription.stripe_subscription_id)

        # Update local record
        subscription.status = stripe_subscription.status
        subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
        subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
        subscription.cancel_at_period_end = stripe_subscription.cancel_at_period_end
        subscription.last_synced_at = datetime.utcnow()

        # Update billing account status based on subscription status (US#164: enhanced handling)
        billing_account = self.db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()

        if billing_account:
            if stripe_subscription.status in ["active", "trialing"]:
                billing_account.status = AccountStatus.ACTIVE.value
            elif stripe_subscription.status == "past_due":
                billing_account.status = AccountStatus.SUSPENDED.value
                # TODO: Trigger past_due notification (US#164 requirement)
                logger.warning(
                    f"Subscription {subscription.stripe_subscription_id} is past_due",
                    extra={
                        "subscription_id": subscription.stripe_subscription_id,
                        "billing_account_id": str(billing_account_id),
                    },
                )
            elif stripe_subscription.status in ["canceled", "unpaid", "incomplete_expired"]:
                billing_account.status = AccountStatus.CANCELED.value

        self.db.commit()
        self.db.refresh(subscription)

        return subscription

    def cancel_subscription(
        self, billing_account_id: uuid.UUID, cancel_at_period_end: bool = True
    ) -> StripeSubscription:
        """
        Cancel Stripe subscription.

        Args:
            billing_account_id: Billing account ID
            cancel_at_period_end: Cancel at period end (default: True)

        Returns:
            Updated StripeSubscription instance
        """
        # Find subscription via StripeCustomer
        stripe_customer = (
            self.db.query(StripeCustomer).filter(StripeCustomer.billing_account_id == billing_account_id).first()
        )

        if not stripe_customer:
            raise ValueError(f"Stripe customer not found for billing account: {billing_account_id}")

        subscription = (
            self.db.query(StripeSubscription)
            .filter(StripeSubscription.stripe_customer_id == stripe_customer.id)
            .first()
        )

        if not subscription:
            raise ValueError(f"Subscription not found for billing account: {billing_account_id}")

        # Cancel in Stripe
        if cancel_at_period_end:
            stripe.Subscription.modify(subscription.stripe_subscription_id, cancel_at_period_end=True)
        else:
            stripe.Subscription.delete(subscription.stripe_subscription_id)
            subscription.status = "canceled"

        # Sync status
        return self.sync_subscription_status(billing_account_id)

    def handle_webhook_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Stripe webhook event with idempotency.

        US#165: Enhanced webhook handling with idempotency and all 8 event types.

        Args:
            event_type: Stripe event type (e.g., "customer.subscription.updated")
            event_data: Stripe event data (contains event ID for idempotency)

        Returns:
            Processing result
        """
        result = {
            "processed": False,
            "event_type": event_type,
            "message": "",
        }

        # Get event ID for idempotency (US#165)
        event_id = event_data.get("id") if isinstance(event_data, dict) else None
        if not event_id and isinstance(event_data, dict) and "object" in event_data:
            # Try to get from parent event structure
            event_id = event_data.get("id")

        # Check idempotency: if we've already processed this event, skip
        if event_id:
            from server.billing.models import StripeWebhookEvent

            existing = self.db.query(StripeWebhookEvent).filter(StripeWebhookEvent.stripe_event_id == event_id).first()
            if existing:
                logger.info(f"Webhook event {event_id} already processed, skipping (idempotency)")
                return {
                    "processed": True,
                    "event_type": event_type,
                    "event_id": event_id,
                    "message": "Event already processed (idempotency)",
                    "skipped": True,
                }

        try:
            # Extract event object if nested
            if isinstance(event_data, dict) and "object" in event_data:
                event_obj = event_data.get("object", {})
            else:
                event_obj = event_data

            # Route to appropriate handler (US#165: all 8 event types)
            if event_type == "customer.subscription.created":
                result = self._handle_subscription_created(event_obj)
            elif event_type == "customer.subscription.updated":
                result = self._handle_subscription_updated(event_obj, event_id)
            elif event_type == "customer.subscription.deleted":
                result = self._handle_subscription_deleted(event_obj)
            elif event_type == "invoice.payment_succeeded":
                result = self._handle_invoice_payment_succeeded(event_obj)
            elif event_type == "invoice.payment_failed":
                result = self._handle_invoice_payment_failed(event_obj)
            elif event_type == "charge.succeeded":
                result = self._handle_charge_succeeded(event_obj)
            elif event_type == "charge.failed":
                result = self._handle_charge_failed(event_obj)
            elif event_type == "payment_intent.succeeded":
                result = self._handle_payment_intent_succeeded(event_obj)
            else:
                result["message"] = f"Unhandled event type: {event_type}"

            # Store event ID for idempotency (US#165)
            if event_id and result.get("processed"):
                try:
                    from server.billing.models import StripeWebhookEvent

                    webhook_event = StripeWebhookEvent(
                        stripe_event_id=event_id,
                        event_type=event_type,
                        processed_at=datetime.utcnow(),
                    )
                    self.db.add(webhook_event)
                except Exception:
                    # StripeWebhookEvent model may not exist yet - skip storing
                    pass

            self.db.commit()
            result["event_id"] = event_id
        except Exception as e:
            self.db.rollback()
            result["error"] = str(e)
            result["message"] = f"Error processing webhook: {e}"
            logger.error(f"Webhook processing error: {e}", exc_info=True)

        return result

    def _handle_subscription_created(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.created webhook"""
        subscription_obj = event_data.get("object", {})
        stripe_subscription_id = subscription_obj.get("id")
        customer_id = subscription_obj.get("customer")

        # Find local subscription
        subscription = (
            self.db.query(StripeSubscription)
            .filter(StripeSubscription.stripe_subscription_id == stripe_subscription_id)
            .first()
        )

        if not subscription:
            # Create new subscription record
            stripe_customer = (
                self.db.query(StripeCustomer).filter(StripeCustomer.stripe_customer_id == customer_id).first()
            )

            if stripe_customer:
                # Get plan tier from metadata or default to free
                plan_tier = subscription_obj.get("metadata", {}).get("plan_tier", "free")

                subscription = StripeSubscription(
                    stripe_customer_id=stripe_customer.id,
                    stripe_subscription_id=stripe_subscription_id,
                    plan_id=plan_tier,
                    status=subscription_obj.get("status"),
                    current_period_start=datetime.fromtimestamp(subscription_obj.get("current_period_start", 0)),
                    current_period_end=datetime.fromtimestamp(subscription_obj.get("current_period_end", 0)),
                )
                self.db.add(subscription)

        return {"processed": True, "message": "Subscription created"}

    def _handle_subscription_updated(
        self, event_data: Dict[str, Any], event_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle subscription.updated webhook (US#164: with idempotency and enhanced status handling)"""
        subscription_obj = event_data if isinstance(event_data, dict) else {}
        stripe_subscription_id = subscription_obj.get("id")

        subscription = (
            self.db.query(StripeSubscription)
            .filter(StripeSubscription.stripe_subscription_id == stripe_subscription_id)
            .first()
        )

        if subscription:
            # Idempotency check: if we've already processed this event, skip (US#164)
            # In production, you'd store processed event IDs in a table
            # For now, we'll update based on subscription status changes

            old_status = subscription.status
            new_status = subscription_obj.get("status")

            subscription.status = new_status
            subscription.current_period_start = datetime.fromtimestamp(subscription_obj.get("current_period_start", 0))
            subscription.current_period_end = datetime.fromtimestamp(subscription_obj.get("current_period_end", 0))
            subscription.cancel_at_period_end = subscription_obj.get("cancel_at_period_end", False)
            subscription.last_synced_at = datetime.utcnow()

            # Update billing account status (US#164: enhanced status handling)
            stripe_customer = (
                self.db.query(StripeCustomer).filter(StripeCustomer.id == subscription.stripe_customer_id).first()
            )

            if stripe_customer:
                billing_account = (
                    self.db.query(BillingAccount)
                    .filter(BillingAccount.id == stripe_customer.billing_account_id)
                    .first()
                )

                if billing_account:
                    # Enhanced status mapping (US#164)
                    if new_status in ["active", "trialing"]:
                        billing_account.status = AccountStatus.ACTIVE.value
                    elif new_status == "past_due":
                        billing_account.status = AccountStatus.SUSPENDED.value
                        # TODO: Trigger past_due notification (US#164 requirement)
                        logger.warning(
                            f"Subscription {stripe_subscription_id} is past_due - billing account {billing_account.id} suspended",
                            extra={
                                "subscription_id": stripe_subscription_id,
                                "billing_account_id": str(billing_account.id),
                                "event_id": event_id,
                            },
                        )
                    elif new_status in ["canceled", "unpaid", "incomplete_expired"]:
                        billing_account.status = AccountStatus.CANCELED.value

                    # Handle trial period (US#164)
                    if new_status == "trialing" and old_status != "trialing":
                        logger.info(
                            f"Subscription {stripe_subscription_id} entered trial period",
                            extra={
                                "subscription_id": stripe_subscription_id,
                                "billing_account_id": str(billing_account.id),
                            },
                        )

        return {"processed": True, "message": "Subscription updated", "event_id": event_id}

    def _handle_subscription_deleted(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.deleted webhook"""
        subscription_obj = event_data if isinstance(event_data, dict) else {}
        stripe_subscription_id = subscription_obj.get("id")

        subscription = (
            self.db.query(StripeSubscription)
            .filter(StripeSubscription.stripe_subscription_id == stripe_subscription_id)
            .first()
        )

        if subscription:
            subscription.status = "canceled"

            # Update billing account
            stripe_customer = (
                self.db.query(StripeCustomer).filter(StripeCustomer.id == subscription.stripe_customer_id).first()
            )

            if stripe_customer:
                billing_account = (
                    self.db.query(BillingAccount)
                    .filter(BillingAccount.id == stripe_customer.billing_account_id)
                    .first()
                )

                if billing_account:
                    billing_account.status = AccountStatus.CANCELED.value

        return {"processed": True, "message": "Subscription deleted"}

    def _handle_invoice_payment_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle invoice.payment_succeeded webhook (US#165: with invoice record creation)

        US#767: BILL-004 - Extract revision from Stripe invoice metadata if present
        """
        invoice_obj = event_data if isinstance(event_data, dict) else {}
        stripe_invoice_id = invoice_obj.get("id")
        subscription_id = invoice_obj.get("subscription")
        customer_id = invoice_obj.get("customer")
        amount_paid = invoice_obj.get("amount_paid", 0) / 100.0  # Convert from cents
        amount_due = invoice_obj.get("amount_due", 0) / 100.0

        # US#767: Extract revision from Stripe invoice metadata
        stripe_metadata = invoice_obj.get("metadata", {})
        revision = int(stripe_metadata.get("revision", "1")) if stripe_metadata else 1
        invoice_number = stripe_metadata.get("invoice_number") if stripe_metadata else f"INV-{stripe_invoice_id[:8]}"

        # Create or update invoice record
        invoice = self.db.query(StripeInvoice).filter(StripeInvoice.stripe_invoice_id == stripe_invoice_id).first()

        if not invoice and subscription_id:
            subscription = (
                self.db.query(StripeSubscription)
                .filter(StripeSubscription.stripe_subscription_id == subscription_id)
                .first()
            )

            if subscription:
                stripe_customer = (
                    self.db.query(StripeCustomer).filter(StripeCustomer.id == subscription.stripe_customer_id).first()
                )
                if stripe_customer:
                    billing_account = (
                        self.db.query(BillingAccount)
                        .filter(BillingAccount.id == stripe_customer.billing_account_id)
                        .first()
                    )
                    if billing_account:
                        # US#767: Get billing period from metadata or use current period
                        billing_period_id = None
                        if stripe_metadata and "billing_period_id" in stripe_metadata:
                            try:
                                billing_period_id = uuid.UUID(stripe_metadata["billing_period_id"])
                            except (ValueError, TypeError):
                                pass

                        # If no billing period from metadata, get current active period
                        if not billing_period_id:
                            from server.billing.models import (
                                BillingPeriod,
                                BillingPeriodStatus,
                            )

                            current_period = (
                                self.db.query(BillingPeriod)
                                .filter(
                                    BillingPeriod.billing_account_id == billing_account.id,
                                    BillingPeriod.status == BillingPeriodStatus.ACTIVE.value,
                                )
                                .order_by(BillingPeriod.period_end.desc())
                                .first()
                            )
                            if current_period:
                                billing_period_id = current_period.id

                        # Create Invoice record first, then link StripeInvoice (US#165, US#767)
                        from server.billing.models import Invoice, InvoiceStatus

                        invoice_record = Invoice(
                            billing_period_id=billing_period_id or billing_account.id,  # Fallback if no period
                            billing_account_id=billing_account.id,
                            invoice_number=invoice_number,
                            revision=revision,  # US#767: Use revision from metadata
                            status=InvoiceStatus.PAID.value,
                            subtotal=Decimal(str(amount_paid)),
                            tax_amount=Decimal("0"),
                            total_amount=Decimal(str(amount_paid)),
                            currency=invoice_obj.get("currency", "usd").upper(),
                            paid_at=datetime.utcnow(),
                            issued_at=(
                                datetime.fromtimestamp(invoice_obj.get("created", 0), tz=timezone.utc)
                                if invoice_obj.get("created")
                                else datetime.utcnow()
                            ),
                        )
                        self.db.add(invoice_record)
                        self.db.flush()

                        # Create StripeInvoice record
                        stripe_invoice = StripeInvoice(
                            invoice_id=invoice_record.id,
                            stripe_invoice_id=stripe_invoice_id,
                            stripe_customer_id=customer_id,
                            status="paid",
                        )
                        self.db.add(stripe_invoice)
                        invoice = stripe_invoice
        elif invoice:
            # Update existing invoice status
            invoice.status = "paid"

            # US#767: Update local invoice status if linked
            if invoice.invoice:
                from server.billing.models import InvoiceStatus

                invoice.invoice.status = InvoiceStatus.PAID.value
                invoice.invoice.paid_at = datetime.utcnow()

        return {"processed": True, "message": "Invoice payment succeeded"}

    def _handle_invoice_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle invoice.payment_failed webhook (US#165: with dunning)

        US#767: BILL-004 - Extract revision from Stripe invoice metadata if present
        """
        invoice_obj = event_data if isinstance(event_data, dict) else {}
        stripe_invoice_id = invoice_obj.get("id")
        subscription_id = invoice_obj.get("subscription")
        customer_id = invoice_obj.get("customer")
        amount_due = invoice_obj.get("amount_due", 0) / 100.0  # Convert from cents

        # US#767: Extract revision from Stripe invoice metadata
        stripe_metadata = invoice_obj.get("metadata", {})
        revision = int(stripe_metadata.get("revision", "1")) if stripe_metadata else 1
        invoice_number = stripe_metadata.get("invoice_number") if stripe_metadata else f"INV-{stripe_invoice_id[:8]}"

        # Update invoice status
        invoice = self.db.query(StripeInvoice).filter(StripeInvoice.stripe_invoice_id == stripe_invoice_id).first()

        if invoice:
            invoice.status = "failed"

            # US#767: Update local invoice status if linked
            if invoice.invoice:
                from server.billing.models import InvoiceStatus

                invoice.invoice.status = InvoiceStatus.ISSUED.value  # Keep as issued, not paid
        else:
            # Create invoice record if it doesn't exist
            if subscription_id:
                subscription = (
                    self.db.query(StripeSubscription)
                    .filter(StripeSubscription.stripe_subscription_id == subscription_id)
                    .first()
                )
                if subscription:
                    stripe_customer = (
                        self.db.query(StripeCustomer)
                        .filter(StripeCustomer.id == subscription.stripe_customer_id)
                        .first()
                    )
                    if stripe_customer:
                        billing_account = (
                            self.db.query(BillingAccount)
                            .filter(BillingAccount.id == stripe_customer.billing_account_id)
                            .first()
                        )
                        if billing_account:
                            # US#767: Get billing period from metadata or use current period
                            billing_period_id = None
                            if stripe_metadata and "billing_period_id" in stripe_metadata:
                                try:
                                    billing_period_id = uuid.UUID(stripe_metadata["billing_period_id"])
                                except (ValueError, TypeError):
                                    pass

                            # If no billing period from metadata, get current active period
                            if not billing_period_id:
                                from server.billing.models import (
                                    BillingPeriod,
                                    BillingPeriodStatus,
                                )

                                current_period = (
                                    self.db.query(BillingPeriod)
                                    .filter(
                                        BillingPeriod.billing_account_id == billing_account.id,
                                        BillingPeriod.status == BillingPeriodStatus.ACTIVE.value,
                                    )
                                    .order_by(BillingPeriod.period_end.desc())
                                    .first()
                                )
                                if current_period:
                                    billing_period_id = current_period.id

                            # Create Invoice record first (US#165, US#767)
                            from server.billing.models import Invoice, InvoiceStatus

                            invoice_record = Invoice(
                                billing_period_id=billing_period_id or billing_account.id,  # Fallback if no period
                                billing_account_id=billing_account.id,
                                invoice_number=invoice_number,  # US#767: Use invoice number from metadata
                                revision=revision,  # US#767: Use revision from metadata
                                status=InvoiceStatus.ISSUED.value,
                                subtotal=Decimal(str(amount_due)),
                                tax_amount=Decimal("0"),
                                total_amount=Decimal(str(amount_due)),
                                currency=invoice_obj.get("currency", "usd").upper(),
                                due_at=datetime.utcnow() + timedelta(days=7),
                                issued_at=(
                                    datetime.fromtimestamp(invoice_obj.get("created", 0), tz=timezone.utc)
                                    if invoice_obj.get("created")
                                    else datetime.utcnow()
                                ),
                            )
                            self.db.add(invoice_record)
                            self.db.flush()

                            # Create StripeInvoice record
                            stripe_invoice = StripeInvoice(
                                invoice_id=invoice_record.id,
                                stripe_invoice_id=stripe_invoice_id,
                                stripe_customer_id=customer_id,
                                status="failed",
                            )
                            self.db.add(stripe_invoice)

        # Handle failed payment (dunning) - US#165
        if subscription_id:
            # Send payment failure notification email
            try:
                import asyncio

                from server.billing.email_notifications import (
                    get_billing_email_notifier,
                )

                notifier = get_billing_email_notifier()
                # Get customer email
                if customer_id:
                    stripe_customer_obj = (
                        self.db.query(StripeCustomer).filter(StripeCustomer.stripe_customer_id == customer_id).first()
                    )
                    if stripe_customer_obj and stripe_customer_obj.email:
                        asyncio.create_task(
                            notifier.send_payment_failure_notification(
                                customer_email=stripe_customer_obj.email,
                                invoice_number=stripe_invoice_id[:8],
                                amount=amount_due,
                                failure_reason="Payment method declined",
                            )
                        )
            except Exception as e:
                logger.error(f"Failed to send payment failure email: {e}", exc_info=True)

            self._handle_failed_payment_dunning(subscription_id, stripe_invoice_id, amount_due)

        return {"processed": True, "message": "Invoice payment failed - dunning initiated"}

    def _handle_failed_payment_dunning(
        self, subscription_id: str, invoice_id: str, amount: float, retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Handle failed payment with dunning (retry logic).

        US#165: Failed payment handling with 3 retry attempts and email notifications.

        Args:
            subscription_id: Stripe subscription ID
            invoice_id: Stripe invoice ID
            amount: Invoice amount
            retry_count: Current retry attempt (0-3)

        Returns:
            Dunning result
        """
        max_retries = 3
        retry_delays = [1, 3, 7]  # Days between retries

        if retry_count >= max_retries:
            # Max retries reached - suspend account
            subscription = (
                self.db.query(StripeSubscription)
                .filter(StripeSubscription.stripe_subscription_id == subscription_id)
                .first()
            )
            if subscription:
                subscription.status = "past_due"
                stripe_customer = (
                    self.db.query(StripeCustomer).filter(StripeCustomer.id == subscription.stripe_customer_id).first()
                )
                if stripe_customer:
                    billing_account = (
                        self.db.query(BillingAccount)
                        .filter(BillingAccount.id == stripe_customer.billing_account_id)
                        .first()
                    )
                    if billing_account:
                        billing_account.status = AccountStatus.SUSPENDED.value
                        self.db.flush()  # Ensure status is persisted
                        logger.warning(
                            f"Account {billing_account.id} suspended after {max_retries} payment retry failures",
                            extra={
                                "billing_account_id": str(billing_account.id),
                                "subscription_id": subscription_id,
                                "invoice_id": invoice_id,
                            },
                        )
                        # Send suspension email notification (US#165)
                        try:
                            import asyncio

                            from server.billing.email_notifications import (
                                get_billing_email_notifier,
                            )

                            notifier = get_billing_email_notifier()
                            # Get customer email
                            customer_email = stripe_customer.email or billing_account.account_id
                            if customer_email and "@" in str(customer_email):
                                try:
                                    # Try to create task if event loop is running
                                    asyncio.create_task(
                                        notifier.send_account_suspension_notification(
                                            customer_email=str(customer_email),
                                            account_id=billing_account.id,
                                            reason="Payment failure after multiple retry attempts",
                                        )
                                    )
                                except RuntimeError:
                                    # No event loop - send synchronously or log
                                    logger.info(f"Would send account suspension email to {customer_email}")
                        except Exception as e:
                            logger.error(f"Failed to send suspension email: {e}", exc_info=True)

            return {"processed": True, "message": "Max retries reached - account suspended"}

        # Retry payment
        try:
            import stripe

            # Retry the invoice payment
            invoice = stripe.Invoice.retrieve(invoice_id)
            # Get customer email from invoice (for both success and failure cases)
            customer_email = invoice.customer_email if hasattr(invoice, "customer_email") else None

            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=invoice.currency,
                customer=invoice.customer,
                payment_method=invoice.default_payment_method,
                confirm=True,
            )

            if payment_intent.status == "succeeded":
                logger.info(
                    f"Payment retry {retry_count + 1} succeeded for invoice {invoice_id}",
                    extra={"invoice_id": invoice_id, "retry_count": retry_count + 1},
                )
                # Send success email notification (US#165)
                try:
                    import asyncio

                    from server.billing.email_notifications import (
                        get_billing_email_notifier,
                    )

                    notifier = get_billing_email_notifier()
                    if customer_email:
                        asyncio.create_task(
                            notifier.send_payment_retry_notification(
                                customer_email=customer_email,
                                invoice_number=invoice.number or invoice_id[:8],
                                retry_number=retry_count + 1,
                                success=True,
                            )
                        )
                except Exception as e:
                    logger.error(f"Failed to send payment success email: {e}", exc_info=True)
                return {"processed": True, "message": f"Payment retry {retry_count + 1} succeeded"}
            else:
                # Retry failed - schedule next retry
                logger.warning(
                    f"Payment retry {retry_count + 1} failed for invoice {invoice_id}, scheduling next retry",
                    extra={"invoice_id": invoice_id, "retry_count": retry_count + 1},
                )
                # Send retry failure email notification (US#165)
                try:
                    import asyncio

                    from server.billing.email_notifications import (
                        get_billing_email_notifier,
                    )

                    notifier = get_billing_email_notifier()
                    if customer_email:
                        try:
                            # Try to create task if event loop is running
                            asyncio.create_task(
                                notifier.send_payment_retry_notification(
                                    customer_email=customer_email,
                                    invoice_number=invoice.number or invoice_id[:8],
                                    retry_number=retry_count + 1,
                                    success=False,
                                )
                            )
                        except RuntimeError:
                            # No event loop - send synchronously or log
                            logger.info(f"Would send payment retry failure email to {customer_email}")
                except Exception as e:
                    logger.error(f"Failed to send payment retry failure email: {e}", exc_info=True)

                # Schedule next retry via Celery task (US#165)
                if retry_count + 1 < max_retries:
                    try:
                        from datetime import timedelta

                        from server.billing.celery_tasks import retry_failed_payment

                        # Calculate delay in seconds (retry_delays[retry_count] is in days)
                        delay_seconds = retry_delays[retry_count] * 24 * 60 * 60

                        retry_failed_payment.apply_async(
                            args=[subscription_id, invoice_id, amount, retry_count + 1],
                            countdown=delay_seconds,
                        )
                        logger.info(
                            f"Scheduled payment retry {retry_count + 2} for invoice {invoice_id} in {retry_delays[retry_count]} days",
                            extra={
                                "invoice_id": invoice_id,
                                "retry_count": retry_count + 1,
                                "delay_days": retry_delays[retry_count],
                            },
                        )
                    except Exception as e:
                        logger.error(f"Failed to schedule payment retry task: {e}", exc_info=True)

                return {
                    "processed": True,
                    "message": f"Payment retry {retry_count + 1} failed, will retry in {retry_delays[retry_count]} days",
                }

        except Exception as exc:
            logger.error(
                f"Error retrying payment for invoice {invoice_id}: {exc}",
                extra={"invoice_id": invoice_id, "retry_count": retry_count, "error": str(exc)},
                exc_info=True,
            )
            # Schedule next retry via Celery task (US#165)
            if retry_count + 1 < max_retries:
                try:
                    from datetime import timedelta

                    from server.billing.celery_tasks import retry_failed_payment

                    # Calculate delay in seconds (retry_delays[retry_count] is in days)
                    delay_seconds = retry_delays[retry_count] * 24 * 60 * 60

                    retry_failed_payment.apply_async(
                        args=[subscription_id, invoice_id, amount, retry_count + 1],
                        countdown=delay_seconds,
                    )
                    logger.info(
                        f"Scheduled payment retry {retry_count + 2} for invoice {invoice_id} in {retry_delays[retry_count]} days (after error)",
                        extra={
                            "invoice_id": invoice_id,
                            "retry_count": retry_count + 1,
                            "delay_days": retry_delays[retry_count],
                        },
                    )
                except Exception as schedule_error:
                    logger.error(f"Failed to schedule payment retry task after error: {schedule_error}", exc_info=True)

            return {"processed": False, "error": str(exc), "message": "Payment retry error"}

    def _handle_charge_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.succeeded webhook (US#165)"""
        charge_obj = event_data if isinstance(event_data, dict) else {}
        charge_id = charge_obj.get("id")
        amount = charge_obj.get("amount", 0) / 100.0  # Convert from cents
        customer_id = charge_obj.get("customer")
        invoice_id = charge_obj.get("invoice")

        logger.info(
            f"Charge succeeded: {charge_id} for customer {customer_id}, amount: ${amount:.2f}",
            extra={"charge_id": charge_id, "customer_id": customer_id, "invoice_id": invoice_id},
        )

        # Update invoice status if linked
        if invoice_id:
            invoice = self.db.query(StripeInvoice).filter(StripeInvoice.stripe_invoice_id == invoice_id).first()
            if invoice:
                invoice.status = "paid"
                # Update linked Invoice record
                if invoice.invoice:
                    from server.billing.models import InvoiceStatus

                    invoice.invoice.status = InvoiceStatus.PAID.value

        return {"processed": True, "message": "Charge succeeded"}

    def _handle_charge_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle charge.failed webhook (US#165)"""
        charge_obj = event_data if isinstance(event_data, dict) else {}
        charge_id = charge_obj.get("id")
        customer_id = charge_obj.get("customer")
        invoice_id = charge_obj.get("invoice")
        failure_code = charge_obj.get("failure_code")
        failure_message = charge_obj.get("failure_message")

        logger.warning(
            f"Charge failed: {charge_id} for customer {customer_id}, code: {failure_code}, message: {failure_message}",
            extra={
                "charge_id": charge_id,
                "customer_id": customer_id,
                "invoice_id": invoice_id,
                "failure_code": failure_code,
            },
        )

        # Update invoice status if linked
        if invoice_id:
            invoice = self.db.query(StripeInvoice).filter(StripeInvoice.stripe_invoice_id == invoice_id).first()
            if invoice:
                invoice.status = "failed"

        return {"processed": True, "message": "Charge failed"}

    def _handle_payment_intent_succeeded(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment_intent.succeeded webhook (US#165)"""
        payment_intent_obj = event_data if isinstance(event_data, dict) else {}
        payment_intent_id = payment_intent_obj.get("id")
        amount = payment_intent_obj.get("amount", 0) / 100.0  # Convert from cents
        customer_id = payment_intent_obj.get("customer")
        invoice_id = payment_intent_obj.get("invoice")

        logger.info(
            f"Payment intent succeeded: {payment_intent_id} for customer {customer_id}, amount: ${amount:.2f}",
            extra={
                "payment_intent_id": payment_intent_id,
                "customer_id": customer_id,
                "invoice_id": invoice_id,
            },
        )

        # Update invoice status if linked
        if invoice_id:
            invoice = self.db.query(StripeInvoice).filter(StripeInvoice.stripe_invoice_id == invoice_id).first()
            if invoice:
                invoice.status = "paid"
                # Update linked Invoice record
                if invoice.invoice:
                    from server.billing.models import InvoiceStatus

                    invoice.invoice.status = InvoiceStatus.PAID.value

        return {"processed": True, "message": "Payment intent succeeded"}

    def _get_price_id_for_plan(self, plan_tier: PlanTier) -> Optional[str]:
        """
        Get Stripe price ID for plan tier.

        Args:
            plan_tier: Plan tier

        Returns:
            Stripe price ID or None
        """
        # Map plan tiers to Stripe price IDs
        # These should be configured in environment variables or database
        price_mapping = {
            PlanTier.STARTER: os.getenv("STRIPE_PRICE_ID_STARTER"),
            PlanTier.PRO: os.getenv("STRIPE_PRICE_ID_PRO"),
            PlanTier.ENTERPRISE: os.getenv("STRIPE_PRICE_ID_ENTERPRISE"),
        }

        return price_mapping.get(plan_tier)

    def sync_all_subscriptions(self) -> Dict[str, Any]:
        """
        Sync all active subscriptions from Stripe.

        This should be run periodically (e.g., hourly cron job).

        Returns:
            Sync results
        """
        results = {
            "synced": 0,
            "errors": 0,
            "errors_detail": [],
        }

        # Get all active subscriptions
        subscriptions = (
            self.db.query(StripeSubscription)
            .filter(StripeSubscription.status.in_(["active", "trialing", "past_due"]))
            .all()
        )

        for subscription in subscriptions:
            try:
                self.sync_subscription_status(subscription.billing_account_id)
                results["synced"] += 1
            except Exception as e:
                results["errors"] += 1
                results["errors_detail"].append(
                    {
                        "subscription_id": str(subscription.id),
                        "error": str(e),
                    }
                )

        return results
