#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# US-228: Customer Invoice Portal Implementation
# Part of SPEC-028: Invoice Management System
#
"""
Customer Invoice Portal API

Provides secure, token-based access to invoices for customers.
Features:
- Time-limited access tokens (24-48h expiration)
- Email-based authentication (no password required)
- Invoice viewing, filtering, and PDF downloads
- Correction request submission
- Mobile-responsive UI support
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from server.billing.models import BillingAccount
from server.billing.models import Invoice as InvoiceModel
from server.billing.tax_config_models import TaxConfiguration
from server.database.models import Team
from server.database.operations import get_db

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/invoicing/portal", tags=["invoice-portal"])


# Pydantic Models
class PortalAccessRequest(BaseModel):
    """Request portal access token"""

    team_id: UUID
    customer_email: EmailStr


class PortalTokenResponse(BaseModel):
    """Portal token response"""

    access_token: str
    expires_at: datetime
    portal_url: str
    message: str


class PortalInvoiceSummary(BaseModel):
    """Invoice summary for portal listing"""

    id: str
    invoice_number: str
    issue_date: datetime
    due_date: Optional[datetime]
    total_amount: float
    currency: str
    status: str
    paid_date: Optional[datetime]


class PortalInvoiceDetail(BaseModel):
    """Full invoice details for portal viewing"""

    id: str
    invoice_number: str
    revision: int
    issue_date: datetime
    due_date: Optional[datetime]
    period_start: Optional[datetime]
    period_end: Optional[datetime]
    subtotal: float
    tax_amount: float
    total_amount: float
    currency: str
    status: str
    line_items: List[Dict[str, Any]]
    paid_date: Optional[datetime]
    payment_method: Optional[str]


class CorrectionRequest(BaseModel):
    """Request invoice correction"""

    invoice_id: UUID
    correction_type: str  # "adjustment", "credit_memo", "void"
    reason: str
    details: Optional[Dict[str, Any]] = None


class EmailUpdateRequest(BaseModel):
    """Update billing email"""

    new_email: EmailStr


# Helper Functions
def generate_portal_token() -> str:
    """Generate secure random token for portal access"""
    return secrets.token_urlsafe(32)


def validate_portal_token(db: Session, token: str) -> Optional[Any]:
    """
    Validate portal access token and return token record.

    Returns:
        InvoicePortalToken if valid, None otherwise
    """
    from server.billing.models import InvoicePortalToken

    token_record = (
        db.query(InvoicePortalToken)
        .filter(
            InvoicePortalToken.access_token == token,
            InvoicePortalToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )

    if not token_record:
        return None

    # Update access tracking
    token_record.accessed_count += 1
    token_record.last_accessed_at = datetime.now(timezone.utc)
    db.commit()

    return token_record


def send_portal_access_email(email: str, token: str, portal_url: str):
    """
    Send portal access email with token link.

    US-228: Email delivery for portal access
    """
    # In production, integrate with email service (SendGrid/SES)
    portal_link = f"{portal_url}?token={token}"

    # Mock implementation - in production use email service
    print(f"Sending portal access email to {email}")
    print(f"Portal link: {portal_link}")
    logger.info("Portal access email sent", email=email, token_preview=token[:8])


# API Endpoints
@router.post("/request-access", response_model=PortalTokenResponse)
async def request_portal_access(
    request: PortalAccessRequest,
    db: Session = Depends(get_db),
) -> PortalTokenResponse:
    """
    Request portal access token via email.

    US-228: Generate time-limited access token and send via email
    """
    from server.billing.models import InvoicePortalToken

    # Verify team exists
    team = db.query(Team).filter(Team.id == request.team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Check if valid token already exists for this email/team
    existing_token = (
        db.query(InvoicePortalToken)
        .filter(
            InvoicePortalToken.team_id == request.team_id,
            InvoicePortalToken.customer_email == request.customer_email,
            InvoicePortalToken.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )

    if existing_token:
        # Return existing token
        portal_url = os.getenv("PORTAL_BASE_URL", "https://app.ninaivalaigal.com/invoices/portal")
        return PortalTokenResponse(
            access_token=existing_token.access_token,
            expires_at=existing_token.expires_at,
            portal_url=f"{portal_url}?token={existing_token.access_token}",
            message="Access token already exists. Check your email for the portal link.",
        )

    # Generate new token
    access_token = generate_portal_token()
    expires_at = datetime.now(timezone.utc) + timedelta(hours=48)  # 48-hour expiration

    # Create token record
    portal_token = InvoicePortalToken(
        team_id=request.team_id,
        customer_email=request.customer_email,
        access_token=access_token,
        expires_at=expires_at,
    )
    db.add(portal_token)
    db.commit()

    # Send email with portal link
    portal_url = os.getenv("PORTAL_BASE_URL", "https://app.ninaivalaigal.com/invoices/portal")
    send_portal_access_email(request.customer_email, access_token, portal_url)

    logger.info(
        "Portal access token generated",
        team_id=str(request.team_id),
        email=request.customer_email,
        expires_at=expires_at.isoformat(),
    )

    return PortalTokenResponse(
        access_token=access_token,
        expires_at=expires_at,
        portal_url=f"{portal_url}?token={access_token}",
        message="Portal access token generated. Check your email for the access link.",
    )


@router.get("/invoices", response_model=List[PortalInvoiceSummary])
async def list_portal_invoices(
    token: str = Query(..., description="Portal access token"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Filter by start date"),
    end_date: Optional[datetime] = Query(None, description="Filter by end date"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of invoices"),
    db: Session = Depends(get_db),
) -> List[PortalInvoiceSummary]:
    """
    List invoices accessible via portal token.

    US-228: Token-based invoice listing with filters
    """
    # Validate token
    token_record = validate_portal_token(db, token)
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid or expired portal access token")

    # Get billing account for team
    billing_account = (
        db.query(BillingAccount)
        .filter(
            BillingAccount.account_type == "team",
            BillingAccount.account_id == token_record.team_id,
        )
        .first()
    )

    if not billing_account:
        return []

    # Query invoices
    query = db.query(InvoiceModel).filter(InvoiceModel.billing_account_id == billing_account.id)

    # Apply filters
    if status:
        query = query.filter(InvoiceModel.status == status)
    if start_date:
        query = query.filter(InvoiceModel.issued_at >= start_date)
    if end_date:
        query = query.filter(InvoiceModel.issued_at <= end_date)

    # Get latest revision for each invoice number
    invoices = query.order_by(InvoiceModel.invoice_number, InvoiceModel.revision.desc()).all()

    # Group by invoice_number and take latest revision
    seen_numbers = set()
    invoice_summaries = []
    for invoice in invoices:
        if invoice.invoice_number not in seen_numbers:
            seen_numbers.add(invoice.invoice_number)
            invoice_summaries.append(
                PortalInvoiceSummary(
                    id=str(invoice.id),
                    invoice_number=invoice.invoice_number,
                    issue_date=invoice.issued_at or invoice.created_at,
                    due_date=invoice.due_at,
                    total_amount=float(invoice.total_amount),
                    currency=invoice.currency,
                    status=invoice.status,
                    paid_date=invoice.paid_at,
                )
            )
            if len(invoice_summaries) >= limit:
                break

    logger.info(
        "Portal invoices listed",
        team_id=str(token_record.team_id),
        email=token_record.customer_email,
        count=len(invoice_summaries),
    )

    return invoice_summaries


@router.get("/invoice/{invoice_id}", response_model=PortalInvoiceDetail)
async def get_portal_invoice(
    invoice_id: UUID,
    token: str = Query(..., description="Portal access token"),
    db: Session = Depends(get_db),
) -> PortalInvoiceDetail:
    """
    Get specific invoice details via portal token.

    US-228: Token-based invoice detail viewing
    """
    # Validate token
    token_record = validate_portal_token(db, token)
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid or expired portal access token")

    # Get invoice
    invoice = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Verify invoice belongs to token's team
    billing_account = (
        db.query(BillingAccount)
        .filter(
            BillingAccount.account_type == "team",
            BillingAccount.account_id == token_record.team_id,
        )
        .first()
    )

    if not billing_account or invoice.billing_account_id != billing_account.id:
        raise HTTPException(status_code=403, detail="Access denied to this invoice")

    # Get line items
    line_items_data = []
    for line_item in invoice.line_items:
        line_items_data.append(
            {
                "id": str(line_item.id),
                "description": line_item.description,
                "quantity": float(line_item.quantity),
                "unit_price": float(line_item.unit_price),
                "amount": float(line_item.amount),
                "resource_type": line_item.resource_type,
            }
        )

    logger.info(
        "Portal invoice viewed",
        invoice_id=str(invoice_id),
        team_id=str(token_record.team_id),
        email=token_record.customer_email,
    )

    return PortalInvoiceDetail(
        id=str(invoice.id),
        invoice_number=invoice.invoice_number,
        revision=invoice.revision,
        issue_date=invoice.issued_at or invoice.created_at,
        due_date=invoice.due_at,
        period_start=invoice.billing_period.period_start if invoice.billing_period else None,
        period_end=invoice.billing_period.period_end if invoice.billing_period else None,
        subtotal=float(invoice.subtotal),
        tax_amount=float(invoice.tax_amount),
        total_amount=float(invoice.total_amount),
        currency=invoice.currency,
        status=invoice.status,
        line_items=line_items_data,
        paid_date=invoice.paid_at,
        payment_method=None,  # Would need to query PaymentConfig if needed
    )


@router.get("/invoice/{invoice_id}/pdf")
async def download_portal_invoice_pdf(
    invoice_id: UUID,
    token: str = Query(..., description="Portal access token"),
    db: Session = Depends(get_db),
) -> Response:
    """
    Download invoice PDF via portal token.

    US-228: Token-based PDF download
    """
    # Validate token
    token_record = validate_portal_token(db, token)
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid or expired portal access token")

    # Get invoice
    invoice = db.query(InvoiceModel).filter(InvoiceModel.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Verify invoice belongs to token's team
    billing_account = (
        db.query(BillingAccount)
        .filter(
            BillingAccount.account_type == "team",
            BillingAccount.account_id == token_record.team_id,
        )
        .first()
    )

    if not billing_account or invoice.billing_account_id != billing_account.id:
        raise HTTPException(status_code=403, detail="Access denied to this invoice")

    # Get tax settings
    tax_config = db.query(TaxConfiguration).filter(TaxConfiguration.team_id == token_record.team_id).first()

    # Convert to Pydantic model for PDF generation
    from server.invoice_management_api import TaxSettings, invoice_model_to_pydantic

    invoice_pydantic = invoice_model_to_pydantic(invoice, db=db)
    invoice_pydantic.team_id = token_record.team_id

    tax_settings = None
    if tax_config:
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
    from server.invoice_management_api import create_pdf_invoice

    pdf_content = create_pdf_invoice(invoice_pydantic, tax_settings)

    logger.info(
        "Portal invoice PDF downloaded",
        invoice_id=str(invoice_id),
        team_id=str(token_record.team_id),
        email=token_record.customer_email,
    )

    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=invoice-{invoice.invoice_number}.pdf"},
    )


@router.post("/request-correction")
async def request_invoice_correction(
    request: CorrectionRequest,
    token: str = Query(..., description="Portal access token"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Request invoice correction via portal.

    US-228: Customer-initiated correction requests
    """
    # Validate token
    token_record = validate_portal_token(db, token)
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid or expired portal access token")

    # Get invoice
    invoice = db.query(InvoiceModel).filter(InvoiceModel.id == request.invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Verify invoice belongs to token's team
    billing_account = (
        db.query(BillingAccount)
        .filter(
            BillingAccount.account_type == "team",
            BillingAccount.account_id == token_record.team_id,
        )
        .first()
    )

    if not billing_account or invoice.billing_account_id != billing_account.id:
        raise HTTPException(status_code=403, detail="Access denied to this invoice")

    # Create correction request (would integrate with invoice correction system)
    # For now, log the request
    logger.info(
        "Portal correction request submitted",
        invoice_id=str(request.invoice_id),
        correction_type=request.correction_type,
        reason=request.reason,
        team_id=str(token_record.team_id),
        email=token_record.customer_email,
    )

    # In production, this would create a correction record via invoice correction workflows
    # For now, return success message
    return {
        "success": True,
        "message": (
            "Correction request submitted successfully. " "Our team will review and respond within 2-3 business days."
        ),
        "correction_type": request.correction_type,
        "invoice_id": str(request.invoice_id),
    }


@router.patch("/update-email")
async def update_billing_email(
    request: EmailUpdateRequest,
    token: str = Query(..., description="Portal access token"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Update billing email via portal.

    US-228: Customer email update
    """
    # Validate token
    token_record = validate_portal_token(db, token)
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid or expired portal access token")

    # Update token email (and potentially team billing email)
    token_record.customer_email = request.new_email
    db.commit()

    logger.info(
        "Portal billing email updated",
        team_id=str(token_record.team_id),
        old_email=token_record.customer_email,
        new_email=request.new_email,
    )

    return {
        "success": True,
        "message": "Billing email updated successfully",
        "new_email": request.new_email,
    }
