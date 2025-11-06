#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing Management API Endpoints
# Developer D - January 2025
#
# BILL-015: Admin and management API endpoints

"""
FastAPI endpoints for billing management operations.

Provides REST API for:
- Billing account management
- Usage metrics and trends
- Quota management and overrides
- Invoice management
- Payment method management
- Subscription management
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from server.billing.models import (
    AccountStatus,
    BillingAccount,
    BillingPeriod,
    Invoice,
    InvoiceStatus,
    PlanTier,
    QuotaBlock,
    ResourceType,
    UsageEvent,
    UsageQuota,
)
from server.billing.quota_enforcement import QuotaEnforcementService
from server.billing.usage_metering import UsageMeteringService
from server.database import get_db

router = APIRouter(prefix="/api/billing/admin", tags=["billing-admin"])


def get_quota_service(db: Session = Depends(get_db)) -> QuotaEnforcementService:
    """Dependency for quota enforcement service"""
    from server.billing.usage_metering import UsageMeteringService

    usage_service = UsageMeteringService(db)
    return QuotaEnforcementService(db, usage_service)


def get_usage_service(db: Session = Depends(get_db)) -> UsageMeteringService:
    """Dependency for usage metering service"""
    return UsageMeteringService(db)


@router.get("/accounts")
async def list_billing_accounts(
    account_type: Optional[str] = Query(None, description="Filter by account type"),
    plan_tier: Optional[str] = Query(None, description="Filter by plan tier"),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    List billing accounts with filtering.

    Args:
        account_type: Filter by account type (organization, team, user)
        plan_tier: Filter by plan tier (free, starter, pro, enterprise)
        status_filter: Filter by status (active, suspended, canceled)
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        List of billing accounts
    """
    query = db.query(BillingAccount)

    # Apply filters
    if account_type:
        query = query.filter(BillingAccount.account_type == account_type)
    if plan_tier:
        query = query.filter(BillingAccount.plan_tier == plan_tier)
    if status_filter:
        query = query.filter(BillingAccount.status == status_filter)

    # Filter out deleted accounts
    query = query.filter(BillingAccount.deleted_at.is_(None))

    # Get total count
    total = query.count()

    # Apply pagination
    accounts = query.order_by(BillingAccount.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "accounts": [
            {
                "id": str(account.id),
                "account_type": account.account_type,
                "account_id": str(account.account_id),
                "plan_tier": account.plan_tier,
                "currency": account.currency,
                "status": account.status,
                "created_at": account.created_at.isoformat(),
            }
            for account in accounts
        ],
    }


@router.get("/accounts/{billing_account_id}")
async def get_billing_account_details(
    billing_account_id: UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get detailed billing account information.

    Args:
        billing_account_id: Billing account ID

    Returns:
        Billing account details with usage summary
    """
    account = db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Billing account not found: {billing_account_id}"
        )

    # Get current billing period
    now = datetime.now(timezone.utc)
    current_period = (
        db.query(BillingPeriod)
        .filter(
            and_(
                BillingPeriod.billing_account_id == billing_account_id,
                BillingPeriod.period_start <= now,
                BillingPeriod.period_end >= now,
                BillingPeriod.status == "active",
            )
        )
        .first()
    )

    # Get usage summary
    usage_summary = {}
    if current_period:
        usage_service = UsageMeteringService(db)
        for resource_type in [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]:
            try:
                used, limit, percentage = usage_service.get_quota_usage_percentage(
                    billing_account_id=billing_account_id,
                    billing_period_id=current_period.id,
                    resource_type=resource_type,
                )
                usage_summary[resource_type.value] = {
                    "used": float(used),
                    "limit": float(limit),
                    "percentage": percentage,
                }
            except Exception:
                usage_summary[resource_type.value] = {
                    "used": 0,
                    "limit": 0,
                    "percentage": 0,
                }

    # Get active quota blocks
    active_blocks = (
        db.query(QuotaBlock)
        .filter(and_(QuotaBlock.billing_account_id == billing_account_id, QuotaBlock.is_active == True))
        .all()
    )

    return {
        "id": str(account.id),
        "account_type": account.account_type,
        "account_id": str(account.account_id),
        "plan_tier": account.plan_tier,
        "currency": account.currency,
        "status": account.status,
        "current_period": {
            "id": str(current_period.id) if current_period else None,
            "start": current_period.period_start.isoformat() if current_period else None,
            "end": current_period.period_end.isoformat() if current_period else None,
        },
        "usage_summary": usage_summary,
        "active_blocks": [
            {
                "resource_type": block.resource_type,
                "block_level": block.block_level,
                "reason": block.reason,
                "created_at": block.created_at.isoformat(),
            }
            for block in active_blocks
        ],
        "created_at": account.created_at.isoformat(),
    }


@router.get("/accounts/{billing_account_id}/usage")
async def get_usage_metrics(
    billing_account_id: UUID,
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get usage metrics for a billing account.

    Args:
        billing_account_id: Billing account ID
        resource_type: Filter by resource type (storage, retrieval, token)
        start_date: Start date for metrics (optional)
        end_date: End date for metrics (optional)

    Returns:
        Usage metrics and trends
    """
    account = db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Billing account not found: {billing_account_id}"
        )

    # Build query
    query = db.query(UsageEvent).filter(UsageEvent.billing_account_id == billing_account_id)

    if resource_type:
        query = query.filter(UsageEvent.resource_type == resource_type)

    if start_date:
        query = query.filter(UsageEvent.recorded_at >= start_date)
    if end_date:
        query = query.filter(UsageEvent.recorded_at <= end_date)

    # Get usage events
    usage_events = query.order_by(UsageEvent.recorded_at.desc()).limit(1000).all()

    # Aggregate by resource type
    usage_by_resource = {}
    for resource in [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]:
        resource_events = [e for e in usage_events if e.resource_type == resource.value]
        total_usage = sum(float(e.quantity) for e in resource_events)

        usage_by_resource[resource.value] = {
            "total": total_usage,
            "event_count": len(resource_events),
            "events": [
                {
                    "quantity": float(e.quantity),
                    "recorded_at": e.recorded_at.isoformat(),
                    "metadata": e.event_metadata,
                }
                for e in resource_events[:100]  # Limit to 100 most recent
            ],
        }

    return {
        "billing_account_id": str(billing_account_id),
        "resource_type": resource_type,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None,
        "usage_by_resource": usage_by_resource,
    }


@router.get("/accounts/{billing_account_id}/invoices")
async def get_invoice_history(
    billing_account_id: UUID,
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get invoice history for a billing account.

    Args:
        billing_account_id: Billing account ID
        status_filter: Filter by status (draft, issued, paid, void)
        limit: Maximum number of results
        offset: Offset for pagination

    Returns:
        Invoice history
    """
    query = db.query(Invoice).filter(Invoice.billing_account_id == billing_account_id)

    if status_filter:
        query = query.filter(Invoice.status == status_filter)

    # Get total count
    total = query.count()

    # Apply pagination
    invoices = query.order_by(Invoice.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "billing_account_id": str(billing_account_id),
        "total": total,
        "limit": limit,
        "offset": offset,
        "invoices": [
            {
                "id": str(inv.id),
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


@router.post("/accounts/{billing_account_id}/quota/override")
async def override_quota(
    billing_account_id: UUID,
    resource_type: str,
    new_limit: float,
    quota_service: QuotaEnforcementService = Depends(get_quota_service),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Override quota limit for a billing account (admin only).

    Args:
        billing_account_id: Billing account ID
        resource_type: Resource type (storage, retrieval, token)
        new_limit: New quota limit

    Returns:
        Updated quota information
    """
    # Get or create usage quota
    quota = (
        db.query(UsageQuota)
        .filter(and_(UsageQuota.billing_account_id == billing_account_id, UsageQuota.resource_type == resource_type))
        .first()
    )

    if not quota:
        # Get current billing period
        now = datetime.now(timezone.utc)
        current_period = (
            db.query(BillingPeriod)
            .filter(
                and_(
                    BillingPeriod.billing_account_id == billing_account_id,
                    BillingPeriod.period_start <= now,
                    BillingPeriod.period_end >= now,
                    BillingPeriod.status == "active",
                )
            )
            .first()
        )

        if not current_period:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active billing period found")

        # Create new quota
        quota = UsageQuota(
            billing_account_id=billing_account_id,
            resource_type=resource_type,
            quota_limit=Decimal(str(new_limit)),
            quota_used=Decimal("0"),
            overage_rate=Decimal("0"),
            period_start=current_period.period_start,
            period_end=current_period.period_end,
        )
        db.add(quota)
    else:
        # Update existing quota
        quota.quota_limit = Decimal(str(new_limit))

    db.commit()
    db.refresh(quota)

    # Remove any active blocks for this resource type
    active_blocks = (
        db.query(QuotaBlock)
        .filter(
            and_(
                QuotaBlock.billing_account_id == billing_account_id,
                QuotaBlock.resource_type == resource_type,
                QuotaBlock.is_active == True,
            )
        )
        .all()
    )

    for block in active_blocks:
        block.is_active = False
        block.unblocked_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "billing_account_id": str(billing_account_id),
        "resource_type": resource_type,
        "quota_limit": float(quota.quota_limit),
        "quota_used": float(quota.quota_used),
        "blocks_removed": len(active_blocks),
    }


@router.delete("/accounts/{billing_account_id}/quota/blocks/{block_id}")
async def remove_quota_block(
    billing_account_id: UUID,
    block_id: UUID,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Remove a quota block (admin override).

    Args:
        billing_account_id: Billing account ID
        block_id: Quota block ID

    Returns:
        Removal result
    """
    block = (
        db.query(QuotaBlock)
        .filter(and_(QuotaBlock.id == block_id, QuotaBlock.billing_account_id == billing_account_id))
        .first()
    )

    if not block:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Quota block not found: {block_id}")

    # Remove block
    block.is_active = False
    block.unblocked_at = datetime.now(timezone.utc)

    db.commit()

    return {
        "block_id": str(block_id),
        "removed": True,
        "removed_at": block.unblocked_at.isoformat(),
    }


@router.get("/metrics/overview")
async def get_billing_overview(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get billing system overview metrics.

    Returns:
        System-wide billing metrics
    """
    # Total accounts
    total_accounts = db.query(BillingAccount).filter(BillingAccount.deleted_at.is_(None)).count()

    # Active accounts
    active_accounts = (
        db.query(BillingAccount)
        .filter(and_(BillingAccount.status == AccountStatus.ACTIVE.value, BillingAccount.deleted_at.is_(None)))
        .count()
    )

    # Accounts by plan tier
    accounts_by_tier = {}
    for tier in [PlanTier.FREE, PlanTier.STARTER, PlanTier.PRO, PlanTier.ENTERPRISE]:
        count = (
            db.query(BillingAccount)
            .filter(and_(BillingAccount.plan_tier == tier.value, BillingAccount.deleted_at.is_(None)))
            .count()
        )
        accounts_by_tier[tier.value] = count

    # Active quota blocks
    active_blocks = db.query(QuotaBlock).filter(QuotaBlock.is_active == True).count()

    # Recent invoices
    recent_invoices = (
        db.query(Invoice).filter(Invoice.created_at >= datetime.now(timezone.utc) - timedelta(days=30)).count()
    )

    # Total revenue (sum of paid invoices)
    total_revenue = (
        db.query(func.sum(Invoice.total_amount)).filter(Invoice.status == InvoiceStatus.PAID.value).scalar() or 0
    )

    return {
        "total_accounts": total_accounts,
        "active_accounts": active_accounts,
        "accounts_by_tier": accounts_by_tier,
        "active_quota_blocks": active_blocks,
        "recent_invoices": recent_invoices,
        "total_revenue": float(total_revenue),
        "currency": "USD",  # Default currency
    }


@router.get("/metrics/trends")
async def get_usage_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Get usage trends over time.

    Args:
        days: Number of days to analyze
        resource_type: Filter by resource type (optional)

    Returns:
        Usage trends and statistics
    """
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    query = db.query(UsageEvent).filter(UsageEvent.recorded_at >= start_date)

    if resource_type:
        query = query.filter(UsageEvent.resource_type == resource_type)

    # Get usage events
    usage_events = query.all()

    # Aggregate by resource type
    trends = {}
    for resource in [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]:
        resource_events = [e for e in usage_events if e.resource_type == resource.value]

        if resource_events:
            total = sum(float(e.quantity) for e in resource_events)
            avg_per_day = total / days

            trends[resource.value] = {
                "total": total,
                "average_per_day": avg_per_day,
                "event_count": len(resource_events),
            }
        else:
            trends[resource.value] = {
                "total": 0,
                "average_per_day": 0,
                "event_count": 0,
            }

    return {
        "period_days": days,
        "start_date": start_date.isoformat(),
        "end_date": datetime.now(timezone.utc).isoformat(),
        "resource_type": resource_type,
        "trends": trends,
    }
