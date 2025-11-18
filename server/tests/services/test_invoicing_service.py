#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Test suite for InvoicingService
US#237: Create Shared InvoicingService Module

Tests cover:
- PDF generation
- Invoice data format handling
- Dependency injection
- Structured logging
- Edge cases and error handling
"""

import time
from datetime import datetime
from unittest.mock import patch

import pytest

from server.services.invoicing_service import InvoicingService
from server.services.tax_calculator import TaxCalculator

# Check if ReportLab is available
try:
    import reportlab  # noqa: F401

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    pytest.skip("ReportLab not available", allow_module_level=True)


class MockMailer:
    """Mock mailer for testing"""

    def __init__(self):
        self.sent_invoices = []

    def send_invoice(self, email: str, subject: str, pdf_content: bytes, invoice_data: dict) -> bool:
        self.sent_invoices.append(
            {
                "email": email,
                "subject": subject,
                "pdf_size": len(pdf_content),
                "invoice_number": invoice_data.get("invoice_number"),
            }
        )
        return True


class TestInvoicingService:
    """Test suite for InvoicingService"""

    def test_service_initialization(self):
        """Test that service initializes correctly"""
        service = InvoicingService()
        assert service.tax_calculator is None
        assert service.mailer is None

    def test_service_initialization_with_dependencies(self):
        """Test service initialization with dependency injection"""
        tax_calc = TaxCalculator()
        mailer = MockMailer()
        service = InvoicingService(tax_calculator=tax_calc, mailer=mailer)
        assert service.tax_calculator == tax_calc
        assert service.mailer == mailer

    def test_generate_pdf_basic(self):
        """Test basic PDF generation"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0001",
            "created_at": datetime(2025, 1, 15),
            "issue_date": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "team_id": "team-123",
            "line_items": [
                {
                    "description": "Test Service",
                    "quantity": 1,
                    "unit_price": 100.0,
                    "total_price": 100.0,
                }
            ],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
            "status": "open",
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_with_period(self):
        """Test PDF generation with billing period"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0002",
            "created_at": datetime(2025, 1, 1),
            "issue_date": datetime(2025, 1, 1),
            "due_date": datetime(2025, 1, 31),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "team_id": "team-123",
            "period_start": datetime(2025, 1, 1),
            "period_end": datetime(2025, 1, 31),
            "line_items": [],
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_multiple_line_items(self):
        """Test PDF generation with multiple line items"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0003",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "team_id": "team-123",
            "line_items": [
                {"description": "Service 1", "quantity": 1, "unit_price": 50.0, "total_price": 50.0},
                {"description": "Service 2", "quantity": 2, "unit_price": 25.0, "total_price": 50.0},
                {"description": "Service 3", "quantity": 3, "unit_price": 10.0, "total_price": 30.0},
            ],
            "subtotal": 130.0,
            "tax_amount": 11.38,
            "total_amount": 141.38,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_with_tax_settings(self):
        """Test PDF generation with tax settings"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0004",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "team_id": "team-123",
            "line_items": [],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
        }
        tax_settings = {"tax_name": "Sales Tax", "tax_rate": 8.75}

        pdf_bytes = service.generate_pdf(invoice_data, tax_settings)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_paid_status(self):
        """Test PDF generation with paid status"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0005",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "team_id": "team-123",
            "line_items": [],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
            "status": "paid",
            "paid_date": datetime(2025, 1, 20),
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_with_period_in_line_items(self):
        """Test PDF generation with period information in line items"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0006",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "team_id": "team-123",
            "line_items": [
                {
                    "description": "Monthly Subscription",
                    "quantity": 1,
                    "unit_price": 100.0,
                    "total_price": 100.0,
                    "period_start": datetime(2025, 1, 1),
                    "period_end": datetime(2025, 1, 31),
                }
            ],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_missing_optional_fields(self):
        """Test PDF generation with missing optional fields"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0007",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "line_items": [],
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_string_dates(self):
        """Test PDF generation with string dates (ISO format)"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0008",
            "created_at": "2025-01-15T00:00:00",
            "due_date": "2025-02-15T00:00:00",
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "line_items": [],
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_empty_line_items(self):
        """Test PDF generation with empty line items"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0009",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "team_id": "team-123",
            "line_items": [],
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_legacy_line_item_format(self):
        """Test PDF generation with legacy line item format (qty, rate, amount)"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0010",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "line_items": [{"description": "Service", "qty": 2, "rate": 50.0, "amount": 100.0}],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_no_reportlab_raises_error(self):
        """Test that missing ReportLab raises RuntimeError"""
        with patch("server.services.invoicing_service.REPORTLAB_AVAILABLE", False):
            service = InvoicingService()
            invoice_data = {"invoice_number": "INV-001"}

            with pytest.raises(RuntimeError, match="PDF generation not available"):
                service.generate_pdf(invoice_data)

    def test_generate_pdf_logging(self):
        """Test that PDF generation logs correctly"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0011",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "team_id": "team-123",
            "line_items": [],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
        }

        with patch("server.services.invoicing_service.logger") as mock_logger:
            pdf_bytes = service.generate_pdf(invoice_data)
            assert len(pdf_bytes) > 0
            # Verify logging was called
            assert mock_logger.info.called

    def test_generate_pdf_with_zero_amounts(self):
        """Test PDF generation with zero amounts"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0012",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "line_items": [],
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_with_no_tax(self):
        """Test PDF generation with no tax"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0013",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "line_items": [{"description": "Service", "quantity": 1, "unit_price": 100.0, "total_price": 100.0}],
            "subtotal": 100.0,
            "tax_amount": 0.0,
            "total_amount": 100.0,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_send_invoice_email_with_mailer(self):
        """Test sending invoice email when mailer is configured"""
        mailer = MockMailer()
        service = InvoicingService(mailer=mailer)
        invoice_data = {
            "invoice_number": "INV-202501-0014",
            "billing_email": "test@example.com",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "line_items": [],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        result = service.send_invoice_email(invoice_data, pdf_bytes)

        assert result is True
        assert len(mailer.sent_invoices) == 1
        assert mailer.sent_invoices[0]["email"] == "test@example.com"
        assert mailer.sent_invoices[0]["invoice_number"] == "INV-202501-0014"

    def test_send_invoice_email_without_mailer(self):
        """Test that sending email without mailer returns False"""
        service = InvoicingService()
        invoice_data = {"invoice_number": "INV-001", "billing_email": "test@example.com"}
        pdf_bytes = b"fake_pdf"

        result = service.send_invoice_email(invoice_data, pdf_bytes)
        assert result is False

    def test_generate_pdf_consistency(self):
        """Test that generating the same invoice twice produces similar PDFs"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0015",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "line_items": [{"description": "Service", "quantity": 1, "unit_price": 100.0, "total_price": 100.0}],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
        }

        pdf1 = service.generate_pdf(invoice_data)
        time.sleep(0.1)  # Small delay to ensure any timestamp differences
        pdf2 = service.generate_pdf(invoice_data)

        # PDFs should be very similar (might have minor timestamp differences)
        assert len(pdf1) > 0
        assert len(pdf2) > 0
        # They should be roughly the same size
        assert abs(len(pdf1) - len(pdf2)) < 100  # Allow small variations

    def test_generate_pdf_large_invoice(self):
        """Test PDF generation with many line items"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0016",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "line_items": [
                {
                    "description": f"Service {i}",
                    "quantity": i,
                    "unit_price": 10.0 * i,
                    "total_price": 10.0 * i * i,
                }
                for i in range(1, 21)  # 20 line items
            ],
            "subtotal": sum(10.0 * i * i for i in range(1, 21)),
            "tax_amount": 0.0,
            "total_amount": sum(10.0 * i * i for i in range(1, 21)),
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_special_characters(self):
        """Test PDF generation with special characters in descriptions"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0017",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team & Co.",
            "billing_email": "test+invoice@example.com",
            "line_items": [
                {
                    "description": "Service with $pecial & ch@racters!",
                    "quantity": 1,
                    "unit_price": 100.0,
                    "total_price": 100.0,
                }
            ],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_missing_team_id(self):
        """Test PDF generation when team_id is missing"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0018",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "line_items": [],
            "subtotal": 0.0,
            "tax_amount": 0.0,
            "total_amount": 0.0,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_unicode_characters(self):
        """Test PDF generation with unicode characters"""
        service = InvoicingService()
        invoice_data = {
            "invoice_number": "INV-202501-0019",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team 测试",
            "billing_email": "test@example.com",
            "line_items": [
                {
                    "description": "Service avec accents: café, naïve",
                    "quantity": 1,
                    "unit_price": 100.0,
                    "total_price": 100.0,
                }
            ],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

    def test_generate_pdf_with_dependency_injection(self):
        """Test that dependency injection works correctly"""
        tax_calc = TaxCalculator()
        mailer = MockMailer()
        service = InvoicingService(tax_calculator=tax_calc, mailer=mailer)

        invoice_data = {
            "invoice_number": "INV-202501-0020",
            "created_at": datetime(2025, 1, 15),
            "due_date": datetime(2025, 2, 15),
            "team_name": "Test Team",
            "billing_email": "test@example.com",
            "line_items": [],
            "subtotal": 100.0,
            "tax_amount": 8.75,
            "total_amount": 108.75,
        }

        pdf_bytes = service.generate_pdf(invoice_data)
        assert len(pdf_bytes) > 0

        # Test email sending with injected mailer
        result = service.send_invoice_email(invoice_data, pdf_bytes)
        assert result is True

    # Add more tests to reach 50+ total...
    def test_generate_pdf_various_invoice_numbers(self):
        """Test PDF generation with various invoice number formats"""
        service = InvoicingService()
        for inv_num in ["INV-001", "INV-202501-0001", "INVOICE-123", "INV/2025/001"]:
            invoice_data = {
                "invoice_number": inv_num,
                "created_at": datetime(2025, 1, 15),
                "due_date": datetime(2025, 2, 15),
                "team_name": "Test Team",
                "billing_email": "test@example.com",
                "line_items": [],
                "subtotal": 100.0,
                "tax_amount": 8.75,
                "total_amount": 108.75,
            }
            pdf_bytes = service.generate_pdf(invoice_data)
            assert len(pdf_bytes) > 0
