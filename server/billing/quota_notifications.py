#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Quota Notification System
# Developer D - January 2025
#
# BILL-003: Email and in-app notifications for quota warnings

"""
Notification system for quota enforcement.

Features:
- Email notifications at 75% usage (soft warning)
- In-app notifications
- Audit trail logging
"""

import uuid
from datetime import datetime
from typing import Dict, Optional

from sqlalchemy.orm import Session

from .models import AuditLog, BillingAccount, BlockLevel, ResourceType


class QuotaNotificationService:
    """
    Service for sending quota-related notifications.

    Features:
    - Email notifications
    - In-app notifications (via database)
    - Audit trail logging
    """

    def __init__(self, db: Session):
        """
        Initialize notification service.

        Args:
            db: Database session
        """
        self.db = db

    def send_soft_warning(
        self,
        billing_account_id: uuid.UUID,
        resource_type: ResourceType,
        usage_percentage: float,
        used: float,
        limit: float,
    ):
        """
        Send soft warning notification (75% threshold).

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type
            usage_percentage: Current usage percentage
            used: Used amount
            limit: Quota limit
        """
        # Get billing account
        billing_account = self.db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()

        if not billing_account:
            return

        # Create audit log entry
        self._log_quota_warning(
            billing_account_id=billing_account_id,
            resource_type=resource_type,
            usage_percentage=usage_percentage,
            message=f"Quota usage at {usage_percentage:.1f}% for {resource_type.value}",
        )

        # TODO: Send email notification
        # TODO: Create in-app notification
        # For now, just log
        print(
            f"📧 Soft warning email: Account {billing_account_id} - {resource_type.value} at {usage_percentage:.1f}%"
        )  # noqa: T201

    def send_hard_block_notification(
        self, billing_account_id: uuid.UUID, resource_type: ResourceType, usage_percentage: float, block_reason: str
    ):
        """
        Send hard block notification (100% threshold).

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type
            usage_percentage: Current usage percentage
            block_reason: Block reason
        """
        # Get billing account
        billing_account = self.db.query(BillingAccount).filter(BillingAccount.id == billing_account_id).first()

        if not billing_account:
            return

        # Create audit log entry
        self._log_quota_block(
            billing_account_id=billing_account_id,
            resource_type=resource_type,
            usage_percentage=usage_percentage,
            message=f"Hard block: {block_reason}",
        )

        # TODO: Send email notification
        # TODO: Create in-app notification
        # For now, just log
        print(f"🚫 Hard block notification: Account {billing_account_id} - {resource_type.value} blocked")  # noqa: T201

    def send_quota_resolved_notification(self, billing_account_id: uuid.UUID, resource_type: ResourceType):
        """
        Send notification when quota issue is resolved.

        Args:
            billing_account_id: Billing account ID
            resource_type: Resource type
        """
        # Create audit log entry
        self._log_quota_resolved(
            billing_account_id=billing_account_id,
            resource_type=resource_type,
            message=f"Quota issue resolved for {resource_type.value}",
        )

        # TODO: Send email notification
        # TODO: Create in-app notification
        print(f"✅ Quota resolved: Account {billing_account_id} - {resource_type.value}")  # noqa: T201

    def _log_quota_warning(
        self, billing_account_id: uuid.UUID, resource_type: ResourceType, usage_percentage: float, message: str
    ):
        """Log quota warning to audit trail"""
        import hashlib
        import json

        event_data = {
            "resource_type": resource_type.value,
            "usage_percentage": usage_percentage,
            "message": message,
        }

        # Generate event hash for immutability
        event_hash = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()

        audit_log = AuditLog(
            billing_account_id=billing_account_id,
            event_type="quota_warning",
            event_data=event_data,
            event_hash=event_hash,
            user_id=None,  # System action
        )

        self.db.add(audit_log)
        self.db.commit()

    def _log_quota_block(
        self, billing_account_id: uuid.UUID, resource_type: ResourceType, usage_percentage: float, message: str
    ):
        """Log quota block to audit trail"""
        import hashlib
        import json

        event_data = {
            "resource_type": resource_type.value,
            "usage_percentage": usage_percentage,
            "message": message,
        }

        # Generate event hash for immutability
        event_hash = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()

        audit_log = AuditLog(
            billing_account_id=billing_account_id,
            event_type="quota_block",
            event_data=event_data,
            event_hash=event_hash,
            user_id=None,  # System action
        )

        self.db.add(audit_log)
        self.db.commit()

    def _log_quota_resolved(self, billing_account_id: uuid.UUID, resource_type: ResourceType, message: str):
        """Log quota resolution to audit trail"""
        import hashlib
        import json

        event_data = {
            "resource_type": resource_type.value,
            "message": message,
        }

        # Generate event hash for immutability
        event_hash = hashlib.sha256(json.dumps(event_data, sort_keys=True).encode()).hexdigest()

        audit_log = AuditLog(
            billing_account_id=billing_account_id,
            event_type="quota_resolved",
            event_data=event_data,
            event_hash=event_hash,
            user_id=None,  # System action
        )

        self.db.add(audit_log)
        self.db.commit()
