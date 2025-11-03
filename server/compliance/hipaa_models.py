#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-011/US-121: HIPAA Compliance Database Models

SQLAlchemy models for HIPAA compliance tables:
- HIPAAAuditLog - HIPAA audit trail logs (7-year retention)
- HIPAABreachIncident - Breach incident tracking
- HIPAAPHIDetection - PHI detection events

Status: Phase 3 - Complete
Assigned To: Developer G
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Import Base from main models to ensure consistency
try:
    from database.models import Base
except ImportError:
    # Fallback for when running from different paths
    try:
        from server.database.models import Base
    except ImportError:
        # Last resort - create new base (shouldn't happen in normal operation)
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()


class HIPAAAuditLog(Base):
    """HIPAA Audit Log Model
    Stores HIPAA-compliant audit trail records with 7-year retention requirement.
    Per 45 CFR 164.308(a)(1)(ii)(D) and 164.312(b).
    """

    __tablename__ = "hipaa_audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(50), nullable=False, comment="Action performed: view, edit, delete, export")
    resource_type = Column(String(100), nullable=False, comment="Type of resource: memory, context, etc.")
    resource_id = Column(UUID(as_uuid=True), nullable=True, comment="ID of resource accessed")
    phi_accessed = Column(Boolean, nullable=False, default=False, comment="Whether PHI was accessed")
    phi_categories = Column(JSONB, nullable=True, comment="PHI categories accessed")
    ip_address = Column(String(45), nullable=True, comment="IP address of access")
    user_agent = Column(String(500), nullable=True, comment="User agent string")
    success = Column(Boolean, nullable=False, default=True, comment="Whether action was successful")
    compliance = Column(String(20), nullable=False, default="HIPAA")
    retention_until = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.text("(CURRENT_TIMESTAMP + INTERVAL '7 years')"),
        comment="Retention until date (7 years per HIPAA)",
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    user = relationship("User", backref="hipaa_audit_logs")

    __table_args__ = {
        "comment": "HIPAA-compliant audit trail logs. Required 7-year retention per HIPAA regulations. - US#121, SPEC-011",
        "extend_existing": True,
    }

    def __repr__(self):
        return f"<HIPAAAuditLog(id={self.id}, user_id={self.user_id}, action={self.action}, phi_accessed={self.phi_accessed})>"


class HIPAABreachIncident(Base):
    """HIPAA Breach Incident Model
    Tracks breach incidents and manages notification requirements per 45 CFR 164.400-414.
    """

    __tablename__ = "hipaa_breach_incidents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    incident_type = Column(String(50), nullable=False, comment="Type: unauthorized_access, improper_disclosure, etc.")
    phi_affected = Column(JSONB, nullable=True, comment="PHI categories affected")
    risk_level = Column(String(20), nullable=False, default="low", comment="Risk level: low, medium, high, critical")
    is_breach = Column(Boolean, nullable=False, default=False, comment="Whether incident constitutes a breach")
    phi_records_affected = Column(Integer, nullable=True, comment="Number of PHI records affected")
    notification_required = Column(Boolean, nullable=False, default=False, comment="Whether notification is required")
    notification_deadline = Column(
        DateTime(timezone=True), nullable=True, comment="Deadline for breach notification (60 days)"
    )
    notification_sent_at = Column(DateTime(timezone=True), nullable=True, comment="When breach notification was sent")
    description = Column(Text, nullable=True, comment="Incident description")
    remediation_steps = Column(JSONB, nullable=True, comment="Remediation steps taken")
    status = Column(
        String(20), nullable=False, default="pending", comment="Status: pending, assessed, notified, resolved"
    )
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    assessed_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True, comment="When incident was resolved")

    # Relationships
    reporter = relationship("User", foreign_keys=[reported_by], backref="reported_hipaa_breaches")
    assessor = relationship("User", foreign_keys=[assessed_by], backref="assessed_hipaa_breaches")

    __table_args__ = {
        "comment": "HIPAA breach incident tracking and notification management - US#121, SPEC-011",
        "extend_existing": True,
    }

    def __repr__(self):
        return f"<HIPAABreachIncident(id={self.id}, incident_type={self.incident_type}, is_breach={self.is_breach}, status={self.status})>"


class HIPAAPHIDetection(Base):
    """HIPAA PHI Detection Model
    Tracks PHI detection events for compliance monitoring.
    """

    __tablename__ = "hipaa_phi_detections"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    resource_type = Column(String(100), nullable=False, comment="Type of resource scanned")
    resource_id = Column(UUID(as_uuid=True), nullable=True, comment="ID of resource scanned")
    has_phi = Column(Boolean, nullable=False, comment="Whether PHI was detected")
    phi_categories = Column(JSONB, nullable=True, comment="PHI categories detected")
    risk_level = Column(String(20), nullable=False, default="low", comment="Risk level: low, medium, high")
    detection_method = Column(String(50), nullable=True, comment="Method: pattern_matching, ml_model, manual_review")
    data_sample = Column(Text, nullable=True, comment="Sample of detected data (redacted)")
    protection_applied = Column(Boolean, nullable=False, default=False, comment="Whether protection was applied")
    detected_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    detector = relationship("User", backref="detected_hipaa_phi")

    __table_args__ = {
        "comment": "PHI detection events for compliance tracking - US#121, SPEC-011",
        "extend_existing": True,
    }

    def __repr__(self):
        return f"<HIPAAPHIDetection(id={self.id}, has_phi={self.has_phi}, risk_level={self.risk_level})>"
