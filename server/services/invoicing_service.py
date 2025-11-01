#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Shared Invoicing Service
Consolidates PDF generation from SPEC-027 and SPEC-028

Part of US#237: Create Shared InvoicingService Module
"""

import logging
import os
import time
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)

# Feature flag
USE_INVOICING_SERVICE = os.getenv("USE_INVOICING_SERVICE", "false").lower() == "true"

# ReportLab imports
try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available - PDF generation disabled")


class TaxCalculatorProtocol(Protocol):
    """Protocol for tax calculator dependency injection"""

    def calculate(
        self,
        subtotal: float,
        country: str = "US",
        state: Optional[str] = None,
        tax_rate: Optional[float] = None,
        is_tax_inclusive: bool = False,
    ) -> float:
        """Calculate tax amount"""
        ...


class MailerProtocol(Protocol):
    """Protocol for mailer dependency injection"""

    def send_invoice(self, email: str, subject: str, pdf_content: bytes, invoice_data: Dict[str, Any]) -> bool:
        """Send invoice email"""
        ...


class InvoicingService:
    """
    Shared invoicing service for PDF generation
    Consolidates logic from SPEC-027 and SPEC-028
    """

    def __init__(
        self,
        tax_calculator: Optional[TaxCalculatorProtocol] = None,
        mailer: Optional[MailerProtocol] = None,
    ):
        """
        Initialize invoicing service

        Args:
            tax_calculator: Tax calculator instance (optional, will create default if None)
            mailer: Email service instance (optional)
        """
        self.tax_calculator = tax_calculator
        self.mailer = mailer

        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available - PDF generation will fail")

    def generate_pdf(
        self,
        invoice_data: Dict[str, Any],
        tax_settings: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """
        Generate PDF invoice

        Uses SPEC-028's more comprehensive implementation as base

        Args:
            invoice_data: Invoice data dictionary with:
                - invoice_number: str
                - issue_date or created_at: datetime
                - due_date: datetime
                - team_name: str
                - billing_email: str
                - team_id: UUID or str
                - line_items: List[Dict] with description, quantity, unit_price, total_price
                - subtotal: float
                - tax_amount: float (optional, will calculate if not provided)
                - total_amount: float
                - period_start: datetime (optional)
                - period_end: datetime (optional)
                - status: str (optional)
                - paid_date: datetime (optional)
            tax_settings: Optional tax settings dict

        Returns:
            PDF bytes

        Raises:
            RuntimeError: If ReportLab not available
        """
        start_time = time.time()
        invoice_id = invoice_data.get("invoice_number", "unknown")
        team_id = str(invoice_data.get("team_id", "unknown"))

        logger.info(
            "Generating PDF invoice",
            extra={
                "invoice_id": invoice_id,
                "team_id": team_id,
            },
        )

        if not REPORTLAB_AVAILABLE:
            raise RuntimeError("PDF generation not available. Install reportlab package.")

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5 * inch)

        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#2563eb"),
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=14,
            spaceAfter=12,
            textColor=colors.HexColor("#1f2937"),
        )

        # Build PDF content
        content = []

        # Header
        content.append(Paragraph("INVOICE", title_style))
        content.append(Spacer(1, 20))

        # Company and invoice info
        issue_date = invoice_data.get("issue_date") or invoice_data.get("created_at")
        if isinstance(issue_date, str):
            issue_date = datetime.fromisoformat(issue_date)
        elif not isinstance(issue_date, datetime):
            issue_date = datetime.utcnow()

        due_date = invoice_data.get("due_date")
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)
        elif not isinstance(due_date, datetime):
            due_date = issue_date

        period_start = invoice_data.get("period_start")
        period_end = invoice_data.get("period_end")

        company_info = [
            ["<b>Ninaivalaigal</b>", f"<b>Invoice #:</b> {invoice_data.get('invoice_number', 'N/A')}"],
            [
                "Memory Management Platform",
                f"<b>Issue Date:</b> {issue_date.strftime('%B %d, %Y')}",
            ],
            [
                "support@ninaivalaigal.com",
                f"<b>Due Date:</b> {due_date.strftime('%B %d, %Y')}",
            ],
        ]

        if period_start and period_end:
            if isinstance(period_start, str):
                period_start = datetime.fromisoformat(period_start)
            if isinstance(period_end, str):
                period_end = datetime.fromisoformat(period_end)
            company_info.append(
                [
                    "",
                    f"<b>Period:</b> {period_start.strftime('%b %d')} - {period_end.strftime('%b %d, %Y')}",
                ]
            )

        company_table = Table(company_info, colWidths=[3 * inch, 3 * inch])
        company_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
        content.append(company_table)
        content.append(Spacer(1, 30))

        # Bill to
        content.append(Paragraph("<b>Bill To:</b>", heading_style))
        bill_to_info = [
            [invoice_data.get("team_name", "N/A")],
            [invoice_data.get("billing_email", "N/A")],
        ]

        if team_id and team_id != "unknown":
            bill_to_info.append([f"Team ID: {str(team_id)[:8]}..."])

        bill_to_table = Table(bill_to_info, colWidths=[6 * inch])
        bill_to_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        content.append(bill_to_table)
        content.append(Spacer(1, 20))

        # Line items
        content.append(Paragraph("<b>Services:</b>", heading_style))
        line_items_data = [["Description", "Period", "Quantity", "Unit Price", "Total"]]

        line_items = invoice_data.get("line_items", [])
        for item in line_items:
            # Handle different item formats
            if isinstance(item, dict):
                description = item.get("description", "")
                quantity = item.get("quantity", item.get("qty", 1))
                unit_price = item.get("unit_price", item.get("rate", 0.0))
                total_price = item.get("total_price", item.get("amount", unit_price * quantity))

                # Period if available
                period_str = ""
                if "period_start" in item and "period_end" in item:
                    ps = item["period_start"]
                    pe = item["period_end"]
                    if isinstance(ps, str):
                        ps = datetime.fromisoformat(ps)
                    if isinstance(pe, str):
                        pe = datetime.fromisoformat(pe)
                    period_str = f"{ps.strftime('%m/%d')} - {pe.strftime('%m/%d/%Y')}"

                line_items_data.append(
                    [
                        description,
                        period_str,
                        str(quantity),
                        f"${unit_price:.2f}",
                        f"${total_price:.2f}",
                    ]
                )

        line_items_table = Table(
            line_items_data,
            colWidths=[2.5 * inch, 1.5 * inch, 0.8 * inch, 1 * inch, 1 * inch],
        )
        line_items_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f3f4f6")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#374151")),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e5e7eb")),
                ]
            )
        )
        content.append(line_items_table)
        content.append(Spacer(1, 20))

        # Totals
        subtotal = invoice_data.get("subtotal", 0.0)
        tax_amount = invoice_data.get("tax_amount", 0.0)
        total_amount = invoice_data.get("total_amount", subtotal + tax_amount)

        totals_data = [["", "", "", "Subtotal:", f"${subtotal:.2f}"]]

        if tax_amount > 0:
            tax_label = "Tax"
            if tax_settings:
                tax_label = tax_settings.get("tax_name", "Tax")
            totals_data.append(["", "", "", f"{tax_label}:", f"${tax_amount:.2f}"])

        totals_data.append(["", "", "", "<b>Total:</b>", f"<b>${total_amount:.2f}</b>"])

        totals_table = Table(totals_data, colWidths=[2.5 * inch, 1.5 * inch, 0.8 * inch, 1 * inch, 1 * inch])
        totals_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LINEABOVE", (3, -1), (-1, -1), 2, colors.HexColor("#374151")),
                ]
            )
        )
        content.append(totals_table)
        content.append(Spacer(1, 30))

        # Payment info
        status = invoice_data.get("status", "pending")
        paid_date = invoice_data.get("paid_date")

        if status == "paid" and paid_date:
            if isinstance(paid_date, str):
                paid_date = datetime.fromisoformat(paid_date)
            content.append(
                Paragraph(
                    f"<b>Payment Status:</b> Paid on {paid_date.strftime('%B %d, %Y')}",
                    styles["Normal"],
                )
            )
        else:
            content.append(
                Paragraph(
                    "<b>Payment Terms:</b> Payment is due within 30 days of invoice date.",
                    styles["Normal"],
                )
            )

        content.append(Spacer(1, 10))
        content.append(
            Paragraph(
                "Thank you for your business! For questions about this invoice, " "contact support@ninaivalaigal.com",
                styles["Normal"],
            )
        )

        # Build PDF
        doc.build(content)
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()

        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "PDF invoice generated successfully",
            extra={
                "invoice_id": invoice_id,
                "team_id": team_id,
                "duration_ms": duration_ms,
                "pdf_size_bytes": len(pdf_bytes),
            },
        )

        return pdf_bytes

    def send_invoice_email(
        self,
        invoice_data: Dict[str, Any],
        pdf_content: bytes,
    ) -> bool:
        """
        Send invoice email

        Args:
            invoice_data: Invoice data
            pdf_content: PDF bytes

        Returns:
            True if sent successfully
        """
        if not self.mailer:
            logger.warning("No mailer configured - cannot send email")
            return False

        email = invoice_data.get("billing_email")
        subject = f"Invoice {invoice_data.get('invoice_number', '')} from ninaivalaigal"

        return self.mailer.send_invoice(email, subject, pdf_content, invoice_data)
