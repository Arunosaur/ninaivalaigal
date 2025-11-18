#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Payment Transfer Service
# Developer D - January 2025
#
# BILL-006: Graceful payment transfer when team payer leaves

"""
Payment transfer service for SPEC-147 billing.

Features:
- Detect when paying user leaves team
- Initiate payment transfer workflow
- 30-day grace period with deadline tracking
- Escalating notifications to backup payers
- Soft block at day 15 (read-only for new features)
- Hard block at day 30 if no new payer assigned
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from .models import (
    AccountStatus,
    BillingAccount,
    BlockLevel,
    PaymentConfig,
    PaymentTransfer,
    QuotaBlock,
    ResourceType,
    TransferStatus,
)


class PaymentTransferService:
    """
    Service for managing payment responsibility transfers.

    Features:
    - Detect payer leaving
    - Initiate transfer workflow
    - Grace period management
    - Block escalation
    - Notification management
    """

    GRACE_PERIOD_DAYS = 30
    SOFT_BLOCK_DAY = 15
    HARD_BLOCK_DAY = 30

    def __init__(self, db: Session):
        """
        Initialize payment transfer service.

        Args:
            db: Database session
        """
        self.db = db

    def detect_payer_leaving(self, billing_account_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """
        Detect if the paying user is leaving the team.

        Args:
            billing_account_id: Billing account ID
            user_id: User ID that is leaving

        Returns:
            True if payer is leaving, False otherwise
        """
        # Get payment config
        payment_config = (
            self.db.query(PaymentConfig).filter(PaymentConfig.billing_account_id == billing_account_id).first()
        )

        if not payment_config:
            return False  # No payment config, no transfer needed

        # Check if this user is the primary payer
        if payment_config.primary_payer_id == user_id:
            return True

        return False

    def initiate_payment_transfer(
        self, billing_account_id: uuid.UUID, from_user_id: uuid.UUID, reason: str = "left_team"
    ) -> PaymentTransfer:
        """
        Initiate payment transfer workflow.

        Args:
            billing_account_id: Billing account ID
            from_user_id: User ID that is leaving
            reason: Transfer reason (left_team, reassigned, voluntary)

        Returns:
            PaymentTransfer instance
        """
        # Get payment config
        payment_config = (
            self.db.query(PaymentConfig).filter(PaymentConfig.billing_account_id == billing_account_id).first()
        )

        if not payment_config:
            raise ValueError(f"Payment config not found for billing account: {billing_account_id}")

        # Verify user is the primary payer
        if payment_config.primary_payer_id != from_user_id:
            raise ValueError(f"User {from_user_id} is not the primary payer")

        # Check if transfer already in progress
        active_transfer = (
            self.db.query(PaymentTransfer)
            .filter(and_(PaymentTransfer.payment_config_id == payment_config.id, PaymentTransfer.status == "pending"))
            .first()
        )

        if active_transfer:
            return active_transfer  # Transfer already in progress

        # Calculate grace period
        now = datetime.now(timezone.utc)
        grace_period_start = now
        grace_period_end = now + timedelta(days=self.GRACE_PERIOD_DAYS)

        # Update payment config
        payment_config.grace_period_start = grace_period_start
        payment_config.grace_period_end = grace_period_end
        payment_config.transfer_status = TransferStatus.GRACE.value

        # Create transfer record
        transfer = PaymentTransfer(
            payment_config_id=payment_config.id,
            from_user_id=from_user_id,
            to_user_id=None,  # To be assigned
            reason=reason,  # left_team, reassigned, or voluntary
            status="pending",  # pending, completed, or failed
        )

        self.db.add(transfer)
        self.db.commit()
        self.db.refresh(transfer)

        return transfer

    def assign_new_payer(
        self, billing_account_id: uuid.UUID, new_payer_id: uuid.UUID, transfer_id: Optional[uuid.UUID] = None
    ) -> PaymentTransfer:
        """
        Assign new payer to complete transfer.

        Args:
            billing_account_id: Billing account ID
            new_payer_id: New payer user ID
            transfer_id: Transfer ID (optional, uses active transfer if None)

        Returns:
            Completed PaymentTransfer instance
        """
        # Get payment config
        payment_config = (
            self.db.query(PaymentConfig).filter(PaymentConfig.billing_account_id == billing_account_id).first()
        )

        if not payment_config:
            raise ValueError(f"Payment config not found for billing account: {billing_account_id}")

        # Get transfer
        if transfer_id:
            transfer = self.db.query(PaymentTransfer).filter(PaymentTransfer.id == transfer_id).first()
        else:
            transfer = (
                self.db.query(PaymentTransfer)
                .filter(
                    and_(PaymentTransfer.payment_config_id == payment_config.id, PaymentTransfer.status == "pending")
                )
                .order_by(PaymentTransfer.initiated_at.desc())
                .first()
            )

        if not transfer:
            raise ValueError("No active payment transfer found")

        # Update transfer
        transfer.to_user_id = new_payer_id
        transfer.status = "completed"
        transfer.completed_at = datetime.now(timezone.utc)

        # Update payment config
        payment_config.primary_payer_id = new_payer_id
        payment_config.grace_period_start = None
        payment_config.grace_period_end = None
        payment_config.transfer_status = TransferStatus.ACTIVE.value

        # Remove any grace period blocks
        self._remove_grace_period_blocks(billing_account_id)

        self.db.commit()
        self.db.refresh(transfer)

        return transfer

    def check_grace_period_status(self, billing_account_id: uuid.UUID) -> Dict[str, Any]:
        """
        Check grace period status and apply blocks if needed.

        Args:
            billing_account_id: Billing account ID

        Returns:
            Grace period status information
        """
        # Get payment config
        payment_config = (
            self.db.query(PaymentConfig).filter(PaymentConfig.billing_account_id == billing_account_id).first()
        )

        if not payment_config or payment_config.transfer_status != TransferStatus.GRACE.value:
            return {
                "in_grace_period": False,
                "message": "No active grace period",
            }

        if not payment_config.grace_period_end:
            return {
                "in_grace_period": False,
                "message": "Grace period not configured",
            }

        now = datetime.now(timezone.utc)
        # Ensure timezone-aware datetime comparisons
        if payment_config.grace_period_end:
            grace_end = payment_config.grace_period_end
            if grace_end.tzinfo is None:
                grace_end = grace_end.replace(tzinfo=timezone.utc)
            days_remaining = (grace_end - now).days
        else:
            days_remaining = 0

        if payment_config.grace_period_start:
            grace_start = payment_config.grace_period_start
            if grace_start.tzinfo is None:
                grace_start = grace_start.replace(tzinfo=timezone.utc)
            days_elapsed = (now - grace_start).days
        else:
            days_elapsed = 0

        # Check if grace period expired
        if payment_config.grace_period_end:
            grace_end = payment_config.grace_period_end
            if grace_end.tzinfo is None:
                grace_end = grace_end.replace(tzinfo=timezone.utc)
            if now >= grace_end:
                # Grace period expired, apply hard block
                self._apply_hard_block(billing_account_id)

                return {
                    "in_grace_period": False,
                    "grace_period_expired": True,
                    "days_elapsed": days_elapsed,
                    "hard_block_applied": True,
                }

        # Check if soft block should be applied (day 15)
        if days_elapsed >= self.SOFT_BLOCK_DAY:
            self._apply_soft_block(billing_account_id)

            return {
                "in_grace_period": True,
                "days_remaining": days_remaining,
                "days_elapsed": days_elapsed,
                "soft_block_applied": True,
                "warning": f"Soft block applied. {days_remaining} days remaining.",
            }

        # Grace period active, no blocks yet
        return {
            "in_grace_period": True,
            "days_remaining": days_remaining,
            "days_elapsed": days_elapsed,
            "soft_block_applied": False,
            "hard_block_applied": False,
        }

    def _apply_soft_block(self, billing_account_id: uuid.UUID) -> Optional[QuotaBlock]:
        """
        Apply soft block at day 15 of grace period.

        Args:
            billing_account_id: Billing account ID

        Returns:
            QuotaBlock instance or None
        """
        # Check if soft block already exists
        existing_block = (
            self.db.query(QuotaBlock)
            .filter(
                and_(
                    QuotaBlock.billing_account_id == billing_account_id,
                    QuotaBlock.block_level == BlockLevel.SOFT.value,
                    QuotaBlock.is_active == True,
                    QuotaBlock.reason.like("%grace period%"),
                )
            )
            .first()
        )

        if existing_block:
            return existing_block

        # Create soft block (applies to all resources via usage_quota_id = None)
        block = QuotaBlock(
            billing_account_id=billing_account_id,
            usage_quota_id=None,  # Applies to all quotas
            block_level=BlockLevel.SOFT.value,
            reason="Grace period: Payment transfer in progress (day 15). Read-only access maintained.",
            is_active=True,
        )
        self.db.add(block)
        self.db.commit()
        return block

    def _apply_hard_block(self, billing_account_id: uuid.UUID) -> Optional[QuotaBlock]:
        """
        Apply hard block at day 30 if no new payer assigned.

        Args:
            billing_account_id: Billing account ID

        Returns:
            QuotaBlock instance or None
        """
        # Remove existing soft blocks
        soft_blocks = (
            self.db.query(QuotaBlock)
            .filter(
                and_(
                    QuotaBlock.billing_account_id == billing_account_id,
                    QuotaBlock.block_level == BlockLevel.SOFT.value,
                    QuotaBlock.is_active == True,
                    QuotaBlock.reason.like("%grace period%"),
                )
            )
            .all()
        )

        for block in soft_blocks:
            block.is_active = False
            block.unblocked_at = datetime.now(timezone.utc)

        # Check if hard block already exists
        existing_block = (
            self.db.query(QuotaBlock)
            .filter(
                and_(
                    QuotaBlock.billing_account_id == billing_account_id,
                    QuotaBlock.block_level == BlockLevel.HARD.value,
                    QuotaBlock.is_active == True,
                    QuotaBlock.reason.like("%grace period%"),
                )
            )
            .first()
        )

        if existing_block:
            return existing_block

        # Create hard block (applies to all resources via usage_quota_id = None)
        block = QuotaBlock(
            billing_account_id=billing_account_id,
            usage_quota_id=None,  # Applies to all quotas
            block_level=BlockLevel.HARD.value,
            reason="Grace period expired: No new payer assigned after 30 days. Account blocked.",
            is_active=True,
        )
        self.db.add(block)

        # Update billing account status
        billing_account = self.db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()

        if billing_account:
            billing_account.status = AccountStatus.SUSPENDED.value

        self.db.commit()
        return block

    def _remove_grace_period_blocks(self, billing_account_id: uuid.UUID):
        """Remove all grace period blocks"""
        blocks = (
            self.db.query(QuotaBlock)
            .filter(
                and_(
                    QuotaBlock.billing_account_id == billing_account_id,
                    QuotaBlock.is_active == True,
                    or_(QuotaBlock.reason.like("%grace period%"), QuotaBlock.reason.like("%Payment transfer%")),
                )
            )
            .all()
        )

        for block in blocks:
            block.is_active = False
            block.unblocked_at = datetime.now(timezone.utc)

        self.db.commit()

    def get_backup_payers(self, billing_account_id: uuid.UUID) -> List[uuid.UUID]:
        """
        Get list of backup payers from payment config.

        Args:
            billing_account_id: Billing account ID

        Returns:
            List of backup payer user IDs
        """
        payment_config = (
            self.db.query(PaymentConfig).filter(PaymentConfig.billing_account_id == billing_account_id).first()
        )

        if not payment_config:
            return []

        # backup_payer_ids is JSONB, could be a list or None
        backup_payers = payment_config.backup_payer_ids
        if not backup_payers:
            return []

        # Ensure it's a list of UUIDs
        if isinstance(backup_payers, list):
            return [uuid.UUID(str(payer_id)) for payer_id in backup_payers if payer_id]

        return []

    def send_notification_to_backup_payers(self, billing_account_id: uuid.UUID, days_remaining: int) -> Dict[str, Any]:
        """
        Send notifications to backup payers.

        Args:
            billing_account_id: Billing account ID
            days_remaining: Days remaining in grace period

        Returns:
            Notification results
        """
        backup_payers = self.get_backup_payers(billing_account_id)

        results = {
            "notified": 0,
            "backup_payers": [str(payer_id) for payer_id in backup_payers],
        }

        # TODO: Integrate with email/notification service
        # For now, just log the notification
        for payer_id in backup_payers:
            # Send notification (placeholder)
            # notification_service.send_payment_transfer_notification(
            #     payer_id=payer_id,
            #     billing_account_id=billing_account_id,
            #     days_remaining=days_remaining
            # )
            results["notified"] += 1

        return results

    def process_all_grace_periods(self) -> Dict[str, Any]:
        """
        Process all active grace periods (should be called periodically).

        Returns:
            Processing results
        """
        results = {
            "processed": 0,
            "soft_blocks_applied": 0,
            "hard_blocks_applied": 0,
            "expired": 0,
            "errors": 0,
            "errors_detail": [],
        }

        # Get all payment configs in grace period
        payment_configs = (
            self.db.query(PaymentConfig).filter(PaymentConfig.transfer_status == TransferStatus.GRACE.value).all()
        )

        for config in payment_configs:
            try:
                status = self.check_grace_period_status(config.billing_account_id)

                if status.get("soft_block_applied"):
                    results["soft_blocks_applied"] += 1

                if status.get("hard_block_applied"):
                    results["hard_blocks_applied"] += 1

                if status.get("grace_period_expired"):
                    results["expired"] += 1

                # Send notifications if needed
                if status.get("in_grace_period") and status.get("days_remaining"):
                    days_remaining = status["days_remaining"]
                    if days_remaining <= 7:  # Send daily notifications in last week
                        self.send_notification_to_backup_payers(config.billing_account_id, days_remaining)

                results["processed"] += 1

            except Exception as e:
                results["errors"] += 1
                results["errors_detail"].append(
                    {
                        "billing_account_id": str(config.billing_account_id),
                        "error": str(e),
                    }
                )

        return results




