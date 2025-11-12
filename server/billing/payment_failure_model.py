#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# US#185: Payment Failure Model
# Database model for tracking payment failures
#
"""
Payment Failure Model

Tracks payment failures for invoices with retry logic.
"""

import uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from server.database.models import Base


class PaymentFailure(Base):
    """
    US#185: Payment failure tracking

    Tracks payment failures for invoices with retry logic and resolution status.
    """

    __tablename__ = "payment_failures"
    __table_args__ = ({"comment": "US#185: Payment failure tracking"},)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    billing_account_id = Column(
        UUID(as_uuid=True), ForeignKey("billing_accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    failure_date = Column(DateTime(timezone=True), nullable=False, index=True)
    failure_reason = Column(Text, nullable=False)
    retry_count = Column(Integer, nullable=False, server_default="0")
    next_retry_date = Column(DateTime(timezone=True), nullable=True, index=True)
    is_resolved = Column(Boolean, nullable=False, server_default="false", index=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    failure_metadata = Column(
        "metadata", Text, nullable=True
    )  # Additional failure details (column name kept as 'metadata' for DB compatibility)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

    # Relationships
    invoice = relationship("Invoice", backref="payment_failures")
    billing_account = relationship("BillingAccount", backref="payment_failures")

    def __repr__(self):
        return f"<PaymentFailure(id={self.id}, invoice_id={self.invoice_id}, retry_count={self.retry_count})>"
