"""
SPEC-027: Invoice and Plan Management API
Complete invoice generation, tax handling, and billing cycle management
"""

import os
import stripe
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from io import BytesIO
import base64

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

# PDF generation imports
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from auth import get_current_user, get_db
from database import Team, User
from models.standalone_teams import StandaloneTeamManager, TeamMembership

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_...")

# Initialize router
router = APIRouter(prefix="/invoicing", tags=["invoice-management"])


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


# Mock databases (in production, use proper database tables)
invoices_db = {}
billing_cycles_db = {}
payment_failures_db = {}
tax_settings_db = {}


def get_team_manager() -> StandaloneTeamManager:
    """Dependency to get team manager"""
    return StandaloneTeamManager()


def calculate_tax(subtotal: float, tax_settings: TaxSettings) -> float:
    """Calculate tax amount based on settings"""
    if tax_settings.is_tax_inclusive:
        # Tax is already included in the subtotal
        return subtotal * (tax_settings.tax_rate / (100 + tax_settings.tax_rate))
    else:
        # Tax is additional to subtotal
        return subtotal * (tax_settings.tax_rate / 100)


def generate_invoice_number() -> str:
    """Generate unique invoice number"""
    timestamp = datetime.utcnow().strftime("%Y%m")
    random_suffix = str(uuid4())[:8].upper()
    return f"INV-{timestamp}-{random_suffix}"


def create_pdf_invoice(invoice: Invoice, tax_settings: Optional[TaxSettings] = None) -> bytes:
    """Generate PDF invoice using ReportLab"""
    if not REPORTLAB_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="PDF generation not available. Install reportlab package."
        )
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch)
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#2563eb')
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        textColor=colors.HexColor('#1f2937')
    )
    
    # Build PDF content
    content = []
    
    # Header
    content.append(Paragraph("INVOICE", title_style))
    content.append(Spacer(1, 20))
    
    # Company and invoice info
    company_info = [
        ["<b>Ninaivalaigal</b>", f"<b>Invoice #:</b> {invoice.invoice_number}"],
        ["Memory Management Platform", f"<b>Issue Date:</b> {invoice.issue_date.strftime('%B %d, %Y')}"],
        ["support@ninaivalaigal.com", f"<b>Due Date:</b> {invoice.due_date.strftime('%B %d, %Y')}"],
        ["", f"<b>Period:</b> {invoice.period_start.strftime('%b %d')} - {invoice.period_end.strftime('%b %d, %Y')}"]
    ]
    
    company_table = Table(company_info, colWidths=[3*inch, 3*inch])
    company_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    content.append(company_table)
    content.append(Spacer(1, 30))
    
    # Bill to
    content.append(Paragraph("<b>Bill To:</b>", heading_style))
    bill_to_info = [
        [invoice.team_name],
        [invoice.billing_email],
        [f"Team ID: {str(invoice.team_id)[:8]}..."]
    ]
    
    bill_to_table = Table(bill_to_info, colWidths=[6*inch])
    bill_to_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    content.append(bill_to_table)
    content.append(Spacer(1, 20))
    
    # Line items
    content.append(Paragraph("<b>Services:</b>", heading_style))
    
    line_items_data = [
        ["Description", "Period", "Quantity", "Unit Price", "Total"]
    ]
    
    for item in invoice.line_items:
        period_str = f"{item.period_start.strftime('%m/%d')} - {item.period_end.strftime('%m/%d/%Y')}"
        line_items_data.append([
            item.description,
            period_str,
            str(item.quantity),
            f"${item.unit_price:.2f}",
            f"${item.total_price:.2f}"
        ])
    
    line_items_table = Table(line_items_data, colWidths=[2.5*inch, 1.5*inch, 0.8*inch, 1*inch, 1*inch])
    line_items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e5e7eb')),
    ]))
    content.append(line_items_table)
    content.append(Spacer(1, 20))
    
    # Totals
    totals_data = [
        ["", "", "", "Subtotal:", f"${invoice.subtotal:.2f}"]
    ]
    
    if invoice.tax_amount > 0:
        tax_label = tax_settings.tax_name if tax_settings else "Tax"
        totals_data.append(["", "", "", f"{tax_label}:", f"${invoice.tax_amount:.2f}"])
    
    totals_data.append(["", "", "", "<b>Total:</b>", f"<b>${invoice.total_amount:.2f}</b>"])
    
    totals_table = Table(totals_data, colWidths=[2.5*inch, 1.5*inch, 0.8*inch, 1*inch, 1*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEABOVE', (3, -1), (-1, -1), 2, colors.HexColor('#374151')),
    ]))
    content.append(totals_table)
    content.append(Spacer(1, 30))
    
    # Payment info
    if invoice.status == "paid" and invoice.paid_date:
        content.append(Paragraph(
            f"<b>Payment Status:</b> Paid on {invoice.paid_date.strftime('%B %d, %Y')}",
            styles['Normal']
        ))
    else:
        content.append(Paragraph(
            "<b>Payment Terms:</b> Payment is due within 30 days of invoice date.",
            styles['Normal']
        ))
    
    content.append(Spacer(1, 10))
    content.append(Paragraph(
        "Thank you for your business! For questions about this invoice, contact support@ninaivalaigal.com",
        styles['Normal']
    ))
    
    # Build PDF
    doc.build(content)
    buffer.seek(0)
    return buffer.getvalue()


@router.post("/generate")
async def generate_invoice(
    team_id: UUID,
    period_start: datetime,
    period_end: datetime,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Invoice:
    """Generate invoice for team's usage period"""
    
    # Get team and verify access
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only team admins can generate invoices"
        )
    
    # Calculate usage and charges
    member_count = db.query(TeamMembership).filter(
        TeamMembership.team_id == team_id,
        TeamMembership.status == "active"
    ).count()
    
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
        line_items.append(InvoiceLineItem(
            description=f"Ninaivalaigal {plan.replace('_', ' ').title()} Plan",
            quantity=1,
            unit_price=monthly_price,
            total_price=monthly_price,
            period_start=period_start,
            period_end=period_end
        ))
    
    # Add usage-based charges (mock data)
    storage_overage = max(0, member_count * 0.8 - 10)  # Estimate storage overage
    if storage_overage > 0:
        overage_charge = storage_overage * 2.0  # $2/GB overage
        line_items.append(InvoiceLineItem(
            description="Storage Overage",
            quantity=int(storage_overage),
            unit_price=2.0,
            total_price=overage_charge,
            period_start=period_start,
            period_end=period_end
        ))
    
    # Calculate totals
    subtotal = sum(item.total_price for item in line_items)
    
    # Get tax settings
    tax_settings = tax_settings_db.get(str(team_id))
    tax_amount = 0.0
    if tax_settings:
        tax_amount = calculate_tax(subtotal, tax_settings)
    
    total_amount = subtotal + tax_amount
    
    # Create invoice
    invoice_id = str(uuid4())
    invoice = Invoice(
        id=invoice_id,
        invoice_number=generate_invoice_number(),
        team_id=team_id,
        team_name=team.name,
        billing_email=current_user.email,  # In production, use team billing email
        issue_date=datetime.utcnow(),
        due_date=datetime.utcnow() + timedelta(days=30),
        period_start=period_start,
        period_end=period_end,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        currency="USD",
        status="draft",
        line_items=line_items,
        payment_method=None,
        paid_date=None,
        stripe_invoice_id=None
    )
    
    # Store invoice
    invoices_db[invoice_id] = invoice.dict()
    
    return invoice


@router.get("/team/{team_id}")
async def get_team_invoices(
    team_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> List[Invoice]:
    """Get all invoices for a team"""
    
    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Access denied to team invoices"
        )
    
    # Filter invoices for this team
    team_invoices = [
        Invoice(**invoice_data) 
        for invoice_data in invoices_db.values()
        if invoice_data["team_id"] == str(team_id)
    ]
    
    # Sort by issue date (newest first)
    team_invoices.sort(key=lambda x: x.issue_date, reverse=True)
    
    return team_invoices[:limit]


@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Invoice:
    """Get specific invoice details"""
    
    if invoice_id not in invoices_db:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice_data = invoices_db[invoice_id]
    invoice = Invoice(**invoice_data)
    
    # Verify access
    membership = team_manager.get_team_membership(invoice.team_id, current_user.id, db)
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this invoice"
        )
    
    return invoice


@router.get("/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Response:
    """Download invoice as PDF"""
    
    if invoice_id not in invoices_db:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice_data = invoices_db[invoice_id]
    invoice = Invoice(**invoice_data)
    
    # Verify access
    membership = team_manager.get_team_membership(invoice.team_id, current_user.id, db)
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Access denied to this invoice"
        )
    
    # Get tax settings
    tax_settings = tax_settings_db.get(str(invoice.team_id))
    if tax_settings:
        tax_settings = TaxSettings(**tax_settings)
    
    # Generate PDF
    pdf_content = create_pdf_invoice(invoice, tax_settings)
    
    # Return PDF response
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=invoice-{invoice.invoice_number}.pdf"
        }
    )


@router.post("/{invoice_id}/send")
async def send_invoice(
    invoice_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Send invoice to customer via email"""
    
    if invoice_id not in invoices_db:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    invoice_data = invoices_db[invoice_id]
    invoice = Invoice(**invoice_data)
    
    # Verify access
    membership = team_manager.get_team_membership(invoice.team_id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only team admins can send invoices"
        )
    
    # Update invoice status
    invoices_db[invoice_id]["status"] = "sent"
    
    # Send email (mock implementation)
    background_tasks.add_task(
        send_invoice_email,
        invoice.billing_email,
        invoice,
        invoice_id
    )
    
    return {
        "success": True,
        "message": "Invoice sent successfully",
        "sent_to": invoice.billing_email
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
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Update tax settings for team"""
    
    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only team admins can update tax settings"
        )
    
    # Store tax settings
    tax_settings_db[str(team_id)] = tax_settings.dict()
    
    return {
        "success": True,
        "message": "Tax settings updated successfully"
    }


@router.get("/tax-settings/{team_id}")
async def get_tax_settings(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Optional[TaxSettings]:
    """Get tax settings for team"""
    
    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership:
        raise HTTPException(
            status_code=403,
            detail="Access denied to team tax settings"
        )
    
    tax_settings_data = tax_settings_db.get(str(team_id))
    if tax_settings_data:
        return TaxSettings(**tax_settings_data)
    
    return None


@router.post("/billing-cycle/{team_id}")
async def setup_billing_cycle(
    team_id: UUID,
    cycle_config: BillingCycle,
    current_user: User = Depends(get_current_user),
    team_manager: StandaloneTeamManager = Depends(get_team_manager),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Setup automated billing cycle for team"""
    
    # Verify access
    membership = team_manager.get_team_membership(team_id, current_user.id, db)
    if not membership or membership.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Only team admins can setup billing cycles"
        )
    
    # Store billing cycle configuration
    billing_cycles_db[str(team_id)] = cycle_config.dict()
    
    return {
        "success": True,
        "message": "Billing cycle configured successfully",
        "next_billing_date": cycle_config.next_billing_date
    }


@router.post("/process-billing-cycles")
async def process_billing_cycles(
    background_tasks: BackgroundTasks
) -> Dict[str, Any]:
    """Process all due billing cycles (admin/cron endpoint)"""
    
    # In production, this would be called by a cron job
    processed_count = 0
    
    for team_id, cycle_data in billing_cycles_db.items():
        cycle = BillingCycle(**cycle_data)
        
        if (cycle.auto_billing_enabled and 
            cycle.next_billing_date <= datetime.utcnow()):
            
            # Generate and send invoice
            background_tasks.add_task(
                process_team_billing_cycle,
                UUID(team_id),
                cycle
            )
            processed_count += 1
    
    return {
        "success": True,
        "processed_cycles": processed_count,
        "message": f"Processing {processed_count} billing cycles"
    }


async def process_team_billing_cycle(team_id: UUID, cycle: BillingCycle):
    """Process billing cycle for a specific team"""
    # In production, this would:
    # 1. Generate invoice for the period
    # 2. Attempt payment via Stripe
    # 3. Send invoice email
    # 4. Update next billing date
    # 5. Handle payment failures
    
    print(f"Processing billing cycle for team {team_id}")
    
    # Update next billing date
    if cycle.cycle_type == "monthly":
        next_date = cycle.next_billing_date + timedelta(days=30)
    else:  # yearly
        next_date = cycle.next_billing_date + timedelta(days=365)
    
    billing_cycles_db[str(team_id)]["next_billing_date"] = next_date.isoformat()
    billing_cycles_db[str(team_id)]["last_invoice_date"] = datetime.utcnow().isoformat()


@router.get("/payment-failures")
async def get_payment_failures(
    team_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user)
) -> List[PaymentFailure]:
    """Get payment failures (admin endpoint)"""
    
    # In production, check admin permissions
    
    failures = []
    for failure_data in payment_failures_db.values():
        failure = PaymentFailure(**failure_data)
        
        if team_id is None or failure.team_id == team_id:
            failures.append(failure)
    
    return failures


@router.post("/retry-payment/{failure_id}")
async def retry_failed_payment(
    failure_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Retry failed payment"""
    
    if failure_id not in payment_failures_db:
        raise HTTPException(status_code=404, detail="Payment failure not found")
    
    failure_data = payment_failures_db[failure_id]
    failure = PaymentFailure(**failure_data)
    
    # Update retry count and schedule retry
    payment_failures_db[failure_id]["retry_count"] += 1
    payment_failures_db[failure_id]["next_retry_date"] = (
        datetime.utcnow() + timedelta(days=3)
    ).isoformat()
    
    # Process retry
    background_tasks.add_task(
        process_payment_retry,
        failure.invoice_id,
        failure.team_id
    )
    
    return {
        "success": True,
        "message": "Payment retry initiated",
        "retry_count": failure.retry_count + 1
    }


async def process_payment_retry(invoice_id: str, team_id: UUID):
    """Process payment retry for failed payment"""
    # In production, this would:
    # 1. Attempt payment via Stripe
    # 2. Update invoice status
    # 3. Send success/failure notifications
    # 4. Schedule next retry if needed
    
    print(f"Retrying payment for invoice {invoice_id}, team {team_id}")
