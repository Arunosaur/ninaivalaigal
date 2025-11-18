#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Billing API Unit Tests
#
"""
Unit tests for server/billing/api.py

Tests FastAPI endpoints for billing system with mocked dependencies.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

try:
    from fastapi import HTTPException
    from fastapi.testclient import TestClient

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    HTTPException = None  # type: ignore
    TestClient = None  # type: ignore

from server.billing.models import ResourceType
from server.billing.quota_enforcement import QuotaStatus

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_usage_metering():
    """Mock UsageMeteringService"""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_quota_enforcement():
    """Mock QuotaEnforcementService"""
    mock = MagicMock()
    mock.check_quota_status.return_value = (QuotaStatus.OK, 50.0, None)
    mock.enforce_quota.return_value = (True, None)
    mock.get_quota_summary.return_value = {
        "storage": {"limit": 1000.0, "used": 500.0, "percentage": 50.0},
        "retrieval": {"limit": 10000.0, "used": 5000.0, "percentage": 50.0},
    }
    return mock


@pytest.fixture
def test_app():
    """Create FastAPI test app with billing router"""
    if not FASTAPI_AVAILABLE:
        pytest.skip("FastAPI not available")

    try:
        from fastapi import FastAPI

        from server.billing.api import router

        app = FastAPI()
        app.include_router(router)
        return app
    except ImportError:
        pytest.skip("FastAPI not available")


@pytest.fixture
def client(test_app, mock_usage_metering, mock_quota_enforcement):
    """Create test client with mocked dependencies"""
    if not FASTAPI_AVAILABLE or TestClient is None:
        pytest.skip("FastAPI not available")

    from server.billing.api import (
        get_quota_enforcement_service,
        get_usage_metering_service,
    )

    def override_usage_metering():
        return mock_usage_metering

    def override_quota_enforcement():
        return mock_quota_enforcement

    test_app.dependency_overrides[get_usage_metering_service] = override_usage_metering
    test_app.dependency_overrides[get_quota_enforcement_service] = override_quota_enforcement

    with TestClient(test_app) as client:
        yield client

    test_app.dependency_overrides.clear()


class TestQuotaStatusEndpoint:
    """Tests for GET /api/billing/accounts/{id}/quota/status"""

    def test_get_quota_status_success(self, client, mock_quota_enforcement):
        """Test successful quota status retrieval"""
        billing_account_id = uuid4()
        billing_period_id = uuid4()

        response = client.get(
            f"/api/billing/accounts/{billing_account_id}/quota/status",
            params={"billing_period_id": str(billing_period_id), "resource_type": "storage"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["billing_account_id"] == str(billing_account_id)
        assert data["resource_type"] == "storage"
        assert data["status"] == "ok"
        assert data["usage_percentage"] == 50.0
        assert data["has_block"] is False

        # Verify service was called correctly
        mock_quota_enforcement.check_quota_status.assert_called_once()
        call_args = mock_quota_enforcement.check_quota_status.call_args[0]
        assert call_args[0] == billing_account_id
        assert call_args[1] == billing_period_id
        assert call_args[2] == ResourceType.STORAGE

    def test_get_quota_status_invalid_resource_type(self, client):
        """Test quota status with invalid resource type"""
        billing_account_id = uuid4()
        billing_period_id = uuid4()

        response = client.get(
            f"/api/billing/accounts/{billing_account_id}/quota/status",
            params={"billing_period_id": str(billing_period_id), "resource_type": "invalid"},
        )

        assert response.status_code == 400
        assert "Invalid resource type" in response.json()["detail"]

    def test_get_quota_status_with_block(self, client, mock_quota_enforcement):
        """Test quota status when quota is blocked"""
        from server.billing.models import BlockLevel, QuotaBlock

        billing_account_id = uuid4()
        billing_period_id = uuid4()

        # Mock a soft block
        mock_block = MagicMock(spec=QuotaBlock)
        mock_block.block_level = BlockLevel.SOFT
        mock_block.reason = "Usage exceeded 80%"

        mock_quota_enforcement.check_quota_status.return_value = (QuotaStatus.BLOCKED, 85.0, mock_block)

        response = client.get(
            f"/api/billing/accounts/{billing_account_id}/quota/status",
            params={"billing_period_id": str(billing_period_id), "resource_type": "storage"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "blocked"
        assert data["has_block"] is True
        assert data["block_level"] == "soft"
        assert data["block_reason"] == "Usage exceeded 80%"


class TestQuotaSummaryEndpoint:
    """Tests for GET /api/billing/accounts/{id}/quota/summary"""

    def test_get_quota_summary_success(self, client, mock_quota_enforcement):
        """Test successful quota summary retrieval"""
        billing_account_id = uuid4()
        billing_period_id = uuid4()

        response = client.get(
            f"/api/billing/accounts/{billing_account_id}/quota/summary",
            params={"billing_period_id": str(billing_period_id)},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["billing_account_id"] == str(billing_account_id)
        assert "quotas" in data
        assert "storage" in data["quotas"]
        assert "retrieval" in data["quotas"]


class TestStorageUsageEndpoint:
    """Tests for POST /api/billing/accounts/{id}/usage/storage"""

    def test_record_storage_usage_success(self, client, mock_usage_metering, mock_quota_enforcement):
        """Test successful storage usage recording"""
        from datetime import datetime

        from server.billing.models import UsageEvent

        billing_account_id = uuid4()
        billing_period_id = uuid4()

        # Mock usage event
        mock_event = MagicMock(spec=UsageEvent)
        mock_event.id = uuid4()
        mock_event.created_at = datetime.utcnow()
        mock_usage_metering.record_storage_usage.return_value = mock_event

        response = client.post(
            f"/api/billing/accounts/{billing_account_id}/usage/storage",
            params={"billing_period_id": str(billing_period_id), "storage_gb": "10.5"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resource_type"] == "storage"
        assert data["quantity"] == 10.5
        assert "event_id" in data

        # Verify quota was checked before recording
        mock_quota_enforcement.enforce_quota.assert_called_once()
        # Verify usage was recorded
        mock_usage_metering.record_storage_usage.assert_called_once()

    def test_record_storage_usage_quota_exceeded(self, client, mock_quota_enforcement):
        """Test storage usage recording when quota is exceeded"""
        billing_account_id = uuid4()
        billing_period_id = uuid4()

        # Mock quota enforcement failure
        mock_quota_enforcement.enforce_quota.return_value = (False, "Quota exceeded")

        response = client.post(
            f"/api/billing/accounts/{billing_account_id}/usage/storage",
            params={"billing_period_id": str(billing_period_id), "storage_gb": "10.5"},
        )

        assert response.status_code == 429
        assert "Quota exceeded" in response.json()["detail"]


class TestRetrievalUsageEndpoint:
    """Tests for POST /api/billing/accounts/{id}/usage/retrieval"""

    def test_record_retrieval_usage_success(self, client, mock_usage_metering, mock_quota_enforcement):
        """Test successful retrieval usage recording"""
        from datetime import datetime

        from server.billing.models import UsageEvent

        billing_account_id = uuid4()
        billing_period_id = uuid4()

        # Mock usage event
        mock_event = MagicMock(spec=UsageEvent)
        mock_event.id = uuid4()
        mock_event.created_at = datetime.utcnow()
        mock_usage_metering.record_retrieval_usage.return_value = mock_event

        response = client.post(
            f"/api/billing/accounts/{billing_account_id}/usage/retrieval",
            params={"billing_period_id": str(billing_period_id), "retrieval_count": "100"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resource_type"] == "retrieval"
        assert data["quantity"] == 100.0

        mock_quota_enforcement.enforce_quota.assert_called_once()
        mock_usage_metering.record_retrieval_usage.assert_called_once()


class TestTokenUsageEndpoint:
    """Tests for POST /api/billing/accounts/{id}/usage/token"""

    def test_record_token_usage_success(self, client, mock_usage_metering, mock_quota_enforcement):
        """Test successful token usage recording"""
        from datetime import datetime

        from server.billing.models import UsageEvent

        billing_account_id = uuid4()
        billing_period_id = uuid4()

        # Mock usage event
        mock_event = MagicMock(spec=UsageEvent)
        mock_event.id = uuid4()
        mock_event.created_at = datetime.utcnow()
        mock_usage_metering.record_token_usage.return_value = mock_event

        response = client.post(
            f"/api/billing/accounts/{billing_account_id}/usage/token",
            params={"billing_period_id": str(billing_period_id), "token_count": "1000"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["resource_type"] == "token"
        assert data["quantity"] == 1000.0

        mock_quota_enforcement.enforce_quota.assert_called_once()
        mock_usage_metering.record_token_usage.assert_called_once()
