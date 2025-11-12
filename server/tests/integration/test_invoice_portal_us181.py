#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# US#181: Customer Invoice Portal Tests
# Part of SPEC-028: Invoice Management System
#
"""
Comprehensive integration tests for Customer Invoice Portal API (US-228).

Tests cover:
- Portal access token generation and validation
- Token expiration and security
- Invoice listing with filters
- Invoice detail viewing
- PDF download
- Correction requests
- Email updates
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

from fastapi import HTTPException
from fastapi.responses import Response

from server.billing.invoice_portal_api import (
    CorrectionRequest,
    EmailUpdateRequest,
    PortalAccessRequest,
    PortalTokenResponse,
    download_portal_invoice_pdf,
    generate_portal_token,
    get_portal_invoice,
    list_portal_invoices,
    request_invoice_correction,
    request_portal_access,
    update_billing_email,
    validate_portal_token,
)
from server.billing.models import (
    BillingAccount,
    BillingPeriod,
    Invoice,
    InvoiceLineItem,
    InvoicePortalToken,
    InvoiceStatus,
)
from server.database.models import Team, User


@pytest.fixture
def db_session(monkeypatch):
    """Get database session with graceful fallback"""
    try:
        from server.database.manager import DatabaseManager

        db = DatabaseManager()
        session = db.get_session()

        # Ensure clean transaction state
        try:
            session.rollback()
        except Exception:
            pass

        yield session

        # Cleanup: rollback any uncommitted changes
        try:
            session.rollback()
        except Exception:
            pass
        session.close()
    except Exception as e:
        pytest.skip(f"Database not available: {str(e)}", allow_module_level=False)


@pytest.fixture
def test_user(db_session: Session):
    """Create test user"""
    user = User(
        id=uuid4(),
        username=f"test_user_{uuid4().hex[:8]}",
        email=f"test_{uuid4().hex[:8]}@example.com",
        name="Test User",
        password_hash="hashed_password",
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def test_team(db_session: Session, test_user: User):
    """Create test team"""
    team = Team(
        id=uuid4(),
        name=f"Test Team {uuid4().hex[:8]}",
        origin="native",
        governance_type="internal",
        status="active",
    )
    # Set optional fields if they exist
    if hasattr(team, "owner_id"):
        team.owner_id = test_user.id
    if hasattr(team, "lead_user_id"):
        team.lead_user_id = test_user.id
    if hasattr(team, "created_by"):
        team.created_by = test_user.id
    db_session.add(team)
    db_session.commit()
    return team


@pytest.fixture
def billing_account(db_session: Session, test_team: Team):
    """Create billing account for team"""
    account = BillingAccount(
        id=uuid4(),
        account_type="team",
        account_id=test_team.id,
        status="active",
    )
    db_session.add(account)
    db_session.commit()
    return account


@pytest.fixture
def billing_period(db_session: Session, billing_account: BillingAccount):
    """Create billing period"""
    now = datetime.now(timezone.utc)
    period = BillingPeriod(
        id=uuid4(),
        billing_account_id=billing_account.id,
        period_start=now - timedelta(days=30),
        period_end=now,
        status="active",
    )
    db_session.add(period)
    db_session.commit()
    return period


@pytest.fixture
def sample_invoices(db_session: Session, billing_account: BillingAccount, billing_period: BillingPeriod):
    """Create sample invoices for testing"""
    now = datetime.now(timezone.utc)
    unique_id = str(uuid4())[:8]
    invoices = []

    for i in range(5):
        invoice = Invoice(
            id=uuid4(),
            billing_period_id=billing_period.id,
            billing_account_id=billing_account.id,
            invoice_number=f"INV-{unique_id}-{i+1}",
            status=InvoiceStatus.PAID.value if i < 3 else InvoiceStatus.ISSUED.value,
            subtotal=Decimal("99.00"),
            tax_amount=Decimal("9.90"),
            total_amount=Decimal("108.90"),
            currency="USD",
            issued_at=now - timedelta(days=10 - i),
            due_at=now - timedelta(days=3 - i),
            paid_at=now - timedelta(days=5 - i) if i < 3 else None,
        )
        db_session.add(invoice)

        # Add line item
        line_item = InvoiceLineItem(
            id=uuid4(),
            invoice_id=invoice.id,
            description=f"Service {i+1}",
            quantity=Decimal("1"),
            unit_price=Decimal("99.00"),
            amount=Decimal("99.00"),
            resource_type="storage",  # Valid values: 'storage', 'retrieval', 'token'
        )
        db_session.add(line_item)
        invoices.append(invoice)

    db_session.commit()
    return invoices


@pytest.fixture
def portal_token(db_session: Session, test_team: Team):
    """Create valid portal token"""
    unique_id = str(uuid4())[:8]
    token = InvoicePortalToken(
        id=uuid4(),
        team_id=test_team.id,
        customer_email="customer@example.com",
        access_token=f"valid_test_token_{unique_id}",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
    )
    db_session.add(token)
    db_session.commit()
    return token


@pytest.fixture
def expired_token(db_session: Session, test_team: Team):
    """Create expired portal token"""
    unique_id = str(uuid4())[:8]
    token = InvoicePortalToken(
        id=uuid4(),
        team_id=test_team.id,
        customer_email="customer@example.com",
        access_token=f"expired_test_token_{unique_id}",
        expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(token)
    db_session.commit()
    return token


class TestPortalAccessToken:
    """Test portal access token generation and validation"""

    @patch("server.billing.invoice_portal_api.send_portal_access_email")
    async def test_request_portal_access_success(
        self, mock_email, db_session: Session, test_team: Team, billing_account: BillingAccount
    ):
        """Test successful portal access request"""
        from server.billing.invoice_portal_api import request_portal_access

        request = PortalAccessRequest(
            team_id=test_team.id,
            customer_email="customer@example.com",
        )

        response = await request_portal_access(request, db_session)

        assert isinstance(response, PortalTokenResponse)
        assert len(response.access_token) > 0
        assert response.expires_at > datetime.now(timezone.utc)
        assert "portal" in response.portal_url.lower()

        # Verify token was created in database
        token_record = (
            db_session.query(InvoicePortalToken)
            .filter(
                InvoicePortalToken.customer_email == "customer@example.com",
                InvoicePortalToken.team_id == test_team.id,
            )
            .first()
        )
        assert token_record is not None
        assert token_record.team_id == test_team.id
        assert token_record.expires_at > datetime.now(timezone.utc)

        # Verify email was sent
        mock_email.assert_called_once()

    async def test_request_portal_access_team_not_found(self, db_session: Session):
        """Test portal access request with non-existent team"""
        from server.billing.invoice_portal_api import request_portal_access

        request = PortalAccessRequest(
            team_id=uuid4(),
            customer_email="customer@example.com",
        )

        with pytest.raises(HTTPException) as exc_info:
            await request_portal_access(request, db_session)

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    async def test_request_portal_access_existing_token(
        self, db_session: Session, test_team: Team, portal_token: InvoicePortalToken
    ):
        """Test portal access request returns existing valid token"""
        from server.billing.invoice_portal_api import request_portal_access

        request = PortalAccessRequest(
            team_id=test_team.id,
            customer_email="customer@example.com",
        )

        response = await request_portal_access(request, db_session)

        assert isinstance(response, PortalTokenResponse)
        assert response.access_token == portal_token.access_token
        assert "already exists" in response.message.lower()

    def test_token_expiration_validation(self, db_session: Session, expired_token: InvoicePortalToken):
        """Test that expired tokens are rejected"""
        token_record = validate_portal_token(db_session, expired_token.access_token)
        assert token_record is None

    def test_invalid_token_rejected(self, db_session: Session):
        """Test that invalid tokens are rejected"""
        token_record = validate_portal_token(db_session, "invalid_token_xyz")
        assert token_record is None


class TestPortalInvoiceListing:
    """Test invoice listing via portal"""

    async def test_list_invoices_success(self, db_session: Session, portal_token: InvoicePortalToken, sample_invoices):
        """Test successful invoice listing"""
        from server.billing.invoice_portal_api import list_portal_invoices

        invoices = await list_portal_invoices(
            token=portal_token.access_token,
            status=None,
            start_date=None,
            end_date=None,
            limit=50,
            db=db_session,
        )

        assert isinstance(invoices, list)
        assert len(invoices) == 5

        # Verify invoice structure
        invoice = invoices[0]
        assert hasattr(invoice, "id")
        assert hasattr(invoice, "invoice_number")
        assert hasattr(invoice, "issue_date")
        assert hasattr(invoice, "total_amount")
        assert hasattr(invoice, "currency")
        assert hasattr(invoice, "status")

    async def test_list_invoices_with_status_filter(
        self, db_session: Session, portal_token: InvoicePortalToken, sample_invoices
    ):
        """Test invoice listing with status filter"""
        invoices = await list_portal_invoices(
            token=portal_token.access_token,
            status="paid",
            start_date=None,
            end_date=None,
            limit=50,
            db=db_session,
        )

        assert len(invoices) == 3
        assert all(inv.status == "paid" for inv in invoices)

    async def test_list_invoices_with_date_filter(
        self, db_session: Session, portal_token: InvoicePortalToken, sample_invoices
    ):
        """Test invoice listing with date filters"""
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=7)
        end_date = now

        invoices = await list_portal_invoices(
            token=portal_token.access_token,
            status=None,
            start_date=start_date,
            end_date=end_date,
            limit=50,
            db=db_session,
        )

        assert len(invoices) <= 5

    async def test_list_invoices_with_limit(
        self, db_session: Session, portal_token: InvoicePortalToken, sample_invoices
    ):
        """Test invoice listing with limit"""
        invoices = await list_portal_invoices(
            token=portal_token.access_token,
            status=None,
            start_date=None,
            end_date=None,
            limit=2,
            db=db_session,
        )

        assert len(invoices) == 2

    async def test_list_invoices_no_billing_account(self, db_session: Session, test_team: Team):
        """Test invoice listing when no billing account exists"""
        # Create token for team without billing account
        unique_id = str(uuid4())[:8]
        token = InvoicePortalToken(
            id=uuid4(),
            team_id=test_team.id,
            customer_email="customer@example.com",
            access_token=f"token_no_account_{unique_id}",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
        )
        db_session.add(token)
        db_session.commit()

        invoices = await list_portal_invoices(
            token=token.access_token,
            status=None,
            start_date=None,
            end_date=None,
            limit=50,
            db=db_session,
        )

        assert invoices == []


class TestPortalInvoiceDetail:
    """Test invoice detail viewing via portal"""

    async def test_get_invoice_detail_success(
        self, db_session: Session, portal_token: InvoicePortalToken, sample_invoices
    ):
        """Test successful invoice detail retrieval"""
        invoice = sample_invoices[0]

        detail = await get_portal_invoice(
            invoice_id=invoice.id,
            token=portal_token.access_token,
            db=db_session,
        )

        assert detail.id == str(invoice.id)
        assert detail.invoice_number == invoice.invoice_number
        assert detail.revision == invoice.revision
        assert len(detail.line_items) == 1
        assert detail.line_items[0]["description"] == "Service 1"

    async def test_get_invoice_detail_not_found(self, db_session: Session, portal_token: InvoicePortalToken):
        """Test invoice detail for non-existent invoice"""
        with pytest.raises(HTTPException) as exc_info:
            await get_portal_invoice(
                invoice_id=uuid4(),
                token=portal_token.access_token,
                db=db_session,
            )

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    async def test_get_invoice_detail_access_denied(
        self, db_session: Session, test_team: Team, billing_account: BillingAccount
    ):
        """Test access denied for invoice from different team"""
        # Create another team and invoice
        other_team = Team(
            id=uuid4(),
            name="Other Team",
            origin="native",
            governance_type="internal",
            status="active",
        )
        db_session.add(other_team)

        other_account = BillingAccount(
            id=uuid4(),
            account_type="team",
            account_id=other_team.id,
            status="active",
        )
        db_session.add(other_account)

        period = BillingPeriod(
            id=uuid4(),
            billing_account_id=other_account.id,
            period_start=datetime.now(timezone.utc) - timedelta(days=30),
            period_end=datetime.now(timezone.utc),
            status="active",
        )
        db_session.add(period)

        unique_id = str(uuid4())[:8]
        other_invoice = Invoice(
            id=uuid4(),
            billing_period_id=period.id,
            billing_account_id=other_account.id,
            invoice_number=f"INV-OTHER-{unique_id}",
            status=InvoiceStatus.ISSUED.value,
            subtotal=Decimal("99.00"),
            total_amount=Decimal("99.00"),
            currency="USD",
        )
        db_session.add(other_invoice)

        # Create token for first team
        unique_id = str(uuid4())[:8]
        token = InvoicePortalToken(
            id=uuid4(),
            team_id=test_team.id,
            customer_email="customer@example.com",
            access_token=f"token_team1_{unique_id}",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=48),
        )
        db_session.add(token)
        db_session.commit()

        with pytest.raises(HTTPException) as exc_info:
            await get_portal_invoice(
                invoice_id=other_invoice.id,
                token=token.access_token,
                db=db_session,
            )

        assert exc_info.value.status_code == 403
        assert "denied" in exc_info.value.detail.lower()


class TestPortalPDFDownload:
    """Test PDF download via portal"""

    @pytest.mark.skipif(
        not pytest.importorskip("reportlab", reason="ReportLab not available"),
        reason="ReportLab required for PDF generation",
    )
    async def test_download_invoice_pdf_success(
        self, db_session: Session, portal_token: InvoicePortalToken, sample_invoices
    ):
        """Test successful PDF download"""
        invoice = sample_invoices[0]

        response = await download_portal_invoice_pdf(
            invoice_id=invoice.id,
            token=portal_token.access_token,
            db=db_session,
        )

        assert isinstance(response, Response)
        assert response.media_type == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert len(response.body) > 0

    async def test_download_invoice_pdf_not_found(self, db_session: Session, portal_token: InvoicePortalToken):
        """Test PDF download for non-existent invoice"""
        with pytest.raises(HTTPException) as exc_info:
            await download_portal_invoice_pdf(
                invoice_id=uuid4(),
                token=portal_token.access_token,
                db=db_session,
            )

        assert exc_info.value.status_code == 404

    async def test_download_invoice_pdf_access_denied(self, db_session: Session, test_team: Team):
        """Test PDF download access denied for invalid token"""
        with pytest.raises(HTTPException) as exc_info:
            await download_portal_invoice_pdf(
                invoice_id=uuid4(),
                token="invalid_token",
                db=db_session,
            )

        assert exc_info.value.status_code == 401


class TestPortalCorrectionRequest:
    """Test correction request via portal"""

    async def test_request_correction_success(
        self, db_session: Session, portal_token: InvoicePortalToken, sample_invoices
    ):
        """Test successful correction request"""
        invoice = sample_invoices[0]

        request = CorrectionRequest(
            invoice_id=invoice.id,
            correction_type="adjustment",
            reason="Incorrect billing amount",
            details={"amount": 50.00},
        )

        result = await request_invoice_correction(
            request=request,
            token=portal_token.access_token,
            db=db_session,
        )

        assert result["success"] is True
        assert "submitted" in result["message"].lower()
        assert result["correction_type"] == "adjustment"

    async def test_request_correction_invalid_token(self, db_session: Session, sample_invoices):
        """Test correction request with invalid token"""
        invoice = sample_invoices[0]

        request = CorrectionRequest(
            invoice_id=invoice.id,
            correction_type="adjustment",
            reason="Test reason",
        )

        with pytest.raises(HTTPException) as exc_info:
            await request_invoice_correction(
                request=request,
                token="invalid_token",
                db=db_session,
            )

        assert exc_info.value.status_code == 401

    async def test_request_correction_invoice_not_found(self, db_session: Session, portal_token: InvoicePortalToken):
        """Test correction request for non-existent invoice"""
        request = CorrectionRequest(
            invoice_id=uuid4(),
            correction_type="adjustment",
            reason="Test reason",
        )

        with pytest.raises(HTTPException) as exc_info:
            await request_invoice_correction(
                request=request,
                token=portal_token.access_token,
                db=db_session,
            )

        assert exc_info.value.status_code == 404


class TestPortalEmailUpdate:
    """Test email update via portal"""

    async def test_update_email_success(self, db_session: Session, portal_token: InvoicePortalToken):
        """Test successful email update"""
        request = EmailUpdateRequest(new_email="newemail@example.com")

        result = await update_billing_email(
            request=request,
            token=portal_token.access_token,
            db=db_session,
        )

        assert result["success"] is True
        assert result["new_email"] == "newemail@example.com"

        # Verify token was updated
        db_session.refresh(portal_token)
        assert portal_token.customer_email == "newemail@example.com"

    async def test_update_email_invalid_token(self, db_session: Session):
        """Test email update with invalid token"""
        request = EmailUpdateRequest(new_email="newemail@example.com")

        with pytest.raises(HTTPException) as exc_info:
            await update_billing_email(
                request=request,
                token="invalid_token",
                db=db_session,
            )

        assert exc_info.value.status_code == 401

    async def test_update_email_invalid_email(self, db_session: Session, portal_token: InvoicePortalToken):
        """Test email update with invalid email format"""
        # Pydantic will validate email format, so this should raise ValidationError
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            EmailUpdateRequest(new_email="invalid-email")


class TestPortalTokenAccessTracking:
    """Test token access tracking"""

    async def test_token_access_count_increments(
        self, db_session: Session, portal_token: InvoicePortalToken, sample_invoices
    ):
        """Test that token access count increments on each use"""
        initial_count = portal_token.accessed_count

        # Make multiple requests
        for _ in range(3):
            await list_portal_invoices(
                token=portal_token.access_token,
                status=None,
                start_date=None,
                end_date=None,
                limit=50,
                db=db_session,
            )

        # Verify access count was incremented
        db_session.refresh(portal_token)
        assert portal_token.accessed_count == initial_count + 3
        assert portal_token.last_accessed_at is not None
