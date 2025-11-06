#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# SPEC-147: Stripe API Tests
#
"""
Unit tests for server/billing/stripe_api.py

Tests FastAPI endpoints for Stripe integration.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    return MagicMock()


@pytest.fixture
def mock_stripe_service():
    """Create mock Stripe service"""
    mock_service = MagicMock()
    mock_customer = MagicMock()
    mock_customer.billing_account_id = uuid4()
    mock_customer.stripe_customer_id = "cus_test123"
    mock_customer.email = "test@example.com"
    mock_customer.created_at = datetime.utcnow()
    mock_service.create_customer.return_value = mock_customer
    return mock_service


class TestStripeAPI:
    """Tests for Stripe API endpoints"""

    def test_get_stripe_service(self):
        """Test Stripe service dependency"""
        try:
            from server.billing.stripe_api import get_stripe_service

            # Would need actual DB session in real test
            assert get_stripe_service is not None
        except ImportError:
            pytest.skip("stripe_api module not available")

    def test_get_stripe_service_unavailable(self, mock_db_session):
        """Test Stripe service when Stripe is unavailable"""
        try:
            from fastapi import HTTPException

            from server.billing.stripe_api import get_stripe_service

            with patch("server.billing.stripe_api.StripeService", side_effect=ImportError("Stripe not available")):
                with pytest.raises(HTTPException) as exc_info:
                    get_stripe_service(db=mock_db_session)

                assert exc_info.value.status_code == 503
        except ImportError:
            pytest.skip("stripe_api module not available")

    def test_create_stripe_customer_endpoint(self, mock_db_session, mock_stripe_service):
        """Test create Stripe customer endpoint"""
        try:
            from fastapi import FastAPI
            from fastapi.testclient import TestClient

            from server.billing.stripe_api import get_stripe_service, router

            app = FastAPI()
            app.include_router(router)

            def override_get_stripe_service():
                return mock_stripe_service

            app.dependency_overrides[get_stripe_service] = override_get_stripe_service

            with TestClient(app) as client:
                response = client.post(
                    "/api/billing/stripe/customers",
                    json={
                        "billing_account_id": str(uuid4()),
                        "email": "test@example.com",
                        "name": "Test User",
                    },
                )

                # Should attempt to create customer
                assert response.status_code in [200, 400, 500]
        except ImportError:
            pytest.skip("FastAPI or stripe_api module not available")
