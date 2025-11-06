#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Quota Enforcement System
# Developer D - January 2025
#
# BILL-003: Soft/hard quota enforcement with blocking logic

"""
Quota enforcement system for SPEC-147 billing.

Features:
- Soft warnings at 75% usage
- Hard blocks at 100% usage
- Configurable per resource type
- Graceful degradation for read operations
"""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from .models import (
    AccountStatus,
    BillingAccount,
    BlockLevel,
    QuotaBlock,
    ResourceType,
    UsageEvent,
    UsageQuota,
)
from .usage_metering import UsageMeteringService


class QuotaStatus(str, Enum):
    """Quota status levels"""

    OK = "ok"
    WARNING = "warning"  # 75% threshold
    BLOCKED = "blocked"  # 100% threshold


class QuotaEnforcementService:
    """
    Service for enforcing usage quotas with soft and hard blocking.

    Features:
    - Soft warnings at 75% usage (email + in-app notifications)
    - Hard blocks at 100% usage (prevent new operations)
    - Configurable per resource type
    - Graceful degradation for read operations
    """

    SOFT_THRESHOLD = 75.0  # 75% usage triggers soft warning
    HARD_THRESHOLD = 100.0  # 100% usage triggers hard block

    def __init__(self, db: Session, usage_metering: Optional[UsageMeteringService] = None):
        """
        Initialize quota enforcement service.

        Args:
            db: Database session
            usage_metering: Optional UsageMeteringService instance
        """
        self.db = db
        self.usage_metering = usage_metering or UsageMeteringService(db)

    def check_quota_status(
        self,
        billing_account_id: uuid.UUID,
        billing_period_id: uuid.UUID,
        resource_type: ResourceType,
        operation_type: str = "write",  # "read" or "write"
    ) -> Tuple[QuotaStatus, float, Optional[QuotaBlock]]:
        """
        Check quota status for a resource type.

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Current billing period ID
            resource_type: Resource type to check
            operation_type: "read" or "write" (read operations may be allowed during blocks)

        Returns:
            Tuple of (status, usage_percentage, active_block)
        """
        # Get current usage and quota
        used, limit, percentage = self.usage_metering.get_quota_usage_percentage(
            billing_account_id, billing_period_id, resource_type
        )

        # Check for active block
        active_block = self.get_active_block(billing_account_id, resource_type)

        # Determine status
        if percentage >= self.HARD_THRESHOLD:
            # Check if read operations are allowed during hard blocks
            if operation_type == "read" and active_block:
                # Check if block allows read operations (graceful degradation)
                allow_read = (
                    active_block.event_metadata.get("allow_read_operations", False)
                    if active_block.event_metadata
                    else False
                )
                if allow_read:
                    return (QuotaStatus.WARNING, percentage, active_block)

            # Hard block - prevent operation
            return (QuotaStatus.BLOCKED, percentage, active_block)
        elif percentage >= self.SOFT_THRESHOLD:
            # Soft warning - allow but warn
            return (QuotaStatus.WARNING, percentage, active_block)
        else:
            # OK - within limits
            return (QuotaStatus.OK, percentage, None)

    def enforce_quota(
        self,
        billing_account_id: uuid.UUID,
        billing_period_id: uuid.UUID,
        resource_type: ResourceType,
        operation_type: str = "write",
    ) -> Tuple[bool, Optional[str]]:
        """
        Enforce quota - check and block if necessary.

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Current billing period ID
            resource_type: Resource type to check
            operation_type: "read" or "write"

        Returns:
            Tuple of (allowed, error_message)
        """
        status, percentage, active_block = self.check_quota_status(
            billing_account_id, billing_period_id, resource_type, operation_type
        )

        if status == QuotaStatus.BLOCKED:
            reason = active_block.reason if active_block else f"Quota exceeded 100% for {resource_type.value}"
            return (False, reason)
        elif status == QuotaStatus.WARNING:
            # Allow operation but log warning
            self._trigger_soft_warning(billing_account_id, resource_type, percentage)
            return (True, None)
        else:
            return (True, None)

    def create_soft_block(
        self,
        billing_account_id: uuid.UUID,
        usage_quota_id: Optional[uuid.UUID],
        resource_type: ResourceType,
        reason: str,
        metadata: Optional[Dict] = None,
    ) -> QuotaBlock:
        """
        Create a soft quota block (warning level).

        Args:
            billing_account_id: Billing account ID
            usage_quota_id: Optional usage quota ID
            resource_type: Resource type
            reason: Block reason
            metadata: Optional metadata

        Returns:
            QuotaBlock instance
        """
        # Check if soft block already exists
        existing = (
            self.db.query(QuotaBlock)
            .filter(
                and_(
                    QuotaBlock.billing_account_id == billing_account_id,
                    QuotaBlock.block_level == BlockLevel.SOFT.value,
                    QuotaBlock.is_active == True,
                    QuotaBlock.resource_type == resource_type.value if hasattr(QuotaBlock, "resource_type") else True,
                )
            )
            .first()
        )

        if existing:
            return existing

        block = QuotaBlock(
            billing_account_id=billing_account_id,
            usage_quota_id=usage_quota_id,
            block_level=BlockLevel.SOFT.value,
            reason=reason,
            event_metadata=metadata or {},
        )

        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)

        return block

    def create_hard_block(
        self,
        billing_account_id: uuid.UUID,
        usage_quota_id: Optional[uuid.UUID],
        resource_type: ResourceType,
        reason: str,
        allow_read_operations: bool = False,
        metadata: Optional[Dict] = None,
    ) -> QuotaBlock:
        """
        Create a hard quota block (blocking level).

        Args:
            billing_account_id: Billing account ID
            usage_quota_id: Optional usage quota ID
            resource_type: Resource type
            reason: Block reason
            allow_read_operations: Allow read operations during block (graceful degradation)
            metadata: Optional metadata

        Returns:
            QuotaBlock instance
        """
        # Deactivate any existing soft blocks
        self.db.query(QuotaBlock).filter(
            and_(
                QuotaBlock.billing_account_id == billing_account_id,
                QuotaBlock.block_level == BlockLevel.SOFT.value,
                QuotaBlock.is_active == True,
            )
        ).update({"is_active": False, "unblocked_at": datetime.utcnow()})

        # Check if hard block already exists
        existing = (
            self.db.query(QuotaBlock)
            .filter(
                and_(
                    QuotaBlock.billing_account_id == billing_account_id,
                    QuotaBlock.block_level == BlockLevel.HARD.value,
                    QuotaBlock.is_active == True,
                )
            )
            .first()
        )

        if existing:
            return existing

        block_metadata = {
            **(metadata or {}),
            "allow_read_operations": allow_read_operations,
            "resource_type": resource_type.value,
        }

        block = QuotaBlock(
            billing_account_id=billing_account_id,
            usage_quota_id=usage_quota_id,
            block_level=BlockLevel.HARD.value,
            reason=reason,
            event_metadata=block_metadata,
        )

        self.db.add(block)
        self.db.commit()
        self.db.refresh(block)

        return block

    def remove_block(self, billing_account_id: uuid.UUID, resource_type: Optional[ResourceType] = None):
        """
        Remove quota blocks for a billing account.

        Args:
            billing_account_id: Billing account ID
            resource_type: Optional resource type (if None, removes all)
        """
        query = self.db.query(QuotaBlock).filter(
            and_(QuotaBlock.billing_account_id == billing_account_id, QuotaBlock.is_active == True)
        )

        if resource_type:
            # Filter by resource type if supported
            # Note: QuotaBlock may not have resource_type column directly
            # This would need to be added or queried via usage_quota
            pass

        blocks = query.all()
        for block in blocks:
            block.is_active = False
            block.unblocked_at = datetime.utcnow()

        self.db.commit()

    def get_active_block(self, billing_account_id: uuid.UUID, resource_type: ResourceType) -> Optional[QuotaBlock]:
        """
        Get active quota block for a resource type.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type

        Returns:
            Active QuotaBlock or None
        """
        # Try to find block via usage_quota
        usage_quota = (
            self.db.query(UsageQuota)
            .filter(
                and_(
                    UsageQuota.billing_account_id == billing_account_id, UsageQuota.resource_type == resource_type.value
                )
            )
            .first()
        )

        if usage_quota:
            block = (
                self.db.query(QuotaBlock)
                .filter(
                    and_(
                        QuotaBlock.billing_account_id == billing_account_id,
                        QuotaBlock.usage_quota_id == usage_quota.id,
                        QuotaBlock.is_active == True,
                    )
                )
                .first()
            )

            if block:
                return block

        # Fallback: check all active blocks for account
        block = (
            self.db.query(QuotaBlock)
            .filter(and_(QuotaBlock.billing_account_id == billing_account_id, QuotaBlock.is_active == True))
            .first()
        )

        return block

    def check_and_enforce(
        self,
        billing_account_id: uuid.UUID,
        billing_period_id: uuid.UUID,
        resource_type: ResourceType,
        operation_type: str = "write",
    ) -> Tuple[bool, Optional[str], Optional[QuotaBlock]]:
        """
        Check quota and enforce blocks - creates blocks if needed.

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Current billing period ID
            resource_type: Resource type to check
            operation_type: "read" or "write"

        Returns:
            Tuple of (allowed, error_message, active_block)
        """
        # Invalidate cache to ensure fresh usage calculation
        # This is important when usage was just recorded
        self.usage_metering.cache.invalidate_usage(billing_account_id, resource_type)

        # Check current status (with fresh calculation)
        status, percentage, active_block = self.check_quota_status(
            billing_account_id, billing_period_id, resource_type, operation_type
        )

        # Get usage quota
        usage_quota = (
            self.db.query(UsageQuota)
            .filter(
                and_(
                    UsageQuota.billing_account_id == billing_account_id, UsageQuota.resource_type == resource_type.value
                )
            )
            .first()
        )

        # Create blocks if needed
        # If percentage >= 100%, always create hard block (even if soft block exists)
        if percentage >= self.HARD_THRESHOLD:
            # If there's an active soft block, deactivate it first
            if active_block and active_block.block_level == BlockLevel.SOFT.value:
                active_block.is_active = False
                active_block.unblocked_at = datetime.utcnow()
                self.db.commit()
                active_block = None  # Reset for hard block creation

            # Create hard block if not already exists
            if not active_block or active_block.block_level != BlockLevel.HARD.value:
                # Create hard block
                block = self.create_hard_block(
                    billing_account_id=billing_account_id,
                    usage_quota_id=usage_quota.id if usage_quota else None,
                    resource_type=resource_type,
                    reason=f"Quota usage exceeded 100% ({percentage:.1f}%) for {resource_type.value}",
                    allow_read_operations=(operation_type == "read"),
                )
                # Send notification
                from .quota_notifications import QuotaNotificationService

                notification_service = QuotaNotificationService(self.db)
                notification_service.send_hard_block_notification(
                    billing_account_id=billing_account_id,
                    resource_type=resource_type,
                    usage_percentage=percentage,
                    block_reason=block.reason,
                )
                return (False, block.reason, block)
            else:
                # Hard block already exists
                return (False, active_block.reason, active_block)
        elif percentage >= self.SOFT_THRESHOLD and not active_block:
            # Create soft block
            block = self.create_soft_block(
                billing_account_id=billing_account_id,
                usage_quota_id=usage_quota.id if usage_quota else None,
                resource_type=resource_type,
                reason=f"Quota usage exceeded 75% ({percentage:.1f}%) for {resource_type.value}",
            )
            # Send notification
            self._trigger_soft_warning(billing_account_id, resource_type, percentage)
            return (True, None, block)

        # Remove blocks if usage dropped below thresholds
        if active_block and percentage < self.SOFT_THRESHOLD:
            self.remove_block(billing_account_id, resource_type)
            # Send resolution notification
            from .quota_notifications import QuotaNotificationService

            notification_service = QuotaNotificationService(self.db)
            notification_service.send_quota_resolved_notification(
                billing_account_id=billing_account_id, resource_type=resource_type
            )
            return (True, None, None)

        # Check if operation is allowed
        if status == QuotaStatus.BLOCKED:
            reason = active_block.reason if active_block else f"Quota exceeded 100% for {resource_type.value}"
            return (False, reason, active_block)

        return (True, None, active_block)

    def _trigger_soft_warning(self, billing_account_id: uuid.UUID, resource_type: ResourceType, percentage: float):
        """
        Trigger soft warning notification.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type
            percentage: Usage percentage
        """
        from .quota_notifications import QuotaNotificationService

        notification_service = QuotaNotificationService(self.db)

        # Get usage details for notification
        # Get current billing period for account
        from .models import BillingPeriod, BillingPeriodStatus

        billing_period = (
            self.db.query(BillingPeriod)
            .filter(
                and_(
                    BillingPeriod.billing_account_id == billing_account_id,
                    BillingPeriod.status == BillingPeriodStatus.ACTIVE.value,
                )
            )
            .first()
        )

        if billing_period:
            used, limit, _ = self.usage_metering.get_quota_usage_percentage(
                billing_account_id, billing_period.id, resource_type
            )

            notification_service.send_soft_warning(
                billing_account_id=billing_account_id,
                resource_type=resource_type,
                usage_percentage=percentage,
                used=float(used),
                limit=float(limit),
            )

    def get_quota_summary(self, billing_account_id: uuid.UUID, billing_period_id: uuid.UUID) -> Dict[str, Dict]:
        """
        Get quota summary for all resource types.

        Args:
            billing_account_id: Billing account ID
            billing_period_id: Current billing period ID

        Returns:
            Dictionary mapping resource_type to quota status
        """
        summary = {}

        for resource_type in [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]:
            status, percentage, active_block = self.check_quota_status(
                billing_account_id, billing_period_id, resource_type
            )

            used, limit, _ = self.usage_metering.get_quota_usage_percentage(
                billing_account_id, billing_period_id, resource_type
            )

            summary[resource_type.value] = {
                "status": status.value,
                "percentage": percentage,
                "used": float(used),
                "limit": float(limit),
                "has_block": active_block is not None,
                "block_level": active_block.block_level if active_block else None,
            }

        return summary
