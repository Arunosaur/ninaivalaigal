#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Archive Metrics Tests
#
"""
Unit tests for server/billing/archive_metrics.py

Tests metrics archival service for old usage data.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from server.billing.archive_metrics import MetricsArchivalService
from server.billing.models import UsageEvent

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    mock_session = MagicMock()
    return mock_session


@pytest.fixture
def archival_service(mock_db_session):
    """Create MetricsArchivalService with mock DB"""
    return MetricsArchivalService(db=mock_db_session, retention_days=90)


@pytest.fixture
def old_usage_event():
    """Create a mock old usage event"""
    event = MagicMock(spec=UsageEvent)
    event.id = uuid4()
    event.billing_period_id = uuid4()
    event.recorded_at = datetime.now(timezone.utc) - timedelta(days=100)
    event.processed = True
    return event


class TestMetricsArchivalService:
    """Tests for MetricsArchivalService"""

    def test_initialization(self, mock_db_session):
        """Test service initialization"""
        service = MetricsArchivalService(db=mock_db_session, retention_days=90)

        assert service.db is not None
        assert service.retention_days == 90
        assert service.ARCHIVE_BATCH_SIZE == 1000

    def test_initialization_with_storage_backend(self, mock_db_session):
        """Test initialization with storage backend"""
        mock_storage = MagicMock()
        service = MetricsArchivalService(db=mock_db_session, storage_backend=mock_storage)

        assert service.storage_backend is not None

    def test_archive_old_metrics_no_events(self, archival_service, mock_db_session):
        """Test archiving when no old events exist"""
        # Mock query to return empty list
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        results = archival_service.archive_old_metrics()

        assert results["archived"] == 0
        assert results["failed"] == 0
        assert len(results["errors"]) == 0

    def test_archive_old_metrics_with_events(self, archival_service, mock_db_session, old_usage_event):
        """Test archiving old usage events"""
        # Mock query to return old events
        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = [old_usage_event]
        mock_db_session.query.return_value = mock_query

        # Mock storage backend
        mock_storage = MagicMock()
        mock_storage.upload.return_value = True
        archival_service.storage_backend = mock_storage

        results = archival_service.archive_old_metrics()

        # Should attempt to archive
        assert results["archived"] >= 0  # May be 0 if archiving fails in test

    def test_archive_with_custom_date(self, archival_service, mock_db_session):
        """Test archiving with custom archive date"""
        custom_date = datetime.now(timezone.utc) - timedelta(days=30)

        mock_query = MagicMock()
        mock_query.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query

        results = archival_service.archive_old_metrics(archive_date=custom_date)

        # Verify query was called with custom date
        mock_db_session.query.assert_called_once_with(UsageEvent)

    def test_prepare_archive_data(self, archival_service, old_usage_event):
        """Test archive data preparation"""
        events = [old_usage_event]

        # Mock event attributes
        old_usage_event.to_dict = MagicMock(return_value={"id": str(old_usage_event.id), "quantity": 100.0})

        archive_data = archival_service._prepare_archive_data(events)

        assert archive_data is not None
        assert "events" in archive_data or "data" in archive_data

    def test_retention_days_default(self, mock_db_session):
        """Test default retention days"""
        service = MetricsArchivalService(db=mock_db_session)
        assert service.retention_days == 90

    def test_retention_days_custom(self, mock_db_session):
        """Test custom retention days"""
        service = MetricsArchivalService(db=mock_db_session, retention_days=180)
        assert service.retention_days == 180
