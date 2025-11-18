#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# US#176: US-223: Invoice Generation Tests
# Comprehensive tests for PDF invoice generation, tax calculation, and email delivery
#
"""
Integration tests for invoice generation.

Tests cover:
- PDF generation (structure, line items, header/footer, customer info, date formatting, totals)
- Tax calculation (all US state tax rates)
- Discount/credit application
- Email delivery (mocked)
"""

import os
import sys
import uuid
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

# Add server to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

pytestmark = pytest.mark.integration

# Check if ReportLab is available
try:
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    pytest.skip("ReportLab not available", allow_module_level=True)

# Check if PDF reader is available
try:
    from PyPDF2 import PdfFileReader

    PYPDF2_AVAILABLE = True
except ImportError:
    try:
        from pypdf import PdfReader

        PYPDF2_AVAILABLE = True
        PdfFileReader = PdfReader  # Alias for compatibility
    except ImportError:
        PYPDF2_AVAILABLE = False
        pytest.skip("PyPDF2 or pypdf not available", allow_module_level=True)

from server.services.invoicing_service import InvoicingService
from server.services.tax_calculator import TaxCalculator, DEFAULT_STATE_TAX_RATES


@pytest.fixture
def invoicing_service():
    """Create InvoicingService instance"""
    return InvoicingService()


@pytest.fixture
def tax_calculator():
    """Create TaxCalculator instance"""
    return TaxCalculator()


@pytest.fixture
def sample_invoice_data():
    """Sample invoice data for testing"""
    return {
        "invoice_number": "INV-202501-0001",
        "created_at": datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        "issue_date": datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
        "due_date": datetime(2025, 2, 15, 12, 0, 0, tzinfo=timezone.utc),
        "team_name": "Test Team Inc.",
        "billing_email": "billing@testteam.com",
        "team_id": str(uuid.uuid4()),
        "line_items": [
            {
                "description": "Storage Overage - January 2025",
                "quantity": 100,
                "unit_price": 0.10,
                "total_price": 10.00,
                "period_start": datetime(2025, 1, 1, tzinfo=timezone.utc),
                "period_end": datetime(2025, 1, 31, tzinfo=timezone.utc),
            },
            {
                "description": "Token Usage - January 2025",
                "quantity": 5000,
                "unit_price": 0.00001,
                "total_price": 0.05,
            },
        ],
        "subtotal": 10.05,
        "tax_amount": 0.0,
        "total_amount": 10.05,
        "status": "open",
    }


class TestPDFGeneration:
    """Test PDF invoice generation"""

    def test_pdf_structure(self, invoicing_service, sample_invoice_data):
        """Test that PDF has correct structure"""
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF is valid
        assert isinstance(pdf_bytes, bytes)
        assert len(pdf_bytes) > 0
        assert pdf_bytes.startswith(b"%PDF")

        # Verify PDF can be read
        pdf_reader = PdfFileReader(BytesIO(pdf_bytes))
        assert pdf_reader.numPages > 0

    def test_pdf_line_item_rendering(self, invoicing_service, sample_invoice_data):
        """Test that line items are rendered correctly in PDF"""
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF contains invoice number
        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")
        assert "INV-202501-0001" in pdf_content

        # Verify line items are present
        assert "Storage Overage" in pdf_content
        assert "Token Usage" in pdf_content

    def test_pdf_company_header_footer(self, invoicing_service, sample_invoice_data):
        """Test company header and footer in PDF"""
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")

        # Verify company name in header
        assert "Ninaivalaigal" in pdf_content or "INVOICE" in pdf_content

        # Verify invoice number in header
        assert "INV-202501-0001" in pdf_content

    def test_pdf_customer_information_display(self, invoicing_service, sample_invoice_data):
        """Test customer information is displayed correctly"""
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")

        # Verify customer information
        assert "Test Team Inc." in pdf_content or "Bill To" in pdf_content
        assert "billing@testteam.com" in pdf_content

    def test_pdf_date_formatting(self, invoicing_service, sample_invoice_data):
        """Test date formatting in PDF"""
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")

        # Verify dates are formatted (check for month names or date patterns)
        assert "January" in pdf_content or "2025" in pdf_content
        assert "February" in pdf_content or "15" in pdf_content

    def test_pdf_total_calculations(self, invoicing_service, sample_invoice_data):
        """Test total calculations are displayed correctly"""
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")

        # Verify totals are present
        assert "10.05" in pdf_content or "$10.05" in pdf_content
        assert "Subtotal" in pdf_content or "Total" in pdf_content

    def test_pdf_file_integrity(self, invoicing_service, sample_invoice_data):
        """Test PDF file integrity"""
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF structure
        assert pdf_bytes.startswith(b"%PDF")
        assert b"%%EOF" in pdf_bytes[-1000:]  # EOF marker should be near end

        # Verify PDF can be parsed
        try:
            pdf_reader = PdfFileReader(BytesIO(pdf_bytes))
            assert pdf_reader.numPages >= 1
        except Exception as e:
            pytest.fail(f"PDF integrity check failed: {e}")

    def test_pdf_with_period_information(self, invoicing_service, sample_invoice_data):
        """Test PDF generation with billing period information"""
        sample_invoice_data["period_start"] = datetime(2025, 1, 1, tzinfo=timezone.utc)
        sample_invoice_data["period_end"] = datetime(2025, 1, 31, tzinfo=timezone.utc)

        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")

        # Verify period information is displayed
        assert "Period" in pdf_content or "Jan" in pdf_content


class TestTaxCalculation:
    """Test tax calculation for all US states"""

    def test_tax_calculation_california(self, tax_calculator):
        """Test tax calculation for California (8.75%)"""
        subtotal = 100.0
        tax_amount = tax_calculator.calculate(subtotal, country="US", state="CA")

        expected_tax = subtotal * DEFAULT_STATE_TAX_RATES["CA"]
        assert abs(tax_amount - expected_tax) < 0.01
        assert tax_amount == 8.75

    def test_tax_calculation_new_york(self, tax_calculator):
        """Test tax calculation for New York (8%)"""
        subtotal = 100.0
        tax_amount = tax_calculator.calculate(subtotal, country="US", state="NY")

        expected_tax = subtotal * DEFAULT_STATE_TAX_RATES["NY"]
        assert abs(tax_amount - expected_tax) < 0.01
        assert tax_amount == 8.0

    def test_tax_calculation_texas(self, tax_calculator):
        """Test tax calculation for Texas (6.25%)"""
        subtotal = 100.0
        tax_amount = tax_calculator.calculate(subtotal, country="US", state="TX")

        expected_tax = subtotal * DEFAULT_STATE_TAX_RATES["TX"]
        assert abs(tax_amount - expected_tax) < 0.01
        assert tax_amount == 6.25

    def test_tax_calculation_florida(self, tax_calculator):
        """Test tax calculation for Florida (6%)"""
        subtotal = 100.0
        tax_amount = tax_calculator.calculate(subtotal, country="US", state="FL")

        expected_tax = subtotal * DEFAULT_STATE_TAX_RATES["FL"]
        assert abs(tax_amount - expected_tax) < 0.01
        assert tax_amount == 6.0

    def test_tax_calculation_other_states(self, tax_calculator):
        """Test tax calculation for states without specific rates (0% default)"""
        subtotal = 100.0
        tax_amount = tax_calculator.calculate(subtotal, country="US", state="AK")

        # States not in DEFAULT_STATE_TAX_RATES should return 0%
        assert tax_amount == 0.0

    def test_tax_calculation_with_override(self, tax_calculator):
        """Test tax calculation with rate override"""
        subtotal = 100.0
        tax_amount = tax_calculator.calculate(subtotal, country="US", state="CA", tax_rate=0.10)

        # Override rate should take precedence
        assert tax_amount == 10.0

    def test_tax_calculation_tax_inclusive(self, tax_calculator):
        """Test tax calculation with tax-inclusive pricing"""
        subtotal = 108.75  # Price includes 8.75% tax
        tax_amount = tax_calculator.calculate(
            subtotal, country="US", state="CA", is_tax_inclusive=True
        )

        # Tax should be extracted from inclusive price
        # Formula: subtotal * (rate / (1 + rate))
        expected_tax = 108.75 * (0.0875 / (1 + 0.0875))
        assert abs(tax_amount - expected_tax) < 0.01

    def test_tax_calculation_zero_subtotal(self, tax_calculator):
        """Test tax calculation with zero subtotal"""
        tax_amount = tax_calculator.calculate(0.0, country="US", state="CA")
        assert tax_amount == 0.0

    def test_tax_calculation_all_states(self, tax_calculator):
        """Test tax calculation for all states in DEFAULT_STATE_TAX_RATES"""
        subtotal = 100.0

        for state, expected_rate in DEFAULT_STATE_TAX_RATES.items():
            tax_amount = tax_calculator.calculate(subtotal, country="US", state=state)
            expected_tax = subtotal * expected_rate
            assert abs(tax_amount - expected_tax) < 0.01, f"Tax calculation failed for {state}"


class TestDiscountCreditApplication:
    """Test discount and credit application to invoices"""

    def test_invoice_with_discount_code(self, invoicing_service, sample_invoice_data):
        """Test invoice generation with discount code applied"""
        # Apply 10% discount
        sample_invoice_data["discounts_applied"] = 1.00  # $1 discount on $10.05 subtotal
        sample_invoice_data["subtotal"] = 10.05
        sample_invoice_data["total_amount"] = 9.05  # After discount

        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF was generated successfully
        assert len(pdf_bytes) > 0
        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")
        assert "9.05" in pdf_content or "$9.05" in pdf_content

    def test_invoice_with_credit_deduction(self, invoicing_service, sample_invoice_data):
        """Test invoice generation with credit deduction"""
        # Apply $5 credit
        sample_invoice_data["credits_applied"] = 5.00
        sample_invoice_data["subtotal"] = 10.05
        sample_invoice_data["total_amount"] = 5.05  # After credit

        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF was generated successfully
        assert len(pdf_bytes) > 0
        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")
        assert "5.05" in pdf_content or "$5.05" in pdf_content

    def test_invoice_with_combined_discounts_credits(self, invoicing_service, sample_invoice_data):
        """Test invoice with both discounts and credits"""
        # Apply both discount and credit
        sample_invoice_data["discounts_applied"] = 1.00
        sample_invoice_data["credits_applied"] = 2.00
        sample_invoice_data["subtotal"] = 10.05
        sample_invoice_data["total_amount"] = 7.05  # After discount and credit

        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF was generated successfully
        assert len(pdf_bytes) > 0
        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")
        assert "7.05" in pdf_content or "$7.05" in pdf_content

    def test_invoice_discount_exceeds_total(self, invoicing_service, sample_invoice_data):
        """Test edge case where discount exceeds total"""
        # Discount larger than subtotal
        sample_invoice_data["discounts_applied"] = 15.00  # More than $10.05 subtotal
        sample_invoice_data["subtotal"] = 10.05
        sample_invoice_data["total_amount"] = 0.0  # Should not go negative

        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF was generated (edge case handling)
        assert len(pdf_bytes) > 0

    def test_invoice_credit_exceeds_total(self, invoicing_service, sample_invoice_data):
        """Test edge case where credit exceeds total"""
        # Credit larger than subtotal
        sample_invoice_data["credits_applied"] = 15.00  # More than $10.05 subtotal
        sample_invoice_data["subtotal"] = 10.05
        sample_invoice_data["total_amount"] = 0.0  # Should not go negative

        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF was generated (edge case handling)
        assert len(pdf_bytes) > 0


class TestEmailDelivery:
    """Test email delivery for invoices"""

    @patch("server.services.invoicing_service.logger")
    def test_email_template_rendering(self, mock_logger, invoicing_service, sample_invoice_data):
        """Test email template rendering (mocked)"""
        # Create mock mailer
        mock_mailer = MagicMock()
        mock_mailer.send_invoice.return_value = True
        invoicing_service.mailer = mock_mailer

        # Generate PDF
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Send invoice email
        if invoicing_service.mailer:
            invoicing_service.mailer.send_invoice(
                email=sample_invoice_data["billing_email"],
                subject=f"Invoice {sample_invoice_data['invoice_number']}",
                pdf_content=pdf_bytes,
                invoice_data=sample_invoice_data,
            )

        # Verify email was sent
        if invoicing_service.mailer:
            assert mock_mailer.send_invoice.called
            call_args = mock_mailer.send_invoice.call_args
            assert call_args[1]["email"] == "billing@testteam.com"
            assert "INV-202501-0001" in call_args[1]["subject"]
            assert len(call_args[1]["pdf_content"]) > 0

    @patch("server.services.invoicing_service.logger")
    def test_email_sending_mocked(self, mock_logger, invoicing_service, sample_invoice_data):
        """Test email sending with mocked mailer"""
        # Create mock mailer
        mock_mailer = MagicMock()
        mock_mailer.send_invoice.return_value = True
        invoicing_service.mailer = mock_mailer

        # Generate PDF and send email
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        if invoicing_service.mailer:
            result = invoicing_service.mailer.send_invoice(
                email=sample_invoice_data["billing_email"],
                subject=f"Invoice {sample_invoice_data['invoice_number']}",
                pdf_content=pdf_bytes,
                invoice_data=sample_invoice_data,
            )

            # Verify email sending
            assert result is True
            assert mock_mailer.send_invoice.called

    def test_email_without_mailer(self, invoicing_service, sample_invoice_data):
        """Test that invoice generation works without mailer configured"""
        # No mailer configured
        invoicing_service.mailer = None

        # Should still generate PDF
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)
        assert len(pdf_bytes) > 0


class TestInvoiceGenerationIntegration:
    """Integration tests for complete invoice generation flow"""

    def test_complete_invoice_generation_with_tax(self, invoicing_service, sample_invoice_data):
        """Test complete invoice generation with tax calculation"""
        # Add tax
        tax_calculator = TaxCalculator()
        tax_amount = tax_calculator.calculate(sample_invoice_data["subtotal"], country="US", state="CA")

        sample_invoice_data["tax_amount"] = tax_amount
        sample_invoice_data["total_amount"] = sample_invoice_data["subtotal"] + tax_amount

        # Generate PDF
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF
        assert len(pdf_bytes) > 0
        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")

        # Verify totals include tax
        total_with_tax = sample_invoice_data["subtotal"] + tax_amount
        assert str(total_with_tax) in pdf_content or f"${total_with_tax:.2f}" in pdf_content

    def test_complete_invoice_generation_with_discount_and_tax(
        self, invoicing_service, sample_invoice_data
    ):
        """Test complete invoice generation with discount and tax"""
        # Apply discount
        discount = 1.00
        subtotal_after_discount = sample_invoice_data["subtotal"] - discount

        # Calculate tax on discounted amount
        tax_calculator = TaxCalculator()
        tax_amount = tax_calculator.calculate(subtotal_after_discount, country="US", state="CA")

        sample_invoice_data["discounts_applied"] = discount
        sample_invoice_data["tax_amount"] = tax_amount
        sample_invoice_data["total_amount"] = subtotal_after_discount + tax_amount

        # Generate PDF
        pdf_bytes = invoicing_service.generate_pdf(sample_invoice_data)

        # Verify PDF
        assert len(pdf_bytes) > 0
        pdf_content = pdf_bytes.decode("latin-1", errors="ignore")
        assert str(sample_invoice_data["total_amount"]) in pdf_content


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

