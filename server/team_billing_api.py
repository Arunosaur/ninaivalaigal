#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
US#204: Team Billing APIs (SPEC-026 Phase 2)
REST API endpoints for team billing management with Stripe integration.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import stripe
from billing.stripe_customer_service import StripeCustomerService
from database.models import Team, TeamBilling, TeamSubscription, User
from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from models.standalone_teams import StandaloneTeamManager
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user, get_db

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/team/billing", tags=["team-billing"])


# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
if not stripe.api_key:
    logger.warning("STRIPE_SECRET_KEY not set - Stripe operations will fail")

# Billing Plan to Stripe Price ID Mapping
# Maps plan_id to Stripe price IDs (monthly and yearly)
STRIPE_PRICE_MAPPING = {
    "free": {
        "monthly": None,  # Free plan has no Stripe price
        "yearly": None,
    },
    "starter": {
        "monthly": "price_starter_monthly",  # Replace with actual Stripe price IDs
        "yearly": "price_starter_yearly",
    },
    "team_pro": {
        "monthly": "price_team_pro_monthly",
        "yearly": "price_team_pro_yearly",
    },
    "team_enterprise": {
        "monthly": "price_team_enterprise_monthly",
        "yearly": "price_team_enterprise_yearly",
    },
    "nonprofit": {
        "monthly": "price_nonprofit_monthly",
        "yearly": "price_nonprofit_yearly",
    },
}


# Initialize team manager
def get_team_manager(db: Session = Depends(get_db)) -> StandaloneTeamManager:
    """Get standalone team manager instance"""
    return StandaloneTeamManager(db)


# Pydantic Models
class BillingInfoResponse(BaseModel):
    """Billing information response"""

    team_id: str
    team_name: str
    subscription_status: str  # active, trialing, past_due, canceled, unpaid
    current_plan: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    next_billing_date: Optional[datetime]
    amount_due: float
    currency: str
    stripe_customer_id: Optional[str]
    payment_method: Optional[Dict[str, Any]]  # Last 4 digits, brand, expiry
    trial_end: Optional[datetime]


class PaymentMethodRequest(BaseModel):
    """Request to add/update payment method"""

    payment_method_id: str = Field(..., description="Stripe payment method ID")
    set_as_default: bool = Field(default=True, description="Set as default payment method")


class InvoiceListItem(BaseModel):
    """Invoice list item response"""

    id: str
    invoice_number: str
    date: datetime
    amount: float
    amount_paid: float
    currency: str
    status: str  # draft, open, paid, void, uncollectible
    period_start: datetime
    period_end: datetime
    pdf_url: Optional[str]
    stripe_invoice_url: Optional[str]


class InvoiceListResponse(BaseModel):
    """Paginated invoice list response"""

    invoices: List[InvoiceListItem]
    total: int
    page: int
    page_size: int
    has_more: bool


class ChangePlanRequest(BaseModel):
    """Request to change subscription plan"""

    new_plan_id: str = Field(..., description="New plan ID (free, starter, team_pro, etc.)")
    prorate: bool = Field(default=True, description="Apply proration for plan changes")
    billing_cycle_anchor: Optional[datetime] = Field(None, description="Anchor date for billing cycle")


class ChangePlanResponse(BaseModel):
    """Response after changing plan"""

    success: bool
    message: str
    new_plan: str
    proration_amount: Optional[float]
    next_billing_date: datetime


class CancelSubscriptionRequest(BaseModel):
    """Request to cancel subscription"""

    cancel_immediately: bool = Field(default=False, description="Cancel immediately or at period end")
    reason: Optional[str] = Field(None, max_length=500, description="Cancellation reason")


class CancelSubscriptionResponse(BaseModel):
    """Response after canceling subscription"""

    success: bool
    message: str
    canceled_at: datetime
    access_until: datetime  # When access will be revoked
    refund_amount: Optional[float]


# Helper Functions
def check_team_admin_access(user_id: UUID, team_id: UUID, db: Session) -> bool:
    """Check if user is admin of the team"""
    team_manager = StandaloneTeamManager(db)
    membership = team_manager.get_team_membership(str(team_id), str(user_id), db)
    return membership is not None and membership.role == "admin"


def get_user_team(user_id: UUID, db: Session) -> Optional[Team]:
    """Get user's team (standalone team)"""
    team_manager = StandaloneTeamManager(db)
    return team_manager.get_user_team(str(user_id), db)


def get_team_billing(team_id: UUID, db: Session) -> Optional[TeamBilling]:
    """Get team billing record"""
    return db.query(TeamBilling).filter(TeamBilling.team_id == team_id).first()


def get_team_subscription(team_id: UUID, db: Session) -> Optional[TeamSubscription]:
    """Get active team subscription"""
    return (
        db.query(TeamSubscription)
        .filter(TeamSubscription.team_id == team_id, TeamSubscription.status.in_(["active", "trialing", "past_due"]))
        .order_by(TeamSubscription.created_at.desc())
        .first()
    )


def sync_payment_method_from_stripe(team_billing: TeamBilling) -> Optional[Dict[str, Any]]:
    """Retrieve payment method info from Stripe"""
    if not team_billing.stripe_customer_id:
        return None

    try:
        customer = stripe.Customer.retrieve(team_billing.stripe_customer_id)
        if customer.invoice_settings.default_payment_method:
            pm = stripe.PaymentMethod.retrieve(customer.invoice_settings.default_payment_method)
            return {
                "id": pm.id,
                "type": pm.type,
                "last4": pm.card.last4 if pm.type == "card" else None,
                "brand": pm.card.brand if pm.type == "card" else None,
                "exp_month": pm.card.exp_month if pm.type == "card" else None,
                "exp_year": pm.card.exp_year if pm.type == "card" else None,
            }
    except stripe.error.StripeError as e:
        logger.error(f"Failed to retrieve payment method from Stripe: {e}")
        return None

    return None


# API Endpoints


@router.get("", response_model=BillingInfoResponse)
async def get_team_billing_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GET /team/billing
    Get billing info and subscription status for current user's team.
    """
    # Get user's team
    team = get_user_team(current_user.id, db)
    if not team:
        raise HTTPException(status_code=404, detail="User is not part of a team")

    # Check admin access
    if not check_team_admin_access(current_user.id, team.id, db):
        raise HTTPException(status_code=403, detail="Team admin access required")

    # Get billing and subscription info
    team_billing = get_team_billing(team.id, db)
    subscription = get_team_subscription(team.id, db)

    # Get payment method from Stripe if available
    payment_method = None
    stripe_customer_id = None
    if team_billing:
        stripe_customer_id = team_billing.stripe_customer_id
        payment_method = sync_payment_method_from_stripe(team_billing)

    # Determine subscription status
    if not subscription:
        subscription_status = "unpaid"
        current_plan = "free"
        current_period_start = datetime.utcnow()
        current_period_end = datetime.utcnow() + timedelta(days=30)
        cancel_at_period_end = False
        amount_due = 0.0
        trial_end = None
    else:
        subscription_status = subscription.status
        current_plan = subscription.plan_id
        current_period_start = subscription.current_period_start
        current_period_end = subscription.current_period_end
        cancel_at_period_end = subscription.cancel_at_period_end
        amount_due = 0.0  # Would be calculated from Stripe
        trial_end = subscription.trial_end

    # Get next billing date
    next_billing_date = current_period_end if subscription_status in ["active", "trialing"] else None

    return BillingInfoResponse(
        team_id=str(team.id),
        team_name=team.name,
        subscription_status=subscription_status,
        current_plan=current_plan,
        current_period_start=current_period_start,
        current_period_end=current_period_end,
        cancel_at_period_end=cancel_at_period_end,
        next_billing_date=next_billing_date,
        amount_due=amount_due,
        currency="usd",
        stripe_customer_id=stripe_customer_id,
        payment_method=payment_method,
        trial_end=trial_end,
    )


@router.post("/payment-method")
async def add_update_payment_method(
    request: PaymentMethodRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /team/billing/payment-method
    Add or update payment method for team billing.
    """
    # Get user's team
    team = get_user_team(current_user.id, db)
    if not team:
        raise HTTPException(status_code=404, detail="User is not part of a team")

    # Check admin access
    if not check_team_admin_access(current_user.id, team.id, db):
        raise HTTPException(status_code=403, detail="Team admin access required")

    # Get or create team billing record
    team_billing = get_team_billing(team.id, db)

    # Auto-create Stripe customer if billing exists but customer doesn't (US#163)
    if team_billing and not team_billing.stripe_customer_id:
        try:
            stripe_service = StripeCustomerService(db)
            customer_data = stripe_service.get_or_create_customer(
                team_id=team.id,
                email=team_billing.billing_email or current_user.email,
                name=team.name,
            )
            team_billing.stripe_customer_id = customer_data["id"]
            db.commit()
            logger.info(f"Auto-created Stripe customer {customer_data['id']} for team {team.id}")
        except Exception as e:
            logger.error(f"Failed to auto-create Stripe customer: {e}")
            raise HTTPException(status_code=500, detail="Failed to set up billing. Please try again.")

    if not team_billing or not team_billing.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Team billing not set up. Please create a subscription first.")

    try:
        # Use Stripe customer service to sync payment method (US#163)
        stripe_service = StripeCustomerService(db)
        payment_method_data = stripe_service.sync_payment_method(
            customer_id=team_billing.stripe_customer_id,
            payment_method_id=request.payment_method_id,
            set_as_default=request.set_as_default,
        )

        return {
            "success": True,
            "message": "Payment method added successfully",
            "payment_method_id": request.payment_method_id,
            "payment_method": payment_method_data,
        }

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error adding payment method: {e}")
        raise HTTPException(status_code=400, detail=f"Payment method update failed: {str(e)}")


@router.get("/invoices", response_model=InvoiceListResponse)
async def list_team_invoices(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    GET /team/billing/invoices
    List invoices for current user's team (paginated).
    """
    # Get user's team
    team = get_user_team(current_user.id, db)
    if not team:
        raise HTTPException(status_code=404, detail="User is not part of a team")

    # Check admin access
    if not check_team_admin_access(current_user.id, team.id, db):
        raise HTTPException(status_code=403, detail="Team admin access required")

    # Get team billing to find Stripe customer
    team_billing = get_team_billing(team.id, db)

    invoices: List[InvoiceListItem] = []

    if team_billing and team_billing.stripe_customer_id:
        try:
            # Retrieve invoices from Stripe
            stripe_invoices = stripe.Invoice.list(
                customer=team_billing.stripe_customer_id,
                limit=page_size,
                starting_after=None if page == 1 else None,  # Would use cursor for pagination
            )

            for inv in stripe_invoices.data:
                invoices.append(
                    InvoiceListItem(
                        id=inv.id,
                        invoice_number=inv.number or inv.id,
                        date=datetime.fromtimestamp(inv.created),
                        amount=inv.amount_due / 100.0,  # Convert cents to dollars
                        amount_paid=inv.amount_paid / 100.0,
                        currency=inv.currency,
                        status=inv.status,
                        period_start=(
                            datetime.fromtimestamp(inv.period_start) if inv.period_start else datetime.utcnow()
                        ),
                        period_end=datetime.fromtimestamp(inv.period_end) if inv.period_end else datetime.utcnow(),
                        pdf_url=inv.invoice_pdf,
                        stripe_invoice_url=inv.hosted_invoice_url,
                    )
                )
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve invoices from Stripe: {e}")
            # Return empty list on error

    # Calculate pagination
    total = len(invoices)
    has_more = len(invoices) >= page_size

    return InvoiceListResponse(
        invoices=invoices,
        total=total,
        page=page,
        page_size=page_size,
        has_more=has_more,
    )


@router.post("/change-plan", response_model=ChangePlanResponse)
async def change_subscription_plan(
    request: ChangePlanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /team/billing/change-plan
    Change subscription tier (upgrade or downgrade) with proration handling.
    """
    # Get user's team
    team = get_user_team(current_user.id, db)
    if not team:
        raise HTTPException(status_code=404, detail="User is not part of a team")

    # Check admin access
    if not check_team_admin_access(current_user.id, team.id, db):
        raise HTTPException(status_code=403, detail="Team admin access required")

    # Get current subscription
    subscription = get_team_subscription(team.id, db)
    if not subscription:
        raise HTTPException(status_code=400, detail="No active subscription found")

    # Get or create team billing
    team_billing = get_team_billing(team.id, db)

    # Auto-create Stripe customer if billing exists but customer doesn't (US#163)
    if team_billing and not team_billing.stripe_customer_id:
        try:
            stripe_service = StripeCustomerService(db)
            customer_data = stripe_service.get_or_create_customer(
                team_id=team.id,
                email=team_billing.billing_email or current_user.email,
                name=team.name,
            )
            team_billing.stripe_customer_id = customer_data["id"]
            db.commit()
            logger.info(f"Auto-created Stripe customer {customer_data['id']} for team {team.id} during plan change")
        except Exception as e:
            logger.error(f"Failed to auto-create Stripe customer: {e}")
            raise HTTPException(status_code=500, detail="Failed to set up billing. Please try again.")

    if not team_billing or not team_billing.stripe_customer_id:
        raise HTTPException(status_code=400, detail="Team billing not configured with Stripe")

    # Validate plan ID
    valid_plans = list(STRIPE_PRICE_MAPPING.keys())
    if request.new_plan_id not in valid_plans:
        raise HTTPException(status_code=400, detail=f"Invalid plan ID: {request.new_plan_id}")

    try:
        # Get Stripe subscription ID from subscription metadata
        stripe_subscription_id = None
        if subscription.subscription_metadata:
            stripe_subscription_id = subscription.subscription_metadata.get("stripe_subscription_id")

        if not stripe_subscription_id:
            raise HTTPException(
                status_code=400, detail="Stripe subscription ID not found. Please create a subscription first."
            )

        # Determine billing cycle from current subscription (default to monthly)
        billing_cycle = "monthly"  # Would be determined from subscription
        new_price_id = STRIPE_PRICE_MAPPING.get(request.new_plan_id, {}).get(billing_cycle)

        if not new_price_id:
            raise HTTPException(
                status_code=400,
                detail=f"Stripe price ID not configured for plan {request.new_plan_id} ({billing_cycle})",
            )

        # Prepare Stripe subscription update
        update_params: Dict[str, Any] = {
            "items": [{"price": new_price_id}],
        }

        if request.prorate:
            update_params["proration_behavior"] = "create_prorations"

        if request.billing_cycle_anchor:
            update_params["billing_cycle_anchor"] = int(request.billing_cycle_anchor.timestamp())

        # Update subscription in Stripe
        updated_subscription = stripe.Subscription.modify(stripe_subscription_id, **update_params)

        # Update database subscription
        subscription.plan_id = request.new_plan_id

        # Update subscription metadata with Stripe response
        if subscription.subscription_metadata is None:
            subscription.subscription_metadata = {}
        subscription.subscription_metadata.update(
            {
                "stripe_subscription_id": updated_subscription.id,
                "last_updated": datetime.utcnow().isoformat(),
            }
        )

        # Update period dates from Stripe
        subscription.current_period_start = datetime.fromtimestamp(updated_subscription.current_period_start)
        subscription.current_period_end = datetime.fromtimestamp(updated_subscription.current_period_end)

        db.commit()

        # Calculate proration amount from Stripe response
        proration_amount = None
        if request.prorate and hasattr(updated_subscription, "latest_invoice"):
            try:
                invoice = stripe.Invoice.retrieve(updated_subscription.latest_invoice)
                # Find proration line item
                for line in invoice.lines.data:
                    if line.proration:
                        proration_amount = line.amount / 100.0  # Convert cents to dollars
                        break
            except Exception as e:
                logger.warning(f"Failed to calculate proration amount: {e}")

        return ChangePlanResponse(
            success=True,
            message=f"Successfully changed plan to {request.new_plan_id}",
            new_plan=request.new_plan_id,
            proration_amount=proration_amount,
            next_billing_date=datetime.fromtimestamp(updated_subscription.current_period_end),
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error changing plan: {e}")
        raise HTTPException(status_code=400, detail=f"Plan change failed: {str(e)}")


@router.post("/cancel", response_model=CancelSubscriptionResponse)
async def cancel_subscription(
    request: CancelSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    POST /team/billing/cancel
    Cancel subscription (at period end or immediately).
    """
    # Get user's team
    team = get_user_team(current_user.id, db)
    if not team:
        raise HTTPException(status_code=404, detail="User is not part of a team")

    # Check admin access
    if not check_team_admin_access(current_user.id, team.id, db):
        raise HTTPException(status_code=403, detail="Team admin access required")

    # Get current subscription
    subscription = get_team_subscription(team.id, db)
    if not subscription:
        raise HTTPException(status_code=400, detail="No active subscription found")

    # Get Stripe subscription ID from subscription metadata
    stripe_subscription_id = None
    if subscription.subscription_metadata:
        stripe_subscription_id = subscription.subscription_metadata.get("stripe_subscription_id")

    if not stripe_subscription_id:
        raise HTTPException(
            status_code=400, detail="Stripe subscription ID not found. Please create a subscription first."
        )

    try:
        if request.cancel_immediately:
            # Cancel immediately (may issue refund)
            canceled_sub = stripe.Subscription.delete(stripe_subscription_id)

            # Update database
            subscription.status = "canceled"
            subscription.canceled_at = datetime.utcnow()
            subscription.cancel_at_period_end = False

            # Update subscription metadata
            if subscription.subscription_metadata is None:
                subscription.subscription_metadata = {}
            subscription.subscription_metadata.update(
                {
                    "canceled_at": datetime.utcnow().isoformat(),
                    "cancel_at_period_end": False,
                    "cancellation_type": "immediate",
                }
            )

            db.commit()

            # Access ends immediately
            access_until = datetime.utcnow()

            # Calculate refund amount (if any)
            refund_amount = None
            try:
                # Check if there's a credit balance or refund
                if hasattr(canceled_sub, "latest_invoice"):
                    invoice = stripe.Invoice.retrieve(canceled_sub.latest_invoice)
                    if invoice.amount_paid > 0:
                        # Would calculate refund based on unused portion
                        # For now, leave as None
                        pass
            except Exception as e:
                logger.warning(f"Failed to calculate refund amount: {e}")

        else:
            # Cancel at period end (preserve access)
            updated_sub = stripe.Subscription.modify(
                stripe_subscription_id,
                cancel_at_period_end=True,
            )

            # Update database
            subscription.cancel_at_period_end = True
            subscription.canceled_at = datetime.utcnow()
            db.commit()

            # Access preserved until period end
            access_until = datetime.fromtimestamp(updated_sub.current_period_end)
            refund_amount = None

        return CancelSubscriptionResponse(
            success=True,
            message="Subscription canceled successfully",
            canceled_at=datetime.utcnow(),
            access_until=access_until,
            refund_amount=refund_amount,
        )

    except stripe.error.StripeError as e:
        logger.error(f"Stripe error canceling subscription: {e}")
        raise HTTPException(status_code=400, detail=f"Subscription cancellation failed: {str(e)}")


# FastAPI application hook primarily for tests (SPEC-139 scope)
app = FastAPI(title="Team Billing API", docs_url=None, redoc_url=None)
app.include_router(router)
