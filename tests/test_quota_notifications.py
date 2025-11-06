#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Quota Notifications Tests
#
"""
Unit tests for server/billing/quota_notifications.py

Tests quota notification system for warnings and blocks.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from server.billing.models import (
    AccountStatus,
    AccountType,
    BillingAccount,
    ResourceType,
)
from server.billing.quota_notifications import QuotaNotificationService

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    mock_session = MagicMock()
    return mock_session


@pytest.fixture
def billing_account():
    """Create a test billing account"""
    return BillingAccount(
        id=uuid4(),
        account_type=AccountType.TEAM.value,
        account_id=uuid4(),
        status=AccountStatus.ACTIVE.value,
    )


@pytest.fixture
def notification_service(mock_db_session):
    """Create QuotaNotificationService with mock DB"""
    return QuotaNotificationService(db=mock_db_session)


class TestQuotaNotificationService:
    """Tests for QuotaNotificationService"""

    def test_send_soft_warning(self, notification_service, mock_db_session, billing_account):
        """Test sending soft warning notification"""
        billing_account_id = billing_account.id
        resource_type = ResourceType.STORAGE
        usage_percentage = 75.5

        # Mock database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = billing_account

        notification_service.send_soft_warning(
            billing_account_id=billing_account_id,
            resource_type=resource_type,
            usage_percentage=usage_percentage,
            used=750.0,
            limit=1000.0,
        )

        # Verify audit log was created
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

        # Verify billing account was queried
        mock_db_session.query.assert_called_once_with(BillingAccount)

    def test_send_soft_warning_account_not_found(self, notification_service, mock_db_session):
        """Test soft warning when billing account not found"""
        billing_account_id = uuid4()

        # Mock database query to return None
        mock_db_session.query.return_value.filter.return_value.first.return_value = None

        # Should not raise error, just return
        notification_service.send_soft_warning(
            billing_account_id=billing_account_id,
            resource_type=ResourceType.STORAGE,
            usage_percentage=75.5,
            used=750.0,
            limit=1000.0,
        )

        # Should not create audit log if account not found
        assert mock_db_session.add.call_count == 0

    def test_send_hard_block_notification(self, notification_service, mock_db_session, billing_account):
        """Test sending hard block notification"""
        billing_account_id = billing_account.id
        resource_type = ResourceType.STORAGE
        usage_percentage = 100.0
        block_reason = "Quota exceeded"

        # Mock database query
        mock_db_session.query.return_value.filter.return_value.first.return_value = billing_account

        notification_service.send_hard_block_notification(
            billing_account_id=billing_account_id,
            resource_type=resource_type,
            usage_percentage=usage_percentage,
            block_reason=block_reason,
        )

        # Verify audit log was created
        mock_db_session.add.assert_called()
        mock_db_session.commit.assert_called()

    def test_send_quota_warning_all_resource_types(self, notification_service, mock_db_session, billing_account):
        """Test quota warnings for all resource types"""
        billing_account_id = billing_account.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = billing_account

        resource_types = [ResourceType.STORAGE, ResourceType.RETRIEVAL, ResourceType.TOKEN]

        for resource_type in resource_types:
            notification_service.send_soft_warning(
                billing_account_id=billing_account_id,
                resource_type=resource_type,
                usage_percentage=75.0,
                used=750.0,
                limit=1000.0,
            )

        # Should create audit log for each resource type
        assert mock_db_session.add.call_count == len(resource_types)

    @patch("server.billing.quota_notifications.print")
    def test_notification_logging(self, mock_print, notification_service, mock_db_session, billing_account):
        """Test that notifications are logged correctly"""
        billing_account_id = billing_account.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = billing_account

        notification_service.send_soft_warning(
            billing_account_id=billing_account_id,
            resource_type=ResourceType.STORAGE,
            usage_percentage=80.0,
            used=800.0,
            limit=1000.0,
        )

        # Verify print was called (notification logging)
        mock_print.assert_called()
        print_call = str(mock_print.call_args)
        assert "Soft warning" in print_call or "80.0%" in print_call

    def test_audit_log_creation(self, notification_service, mock_db_session, billing_account):
        """Test that audit logs are created with correct information"""
        from server.billing.models import AuditLog

        billing_account_id = billing_account.id
        mock_db_session.query.return_value.filter.return_value.first.return_value = billing_account

        notification_service.send_soft_warning(
            billing_account_id=billing_account_id,
            resource_type=ResourceType.STORAGE,
            usage_percentage=75.5,
            used=755.0,
            limit=1000.0,
        )

        # Verify audit log was added
        add_calls = mock_db_session.add.call_args_list
        audit_logs = [call[0][0] for call in add_calls if isinstance(call[0][0], AuditLog)]

        assert len(audit_logs) > 0
        audit_log = audit_logs[0]
        assert audit_log.billing_account_id == billing_account_id
        # Check that audit log has relevant fields set
        assert audit_log.event_type is not None or audit_log.details is not None
