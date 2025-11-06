#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Stripe API Endpoints
# Developer D - January 2025
#
# BILL-004: FastAPI endpoints for Stripe integration

"""
FastAPI endpoints for Stripe integration.

Provides REST API for:
- Stripe customer creation
- Subscription management
- Webhook handling
- Payment method management
"""

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from server.billing.models import PlanTier
from server.billing.stripe_service import StripeService
from server.database import get_db

router = APIRouter(prefix="/api/billing/stripe", tags=["stripe"])


def get_stripe_service(db: Session = Depends(get_db)) -> StripeService:
    """Dependency for Stripe service"""
    try:
        return StripeService(db)
    except (ImportError, ValueError) as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=f"Stripe service unavailable: {str(e)}"
        )


@router.post("/customers")
async def create_stripe_customer(
    billing_account_id: UUID,
    email: str,
    name: Optional[str] = None,
    stripe_service: StripeService = Depends(get_stripe_service),
) -> Dict[str, Any]:
    """
    Create Stripe customer for billing account.

    Args:
        billing_account_id: Billing account ID
        email: Customer email
        name: Customer name (optional)

    Returns:
        Stripe customer details
    """
    try:
        customer = stripe_service.create_customer(
            billing_account_id=billing_account_id,
            email=email,
            name=name,
        )

        return {
            "billing_account_id": str(customer.billing_account_id),
            "stripe_customer_id": customer.stripe_customer_id,
            "email": customer.email,
            "created_at": customer.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/subscriptions")
async def create_subscription(
    billing_account_id: UUID,
    plan_tier: str,
    payment_method_id: Optional[str] = None,
    stripe_service: StripeService = Depends(get_stripe_service),
) -> Dict[str, Any]:
    """
    Create Stripe subscription.

    Args:
        billing_account_id: Billing account ID
        plan_tier: Plan tier (starter, pro, enterprise)
        payment_method_id: Stripe payment method ID (optional)

    Returns:
        Subscription details
    """
    try:
        plan_tier_enum = PlanTier(plan_tier.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan tier: {plan_tier}. Must be one of: starter, pro, enterprise",
        )

    try:
        subscription = stripe_service.create_subscription(
            billing_account_id=billing_account_id,
            plan_tier=plan_tier_enum,
            payment_method_id=payment_method_id,
        )

        return {
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "plan_id": subscription.plan_id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/subscriptions/{billing_account_id}/sync")
async def sync_subscription(
    billing_account_id: UUID,
    stripe_service: StripeService = Depends(get_stripe_service),
) -> Dict[str, Any]:
    """
    Sync subscription status from Stripe.

    Args:
        billing_account_id: Billing account ID

    Returns:
        Updated subscription details
    """
    subscription = stripe_service.sync_subscription_status(billing_account_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subscription not found for billing account: {billing_account_id}",
        )

        return {
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "plan_id": subscription.plan_id,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
        }


@router.delete("/subscriptions/{billing_account_id}")
async def cancel_subscription(
    billing_account_id: UUID,
    cancel_at_period_end: bool = True,
    stripe_service: StripeService = Depends(get_stripe_service),
) -> Dict[str, Any]:
    """
    Cancel Stripe subscription.

    Args:
        billing_account_id: Billing account ID
        cancel_at_period_end: Cancel at period end (default: True)

    Returns:
        Cancellation details
    """
    try:
        subscription = stripe_service.cancel_subscription(
            billing_account_id=billing_account_id,
            cancel_at_period_end=cancel_at_period_end,
        )

        return {
            "stripe_subscription_id": subscription.stripe_subscription_id,
            "status": subscription.status,
            "canceled": True,
            "cancel_at_period_end": cancel_at_period_end,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/webhooks")
async def handle_stripe_webhook(
    request: Request,
    stripe_service: StripeService = Depends(get_stripe_service),
) -> Dict[str, Any]:
    """
    Handle Stripe webhook events.

    This endpoint should be configured in Stripe dashboard to receive webhook events.

    Args:
        request: FastAPI request (contains Stripe event)

    Returns:
        Webhook processing result
    """
    try:
        import stripe

        # Get webhook signature from header
        signature = request.headers.get("stripe-signature")
        if not signature:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Stripe signature header")

        # Get webhook secret from environment
        webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not webhook_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe webhook secret not configured"
            )

        # Get request body
        body = await request.body()

        # Verify webhook signature
        try:
            event = stripe.Webhook.construct_event(body, signature, webhook_secret)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")
        except stripe.error.SignatureVerificationError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature")

        # Handle event
        result = stripe_service.handle_webhook_event(event_type=event["type"], event_data=event["data"])

        return result

    except ImportError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Stripe package not available")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error processing webhook: {str(e)}"
        )


@router.post("/sync/all")
async def sync_all_subscriptions(
    stripe_service: StripeService = Depends(get_stripe_service),
) -> Dict[str, Any]:
    """
    Sync all active subscriptions from Stripe.

    This endpoint should be called periodically (e.g., hourly cron job).
    Requires admin authentication (not implemented here - add as needed).

    Returns:
        Sync results
    """
    results = stripe_service.sync_all_subscriptions()

    return {
        "synced": results["synced"],
        "errors": results["errors"],
        "errors_detail": results["errors_detail"],
    }
