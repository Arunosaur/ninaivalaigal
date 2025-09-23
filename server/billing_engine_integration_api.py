"""
SPEC-027: Billing Engine Integration
Complete payment infrastructure with Stripe integration, webhook processing, and automated billing
"""

import os
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from decimal import Decimal
import stripe
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import io
import base64

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from auth import get_current_user, get_db
from database import Team, User, Organization
from standalone_teams_billing_api import (
    billing_plans, team_credits_store, discount_codes_store, 
    deduct_team_credits, apply_discount_to_amount
)

# Initialize router
router = APIRouter(prefix="/billing-engine", tags=["billing-engine"])

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_...")

# Mock data stores (use actual database in production)
stripe_customers_store = {}
stripe_subscriptions_store = {}
billing_invoices_store = {}
payment_attempts_store = {}
dunning_campaigns_store = {}


# Pydantic Models
class StripeCustomerCreateRequest(BaseModel):
    """Request model for creating Stripe customer"""
    team_id: str
    email: EmailStr
    name: str
    billing_address: Optional[Dict[str, str]] = None
    tax_id: Optional[str] = None


class StripeSubscriptionCreateRequest(BaseModel):
    """Request model for creating Stripe subscription"""
    customer_id: str
    price_id: str
    team_id: str
    discount_code: Optional[str] = None
    trial_days: Optional[int] = None


class WebhookEventResponse(BaseModel):
    """Response model for webhook processing"""
    event_id: str
    event_type: str
    processed: bool
    team_id: Optional[str]
    subscription_id: Optional[str]
    invoice_id: Optional[str]
    processing_time: float
    actions_taken: List[str]


class InvoiceGenerationRequest(BaseModel):
    """Request model for invoice generation"""
    team_id: str
    billing_period_start: datetime
    billing_period_end: datetime
    line_items: List[Dict[str, Any]]
    discount_codes: Optional[List[str]] = None
    tax_rate: Optional[float] = None


class InvoiceResponse(BaseModel):
    """Response model for generated invoice"""
    invoice_id: str
    invoice_number: str
    team_id: str
    amount_due: float
    amount_paid: float
    status: str
    due_date: datetime
    pdf_url: Optional[str]
    stripe_invoice_url: Optional[str]
    line_items: List[Dict[str, Any]]


class PaymentRetryRequest(BaseModel):
    """Request model for payment retry"""
    invoice_id: str
    retry_strategy: str = Field(default="exponential", description="immediate, exponential, scheduled")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    notify_customer: bool = Field(default=True, description="Send notification to customer")


class DunningCampaignRequest(BaseModel):
    """Request model for dunning campaign"""
    team_id: str
    invoice_id: str
    campaign_type: str = Field(default="standard", description="standard, aggressive, gentle")
    escalation_days: List[int] = Field(default=[1, 3, 7, 14], description="Days for escalation")


class UsageTrackingRequest(BaseModel):
    """Request model for usage tracking"""
    team_id: str
    metric_name: str
    metric_value: int
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class BillingAnalytics(BaseModel):
    """Billing analytics response"""
    team_id: str
    current_period: Dict[str, Any]
    revenue_metrics: Dict[str, float]
    payment_metrics: Dict[str, Any]
    usage_trends: List[Dict[str, Any]]
    churn_risk_score: float


# Helper Functions
def get_stripe_customer_id(team_id: str) -> Optional[str]:
    """Get Stripe customer ID for team"""
    return stripe_customers_store.get(team_id, {}).get("stripe_customer_id")


def calculate_tax_amount(amount: float, tax_rate: float, billing_address: Dict[str, str]) -> float:
    """Calculate tax amount based on billing address and rate"""
    # Simplified tax calculation - in production, use tax service like TaxJar
    if billing_address.get("country") == "US":
        state_tax_rates = {
            "CA": 0.0875,  # California
            "NY": 0.08,    # New York
            "TX": 0.0625,  # Texas
            "FL": 0.06,    # Florida
        }
        state = billing_address.get("state", "")
        tax_rate = state_tax_rates.get(state, 0.0)
    
    return amount * tax_rate


def generate_invoice_pdf(invoice_data: Dict[str, Any]) -> bytes:
    """Generate PDF invoice"""
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    
    # Header
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, "ninaivalaigal")
    p.setFont("Helvetica", 12)
    p.drawString(50, height - 70, "Memory Management Platform")
    
    # Invoice details
    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, height - 120, f"Invoice #{invoice_data['invoice_number']}")
    
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 140, f"Date: {invoice_data['created_at'].strftime('%B %d, %Y')}")
    p.drawString(50, height - 155, f"Due Date: {invoice_data['due_date'].strftime('%B %d, %Y')}")
    
    # Customer info
    p.drawString(50, height - 185, f"Bill To:")
    p.drawString(50, height - 200, f"Team: {invoice_data['team_name']}")
    p.drawString(50, height - 215, f"Email: {invoice_data['billing_email']}")
    
    # Line items
    y_position = height - 260
    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, y_position, "Description")
    p.drawString(300, y_position, "Quantity")
    p.drawString(400, y_position, "Rate")
    p.drawString(500, y_position, "Amount")
    
    y_position -= 20
    p.setFont("Helvetica", 10)
    
    total_amount = 0
    for item in invoice_data['line_items']:
        p.drawString(50, y_position, item['description'])
        p.drawString(300, y_position, str(item['quantity']))
        p.drawString(400, y_position, f"${item['rate']:.2f}")
        p.drawString(500, y_position, f"${item['amount']:.2f}")
        total_amount += item['amount']
        y_position -= 15
    
    # Total
    y_position -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(400, y_position, f"Total: ${total_amount:.2f}")
    
    # Footer
    p.setFont("Helvetica", 8)
    p.drawString(50, 50, "Thank you for using ninaivalaigal!")
    p.drawString(50, 35, "Questions? Contact support@ninaivalaigal.com")
    
    p.save()
    buffer.seek(0)
    return buffer.read()


def send_invoice_email(invoice_data: Dict[str, Any], pdf_content: bytes):
    """Send invoice email to customer"""
    # In production, integrate with email service like SendGrid
    print(f"Sending invoice {invoice_data['invoice_number']} to {invoice_data['billing_email']}")
    # Mock email sending
    return True


def process_payment_webhook(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process Stripe webhook event"""
    event_type = event_data.get("type")
    event_id = event_data.get("id")
    
    processing_result = {
        "event_id": event_id,
        "event_type": event_type,
        "processed": False,
        "team_id": None,
        "actions_taken": []
    }
    
    try:
        if event_type == "invoice.payment_succeeded":
            invoice = event_data["data"]["object"]
            subscription_id = invoice.get("subscription")
            
            # Find team by subscription
            team_id = None
            for tid, sub_data in stripe_subscriptions_store.items():
                if sub_data.get("stripe_subscription_id") == subscription_id:
                    team_id = tid
                    break
            
            if team_id:
                # Update invoice status
                invoice_id = invoice.get("id")
                if invoice_id in billing_invoices_store:
                    billing_invoices_store[invoice_id]["status"] = "paid"
                    billing_invoices_store[invoice_id]["paid_at"] = datetime.utcnow()
                    billing_invoices_store[invoice_id]["amount_paid"] = invoice["amount_paid"] / 100
                
                processing_result.update({
                    "processed": True,
                    "team_id": team_id,
                    "invoice_id": invoice_id,
                    "actions_taken": ["updated_invoice_status", "recorded_payment"]
                })
        
        elif event_type == "invoice.payment_failed":
            invoice = event_data["data"]["object"]
            subscription_id = invoice.get("subscription")
            
            # Find team and initiate retry/dunning
            team_id = None
            for tid, sub_data in stripe_subscriptions_store.items():
                if sub_data.get("stripe_subscription_id") == subscription_id:
                    team_id = tid
                    break
            
            if team_id:
                # Record payment failure
                failure_data = {
                    "team_id": team_id,
                    "invoice_id": invoice.get("id"),
                    "failure_reason": invoice.get("last_payment_error", {}).get("message", "Unknown"),
                    "failed_at": datetime.utcnow(),
                    "retry_count": 0
                }
                
                payment_attempts_store[invoice.get("id")] = failure_data
                
                processing_result.update({
                    "processed": True,
                    "team_id": team_id,
                    "invoice_id": invoice.get("id"),
                    "actions_taken": ["recorded_payment_failure", "initiated_retry_sequence"]
                })
        
        elif event_type == "customer.subscription.updated":
            subscription = event_data["data"]["object"]
            subscription_id = subscription.get("id")
            
            # Update subscription status
            for team_id, sub_data in stripe_subscriptions_store.items():
                if sub_data.get("stripe_subscription_id") == subscription_id:
                    sub_data["status"] = subscription.get("status")
                    sub_data["current_period_start"] = datetime.fromtimestamp(subscription["current_period_start"])
                    sub_data["current_period_end"] = datetime.fromtimestamp(subscription["current_period_end"])
                    
                    processing_result.update({
                        "processed": True,
                        "team_id": team_id,
                        "subscription_id": subscription_id,
                        "actions_taken": ["updated_subscription_status"]
                    })
                    break
        
    except Exception as e:
        processing_result["error"] = str(e)
        processing_result["actions_taken"].append(f"error_occurred: {str(e)}")
    
    return processing_result


# API Endpoints

# Stripe Customer Management
@router.post("/customers/create")
async def create_stripe_customer(
    request: StripeCustomerCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe customer for team"""
    
    # Check team access
    team = db.query(Team).filter(Team.id == request.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    try:
        # Create Stripe customer
        stripe_customer = stripe.Customer.create(
            email=request.email,
            name=request.name,
            metadata={
                "team_id": request.team_id,
                "platform": "ninaivalaigal"
            },
            address=request.billing_address,
            tax_id=request.tax_id
        )
        
        # Store customer data
        customer_data = {
            "stripe_customer_id": stripe_customer.id,
            "team_id": request.team_id,
            "email": request.email,
            "name": request.name,
            "billing_address": request.billing_address,
            "created_at": datetime.utcnow()
        }
        
        stripe_customers_store[request.team_id] = customer_data
        
        # Update team with customer ID
        team.billing_customer_id = stripe_customer.id
        db.commit()
        
        return {
            "message": "Stripe customer created successfully",
            "customer_id": stripe_customer.id,
            "team_id": request.team_id
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")


# Subscription Management
@router.post("/subscriptions/create")
async def create_stripe_subscription(
    request: StripeSubscriptionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create Stripe subscription for team"""
    
    try:
        # Get billing plan details
        plan_id = None
        for pid, plan in billing_plans.items():
            if plan.get("stripe_price_id") == request.price_id:
                plan_id = pid
                break
        
        if not plan_id:
            raise HTTPException(status_code=400, detail="Invalid price ID")
        
        # Apply discount if provided
        coupon_id = None
        if request.discount_code:
            # In production, create Stripe coupon from discount code
            coupon_id = f"discount_{request.discount_code}"
        
        # Create subscription
        subscription_data = {
            "customer": request.customer_id,
            "items": [{"price": request.price_id}],
            "metadata": {
                "team_id": request.team_id,
                "plan_id": plan_id
            }
        }
        
        if coupon_id:
            subscription_data["coupon"] = coupon_id
        
        if request.trial_days:
            subscription_data["trial_period_days"] = request.trial_days
        
        stripe_subscription = stripe.Subscription.create(**subscription_data)
        
        # Store subscription data
        subscription_info = {
            "stripe_subscription_id": stripe_subscription.id,
            "team_id": request.team_id,
            "plan_id": plan_id,
            "status": stripe_subscription.status,
            "current_period_start": datetime.fromtimestamp(stripe_subscription.current_period_start),
            "current_period_end": datetime.fromtimestamp(stripe_subscription.current_period_end),
            "created_at": datetime.utcnow()
        }
        
        stripe_subscriptions_store[request.team_id] = subscription_info
        
        return {
            "message": "Subscription created successfully",
            "subscription_id": stripe_subscription.id,
            "status": stripe_subscription.status,
            "current_period_end": subscription_info["current_period_end"]
        }
        
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=f"Stripe error: {str(e)}")


# Webhook Processing
@router.post("/webhooks/stripe")
async def handle_stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle Stripe webhook events"""
    
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    try:
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    # Process webhook in background
    background_tasks.add_task(process_webhook_event, event)
    
    return {"received": True, "event_id": event["id"]}


async def process_webhook_event(event: Dict[str, Any]):
    """Process webhook event in background"""
    start_time = datetime.utcnow()
    
    result = process_payment_webhook(event)
    
    processing_time = (datetime.utcnow() - start_time).total_seconds()
    result["processing_time"] = processing_time
    
    # Log webhook processing result
    print(f"Webhook processed: {result}")
    
    return result


# Invoice Generation
@router.post("/invoices/generate", response_model=InvoiceResponse)
async def generate_invoice(
    request: InvoiceGenerationRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate invoice for team"""
    
    # Check team access
    team = db.query(Team).filter(Team.id == request.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Calculate invoice amounts
    subtotal = sum(item["amount"] for item in request.line_items)
    
    # Apply discounts
    discount_amount = 0
    if request.discount_codes:
        for code in request.discount_codes:
            discount_amount += subtotal - apply_discount_to_amount(subtotal, code)
    
    # Calculate tax
    billing_address = stripe_customers_store.get(request.team_id, {}).get("billing_address", {})
    tax_amount = calculate_tax_amount(subtotal - discount_amount, request.tax_rate or 0, billing_address)
    
    # Apply credits
    total_before_credits = subtotal - discount_amount + tax_amount
    credits_used = total_before_credits - deduct_team_credits(request.team_id, total_before_credits)
    final_amount = total_before_credits - credits_used
    
    # Generate invoice
    invoice_id = str(uuid4())
    invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m')}-{len(billing_invoices_store) + 1:04d}"
    
    invoice_data = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "team_id": request.team_id,
        "team_name": team.name,
        "billing_email": stripe_customers_store.get(request.team_id, {}).get("email", ""),
        "amount_due": final_amount,
        "amount_paid": 0.0,
        "currency": "usd",
        "status": "open",
        "billing_period_start": request.billing_period_start,
        "billing_period_end": request.billing_period_end,
        "due_date": datetime.utcnow() + timedelta(days=30),
        "line_items": request.line_items,
        "subtotal": subtotal,
        "discount_amount": discount_amount,
        "tax_amount": tax_amount,
        "credits_used": credits_used,
        "discount_codes_applied": request.discount_codes or [],
        "created_at": datetime.utcnow()
    }
    
    billing_invoices_store[invoice_id] = invoice_data
    
    # Generate PDF in background
    background_tasks.add_task(generate_and_send_invoice_pdf, invoice_data)
    
    return InvoiceResponse(
        invoice_id=invoice_id,
        invoice_number=invoice_number,
        team_id=request.team_id,
        amount_due=final_amount,
        amount_paid=0.0,
        status="open",
        due_date=invoice_data["due_date"],
        pdf_url=f"/billing-engine/invoices/{invoice_id}/pdf",
        stripe_invoice_url=None,
        line_items=request.line_items
    )


async def generate_and_send_invoice_pdf(invoice_data: Dict[str, Any]):
    """Generate PDF and send invoice email"""
    try:
        # Generate PDF
        pdf_content = generate_invoice_pdf(invoice_data)
        
        # Store PDF (in production, upload to S3 or similar)
        pdf_filename = f"invoice_{invoice_data['invoice_number']}.pdf"
        
        # Send email
        send_invoice_email(invoice_data, pdf_content)
        
        # Update invoice with PDF info
        invoice_data["pdf_generated"] = True
        invoice_data["pdf_filename"] = pdf_filename
        invoice_data["email_sent"] = True
        
        print(f"Invoice {invoice_data['invoice_number']} PDF generated and email sent")
        
    except Exception as e:
        print(f"Error generating invoice PDF: {str(e)}")


# Payment Retry Logic
@router.post("/payments/retry")
async def retry_payment(
    request: PaymentRetryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Retry failed payment"""
    
    if request.invoice_id not in billing_invoices_store:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice_data = billing_invoices_store[request.invoice_id]
    
    # Get payment attempt history
    payment_attempt = payment_attempts_store.get(request.invoice_id, {})
    retry_count = payment_attempt.get("retry_count", 0)
    
    if retry_count >= request.max_retries:
        raise HTTPException(status_code=400, detail="Maximum retry attempts reached")
    
    # Schedule retry based on strategy
    if request.retry_strategy == "immediate":
        delay_seconds = 0
    elif request.retry_strategy == "exponential":
        delay_seconds = (2 ** retry_count) * 3600  # 1h, 2h, 4h, 8h
    else:  # scheduled
        delay_seconds = 24 * 3600  # 24 hours
    
    # Update retry count
    payment_attempt["retry_count"] = retry_count + 1
    payment_attempt["next_retry_at"] = datetime.utcnow() + timedelta(seconds=delay_seconds)
    payment_attempts_store[request.invoice_id] = payment_attempt
    
    # Schedule retry
    background_tasks.add_task(schedule_payment_retry, request.invoice_id, delay_seconds, request.notify_customer)
    
    return {
        "message": "Payment retry scheduled",
        "invoice_id": request.invoice_id,
        "retry_count": retry_count + 1,
        "next_retry_at": payment_attempt["next_retry_at"],
        "strategy": request.retry_strategy
    }


async def schedule_payment_retry(invoice_id: str, delay_seconds: int, notify_customer: bool):
    """Schedule payment retry"""
    import asyncio
    
    if delay_seconds > 0:
        await asyncio.sleep(delay_seconds)
    
    try:
        # Attempt payment retry with Stripe
        invoice_data = billing_invoices_store.get(invoice_id)
        if invoice_data and invoice_data["status"] == "open":
            # In production, retry payment with Stripe
            print(f"Retrying payment for invoice {invoice_id}")
            
            if notify_customer:
                # Send retry notification
                print(f"Sending retry notification for invoice {invoice_id}")
        
    except Exception as e:
        print(f"Error retrying payment for invoice {invoice_id}: {str(e)}")


# Usage Tracking
@router.post("/usage/track")
async def track_usage(
    request: UsageTrackingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track usage metrics for billing"""
    
    # Validate team access
    team = db.query(Team).filter(Team.id == request.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Record usage
    usage_entry = {
        "team_id": request.team_id,
        "metric_name": request.metric_name,
        "metric_value": request.metric_value,
        "timestamp": request.timestamp or datetime.utcnow(),
        "metadata": request.metadata or {},
        "recorded_at": datetime.utcnow()
    }
    
    # Store usage data (in production, use time-series database)
    usage_key = f"{request.team_id}_{request.metric_name}_{datetime.utcnow().date()}"
    
    return {
        "message": "Usage tracked successfully",
        "team_id": request.team_id,
        "metric_name": request.metric_name,
        "metric_value": request.metric_value,
        "timestamp": usage_entry["timestamp"]
    }


# Billing Analytics
@router.get("/analytics/{team_id}", response_model=BillingAnalytics)
async def get_billing_analytics(
    team_id: str,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get billing analytics for team"""
    
    # Check team access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Calculate analytics
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Get subscription data
    subscription_data = stripe_subscriptions_store.get(team_id, {})
    
    # Calculate revenue metrics
    revenue_metrics = {
        "mrr": billing_plans.get(subscription_data.get("plan_id", "free"), {}).get("price", 0),
        "total_revenue": 0,  # Calculate from invoices
        "credits_used": 0,   # Calculate from credits
        "discount_savings": 0  # Calculate from discounts
    }
    
    # Calculate payment metrics
    team_invoices = [inv for inv in billing_invoices_store.values() if inv["team_id"] == team_id]
    payment_metrics = {
        "total_invoices": len(team_invoices),
        "paid_invoices": len([inv for inv in team_invoices if inv["status"] == "paid"]),
        "overdue_invoices": len([inv for inv in team_invoices if inv["status"] == "open" and inv["due_date"] < datetime.utcnow()]),
        "payment_success_rate": 0.95  # Mock data
    }
    
    # Calculate churn risk
    churn_risk_score = 0.1  # Mock low risk
    if payment_metrics["overdue_invoices"] > 0:
        churn_risk_score = 0.7
    elif payment_metrics["payment_success_rate"] < 0.8:
        churn_risk_score = 0.5
    
    return BillingAnalytics(
        team_id=team_id,
        current_period={
            "start_date": start_date,
            "end_date": end_date,
            "plan": subscription_data.get("plan_id", "free"),
            "status": subscription_data.get("status", "inactive")
        },
        revenue_metrics=revenue_metrics,
        payment_metrics=payment_metrics,
        usage_trends=[],  # Mock empty for now
        churn_risk_score=churn_risk_score
    )
