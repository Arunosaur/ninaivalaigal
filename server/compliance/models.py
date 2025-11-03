#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-074/SPEC-011: Compliance Database Models (Backward Compatibility)

This module re-exports models from gdpr_models.py and hipaa_models.py
for backward compatibility. New code should import directly from
gdpr_models or hipaa_models to avoid loading unnecessary models.

Status: Deprecated - Use gdpr_models or hipaa_models directly
Assigned To: Developer G
"""

# Re-export GDPR models
from .gdpr_models import (
    DataExport,
    DataSubjectRequest,
    DataSubjectRequestType,
    ExportFormat,
    ExportStatus,
    RequestStatus,
)

# Re-export HIPAA models
from .hipaa_models import HIPAAAuditLog, HIPAABreachIncident, HIPAAPHIDetection

__all__ = [
    # GDPR models
    "DataExport",
    "DataSubjectRequest",
    "DataSubjectRequestType",
    "ExportFormat",
    "ExportStatus",
    "RequestStatus",
    # HIPAA models
    "HIPAAAuditLog",
    "HIPAABreachIncident",
    "HIPAAPHIDetection",
]
