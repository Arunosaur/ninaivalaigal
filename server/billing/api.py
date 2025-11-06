#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing API Endpoints
# Developer D - January 2025
#
# FastAPI endpoints for billing system integration

"""
FastAPI endpoints for SPEC-147 billing system.

Provides REST API for:
- Quota status checking
- Usage metering
- Quota enforcement
- Billing account management
"""

from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from server.billing.models import ResourceType
from server.billing.quota_enforcement import QuotaEnforcementService, QuotaStatus
from server.billing.usage_metering import UsageMeteringService
from server.database import get_db

router = APIRouter(prefix="/api/billing", tags=["billing"])


def get_usage_metering_service(db: Session = Depends(get_db)) -> UsageMeteringService:
    """Dependency for usage metering service"""
    return UsageMeteringService(db)


def get_quota_enforcement_service(
    db: Session = Depends(get_db), usage_metering: UsageMeteringService = Depends(get_usage_metering_service)
) -> QuotaEnforcementService:
    """Dependency for quota enforcement service"""
    return QuotaEnforcementService(db, usage_metering)


@router.get("/accounts/{billing_account_id}/quota/status")
async def get_quota_status(
    billing_account_id: UUID,
    billing_period_id: UUID,
    resource_type: str,
    enforcement_service: QuotaEnforcementService = Depends(get_quota_enforcement_service),
) -> Dict[str, Any]:
    """
    Get quota status for a billing account.

    Args:
        billing_account_id: Billing account ID
        billing_period_id: Current billing period ID
        resource_type: Resource type (storage, retrieval, token)

    Returns:
        Quota status with usage percentage and block information
    """
    try:
        resource_type_enum = ResourceType(resource_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type: {resource_type}. Must be one of: storage, retrieval, token",
        )

    status_result, percentage, active_block = enforcement_service.check_quota_status(
        billing_account_id, billing_period_id, resource_type_enum
    )

    return {
        "billing_account_id": str(billing_account_id),
        "billing_period_id": str(billing_period_id),
        "resource_type": resource_type,
        "status": status_result.value,
        "usage_percentage": percentage,
        "has_block": active_block is not None,
        "block_level": active_block.block_level if active_block else None,
        "block_reason": active_block.reason if active_block else None,
    }


@router.get("/accounts/{billing_account_id}/quota/summary")
async def get_quota_summary(
    billing_account_id: UUID,
    billing_period_id: UUID,
    enforcement_service: QuotaEnforcementService = Depends(get_quota_enforcement_service),
) -> Dict[str, Any]:
    """
    Get quota summary for all resource types.

    Args:
        billing_account_id: Billing account ID
        billing_period_id: Current billing period ID

    Returns:
        Quota summary for all resource types
    """
    summary = enforcement_service.get_quota_summary(billing_account_id, billing_period_id)

    return {
        "billing_account_id": str(billing_account_id),
        "billing_period_id": str(billing_period_id),
        "quotas": summary,
    }


@router.post("/accounts/{billing_account_id}/usage/storage")
async def record_storage_usage(
    billing_account_id: UUID,
    billing_period_id: UUID,
    storage_gb: Decimal,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    usage_metering: UsageMeteringService = Depends(get_usage_metering_service),
    enforcement_service: QuotaEnforcementService = Depends(get_quota_enforcement_service),
) -> Dict[str, Any]:
    """
    Record storage usage.

    Args:
        billing_account_id: Billing account ID
        billing_period_id: Current billing period ID
        storage_gb: Storage usage in GB
        idempotency_key: Optional idempotency key for duplicate prevention
        metadata: Optional metadata

    Returns:
        Usage event details
    """
    # Check quota before recording
    allowed, error = enforcement_service.enforce_quota(
        billing_account_id, billing_period_id, ResourceType.STORAGE, operation_type="write"
    )

    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Quota exceeded: {error}")

    # Record usage
    event = usage_metering.record_storage_usage(
        billing_account_id=billing_account_id,
        billing_period_id=billing_period_id,
        storage_gb=storage_gb,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )

    return {
        "event_id": str(event.id),
        "billing_account_id": str(billing_account_id),
        "resource_type": "storage",
        "quantity": float(storage_gb),
        "recorded_at": event.created_at.isoformat(),
    }


@router.post("/accounts/{billing_account_id}/usage/retrieval")
async def record_retrieval_usage(
    billing_account_id: UUID,
    billing_period_id: UUID,
    retrieval_count: Decimal,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    usage_metering: UsageMeteringService = Depends(get_usage_metering_service),
    enforcement_service: QuotaEnforcementService = Depends(get_quota_enforcement_service),
) -> Dict[str, Any]:
    """
    Record retrieval usage.

    Args:
        billing_account_id: Billing account ID
        billing_period_id: Current billing period ID
        retrieval_count: Number of retrievals
        idempotency_key: Optional idempotency key
        metadata: Optional metadata

    Returns:
        Usage event details
    """
    # Check quota before recording
    allowed, error = enforcement_service.enforce_quota(
        billing_account_id, billing_period_id, ResourceType.RETRIEVAL, operation_type="write"
    )

    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Quota exceeded: {error}")

    # Record usage
    event = usage_metering.record_retrieval_usage(
        billing_account_id=billing_account_id,
        billing_period_id=billing_period_id,
        retrieval_count=retrieval_count,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )

    return {
        "event_id": str(event.id),
        "billing_account_id": str(billing_account_id),
        "resource_type": "retrieval",
        "quantity": float(retrieval_count),
        "recorded_at": event.created_at.isoformat(),
    }


@router.post("/accounts/{billing_account_id}/usage/token")
async def record_token_usage(
    billing_account_id: UUID,
    billing_period_id: UUID,
    token_count: Decimal,
    idempotency_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    usage_metering: UsageMeteringService = Depends(get_usage_metering_service),
    enforcement_service: QuotaEnforcementService = Depends(get_quota_enforcement_service),
) -> Dict[str, Any]:
    """
    Record token usage.

    Args:
        billing_account_id: Billing account ID
        billing_period_id: Current billing period ID
        token_count: Number of tokens
        idempotency_key: Optional idempotency key
        metadata: Optional metadata

    Returns:
        Usage event details
    """
    # Check quota before recording
    allowed, error = enforcement_service.enforce_quota(
        billing_account_id, billing_period_id, ResourceType.TOKEN, operation_type="write"
    )

    if not allowed:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=f"Quota exceeded: {error}")

    # Record usage
    event = usage_metering.record_token_usage(
        billing_account_id=billing_account_id,
        billing_period_id=billing_period_id,
        token_count=token_count,
        idempotency_key=idempotency_key,
        metadata=metadata,
    )

    return {
        "event_id": str(event.id),
        "billing_account_id": str(billing_account_id),
        "resource_type": "token",
        "quantity": float(token_count),
        "recorded_at": event.created_at.isoformat(),
    }


@router.get("/accounts/{billing_account_id}/usage/current")
async def get_current_usage(
    billing_account_id: UUID,
    billing_period_id: UUID,
    resource_type: str,
    usage_metering: UsageMeteringService = Depends(get_usage_metering_service),
) -> Dict[str, Any]:
    """
    Get current usage for a resource type.

    Args:
        billing_account_id: Billing account ID
        billing_period_id: Current billing period ID
        resource_type: Resource type (storage, retrieval, token)

    Returns:
        Current usage information
    """
    try:
        resource_type_enum = ResourceType(resource_type.lower())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type: {resource_type}. Must be one of: storage, retrieval, token",
        )

    usage = usage_metering.get_current_usage(billing_account_id, billing_period_id, resource_type_enum)

    used, limit, percentage = usage_metering.get_quota_usage_percentage(
        billing_account_id, billing_period_id, resource_type_enum
    )

    return {
        "billing_account_id": str(billing_account_id),
        "billing_period_id": str(billing_period_id),
        "resource_type": resource_type,
        "used": float(used),
        "limit": float(limit),
        "usage_percentage": percentage,
    }
