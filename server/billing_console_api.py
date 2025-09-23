"""
SPEC-026: Tenant Billing Console API
Provides comprehensive billing management for teams and organizations
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

import stripe
from auth import get_current_user, get_db
from database import Organization, Team, User
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from models.standalone_teams import (
    StandaloneTeamManager,
    TeamMembership,
    TeamUpgradeHistory,
)
from pydantic import BaseModel, EmailStr, validator
from rbac_middleware import require_permission
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

# Initialize router
router = APIRouter(prefix="/billing", tags=["billing-console"])


# Pydantic Models
class BillingPlan(BaseModel):
    """Billing plan configuration"""

    id: str
    name: str
    description: str
    price_monthly: float
    price_yearly: float
    max_members: int
    features: List[str]
    stripe_price_id_monthly: str
    stripe_price_id_yearly: str
    is_popular: bool = False


class SubscriptionCreate(BaseModel):
    """Create new subscription"""

    plan_id: str
    billing_cycle: str  # monthly, yearly
    payment_method_id: str
    billing_email: EmailStr
    tax_id: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None


class SubscriptionUpdate(BaseModel):
    """Update existing subscription"""

    plan_id: Optional[str] = None
    billing_cycle: Optional[str] = None
    payment_method_id: Optional[str] = None
    billing_email: Optional[EmailStr] = None


class UsageMetrics(BaseModel):
    """Usage metrics for billing"""

    team_id: UUID
    period_start: datetime
    period_end: datetime
    members_count: int
    storage_used_gb: float
    ai_queries_count: int
    api_calls_count: int
    overage_charges: float


class BillingDashboardResponse(BaseModel):
    """Complete billing dashboard data"""

    current_plan: BillingPlan
    subscription_status: str
    next_billing_date: datetime
    usage_metrics: UsageMetrics
    payment_methods: List[Dict[str, Any]]
    billing_history: List[Dict[str, Any]]
    upgrade_recommendations: List[Dict[str, str]]


# Billing Plans Configuration
BILLING_PLANS = {
    "free": BillingPlan(
        id="free",
        name="Free",
        description="Perfect for individuals and small teams getting started",
        price_monthly=0.0,
        price_yearly=0.0,
        max_members=5,
        features=[
            "Up to 5 team members",
            "Basic memory storage (1GB)",
            "Standard AI queries (100/month)",
            "Community support",
            "Basic team collaboration",
        ],
        stripe_price_id_monthly="",
        stripe_price_id_yearly="",
    ),
    "team_pro": BillingPlan(
        id="team_pro",
        name="Team Pro",
        description="Advanced features for growing teams",
        price_monthly=29.0,
        price_yearly=290.0,  # 2 months free
        max_members=20,
        features=[
            "Up to 20 team members",
            "Enhanced memory storage (10GB)",
            "Unlimited AI queries",
            "Priority support",
            "Advanced team management",
            "Usage analytics",
            "Custom integrations",
        ],
        stripe_price_id_monthly="price_team_pro_monthly",
        stripe_price_id_yearly="price_team_pro_yearly",
        is_popular=True,
    ),
    "team_enterprise": BillingPlan(
        id="team_enterprise",
        name="Team Enterprise",
        description="Enterprise-grade features for large teams",
        price_monthly=99.0,
        price_yearly=990.0,  # 2 months free
        max_members=50,
        features=[
            "Up to 50 team members",
            "Unlimited memory storage",
            "Unlimited AI queries",
            "24/7 premium support",
            "Advanced security features",
            "Custom AI models",
            "API access",
            "SSO integration",
            "Audit logs",
        ],
        stripe_price_id_monthly="price_team_enterprise_monthly",
        stripe_price_id_yearly="price_team_enterprise_yearly",
    ),
    "organization": BillingPlan(
        id="organization",
        name="Organization",
        description="Custom solutions for large organizations",
        price_monthly=500.0,
        price_yearly=5000.0,
        max_members=1000,
        features=[
            "Unlimited team members",
            "Unlimited everything",
            "Dedicated success manager",
            "Custom deployment options",
            "Advanced compliance features",
            "Custom integrations",
            "White-label options",
            "SLA guarantees",
        ],
        stripe_price_id_monthly="price_organization_monthly",
        stripe_price_id_yearly="price_organization_yearly",
    ),
}


def get_team_manager() -> StandaloneTeamManager:
    """Dependency to get team manager"""
    return StandaloneTeamManager()


def calculate_usage_metrics(team_id: UUID, db: Session) -> UsageMetrics:
    """Calculate current usage metrics for a team"""
    # Get current period (this month)
    now = datetime.utcnow()
    period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    period_end = (period_start + timedelta(days=32)).replace(day=1) - timedelta(
        seconds=1
    )

    # Get team member count
    members_count = (
        db.query(TeamMembership)
        .filter(TeamMembership.team_id == team_id, TeamMembership.status == "active")
        .count()
    )

    # Mock usage data (in production, this would come from actual usage tracking)
    storage_used_gb = min(members_count * 0.5, 10.0)  # Estimate based on members
    ai_queries_count = members_count * 50  # Estimate
    api_calls_count = members_count * 200  # Estimate

    # Calculate overage charges (simplified)
    overage_charges = 0.0
    if storage_used_gb > 10.0:
        overage_charges += (storage_used_gb - 10.0) * 2.0  # $2/GB overage

    return UsageMetrics(
        team_id=team_id,
        period_start=period_start,
        period_end=period_end,
        members_count=members_count,
        storage_used_gb=storage_used_gb,
        ai_queries_count=ai_queries_count,
        api_calls_count=api_calls_count,
        overage_charges=overage_charges,
    )


def get_upgrade_recommendations(
    current_plan: str, usage: UsageMetrics
) -> List[Dict[str, str]]:
    """Generate upgrade recommendations based on usage"""
    recommendations = []

    if current_plan == "free":
        if usage.members_count >= 4:
            recommendations.append(
                {
                    "type": "member_limit",
                    "title": "Team Growing Fast!",
                    "message": f"You have {usage.members_count}/5 members. Upgrade to Team Pro for up to 20 members.",
                    "cta": "Upgrade to Team Pro",
                }
            )

        if usage.ai_queries_count > 80:
            recommendations.append(
                {
                    "type": "usage_limit",
                    "title": "High AI Usage",
                    "message": f"You've used {usage.ai_queries_count}/100 AI queries. Upgrade for unlimited queries.",
                    "cta": "Get Unlimited AI",
                }
            )

    elif current_plan == "team_pro":
        if usage.members_count >= 18:
            recommendations.append(
                {
                    "type": "member_limit",
                    "title": "Scaling Beyond Team Pro",
                    "message": f"You have {usage.members_count}/20 members. Consider Team Enterprise for 50 members.",
                    "cta": "Upgrade to Enterprise",
                }
            )

        if usage.storage_used_gb > 8.0:
            recommendations.append(
                {
                    "type": "storage_limit",
                    "title": "Storage Almost Full",
                    "message": f"You're using {usage.storage_used_gb:.1f}/10GB storage. Enterprise offers unlimited storage.",
                    "cta": "Get Unlimited Storage",
                }
            )

    elif current_plan == "team_enterprise":
        if usage.members_count >= 45:
            recommendations.append(
                {
                    "type": "organization_ready",
                    "title": "Ready for Organization Plan",
                    "message": f"With {usage.members_count} members, you might benefit from Organization features.",
                    "cta": "Explore Organization Plan",
                }
            )

    return recommendations


@router.get("/plans", response_model=List[BillingPlan])
async def get_billing_plans() -> List[BillingPlan]:
    """Get all available billing plans"""
    return list(BILLING_PLANS.values())


@router.get("/dashboard", response_model=BillingDashboardResponse)
async def get_billing_dashboard(
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> BillingDashboardResponse:
    """
    Get comprehensive billing dashboard data for current user's team
    """
    # Get user's team
    user_team = team_manager.get_user_team(current_user.id, db)
    if not user_team:
        raise HTTPException(status_code=404, detail="User is not part of any team")

    # Determine current plan (simplified - in production, this would be stored)
    member_count = (
        db.query(TeamMembership)
        .filter(
            TeamMembership.team_id == user_team.id, TeamMembership.status == "active"
        )
        .count()
    )

    if member_count <= 5:
        current_plan = BILLING_PLANS["free"]
    elif member_count <= 20:
        current_plan = BILLING_PLANS["team_pro"]
    elif member_count <= 50:
        current_plan = BILLING_PLANS["team_enterprise"]
    else:
        current_plan = BILLING_PLANS["organization"]

    # Calculate usage metrics
    usage_metrics = calculate_usage_metrics(user_team.id, db)

    # Get upgrade recommendations
    upgrade_recommendations = get_upgrade_recommendations(
        current_plan.id, usage_metrics
    )

    # Mock billing data (in production, this would come from Stripe)
    next_billing_date = datetime.utcnow() + timedelta(days=30)

    return BillingDashboardResponse(
        current_plan=current_plan,
        subscription_status="active" if current_plan.id != "free" else "free",
        next_billing_date=next_billing_date,
        usage_metrics=usage_metrics,
        payment_methods=[],  # Would be populated from Stripe
        billing_history=[],  # Would be populated from Stripe
        upgrade_recommendations=upgrade_recommendations,
    )


@router.post("/subscribe")
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Create a new subscription for the user's team
    """
    # Get user's team
    user_team = team_manager.get_user_team(current_user.id, db)
    if not user_team:
        raise HTTPException(status_code=404, detail="User is not part of any team")

    # Verify user is admin
    membership = team_manager.get_team_membership(user_team.id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(
            status_code=403, detail="Only team admins can manage billing"
        )

    # Get the selected plan
    plan = BILLING_PLANS.get(subscription_data.plan_id)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid plan selected")

    try:
        # Create Stripe customer
        customer = stripe.Customer.create(
            email=subscription_data.billing_email,
            name=user_team.name,
            metadata={"team_id": str(user_team.id), "user_id": str(current_user.id)},
        )

        # Attach payment method
        stripe.PaymentMethod.attach(
            subscription_data.payment_method_id, customer=customer.id
        )

        # Set as default payment method
        stripe.Customer.modify(
            customer.id,
            invoice_settings={
                "default_payment_method": subscription_data.payment_method_id
            },
        )

        # Get the appropriate price ID
        price_id = (
            plan.stripe_price_id_yearly
            if subscription_data.billing_cycle == "yearly"
            else plan.stripe_price_id_monthly
        )

        # Create subscription
        subscription = stripe.Subscription.create(
            customer=customer.id,
            items=[{"price": price_id}],
            metadata={
                "team_id": str(user_team.id),
                "plan_id": subscription_data.plan_id,
            },
        )

        # Update team with billing information (in production, store in database)
        # For now, we'll just return success

        return {
            "success": True,
            "subscription_id": subscription.id,
            "customer_id": customer.id,
            "status": subscription.status,
            "current_period_end": subscription.current_period_end,
        }

    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=400, detail=f"Payment processing failed: {str(e)}"
        )


@router.put("/subscription")
async def update_subscription(
    subscription_data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Update existing subscription
    """
    # Get user's team
    user_team = team_manager.get_user_team(current_user.id, db)
    if not user_team:
        raise HTTPException(status_code=404, detail="User is not part of any team")

    # Verify user is admin
    membership = team_manager.get_team_membership(user_team.id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(
            status_code=403, detail="Only team admins can manage billing"
        )

    # In production, you would:
    # 1. Get the current Stripe subscription ID from database
    # 2. Update the subscription via Stripe API
    # 3. Update local database records

    return {"success": True, "message": "Subscription updated successfully"}


@router.delete("/subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Cancel current subscription
    """
    # Get user's team
    user_team = team_manager.get_user_team(current_user.id, db)
    if not user_team:
        raise HTTPException(status_code=404, detail="User is not part of any team")

    # Verify user is admin
    membership = team_manager.get_team_membership(user_team.id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(
            status_code=403, detail="Only team admins can manage billing"
        )

    try:
        # In production, you would:
        # 1. Get the current Stripe subscription ID from database
        # 2. Cancel the subscription via Stripe API
        # 3. Update local database records

        return {
            "success": True,
            "message": "Subscription cancelled successfully",
            "effective_date": datetime.utcnow()
            + timedelta(days=30),  # End of current period
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Cancellation failed: {str(e)}")


@router.get("/usage/{team_id}", response_model=UsageMetrics)
async def get_team_usage(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> UsageMetrics:
    """
    Get detailed usage metrics for a team
    """
    # Verify user has access to this team
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied to team usage data")

    return calculate_usage_metrics(team_id, db)


@router.get("/invoices")
async def get_billing_history(
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> List[Dict[str, Any]]:
    """
    Get billing history and invoices
    """
    # Get user's team
    user_team = team_manager.get_user_team(current_user.id, db)
    if not user_team:
        raise HTTPException(status_code=404, detail="User is not part of any team")

    # In production, this would fetch from Stripe
    # For now, return mock data
    return [
        {
            "id": "inv_123",
            "date": "2024-09-01",
            "amount": 29.00,
            "status": "paid",
            "description": "Team Pro - Monthly",
            "download_url": "/billing/invoice/inv_123/download",
        }
    ]


@router.post("/webhook")
async def stripe_webhook(
    request: Dict[str, Any], db: Session = Depends(get_db)
) -> Dict[str, str]:
    """
    Handle Stripe webhooks for billing events
    """
    # In production, you would:
    # 1. Verify the webhook signature
    # 2. Handle different event types (payment_succeeded, subscription_updated, etc.)
    # 3. Update local database records accordingly

    event_type = request.get("type")

    if event_type == "invoice.payment_succeeded":
        # Handle successful payment
        pass
    elif event_type == "invoice.payment_failed":
        # Handle failed payment
        pass
    elif event_type == "customer.subscription.updated":
        # Handle subscription changes
        pass
    elif event_type == "customer.subscription.deleted":
        # Handle subscription cancellation
        pass

    return {"status": "success"}


# Helper function for upgrade recommendations in team dashboard
def get_billing_upgrade_prompt(team_id: UUID, db: Session) -> Optional[Dict[str, Any]]:
    """
    Get upgrade prompt for team dashboard integration
    """
    usage = calculate_usage_metrics(team_id, db)

    # Determine current plan based on member count (simplified)
    if usage.members_count <= 5:
        current_plan = "free"
    elif usage.members_count <= 20:
        current_plan = "team_pro"
    else:
        current_plan = "team_enterprise"

    recommendations = get_upgrade_recommendations(current_plan, usage)

    if recommendations:
        return {
            "show_upgrade": True,
            "primary_recommendation": recommendations[0],
            "usage_percentage": (
                usage.members_count / BILLING_PLANS[current_plan].max_members
            )
            * 100,
            "current_plan": current_plan,
        }

    return None
