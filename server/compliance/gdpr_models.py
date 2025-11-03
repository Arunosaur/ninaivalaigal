#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-074: GDPR Compliance Database Models

SQLAlchemy models for GDPR compliance tables:
- DataSubjectRequest - GDPR data subject requests
- DataExport - Encrypted data export tracking

Status: Phase 2 - Complete
Assigned To: Developer G
"""

import uuid
from datetime import datetime
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


class DataSubjectRequestType(Enum):
    """GDPR data subject request types"""

    ACCESS = "access"  # Article 15: Right of Access (DSAR)
    RECTIFICATION = "rectification"  # Article 16: Right to Rectification
    ERASURE = "erasure"  # Article 17: Right to Erasure ("Right to be Forgotten")
    RESTRICTION = "restriction"  # Article 18: Right to Restrict Processing
    PORTABILITY = "portability"  # Article 20: Right to Data Portability
    OBJECTION = "objection"  # Article 21: Right to Object


class RequestStatus(Enum):
    """Status of a data subject request"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIAL = "partial"  # Partial completion (e.g., some data retained due to legal obligations)
    REJECTED = "rejected"
    EXPIRED = "expired"  # Not processed within time limit


class ExportFormat(Enum):
    """Supported export formats"""

    JSON = "json"
    XML = "xml"
    CSV = "csv"


class ExportStatus(Enum):
    """Status of a data export"""

    PENDING = "pending"
    GENERATING = "generating"
    READY = "ready"
    EXPIRED = "expired"
    DOWNLOADED = "downloaded"
    FAILED = "failed"


class DataSubjectRequest(Base):
    """GDPR data subject request model"""

    __tablename__ = "data_subject_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    request_type = Column(
        String(50),
        nullable=False,
        comment="Type: access, rectification, erasure, portability, restriction, objection",
    )
    status = Column(
        String(50),
        nullable=False,
        server_default="pending",
        comment="Status: pending, in_progress, completed, partial, rejected, expired",
    )
    description = Column(Text, nullable=True, comment="Optional description or notes from user")
    response_data = Column(
        JSONB,
        nullable=True,
        comment="Response data (export_id, erasure_summary, retained_data_categories, etc.)",
    )
    rejection_reason = Column(Text, nullable=True, comment="Reason if request was rejected")
    retained_data_categories = Column(
        JSONB,
        nullable=True,
        comment="Categories of data retained (for partial erasures due to legal obligations)",
    )

    completed_at = Column(DateTime(timezone=True), nullable=True, comment="When request was completed")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    # Use backref - conflicts will be handled during mapper configuration
    user = relationship("User", backref="data_subject_requests")
    exports = relationship("DataExport", back_populates="request", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint(
            "request_type IN ('access', 'rectification', 'erasure', 'portability', 'restriction', 'objection')",
            name="check_request_type_valid",
        ),
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'partial', 'rejected', 'expired')",
            name="check_status_valid",
        ),
        {
            "comment": "GDPR data subject requests (DSAR, erasure, portability, etc.) - US#558, SPEC-074",
            "extend_existing": True,
        },
    )

    def __repr__(self):
        return f"<DataSubjectRequest(id={self.id}, user_id={self.user_id}, type={self.request_type}, status={self.status})>"


class DataExport(Base):
    """Encrypted data export model for GDPR Article 15 & 20"""

    __tablename__ = "data_exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("data_subject_requests.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Link to originating data subject request (if applicable)",
    )

    format = Column(
        String(50),
        nullable=False,
        comment="Export format: json, xml, csv",
    )
    status = Column(
        String(50),
        nullable=False,
        server_default="pending",
        comment="Status: pending, generating, ready, expired, downloaded, failed",
    )
    download_url = Column(String(500), nullable=True, comment="Secure download URL (expires after expiry period)")
    encryption_key_id = Column(
        String(255),
        nullable=True,
        comment="Identifier for encryption key used (not the key itself)",
    )
    file_size = Column(BigInteger, nullable=True, comment="Export file size in bytes")
    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When download link expires (default: 30 days per GDPR)",
    )
    downloaded_at = Column(DateTime(timezone=True), nullable=True, comment="When export was downloaded")
    error_message = Column(Text, nullable=True, comment="Error message if export generation failed")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", backref="data_exports")
    request = relationship("DataSubjectRequest", back_populates="exports")

    __table_args__ = (
        CheckConstraint("format IN ('json', 'xml', 'csv')", name="check_format_valid"),
        CheckConstraint(
            "status IN ('pending', 'generating', 'ready', 'expired', 'downloaded', 'failed')",
            name="check_export_status_valid",
        ),
        CheckConstraint("file_size >= 0 OR file_size IS NULL", name="check_file_size_non_negative"),
        {
            "comment": "Encrypted data exports for GDPR Article 15 (DSAR) and Article 20 (Portability) - US#558, SPEC-074",
            "extend_existing": True,
        },
    )

    def __repr__(self):
        return f"<DataExport(id={self.id}, user_id={self.user_id}, format={self.format}, status={self.status})>"
