#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-027: Invoice and Plan Management API
Complete invoice generation, tax handling, and billing cycle management
"""

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import stripe
from database import Team, TeamMembership, User
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from models.standalone_teams import StandaloneTeamManager
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user, get_db

# Import database models for invoice management (US#185)
from server.billing.models import (
    AccountStatus,
    BillingAccount,
    BillingPeriod,
    BillingPeriodStatus,
)
from server.billing.models import Invoice as InvoiceModel
from server.billing.models import InvoiceLineItem as InvoiceLineItemModel
from server.billing.models import InvoiceStatus, PlanTier
from server.billing.payment_failure_model import PaymentFailure as PaymentFailureModel
from server.billing.tax_config_models import TaxConfiguration
from services import InvoicingService, TaxCalculator

# Shared invoicing services (US#237-243: SPEC-027/028 refactoring complete)
# Always use shared services - legacy code removed
tax_calculator = TaxCalculator()
invoicing_service = InvoicingService(tax_calculator=tax_calculator)

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

# Initialize router
router = APIRouter(prefix="/invoicing", tags=["billing"])


# Pydantic Models
class TaxSettings(BaseModel):
    """Tax configuration for billing"""

    tax_rate: float  # Percentage (e.g., 8.5 for 8.5%)
    tax_name: str  # e.g., "Sales Tax", "VAT", "GST"
    tax_id: Optional[str] = None  # Tax registration number
    tax_address: Optional[Dict[str, str]] = None
    is_tax_inclusive: bool = False  # Whether prices include tax


class InvoiceLineItem(BaseModel):
    """Individual line item on invoice"""

    description: str
    quantity: int
    unit_price: float
    total_price: float
    period_start: datetime
    period_end: datetime


class Invoice(BaseModel):
    """Complete invoice model"""

    id: str
    invoice_number: str
    team_id: UUID
    team_name: str
    billing_email: str
    issue_date: datetime
    due_date: datetime
    period_start: datetime
    period_end: datetime
    subtotal: float
    tax_amount: float
    total_amount: float
    currency: str
    status: str  # "draft", "sent", "paid", "overdue", "cancelled"
    line_items: List[InvoiceLineItem]
    payment_method: Optional[str]
    paid_date: Optional[datetime]
    stripe_invoice_id: Optional[str]


class BillingCycle(BaseModel):
    """Billing cycle configuration"""

    team_id: UUID
    cycle_type: str  # "monthly", "yearly"
    next_billing_date: datetime
    last_invoice_date: Optional[datetime]
    auto_billing_enabled: bool
    payment_method_id: Optional[str]
    billing_email: str


class PaymentFailure(BaseModel):
    """Payment failure tracking"""

    id: str
    team_id: UUID
    invoice_id: str
    failure_date: datetime
    failure_reason: str
    retry_count: int
    next_retry_date: Optional[datetime]
    is_resolved: bool


# US#185: Mock databases removed - using database models instead
# All CRUD operations now use database models:
# - invoices_db → server.billing.models.Invoice (✅ migrated)
# - billing_cycles_db → server.billing.models.BillingPeriod (✅ migrated)
# - payment_failures_db → server.billing.payment_failure_model.PaymentFailure (✅ migrated)
# - tax_settings_db → server.billing.tax_config_models.TaxConfiguration (✅ migrated)
#
# All mock stores have been removed. All operations use database models.


# Helper functions for database operations
def get_or_create_billing_account(db: Session, team_id: UUID) -> BillingAccount:
    """
    Get or create BillingAccount for a team.

    US#185: Migrated from mock stores to database model.
    """
    # Check if billing account exists
    billing_account = (
        db.query(BillingAccount)
        .filter(
            BillingAccount.account_type == "team",
            BillingAccount.account_id == team_id,
            BillingAccount.status != AccountStatus.DELETED.value,
        )
        .first()
    )

    if billing_account:
        return billing_account

    # Create new billing account
    billing_account = BillingAccount(
        account_type="team",
        account_id=team_id,
        plan_tier=PlanTier.FREE.value,
        currency="USD",
        status=AccountStatus.ACTIVE.value,
    )
    db.add(billing_account)
    db.flush()
    return billing_account


def get_or_create_billing_period(
    db: Session, billing_account_id: UUID, period_start: datetime, period_end: datetime
) -> BillingPeriod:
    """
    Get or create BillingPeriod for a billing account and period.

    US#185: Migrated from mock stores to database model.
    """
    # Check if billing period exists
    billing_period = (
        db.query(BillingPeriod)
        .filter(
            BillingPeriod.billing_account_id == billing_account_id,
            BillingPeriod.period_start == period_start,
            BillingPeriod.period_end == period_end,
        )
        .first()
    )

    if billing_period:
        return billing_period

    # Create new billing period
    billing_period = BillingPeriod(
        billing_account_id=billing_account_id,
        period_start=period_start,
        period_end=period_end,
        status=BillingPeriodStatus.ACTIVE.value,
    )
    db.add(billing_period)
    db.flush()
    return billing_period


def invoice_model_to_pydantic(invoice_model: InvoiceModel) -> Invoice:
    """
    Convert database InvoiceModel to Pydantic Invoice for API responses.

    US#185: Helper function for database-to-API conversion.
    """
    # Get line items
    line_items_data = []
    for line_item in invoice_model.line_items:
        line_items_data.append(
            InvoiceLineItem(
                description=line_item.description,
                quantity=float(line_item.quantity),
                unit_price=float(line_item.unit_price),
                total_price=float(line_item.amount),
                period_start=invoice_model.billing_period.period_start if invoice_model.billing_period else None,
                period_end=invoice_model.billing_period.period_end if invoice_model.billing_period else None,
            )
        )

    # Get team info from billing account
    team_id = invoice_model.billing_account.account_id if invoice_model.billing_account else None

    return Invoice(
        id=str(invoice_model.id),
        invoice_number=invoice_model.invoice_number,
        team_id=team_id,
        team_name=None,  # Would need to query Team model if needed
        billing_email=None,  # Would need to query TeamBilling if needed
        issue_date=invoice_model.issued_at or invoice_model.created_at,
        due_date=invoice_model.due_at,
        period_start=invoice_model.billing_period.period_start if invoice_model.billing_period else None,
        period_end=invoice_model.billing_period.period_end if invoice_model.billing_period else None,
        subtotal=float(invoice_model.subtotal),
        tax_amount=float(invoice_model.tax_amount),
        total_amount=float(invoice_model.total_amount),
        currency=invoice_model.currency,
        status=invoice_model.status,
        line_items=line_items_data,
        payment_method=None,  # Would need to query PaymentConfig if needed
        paid_date=invoice_model.paid_at,
        stripe_invoice_id=None,  # Would need to query StripeInvoice if needed
    )


def get_team_manager() -> StandaloneTeamManager:
    """Dependency to get team manager"""
    return StandaloneTeamManager()


# calculate_tax() removed - use tax_calculator.calculate() directly (US#243)


def generate_invoice_number() -> str:
    """Generate unique invoice number"""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m")
    random_suffix = str(uuid4())[:8].upper()
    return f"INV-{timestamp}-{random_suffix}"


def create_pdf_invoice(invoice: Invoice, tax_settings: Optional[TaxSettings] = None) -> bytes:
    """
    Generate PDF invoice using shared InvoicingService (US#237-243)

    This is a wrapper function that transforms Invoice model to dict format
    and calls the shared InvoicingService. All PDF generation is now centralized.
    """
    invoice_data = {
        "invoice_number": invoice.invoice_number,
        "issue_date": invoice.issue_date,
        "created_at": invoice.issue_date,
        "due_date": invoice.due_date,
        "team_name": invoice.team_name,
        "billing_email": invoice.billing_email,
        "team_id": str(invoice.team_id),
        "period_start": invoice.period_start,
        "period_end": invoice.period_end,
        "line_items": [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "period_start": item.period_start,
                "period_end": item.period_end,
            }
            for item in invoice.line_items
        ],
        "subtotal": invoice.subtotal,
        "tax_amount": invoice.tax_amount,
        "total_amount": invoice.total_amount,
        "status": invoice.status,
        "paid_date": invoice.paid_date,
    }

    tax_settings_dict = None
    if tax_settings:
        tax_settings_dict = {
            "tax_name": tax_settings.tax_name,
            "tax_rate": tax_settings.tax_rate,
        }

    return invoicing_service.generate_pdf(invoice_data, tax_settings_dict)


@router.post("/generate")
async def generate_invoice(
    team_id: UUID,
    period_start: datetime,
    period_end: datetime,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Invoice:
    """Generate invoice for team's usage period"""

    # Get team and verify access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only team admins can generate invoices")

    # Calculate usage and charges
    member_count = (
        db.query(TeamMembership).filter(TeamMembership.team_id == team_id, TeamMembership.status == "active").count()
    )

    # Determine plan and pricing
    if member_count <= 5:
        plan = "free"
        monthly_price = 0.0
    elif member_count <= 20:
        plan = "team_pro"
        monthly_price = 29.0
    elif member_count <= 50:
        plan = "team_enterprise"
        monthly_price = 99.0
    else:
        plan = "organization"
        monthly_price = 500.0

    # Create line items
    line_items = []

    if monthly_price > 0:
        line_items.append(
            InvoiceLineItem(
                description=f"Ninaivalaigal {plan.replace('_', ' ').title()} Plan",
                quantity=1,
                unit_price=monthly_price,
                total_price=monthly_price,
                period_start=period_start,
                period_end=period_end,
            )
        )

    # Add usage-based charges (mock data)
    storage_overage = max(0, member_count * 0.8 - 10)  # Estimate storage overage
    if storage_overage > 0:
        overage_charge = storage_overage * 2.0  # $2/GB overage
        line_items.append(
            InvoiceLineItem(
                description="Storage Overage",
                quantity=int(storage_overage),
                unit_price=2.0,
                total_price=overage_charge,
                period_start=period_start,
                period_end=period_end,
            )
        )

    # Calculate totals
    subtotal = sum(item.total_price for item in line_items)

    # Get tax settings from database and calculate tax using shared TaxCalculator service (US#185, US#237-243)
    tax_config = db.query(TaxConfiguration).filter(TaxConfiguration.team_id == team_id).first()
    tax_amount = 0.0
    if tax_config:
        # Get tax rate from tax_config settings or use default
        tax_rate = 0.0
        if tax_config.settings and isinstance(tax_config.settings, dict):
            tax_rate = tax_config.settings.get("tax_rate", 0.0)

        tax_amount = tax_calculator.calculate(
            subtotal=subtotal,
            tax_rate=tax_rate / 100.0 if tax_rate > 0 else 0.0,  # Convert percentage to decimal
            is_tax_inclusive=tax_config.tax_inclusive_pricing,
        )

    total_amount = subtotal + tax_amount

    # US#185: Get or create billing account and period
    billing_account = get_or_create_billing_account(db, team_id)
    billing_period = get_or_create_billing_period(db, billing_account.id, period_start, period_end)

    # US#185: Create invoice in database
    invoice_number = generate_invoice_number()
    invoice_model = InvoiceModel(
        billing_account_id=billing_account.id,
        billing_period_id=billing_period.id,
        invoice_number=invoice_number,
        subtotal=Decimal(str(subtotal)),
        tax_amount=Decimal(str(tax_amount)),
        total_amount=Decimal(str(total_amount)),
        currency="USD",
        status=InvoiceStatus.DRAFT.value,
        issued_at=datetime.now(timezone.utc),
        due_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(invoice_model)
    db.flush()

    # Create line items in database
    for line_item in line_items:
        line_item_model = InvoiceLineItemModel(
            invoice_id=invoice_model.id,
            resource_type="subscription",  # Default, can be customized
            description=line_item.description,
            quantity=Decimal(str(line_item.quantity)),
            unit_price=Decimal(str(line_item.unit_price)),
            amount=Decimal(str(line_item.total_price)),
        )
        db.add(line_item_model)

    db.commit()
    db.refresh(invoice_model)

    # Convert to Pydantic model for response
    invoice = invoice_model_to_pydantic(invoice_model)
    invoice.team_id = team_id
    invoice.team_name = team.name
    invoice.billing_email = current_user.email

    return invoice


@router.get("/team/{team_id}")
async def get_team_invoices(
    team_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> List[Invoice]:
    """Get all invoices for a team"""

    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied to team invoices")

    # US#185: Query invoices from database
    billing_account = (
        db.query(BillingAccount)
        .filter(
            BillingAccount.account_type == "team",
            BillingAccount.account_id == team_id,
            BillingAccount.status != AccountStatus.DELETED.value,
        )
        .first()
    )

    if not billing_account:
        return []

    # Get invoices for this billing account
    invoice_models = (
        db.query(InvoiceModel)
        .filter(InvoiceModel.billing_account_id == billing_account.id)
        .order_by(InvoiceModel.created_at.desc())
        .limit(limit)
        .all()
    )

    # Convert to Pydantic models
    team_invoices = [invoice_model_to_pydantic(inv) for inv in invoice_models]

    # Set team info
    for inv in team_invoices:
        inv.team_id = team_id
        # Could query team name and billing email if needed

    return team_invoices


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Invoice:
    """Get specific invoice details"""

    # US#185: Query invoice from database
    try:
        invoice_uuid = UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid invoice ID format")

    invoice_model = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_uuid).first()
    if not invoice_model:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get team_id from billing account
    team_id = invoice_model.billing_account.account_id if invoice_model.billing_account else None
    if not team_id:
        raise HTTPException(status_code=404, detail="Invoice billing account not found")

    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied to this invoice")

    # Convert to Pydantic model
    invoice = invoice_model_to_pydantic(invoice_model)
    invoice.team_id = team_id

    return invoice


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Response:
    """Download invoice as PDF"""

    # US#185: Query invoice from database
    try:
        invoice_uuid = UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid invoice ID format")

    invoice_model = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_uuid).first()
    if not invoice_model:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get team_id from billing account
    team_id = invoice_model.billing_account.account_id if invoice_model.billing_account else None
    if not team_id:
        raise HTTPException(status_code=404, detail="Invoice billing account not found")

    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied to this invoice")

    # Convert to Pydantic model
    invoice = invoice_model_to_pydantic(invoice_model)
    invoice.team_id = team_id

    # Get tax settings from database (US#185)
    tax_config = db.query(TaxConfiguration).filter(TaxConfiguration.team_id == invoice.team_id).first()
    tax_settings = None
    if tax_config:
        # Convert TaxConfiguration to TaxSettings Pydantic model for compatibility
        tax_rate = 0.0
        if tax_config.settings and isinstance(tax_config.settings, dict):
            tax_rate = tax_config.settings.get("tax_rate", 0.0)
        tax_settings = TaxSettings(
            tax_rate=tax_rate,
            tax_name=tax_config.settings.get("tax_name", "Tax") if tax_config.settings else "Tax",
            tax_id=tax_config.settings.get("tax_id") if tax_config.settings else None,
            is_tax_inclusive=tax_config.tax_inclusive_pricing,
        )

    # Generate PDF
    pdf_content = create_pdf_invoice(invoice, tax_settings)

    # Return PDF response
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{invoice.invoice_number}.pdf"},
    )


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Send invoice to customer via email"""

    # US#185: Query invoice from database
    try:
        invoice_uuid = UUID(invoice_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid invoice ID format")

    invoice_model = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_uuid).first()
    if not invoice_model:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Get team_id from billing account
    team_id = invoice_model.billing_account.account_id if invoice_model.billing_account else None
    if not team_id:
        raise HTTPException(status_code=404, detail="Invoice billing account not found")

    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only team admins can send invoices")

    # US#185: Update invoice status in database
    invoice_model.status = InvoiceStatus.ISSUED.value
    invoice_model.issued_at = datetime.now(timezone.utc)
    db.commit()

    # Convert to Pydantic model for email
    invoice = invoice_model_to_pydantic(invoice_model)
    invoice.team_id = team_id

    # Send email (mock implementation)
    background_tasks.add_task(send_invoice_email, invoice.billing_email, invoice, invoice_id)

    return {
        "success": True,
        "message": "Invoice sent successfully",
        "sent_to": invoice.billing_email,
    }


def send_invoice_email(email: str, invoice: Invoice, invoice_id: str):
    """Send invoice email (mock implementation)"""
    # In production, integrate with email service
    print(f"Sending invoice {invoice.invoice_number} to {email}")
    print(f"Amount: ${invoice.total_amount:.2f}")
    print(f"Due date: {invoice.due_date.strftime('%B %d, %Y')}")


@router.post("/tax-settings/{team_id}")
async def update_tax_settings(
    team_id: UUID,
    tax_settings: TaxSettings,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Update tax settings for team"""

    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only team admins can update tax settings")

    # Store tax settings in database (US#185)
    tax_config = db.query(TaxConfiguration).filter(TaxConfiguration.team_id == team_id).first()

    if tax_config:
        # Update existing configuration
        tax_config.tax_inclusive_pricing = tax_settings.is_tax_inclusive
        if not tax_config.settings:
            tax_config.settings = {}
        tax_config.settings.update(
            {
                "tax_rate": tax_settings.tax_rate,
                "tax_name": tax_settings.tax_name,
                "tax_id": tax_settings.tax_id,
            }
        )
        tax_config.updated_at = datetime.now(timezone.utc)
    else:
        # Create new configuration
        tax_config = TaxConfiguration(
            team_id=team_id,
            tax_inclusive_pricing=tax_settings.is_tax_inclusive,
            settings={
                "tax_rate": tax_settings.tax_rate,
                "tax_name": tax_settings.tax_name,
                "tax_id": tax_settings.tax_id,
            },
        )
        db.add(tax_config)

    db.commit()

    return {"success": True, "message": "Tax settings updated successfully"}


@router.get("/tax-settings/{team_id}")
async def get_tax_settings(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Optional[TaxSettings]:
    """Get tax settings for team"""

    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership:
        raise HTTPException(status_code=403, detail="Access denied to team tax settings")

    # Get tax settings from database (US#185)
    tax_config = db.query(TaxConfiguration).filter(TaxConfiguration.team_id == team_id).first()

    if tax_config:
        # Convert TaxConfiguration to TaxSettings Pydantic model
        tax_rate = 0.0
        tax_name = "Tax"
        tax_id = None
        if tax_config.settings and isinstance(tax_config.settings, dict):
            tax_rate = tax_config.settings.get("tax_rate", 0.0)
            tax_name = tax_config.settings.get("tax_name", "Tax")
            tax_id = tax_config.settings.get("tax_id")

        return TaxSettings(
            tax_rate=tax_rate,
            tax_name=tax_name,
            tax_id=tax_id,
            is_tax_inclusive=tax_config.tax_inclusive_pricing,
        )

    return None


@router.post("/billing-cycle/{team_id}")
async def setup_billing_cycle(
    team_id: UUID,
    cycle_config: BillingCycle,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Set up automated billing cycle for team"""

    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(status_code=403, detail="Only team admins can setup billing cycles")

    # US#185: Get or create billing account
    billing_account = get_or_create_billing_account(db, team_id)

    # US#185: Create billing period based on cycle config
    # Calculate period start/end from cycle config
    period_start = cycle_config.next_billing_date
    if cycle_config.cycle_type == "monthly":
        period_end = period_start + timedelta(days=30)
    elif cycle_config.cycle_type == "quarterly":
        period_end = period_start + timedelta(days=90)
    elif cycle_config.cycle_type == "yearly":
        period_end = period_start + timedelta(days=365)
    else:
        period_end = period_start + timedelta(days=30)  # Default monthly

    billing_period = get_or_create_billing_period(db, billing_account.id, period_start, period_end)

    return {
        "success": True,
        "message": "Billing cycle configured successfully",
        "next_billing_date": cycle_config.next_billing_date.isoformat(),
        "billing_period_id": str(billing_period.id),
    }


@router.post("/process-billing-cycles")
async def process_billing_cycles(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Process all due billing cycles (admin/cron endpoint)"""

    # US#185: Query active billing periods from database
    active_periods = (
        db.query(BillingPeriod)
        .join(BillingAccount)
        .filter(
            BillingPeriod.status == BillingPeriodStatus.ACTIVE.value,
            BillingPeriod.period_end <= datetime.now(timezone.utc),
            BillingAccount.status != AccountStatus.DELETED.value,
        )
        .all()
    )

    processed_count = 0
    for period in active_periods:
        team_id = period.billing_account.account_id if period.billing_account else None
        if team_id:
            # Generate and send invoice
            background_tasks.add_task(process_team_billing_cycle, team_id, period.id, db)
            processed_count += 1

    return {
        "success": True,
        "processed_cycles": processed_count,
        "message": f"Processing {processed_count} billing cycles",
    }


async def process_team_billing_cycle(team_id: UUID, period_id: UUID, db: Session):
    """Process billing cycle for a specific team"""
    # In production, this would:
    # 1. Generate invoice for the period
    # 2. Attempt payment via Stripe
    # 3. Send invoice email
    # 4. Update next billing date
    # 5. Handle payment failures

    print(f"Processing billing cycle for team {team_id}, period {period_id}")

    # US#185: Get billing period
    period = db.query(BillingPeriod).filter(BillingPeriod.id == period_id).first()
    if not period:
        print(f"Billing period {period_id} not found")
        return

    # Close current period and create next period
    period.status = BillingPeriodStatus.CLOSED.value
    period_duration = period.period_end - period.period_start
    next_period = BillingPeriod(
        billing_account_id=period.billing_account_id,
        period_start=period.period_end,
        period_end=period.period_end + period_duration,
        status=BillingPeriodStatus.ACTIVE.value,
    )
    db.add(next_period)
    db.commit()


@router.get("/payment-failures")
async def get_payment_failures(
    team_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    unresolved_only: bool = False,
) -> List[PaymentFailure]:
    """Get payment failures (admin endpoint)"""

    # US#185: Query payment failures from database
    query = db.query(PaymentFailureModel)

    if unresolved_only:
        query = query.filter(PaymentFailureModel.is_resolved == False)

    if team_id:
        # Filter by team via billing account
        query = query.join(BillingAccount).filter(BillingAccount.account_id == team_id)

    failure_models = query.order_by(PaymentFailureModel.failure_date.desc()).all()

    # Convert to Pydantic models
    failures = []
    for failure_model in failure_models:
        team_id_from_account = failure_model.billing_account.account_id if failure_model.billing_account else None
        if team_id_from_account:
            failures.append(
                PaymentFailure(
                    id=str(failure_model.id),
                    team_id=team_id_from_account,
                    invoice_id=str(failure_model.invoice_id),
                    failure_date=failure_model.failure_date,
                    failure_reason=failure_model.failure_reason,
                    retry_count=failure_model.retry_count,
                    next_retry_date=failure_model.next_retry_date,
                    is_resolved=failure_model.is_resolved,
                )
            )

    return failures


@router.post("/retry-payment/{failure_id}")
async def retry_failed_payment(
    failure_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """Retry failed payment"""

    # US#185: Query payment failure from database
    try:
        failure_uuid = UUID(failure_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Invalid payment failure ID format")

    failure_model = db.query(PaymentFailureModel).filter(PaymentFailureModel.id == failure_uuid).first()
    if not failure_model:
        raise HTTPException(status_code=404, detail="Payment failure not found")

    # Update retry count and schedule retry
    failure_model.retry_count += 1
    failure_model.next_retry_date = datetime.now(timezone.utc) + timedelta(days=3)
    failure_model.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Get team_id for background task
    team_id = failure_model.billing_account.account_id if failure_model.billing_account else None

    # Process retry
    if team_id:
        background_tasks.add_task(process_payment_retry, str(failure_model.invoice_id), team_id)

    return {
        "success": True,
        "message": "Payment retry initiated",
        "retry_count": failure_model.retry_count,
        "next_retry_date": failure_model.next_retry_date.isoformat() if failure_model.next_retry_date else None,
    }


async def process_payment_retry(invoice_id: str, team_id: UUID):
    """Process payment retry for failed payment"""
    # In production, this would:
    # 1. Attempt payment via Stripe
    # 2. Update invoice status
    # 3. Send success/failure notifications
    # 4. Schedule next retry if needed

    print(f"Retrying payment for invoice {invoice_id}, team {team_id}")
