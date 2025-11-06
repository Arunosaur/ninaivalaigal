#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Payment Transfer API Endpoints
# Developer D - January 2025
#
# BILL-006: FastAPI endpoints for payment transfer

"""
FastAPI endpoints for payment transfer operations.

Provides REST API for:
- Initiating payment transfers
- Assigning new payers
- Checking grace period status
- Managing payment transfers
"""

from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.billing.models import PaymentConfig, PaymentTransfer
from server.billing.payment_transfer import PaymentTransferService
from server.database import get_db

router = APIRouter(prefix="/api/billing/payment-transfer", tags=["payment-transfer"])


def get_payment_transfer_service(db: Session = Depends(get_db)) -> PaymentTransferService:
    """Dependency for payment transfer service"""
    return PaymentTransferService(db)


@router.post("/initiate")
async def initiate_payment_transfer(
    billing_account_id: UUID,
    from_user_id: UUID,
    reason: str = "left_team",
    transfer_service: PaymentTransferService = Depends(get_payment_transfer_service),
) -> Dict[str, Any]:
    """
    Initiate payment transfer workflow.

    Args:
        billing_account_id: Billing account ID
        from_user_id: User ID that is leaving
        reason: Transfer reason (left_team, reassigned, voluntary)

    Returns:
        Transfer details
    """
    try:
        transfer = transfer_service.initiate_payment_transfer(
            billing_account_id=billing_account_id, from_user_id=from_user_id, reason=reason
        )

        return {
            "transfer_id": str(transfer.id),
            "billing_account_id": str(billing_account_id),
            "from_user_id": str(transfer.from_user_id),
            "status": transfer.status,
            "reason": transfer.reason,
            "initiated_at": transfer.initiated_at.isoformat(),
            "grace_period_days": 30,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/assign-payer")
async def assign_new_payer(
    billing_account_id: UUID,
    new_payer_id: UUID,
    transfer_id: Optional[UUID] = None,
    transfer_service: PaymentTransferService = Depends(get_payment_transfer_service),
) -> Dict[str, Any]:
    """
    Assign new payer to complete transfer.

    Args:
        billing_account_id: Billing account ID
        new_payer_id: New payer user ID
        transfer_id: Transfer ID (optional)

    Returns:
        Completed transfer details
    """
    try:
        transfer = transfer_service.assign_new_payer(
            billing_account_id=billing_account_id, new_payer_id=new_payer_id, transfer_id=transfer_id
        )

        return {
            "transfer_id": str(transfer.id),
            "billing_account_id": str(billing_account_id),
            "from_user_id": str(transfer.from_user_id),
            "to_user_id": str(transfer.to_user_id),
            "status": transfer.status,
            "completed_at": transfer.completed_at.isoformat() if transfer.completed_at else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/status/{billing_account_id}")
async def get_grace_period_status(
    billing_account_id: UUID,
    transfer_service: PaymentTransferService = Depends(get_payment_transfer_service),
) -> Dict[str, Any]:
    """
    Check grace period status.

    Args:
        billing_account_id: Billing account ID

    Returns:
        Grace period status information
    """
    status_info = transfer_service.check_grace_period_status(billing_account_id)

    return {
        "billing_account_id": str(billing_account_id),
        **status_info,
    }


@router.get("/transfers/{billing_account_id}")
async def get_transfer_history(
    billing_account_id: UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get payment transfer history for a billing account.

    Args:
        billing_account_id: Billing account ID

    Returns:
        Transfer history
    """
    # Get payment config
    payment_config = db.query(PaymentConfig).filter(PaymentConfig.billing_account_id == billing_account_id).first()

    if not payment_config:
        return {
            "billing_account_id": str(billing_account_id),
            "transfers": [],
            "count": 0,
        }

    # Get transfers
    transfers = (
        db.query(PaymentTransfer)
        .filter(PaymentTransfer.payment_config_id == payment_config.id)
        .order_by(PaymentTransfer.initiated_at.desc())
        .all()
    )

    return {
        "billing_account_id": str(billing_account_id),
        "count": len(transfers),
        "transfers": [
            {
                "transfer_id": str(t.id),
                "from_user_id": str(t.from_user_id),
                "to_user_id": str(t.to_user_id) if t.to_user_id else None,
                "reason": t.reason,
                "status": t.status,
                "initiated_at": t.initiated_at.isoformat(),
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in transfers
        ],
    }


@router.post("/process-grace-periods")
async def process_all_grace_periods(
    transfer_service: PaymentTransferService = Depends(get_payment_transfer_service),
) -> Dict[str, Any]:
    """
    Process all active grace periods (admin endpoint, should be called periodically).

    Returns:
        Processing results
    """
    results = transfer_service.process_all_grace_periods()

    return {
        "success": True,
        "processed": results["processed"],
        "soft_blocks_applied": results["soft_blocks_applied"],
        "hard_blocks_applied": results["hard_blocks_applied"],
        "expired": results["expired"],
        "errors": results["errors"],
        "errors_detail": results["errors_detail"],
    }


@router.get("/backup-payers/{billing_account_id}")
async def get_backup_payers(
    billing_account_id: UUID,
    transfer_service: PaymentTransferService = Depends(get_payment_transfer_service),
) -> Dict[str, Any]:
    """
    Get list of backup payers for a billing account.

    Args:
        billing_account_id: Billing account ID

    Returns:
        Backup payer list
    """
    backup_payers = transfer_service.get_backup_payers(billing_account_id)

    return {
        "billing_account_id": str(billing_account_id),
        "backup_payers": [str(payer_id) for payer_id in backup_payers],
        "count": len(backup_payers),
    }


@router.post("/notify-backup-payers")
async def notify_backup_payers(
    billing_account_id: UUID,
    days_remaining: int,
    transfer_service: PaymentTransferService = Depends(get_payment_transfer_service),
) -> Dict[str, Any]:
    """
    Send notifications to backup payers.

    Args:
        billing_account_id: Billing account ID
        days_remaining: Days remaining in grace period

    Returns:
        Notification results
    """
    results = transfer_service.send_notification_to_backup_payers(
        billing_account_id=billing_account_id, days_remaining=days_remaining
    )

    return {
        "billing_account_id": str(billing_account_id),
        "notified": results["notified"],
        "backup_payers": results["backup_payers"],
    }
