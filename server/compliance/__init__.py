#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-074: GDPR Compliance Module

This module implements comprehensive GDPR (General Data Protection Regulation)
compliance tools for the platform.

Core Features:
- Data Subject Access Requests (DSAR)
- Right to Erasure (Right to be Forgotten)
- Data Portability (encrypted exports)
- GDPR-compliant Consent Management
- Data Processing Records (Article 30)
- Compliance Reporting

Status: Phase 2 - Complete
Assigned To: Developer G
"""

from .data_collector import GDPRDataCollector
from .export import EncryptedDataExporter
from .gdpr import GDPRComplianceManager

# Import GDPR models
from .gdpr_models import (
    DataExport,
    DataSubjectRequest,
    DataSubjectRequestType,
    ExportFormat,
    ExportStatus,
    RequestStatus,
)
from .hipaa import HIPAAComplianceManager, HIPAAViolationType, PHICategory

# Import HIPAA models
from .hipaa_models import HIPAAAuditLog, HIPAABreachIncident, HIPAAPHIDetection
from .hipaa_notifications import HIPAAEmailNotifier

__all__ = [
    "GDPRComplianceManager",
    "HIPAAComplianceManager",
    "HIPAAEmailNotifier",
    "EncryptedDataExporter",
    "GDPRDataCollector",
    "DataSubjectRequest",
    "DataExport",
    "DataSubjectRequestType",
    "RequestStatus",
    "ExportFormat",
    "ExportStatus",
    "HIPAAAuditLog",
    "HIPAABreachIncident",
    "HIPAAPHIDetection",
    "PHICategory",
    "HIPAAViolationType",
]
