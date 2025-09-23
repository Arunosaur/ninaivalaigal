"""
SPEC-068: Team Billing Portal
Self-service billing dashboard for teams with plan management, invoices, and usage tracking
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID
import stripe

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from database import Team, User
from models.standalone_teams import StandaloneTeamManager, TeamMembership

# Initialize router
router = APIRouter(prefix="/teams", tags=["team-billing-portal"])

# Mock data stores (use actual database in production)
team_subscriptions = {}
team_invoices = {}
team_usage_data = {}
team_payment_methods = {}


# Pydantic Models
class UsageMeter(BaseModel):
    """Usage meter for tracking team consumption"""
    metric_name: str
    current_usage: int
    limit: int
    unit: str
    percentage_used: float
    reset_date: datetime
    overage_cost_per_unit: Optional[float] = None


class PaymentMethod(BaseModel):
    """Payment method information"""
    id: str
    type: str  # card, bank_account
    brand: Optional[str] = None
    last4: str
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool
    created_at: datetime


class Invoice(BaseModel):
    """Invoice information"""
    id: str
    invoice_number: str
    status: str  # draft, open, paid, void, uncollectible
    amount_due: float
    amount_paid: float
    currency: str
    created_at: datetime
    due_date: Optional[datetime]
    paid_at: Optional[datetime]
    description: str
    line_items: List[Dict[str, Any]]
    pdf_url: Optional[str] = None


class BillingPlan(BaseModel):
    """Billing plan information"""
    id: str
    name: str
    price: float
    currency: str
    interval: str  # month, year
    features: List[str]
    limits: Dict[str, int]
    is_current: bool


class TeamBillingDashboard(BaseModel):
    """Complete team billing dashboard data"""
    team_id: str
    team_name: str
    current_plan: BillingPlan
    subscription_status: str
    next_billing_date: Optional[datetime]
    usage_meters: List[UsageMeter]
    recent_invoices: List[Invoice]
    payment_methods: List[PaymentMethod]
    billing_alerts: List[Dict[str, Any]]
    auto_renewal_enabled: bool
    total_spent_this_month: float
    projected_monthly_cost: float


class PlanUpgradeRequest(BaseModel):
    """Plan upgrade/downgrade request"""
    new_plan_id: str
    effective_date: Optional[datetime] = None
    prorate: bool = True


class PaymentMethodRequest(BaseModel):
    """Payment method addition request"""
    stripe_payment_method_id: str
    set_as_default: bool = False


# Helper Functions
def get_team_subscription(team_id: str) -> Optional[Dict[str, Any]]:
    """Get team subscription data"""
    return team_subscriptions.get(team_id)


def get_available_plans() -> List[BillingPlan]:
    """Get all available billing plans"""
    return [
        BillingPlan(
            id="free",
            name="Free Plan",
            price=0.0,
            currency="usd",
            interval="month",
            features=["5 team members", "1GB storage", "Basic support"],
            limits={"members": 5, "storage_gb": 1, "api_calls": 1000},
            is_current=False
        ),
        BillingPlan(
            id="pro",
            name="Pro Plan",
            price=29.0,
            currency="usd",
            interval="month",
            features=["25 team members", "10GB storage", "Priority support", "Advanced analytics"],
            limits={"members": 25, "storage_gb": 10, "api_calls": 50000},
            is_current=False
        ),
        BillingPlan(
            id="enterprise",
            name="Enterprise Plan",
            price=99.0,
            currency="usd",
            interval="month",
            features=["Unlimited members", "100GB storage", "24/7 support", "Custom integrations"],
            limits={"members": -1, "storage_gb": 100, "api_calls": 500000},
            is_current=False
        )
    ]


def calculate_usage_meters(team_id: str) -> List[UsageMeter]:
    """Calculate current usage meters for team"""
    # Mock usage data - in production, query actual usage
    usage_data = team_usage_data.get(team_id, {})
    
    return [
        UsageMeter(
            metric_name="Team Members",
            current_usage=usage_data.get("members", 3),
            limit=25,
            unit="members",
            percentage_used=round((usage_data.get("members", 3) / 25) * 100, 1),
            reset_date=datetime.utcnow().replace(day=1) + timedelta(days=32)
        ),
        UsageMeter(
            metric_name="Storage",
            current_usage=usage_data.get("storage_mb", 2048),
            limit=10240,  # 10GB in MB
            unit="MB",
            percentage_used=round((usage_data.get("storage_mb", 2048) / 10240) * 100, 1),
            reset_date=datetime.utcnow().replace(day=1) + timedelta(days=32)
        ),
        UsageMeter(
            metric_name="API Calls",
            current_usage=usage_data.get("api_calls", 15420),
            limit=50000,
            unit="calls",
            percentage_used=round((usage_data.get("api_calls", 15420) / 50000) * 100, 1),
            reset_date=datetime.utcnow().replace(day=1) + timedelta(days=32),
            overage_cost_per_unit=0.001
        ),
        UsageMeter(
            metric_name="Memory Tokens",
            current_usage=usage_data.get("memory_tokens", 8750),
            limit=100000,
            unit="tokens",
            percentage_used=round((usage_data.get("memory_tokens", 8750) / 100000) * 100, 1),
            reset_date=datetime.utcnow().replace(day=1) + timedelta(days=32)
        )
    ]


def get_team_invoices(team_id: str, limit: int = 10) -> List[Invoice]:
    """Get recent invoices for team"""
    invoices = team_invoices.get(team_id, [])
    
    # Mock invoice data
    if not invoices:
        invoices = [
            Invoice(
                id="in_001",
                invoice_number="INV-2024-001",
                status="paid",
                amount_due=29.00,
                amount_paid=29.00,
                currency="usd",
                created_at=datetime.utcnow() - timedelta(days=15),
                due_date=datetime.utcnow() - timedelta(days=10),
                paid_at=datetime.utcnow() - timedelta(days=10),
                description="Pro Plan - Monthly Subscription",
                line_items=[
                    {"description": "Pro Plan", "amount": 29.00, "quantity": 1}
                ],
                pdf_url="/invoices/in_001.pdf"
            ),
            Invoice(
                id="in_002",
                invoice_number="INV-2024-002",
                status="open",
                amount_due=29.00,
                amount_paid=0.00,
                currency="usd",
                created_at=datetime.utcnow() - timedelta(days=5),
                due_date=datetime.utcnow() + timedelta(days=10),
                paid_at=None,
                description="Pro Plan - Monthly Subscription",
                line_items=[
                    {"description": "Pro Plan", "amount": 29.00, "quantity": 1}
                ],
                pdf_url="/invoices/in_002.pdf"
            )
        ]
        team_invoices[team_id] = invoices
    
    return sorted(invoices, key=lambda x: x.created_at, reverse=True)[:limit]


def get_billing_alerts(team_id: str) -> List[Dict[str, Any]]:
    """Get billing alerts for team"""
    alerts = []
    
    # Check usage meters for alerts
    usage_meters = calculate_usage_meters(team_id)
    
    for meter in usage_meters:
        if meter.percentage_used >= 90:
            alerts.append({
                "type": "usage_warning",
                "severity": "high",
                "title": f"{meter.metric_name} Usage Alert",
                "message": f"You've used {meter.percentage_used}% of your {meter.metric_name} limit",
                "action_required": True,
                "created_at": datetime.utcnow()
            })
        elif meter.percentage_used >= 75:
            alerts.append({
                "type": "usage_warning",
                "severity": "medium",
                "title": f"{meter.metric_name} Usage Warning",
                "message": f"You've used {meter.percentage_used}% of your {meter.metric_name} limit",
                "action_required": False,
                "created_at": datetime.utcnow()
            })
    
    # Check for failed payments
    recent_invoices = get_team_invoices(team_id, 5)
    overdue_invoices = [inv for inv in recent_invoices if inv.status == "open" and inv.due_date and inv.due_date < datetime.utcnow()]
    
    if overdue_invoices:
        alerts.append({
            "type": "payment_overdue",
            "severity": "critical",
            "title": "Payment Overdue",
            "message": f"You have {len(overdue_invoices)} overdue invoice(s)",
            "action_required": True,
            "created_at": datetime.utcnow()
        })
    
    return alerts


# API Endpoints
@router.get("/{team_id}/billing-dashboard", response_model=TeamBillingDashboard)
async def get_team_billing_dashboard(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get complete team billing dashboard"""
    
    # Check team access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Check user permissions (team member or admin)
    if not (current_user.role == "admin" or current_user.id.endswith("owner")):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Get current plan
    subscription = get_team_subscription(team_id)
    current_plan_id = subscription.get("plan_id", "free") if subscription else "free"
    
    available_plans = get_available_plans()
    current_plan = next((plan for plan in available_plans if plan.id == current_plan_id), available_plans[0])
    current_plan.is_current = True
    
    # Get usage meters
    usage_meters = calculate_usage_meters(team_id)
    
    # Get recent invoices
    recent_invoices = get_team_invoices(team_id, 5)
    
    # Get payment methods
    payment_methods = team_payment_methods.get(team_id, [
        PaymentMethod(
            id="pm_001",
            type="card",
            brand="visa",
            last4="4242",
            exp_month=12,
            exp_year=2025,
            is_default=True,
            created_at=datetime.utcnow() - timedelta(days=30)
        )
    ])
    
    # Get billing alerts
    billing_alerts = get_billing_alerts(team_id)
    
    # Calculate costs
    total_spent_this_month = sum(inv.amount_paid for inv in recent_invoices if inv.paid_at and inv.paid_at.month == datetime.utcnow().month)
    projected_monthly_cost = current_plan.price
    
    return TeamBillingDashboard(
        team_id=team_id,
        team_name=team.name,
        current_plan=current_plan,
        subscription_status=subscription.get("status", "active") if subscription else "inactive",
        next_billing_date=subscription.get("next_billing_date") if subscription else None,
        usage_meters=usage_meters,
        recent_invoices=recent_invoices,
        payment_methods=payment_methods,
        billing_alerts=billing_alerts,
        auto_renewal_enabled=subscription.get("auto_renewal", True) if subscription else False,
        total_spent_this_month=total_spent_this_month,
        projected_monthly_cost=projected_monthly_cost
    )


@router.get("/{team_id}/billing-plans", response_model=List[BillingPlan])
async def get_available_billing_plans(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all available billing plans for team"""
    
    # Check team access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Get current plan
    subscription = get_team_subscription(team_id)
    current_plan_id = subscription.get("plan_id", "free") if subscription else "free"
    
    plans = get_available_plans()
    for plan in plans:
        plan.is_current = (plan.id == current_plan_id)
    
    return plans


@router.post("/{team_id}/billing-plans/upgrade")
async def upgrade_team_plan(
    team_id: str,
    request: PlanUpgradeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upgrade or downgrade team billing plan"""
    
    # Check team admin permissions
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not (current_user.role == "admin" or current_user.id.endswith("owner")):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate new plan
    available_plans = get_available_plans()
    new_plan = next((plan for plan in available_plans if plan.id == request.new_plan_id), None)
    if not new_plan:
        raise HTTPException(status_code=400, detail="Invalid plan ID")
    
    # Get current subscription
    current_subscription = get_team_subscription(team_id)
    current_plan_id = current_subscription.get("plan_id", "free") if current_subscription else "free"
    
    if current_plan_id == request.new_plan_id:
        raise HTTPException(status_code=400, detail="Already on this plan")
    
    # Create/update subscription
    effective_date = request.effective_date or datetime.utcnow()
    
    new_subscription = {
        "team_id": team_id,
        "plan_id": request.new_plan_id,
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "next_billing_date": effective_date + timedelta(days=30),
        "auto_renewal": True,
        "prorate": request.prorate
    }
    
    team_subscriptions[team_id] = new_subscription
    
    # In production, integrate with Stripe
    # stripe.Subscription.modify(subscription_id, items=[{"price": new_plan.stripe_price_id}])
    
    return {
        "message": f"Successfully upgraded to {new_plan.name}",
        "new_plan": new_plan.dict(),
        "effective_date": effective_date,
        "next_billing_date": new_subscription["next_billing_date"]
    }


@router.get("/{team_id}/invoices", response_model=List[Invoice])
async def get_team_invoices_list(
    team_id: str,
    limit: int = Query(20, description="Number of invoices to return"),
    status: Optional[str] = Query(None, description="Filter by invoice status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get team invoices with filtering"""
    
    # Check team access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not (current_user.role == "admin" or current_user.id.endswith("owner")):
        raise HTTPException(status_code=403, detail="Access denied")
    
    invoices = get_team_invoices(team_id, limit)
    
    # Filter by status if provided
    if status:
        invoices = [inv for inv in invoices if inv.status == status]
    
    return invoices


@router.get("/{team_id}/invoices/{invoice_id}/download")
async def download_invoice_pdf(
    team_id: str,
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Download invoice PDF"""
    
    # Check team access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not (current_user.role == "admin" or current_user.id.endswith("owner")):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Find invoice
    invoices = get_team_invoices(team_id, 100)  # Get more invoices to find the specific one
    invoice = next((inv for inv in invoices if inv.id == invoice_id), None)
    
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    # In production, generate and return actual PDF
    return {
        "message": "PDF download initiated",
        "invoice_id": invoice_id,
        "download_url": f"/invoices/{invoice_id}.pdf",
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    }


@router.post("/{team_id}/payment-methods")
async def add_payment_method(
    team_id: str,
    request: PaymentMethodRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add new payment method to team"""
    
    # Check team admin permissions
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not (current_user.role == "admin" or current_user.id.endswith("owner")):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # In production, integrate with Stripe to attach payment method
    # payment_method = stripe.PaymentMethod.retrieve(request.stripe_payment_method_id)
    # stripe.PaymentMethod.attach(request.stripe_payment_method_id, customer=customer_id)
    
    # Mock payment method creation
    new_payment_method = PaymentMethod(
        id=request.stripe_payment_method_id,
        type="card",
        brand="visa",
        last4="4242",
        exp_month=12,
        exp_year=2025,
        is_default=request.set_as_default,
        created_at=datetime.utcnow()
    )
    
    # Update team payment methods
    if team_id not in team_payment_methods:
        team_payment_methods[team_id] = []
    
    # If setting as default, update existing methods
    if request.set_as_default:
        for pm in team_payment_methods[team_id]:
            pm.is_default = False
    
    team_payment_methods[team_id].append(new_payment_method)
    
    return {
        "message": "Payment method added successfully",
        "payment_method": new_payment_method.dict()
    }


@router.post("/{team_id}/auto-renewal/toggle")
async def toggle_auto_renewal(
    team_id: str,
    enabled: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle auto-renewal for team subscription"""
    
    # Check team admin permissions
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not (current_user.role == "admin" or current_user.id.endswith("owner")):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Update subscription
    subscription = get_team_subscription(team_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    subscription["auto_renewal"] = enabled
    subscription["updated_at"] = datetime.utcnow()
    
    team_subscriptions[team_id] = subscription
    
    return {
        "message": f"Auto-renewal {'enabled' if enabled else 'disabled'}",
        "auto_renewal_enabled": enabled
    }


@router.get("/{team_id}/usage-export")
async def export_usage_data(
    team_id: str,
    start_date: datetime = Query(..., description="Start date for export"),
    end_date: datetime = Query(..., description="End date for export"),
    format: str = Query("csv", description="Export format: csv, json"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export team usage data"""
    
    # Check team access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    if not (current_user.role == "admin" or current_user.id.endswith("owner")):
        raise HTTPException(status_code=403, detail="Access denied")
    
    # In production, generate actual export file
    export_data = {
        "team_id": team_id,
        "team_name": team.name,
        "export_period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "usage_summary": {
            "total_api_calls": 15420,
            "total_storage_used": 2048,
            "total_members": 3,
            "total_memory_tokens": 8750
        },
        "generated_at": datetime.utcnow().isoformat()
    }
    
    return {
        "message": "Usage data export generated",
        "export_id": f"export_{team_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
        "format": format,
        "download_url": f"/exports/usage_{team_id}_{datetime.utcnow().strftime('%Y%m%d')}.{format}",
        "expires_at": datetime.utcnow() + timedelta(hours=24),
        "data": export_data if format == "json" else None
    }
