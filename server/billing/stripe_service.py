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

import os
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Optional

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
        self, billing_account_id: uuid.UUID, plan_tier: PlanTier, payment_method_id: Optional[str] = None
    ) -> StripeSubscription:
        """
        Create Stripe subscription for billing account.

        Args:
            billing_account_id: Billing account ID
            plan_tier: Plan tier (FREE, STARTER, PRO, ENTERPRISE)
            payment_method_id: Stripe payment method ID (optional)

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

        # Create Stripe subscription
        subscription_data = {
            "customer": stripe_customer_record.stripe_customer_id,
            "items": [{"price": price_id}],
            "metadata": {
                "billing_account_id": str(billing_account_id),
                "plan_tier": plan_tier.value,
            },
        }

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
        Sync subscription status from Stripe.

        Args:
            billing_account_id: Billing account ID

        Returns:
            Updated StripeSubscription instance or None
        """
        subscription = (
            self.db.query(StripeSubscription)
            .filter(StripeSubscription.billing_account_id == billing_account_id)
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

        # Update billing account status based on subscription status
        if stripe_customer:
            billing_account = self.db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()

            if billing_account:
                if stripe_subscription.status in ["active", "trialing"]:
                    billing_account.status = AccountStatus.ACTIVE.value
                elif stripe_subscription.status == "past_due":
                    billing_account.status = AccountStatus.SUSPENDED.value
                elif stripe_subscription.status in ["canceled", "unpaid"]:
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
        Handle Stripe webhook event.

        Args:
            event_type: Stripe event type (e.g., "customer.subscription.updated")
            event_data: Stripe event data

        Returns:
            Processing result
        """
        result = {
            "processed": False,
            "event_type": event_type,
            "message": "",
        }

        try:
            if event_type == "customer.subscription.created":
                result = self._handle_subscription_created(event_data)
            elif event_type == "customer.subscription.updated":
                result = self._handle_subscription_updated(event_data)
            elif event_type == "customer.subscription.deleted":
                result = self._handle_subscription_deleted(event_data)
            elif event_type == "invoice.payment_succeeded":
                result = self._handle_invoice_payment_succeeded(event_data)
            elif event_type == "invoice.payment_failed":
                result = self._handle_invoice_payment_failed(event_data)
            else:
                result["message"] = f"Unhandled event type: {event_type}"

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            result["error"] = str(e)
            result["message"] = f"Error processing webhook: {e}"

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

    def _handle_subscription_updated(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.updated webhook"""
        subscription_obj = event_data.get("object", {})
        stripe_subscription_id = subscription_obj.get("id")

        subscription = (
            self.db.query(StripeSubscription)
            .filter(StripeSubscription.stripe_subscription_id == stripe_subscription_id)
            .first()
        )

        if subscription:
            subscription.status = subscription_obj.get("status")
            subscription.current_period_start = datetime.fromtimestamp(subscription_obj.get("current_period_start", 0))
            subscription.current_period_end = datetime.fromtimestamp(subscription_obj.get("current_period_end", 0))

            # Update billing account status
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
                    status = subscription_obj.get("status")
                    if status in ["active", "trialing"]:
                        billing_account.status = AccountStatus.ACTIVE.value
                    elif status == "past_due":
                        billing_account.status = AccountStatus.SUSPENDED.value

        return {"processed": True, "message": "Subscription updated"}

    def _handle_subscription_deleted(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription.deleted webhook"""
        subscription_obj = event_data.get("object", {})
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
        """Handle invoice.payment_succeeded webhook"""
        invoice_obj = event_data.get("object", {})
        stripe_invoice_id = invoice_obj.get("id")
        subscription_id = invoice_obj.get("subscription")

        # Create or update invoice record
        invoice = self.db.query(StripeInvoice).filter(StripeInvoice.stripe_invoice_id == stripe_invoice_id).first()

        if not invoice and subscription_id:
            subscription = (
                self.db.query(StripeSubscription)
                .filter(StripeSubscription.stripe_subscription_id == subscription_id)
                .first()
            )

            if subscription:
                # Note: StripeInvoice model requires invoice_id (FK to Invoice table)
                # For now, we'll create a placeholder Invoice record or skip
                # This would need to be integrated with the Invoice model
                # TODO: Create Invoice record first, then link StripeInvoice
                pass

        return {"processed": True, "message": "Invoice payment succeeded"}

    def _handle_invoice_payment_failed(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle invoice.payment_failed webhook"""
        invoice_obj = event_data.get("object", {})
        stripe_invoice_id = invoice_obj.get("id")
        subscription_id = invoice_obj.get("subscription")

        # Update invoice status
        invoice = self.db.query(StripeInvoice).filter(StripeInvoice.stripe_invoice_id == stripe_invoice_id).first()

        if invoice:
            invoice.status = "failed"
        # Note: StripeInvoice model requires invoice_id (FK to Invoice table)
        # For now, we'll skip creating new invoices here
        # This would need to be integrated with the Invoice model

        return {"processed": True, "message": "Invoice payment failed"}

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
