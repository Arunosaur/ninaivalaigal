#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Invoice Generation API Endpoints
# Developer D - January 2025
#
# BILL-005: FastAPI endpoints for invoice generation

"""
FastAPI endpoints for invoice generation and management.

Provides REST API for:
- Monthly invoice generation
- Manual invoice regeneration
- Invoice status queries
- Invoice history
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.billing.invoice_generation import InvoiceGenerationService
from server.billing.models import Invoice, InvoiceStatus
from server.database import get_db

router = APIRouter(prefix="/api/billing/invoices", tags=["invoices"])


def get_invoice_service(db: Session = Depends(get_db)) -> InvoiceGenerationService:
    """Dependency for invoice generation service"""
    return InvoiceGenerationService(db)


@router.post("/generate/monthly")
async def generate_monthly_invoices(
    billing_period_id: Optional[UUID] = None,
    force_regenerate: bool = False,
    invoice_service: InvoiceGenerationService = Depends(get_invoice_service),
) -> Dict[str, Any]:
    """
    Generate monthly invoices for all active billing accounts.

    This endpoint should be called on the 1st of each month (via cron job).

    Args:
        billing_period_id: Specific billing period (optional, uses last completed period if None)
        force_regenerate: Force regeneration even if invoice exists

    Returns:
        Generation results summary
    """
    try:
        results = invoice_service.generate_monthly_invoices(
            billing_period_id=billing_period_id, force_regenerate=force_regenerate
        )

        return {
            "success": True,
            "processed": results["processed"],
            "created": results["created"],
            "skipped": results["skipped"],
            "errors": results["errors"],
            "errors_detail": results["errors_detail"],
            "invoices": results["invoices"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating invoices: {str(e)}"
        )


@router.post("/generate/{billing_account_id}")
async def generate_invoice_for_account(
    billing_account_id: UUID,
    billing_period_id: UUID,
    regenerate: bool = False,
    invoice_service: InvoiceGenerationService = Depends(get_invoice_service),
) -> Dict[str, Any]:
    """
    Generate invoice for a specific billing account.

    Args:
        billing_account_id: Billing account ID
        billing_period_id: Billing period ID
        regenerate: Regenerate existing invoice

    Returns:
        Invoice details
    """
    try:
        invoice = invoice_service.generate_invoice_for_account(
            billing_account_id=billing_account_id, billing_period_id=billing_period_id, regenerate=regenerate
        )

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No invoice generated (no overages or invoice already exists)",
            )

        return {
            "invoice_id": str(invoice.id),
            "invoice_number": invoice.invoice_number,
            "billing_account_id": str(invoice.billing_account_id),
            "billing_period_id": str(invoice.billing_period_id),
            "total_amount": float(invoice.total_amount),
            "currency": invoice.currency,
            "status": invoice.status,
            "due_at": invoice.due_at.isoformat() if invoice.due_at else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error generating invoice: {str(e)}"
        )


@router.post("/{invoice_id}/create-stripe")
async def create_stripe_invoice(
    invoice_id: UUID,
    invoice_service: InvoiceGenerationService = Depends(get_invoice_service),
) -> Dict[str, Any]:
    """
    Create Stripe invoice from local invoice.

    Args:
        invoice_id: Local invoice ID

    Returns:
        Stripe invoice details
    """
    try:
        stripe_invoice_id = invoice_service.create_stripe_invoice(invoice_id)

        if not stripe_invoice_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create Stripe invoice (no Stripe customer or Stripe unavailable)",
            )

        return {
            "invoice_id": str(invoice_id),
            "stripe_invoice_id": stripe_invoice_id,
            "status": "created",
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error creating Stripe invoice: {str(e)}"
        )


@router.get("/{billing_account_id}")
async def get_invoices_for_account(
    billing_account_id: UUID,
    status_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get invoices for a billing account.

    Args:
        billing_account_id: Billing account ID
        status_filter: Filter by status (draft, issued, paid, void)
        limit: Maximum number of invoices to return

    Returns:
        List of invoices
    """
    query = db.query(Invoice).filter(Invoice.billing_account_id == billing_account_id)

    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    invoices = query.order_by(Invoice.created_at.desc()).limit(limit).all()

    return {
        "billing_account_id": str(billing_account_id),
        "count": len(invoices),
        "invoices": [
            {
                "invoice_id": str(inv.id),
                "invoice_number": inv.invoice_number,
                "billing_period_id": str(inv.billing_period_id),
                "total_amount": float(inv.total_amount),
                "currency": inv.currency,
                "status": inv.status,
                "issued_at": inv.issued_at.isoformat() if inv.issued_at else None,
                "due_at": inv.due_at.isoformat() if inv.due_at else None,
                "paid_at": inv.paid_at.isoformat() if inv.paid_at else None,
                "created_at": inv.created_at.isoformat(),
            }
            for inv in invoices
        ],
    }


@router.get("/{invoice_id}/line-items")
async def get_invoice_line_items(
    invoice_id: UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get line items for an invoice.

    Args:
        invoice_id: Invoice ID

    Returns:
        Invoice with line items
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()

    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice not found: {invoice_id}")

    return {
        "invoice_id": str(invoice.id),
        "invoice_number": invoice.invoice_number,
        "total_amount": float(invoice.total_amount),
        "currency": invoice.currency,
        "status": invoice.status,
        "line_items": [
            {
                "resource_type": item.resource_type,
                "description": item.description,
                "quantity": float(item.quantity),
                "unit_price": float(item.unit_price),
                "amount": float(item.amount),
                "is_overage": item.is_overage,
            }
            for item in invoice.line_items
        ],
    }


@router.post("/reset-quotas")
async def reset_quotas_after_billing(
    billing_period_id: UUID,
    invoice_service: InvoiceGenerationService = Depends(get_invoice_service),
) -> Dict[str, Any]:
    """
    Reset quotas after successful billing (for next period).

    This should be called after invoices are paid.

    Args:
        billing_period_id: Completed billing period

    Returns:
        Reset results
    """
    try:
        results = invoice_service.reset_quotas_after_billing(billing_period_id)

        return {
            "success": True,
            "reset": results["reset"],
            "errors": results["errors"],
            "errors_detail": results["errors_detail"],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error resetting quotas: {str(e)}"
        )
