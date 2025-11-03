#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-011/US-121: HIPAA Compliance Manager

Implements HIPAA (Health Insurance Portability and Accountability Act) compliance:
- PHI (Protected Health Information) detection and protection
- HIPAA audit trails
- Minimum necessary access enforcement
- Breach notification
- Business Associate Agreements (BAA) tracking

Status: Phase 1 - In Progress
Assigned To: Developer G
"""

import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PHICategory(Enum):
    """Categories of Protected Health Information (PHI)"""

    # Identifiers (18 types)
    NAMES = "names"
    DATES = "dates"  # Birth dates, admission dates, discharge dates, death dates
    TELEPHONE_NUMBERS = "telephone_numbers"
    FAX_NUMBERS = "fax_numbers"
    EMAIL_ADDRESSES = "email_addresses"
    SOCIAL_SECURITY_NUMBERS = "ssn"
    MEDICAL_RECORD_NUMBERS = "medical_record_numbers"
    HEALTH_PLAN_BENEFICIARY_NUMBERS = "health_plan_beneficiary_numbers"
    ACCOUNT_NUMBERS = "account_numbers"
    CERTIFICATE_LICENSE_NUMBERS = "certificate_license_numbers"
    VEHICLE_IDENTIFIERS = "vehicle_identifiers"
    DEVICE_IDENTIFIERS = "device_identifiers"
    WEB_URLS = "web_urls"
    IP_ADDRESSES = "ip_addresses"
    BIOMETRIC_IDENTIFIERS = "biometric_identifiers"
    FULL_FACE_PHOTOS = "full_face_photos"
    UNIQUE_IDENTIFIERS = "unique_identifiers"

    # Health Information
    DIAGNOSIS_CODES = "diagnosis_codes"
    TREATMENT_CODES = "treatment_codes"
    PRESCRIPTION_INFO = "prescription_info"
    LAB_RESULTS = "lab_results"
    MEDICAL_HISTORY = "medical_history"


class HIPAAViolationType(Enum):
    """Types of HIPAA violations"""

    UNAUTHORIZED_ACCESS = "unauthorized_access"
    IMPROPER_DISCLOSURE = "improper_disclosure"
    LACK_OF_ENCRYPTION = "lack_of_encryption"
    MISSING_AUDIT_TRAIL = "missing_audit_trail"
    BREACH_OF_PHI = "breach_of_phi"
    IMPROPER_DISPOSAL = "improper_disposal"
    LACK_OF_ACCESS_CONTROLS = "lack_of_access_controls"


class HIPAAComplianceManager:
    """
    HIPAA Compliance Manager

    Implements HIPAA compliance requirements for healthcare data protection.
    """

    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize HIPAA Compliance Manager.

        Args:
            db_session: SQLAlchemy database session
        """
        self.db_session = db_session
        logger.info("HIPAA Compliance Manager initialized")

    async def detect_phi(self, data: str) -> Dict[str, Any]:
        """
        Detect Protected Health Information (PHI) in data.

        HIPAA defines 18 types of identifiers that constitute PHI.

        Args:
            data: Data string to analyze

        Returns:
            Dictionary with detected PHI categories and locations
        """
        logger.info("Scanning data for PHI")

        detected_phi = {"has_phi": False, "categories": [], "locations": [], "risk_level": "low"}

        # Check for common PHI patterns
        import re

        # SSN pattern
        ssn_pattern = r"\b\d{3}-\d{2}-\d{4}\b|\b\d{9}\b"
        if re.search(ssn_pattern, data):
            detected_phi["has_phi"] = True
            detected_phi["categories"].append(PHICategory.SOCIAL_SECURITY_NUMBERS.value)
            detected_phi["risk_level"] = "high"

        # Medical record numbers (varied formats)
        mrn_pattern = r"\bMRN[:\s]+\d+\b|\bMedical\s+Record[:\s]+(?:\w+[:\s]+)?\d+\b"
        if re.search(mrn_pattern, data, re.IGNORECASE):
            detected_phi["has_phi"] = True
            detected_phi["categories"].append(PHICategory.MEDICAL_RECORD_NUMBERS.value)
            detected_phi["risk_level"] = "high"

        # Health plan beneficiary numbers
        hbn_pattern = r"\bHBN[:\s]?\d+\b|\bHealth\s+Plan[:\s]?\d+\b"
        if re.search(hbn_pattern, data, re.IGNORECASE):
            detected_phi["has_phi"] = True
            detected_phi["categories"].append(PHICategory.HEALTH_PLAN_BENEFICIARY_NUMBERS.value)

        # ICD-10 diagnosis codes (A00.0 to Z99.9)
        icd10_pattern = r"\b[A-Z]\d{2}\.?\d{0,2}\b"
        if re.search(icd10_pattern, data):
            detected_phi["has_phi"] = True
            detected_phi["categories"].append(PHICategory.DIAGNOSIS_CODES.value)

        # CPT treatment codes (5 digits)
        cpt_pattern = r"\b\d{5}\b"
        # Context check - if near medical terms
        medical_terms = ["procedure", "treatment", "therapy", "diagnosis", "examination"]
        if any(term in data.lower() for term in medical_terms):
            if re.search(cpt_pattern, data):
                detected_phi["has_phi"] = True
                detected_phi["categories"].append(PHICategory.TREATMENT_CODES.value)

        # Email addresses (could be patient email)
        email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        emails = re.findall(email_pattern, data)
        if emails:
            # Check if in healthcare context
            healthcare_domains = ["health", "medical", "hospital", "clinic", "physician"]
            for email in emails:
                if any(domain in email.lower() for domain in healthcare_domains):
                    detected_phi["has_phi"] = True
                    if PHICategory.EMAIL_ADDRESSES.value not in detected_phi["categories"]:
                        detected_phi["categories"].append(PHICategory.EMAIL_ADDRESSES.value)

        # Dates that could be birthdates (in healthcare context)
        date_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
        dates = re.findall(date_pattern, data)
        if dates and any(term in data.lower() for term in ["birth", "dob", "patient", "admission", "discharge"]):
            detected_phi["has_phi"] = True
            if PHICategory.DATES.value not in detected_phi["categories"]:
                detected_phi["categories"].append(PHICategory.DATES.value)

        # Phone numbers (could be patient contact)
        phone_pattern = r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b|\(\d{3}\)\s?\d{3}[-.\s]?\d{4}\b"
        if re.search(phone_pattern, data) and any(term in data.lower() for term in ["patient", "contact", "emergency"]):
            detected_phi["has_phi"] = True
            if PHICategory.TELEPHONE_NUMBERS.value not in detected_phi["categories"]:
                detected_phi["categories"].append(PHICategory.TELEPHONE_NUMBERS.value)

        logger.info(f"PHI detection complete: {len(detected_phi['categories'])} categories found")
        return detected_phi

    async def ensure_phi_protection(self, data: Dict[str, Any], user_id: UUID) -> Dict[str, Any]:
        """
        Ensure PHI in data is properly protected.

        Checks:
        - Encryption at rest and in transit
        - Access controls
        - Audit logging
        - Minimum necessary principle

        Args:
            data: Data containing potential PHI
            user_id: User accessing the data

        Returns:
            Protection status and recommendations
        """
        logger.info(f"Ensuring PHI protection for user {user_id}")

        # Detect PHI
        data_str = str(data)
        phi_detection = await self.detect_phi(data_str)

        protection_status = {
            "phi_detected": phi_detection["has_phi"],
            "categories": phi_detection["categories"],
            "protected": False,
            "recommendations": [],
        }

        if not phi_detection["has_phi"]:
            protection_status["protected"] = True
            return protection_status

        # Phase 1: Basic protection checks
        # In production, check:
        # - Encryption status
        # - Access controls
        # - Audit logging enabled

        protection_status["recommendations"] = [
            "Ensure data is encrypted at rest",
            "Use encrypted connections (TLS) for transmission",
            "Implement access controls (minimum necessary principle)",
            "Enable audit logging for all PHI access",
            "Store PHI only when necessary for business purposes",
        ]

        # For Phase 1, assume protected if encryption is used
        # (Would integrate with actual encryption/security checks)
        protection_status["protected"] = True  # Placeholder

        logger.info(f"PHI protection ensured: {len(protection_status['categories'])} PHI categories protected")
        return protection_status

    async def generate_hipaa_audit_trail(
        self,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[UUID] = None,
        phi_accessed: bool = False,
        phi_categories: Optional[List[str]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
    ) -> Dict[str, Any]:
        """
        Generate HIPAA-compliant audit trail.

        HIPAA requires logging:
        - Who accessed PHI
        - What PHI was accessed
        - When it was accessed
        - What action was performed
        - Whether access was authorized

        Args:
            user_id: User performing action
            action: Action performed (view, edit, delete, export)
            resource_type: Type of resource (memory, context, etc.)
            resource_id: ID of resource accessed
            phi_accessed: Whether PHI was accessed
            phi_categories: List of PHI categories accessed
            ip_address: IP address of access
            user_agent: User agent string
            success: Whether action was successful

        Returns:
            Audit trail record with database ID
        """
        logger.info(f"Generating HIPAA audit trail: {action} on {resource_type} by user {user_id}")

        if self.db_session:
            try:
                from uuid import uuid4

                from .hipaa_models import HIPAAAuditLog

                audit_log = HIPAAAuditLog(
                    id=uuid4(),
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    phi_accessed=phi_accessed,
                    phi_categories=phi_categories or [],
                    ip_address=ip_address,
                    user_agent=user_agent,
                    success=success,
                    compliance="HIPAA",
                )

                self.db_session.add(audit_log)
                self.db_session.commit()

                logger.info(f"HIPAA audit log saved to database: {audit_log.id}")

                return {
                    "id": str(audit_log.id),
                    "timestamp": (
                        audit_log.created_at.isoformat() if audit_log.created_at else datetime.utcnow().isoformat()
                    ),
                    "user_id": str(user_id),
                    "action": action,
                    "resource_type": resource_type,
                    "resource_id": str(resource_id) if resource_id else None,
                    "phi_accessed": phi_accessed,
                    "phi_categories": phi_categories or [],
                    "compliance": "HIPAA",
                    "retention_until": audit_log.retention_until.isoformat() if audit_log.retention_until else None,
                    "success": success,
                }
            except Exception as e:
                logger.error(f"Failed to save HIPAA audit log to database: {e}")
                self.db_session.rollback()
                # Fall through to return basic record

        # Fallback if database not available
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "phi_accessed": phi_accessed,
            "phi_categories": phi_categories or [],
            "compliance": "HIPAA",
            "retention_period_days": 2555,  # 7 years (HIPAA requirement)
            "success": success,
        }

        logger.info(f"HIPAA Audit (logged): {audit_record}")
        return audit_record

    async def enforce_minimum_necessary_access(
        self, user_id: UUID, requested_data: List[str], purpose: str
    ) -> Dict[str, Any]:
        """
        Enforce HIPAA minimum necessary access principle.

        Users should only access PHI necessary for their job function.

        Args:
            user_id: User requesting access
            requested_data: List of data fields/categories requested
            purpose: Purpose of access (treatment, payment, operations)

        Returns:
            Access decision and allowed fields
        """
        logger.info(f"Enforcing minimum necessary access for user {user_id}")

        # Phase 1: Basic implementation
        # In production, this would:
        # - Check user role/permissions
        # - Validate purpose against allowed purposes
        # - Filter data fields based on minimum necessary

        access_decision = {
            "allowed": True,
            "purpose_valid": True,
            "allowed_fields": requested_data,
            "restricted_fields": [],
            "reason": "Minimum necessary access granted",
        }

        # Validate purpose
        valid_purposes = ["treatment", "payment", "operations", "required_by_law"]
        if purpose.lower() not in valid_purposes:
            access_decision["allowed"] = False
            access_decision["purpose_valid"] = False
            access_decision["reason"] = f"Invalid purpose: {purpose}. Must be one of: {valid_purposes}"
            logger.warning(f"Access denied: Invalid purpose '{purpose}'")
            return access_decision

        # Phase 1: Basic filtering (placeholder)
        # In production, would filter based on:
        # - User role (e.g., billing can only see payment-related PHI)
        # - Context (e.g., specific patient case)
        # - Purpose (treatment vs payment vs operations)

        logger.info(f"Minimum necessary access granted: {len(access_decision['allowed_fields'])} fields")
        return access_decision

    async def detect_breach(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detect and assess potential HIPAA breach.

        Breach is unauthorized access/disclosure that compromises security or privacy of PHI.

        Args:
            incident_data: Incident details

        Returns:
            Breach assessment
        """
        logger.info("Assessing potential HIPAA breach")

        breach_assessment = {
            "is_breach": False,
            "risk_level": "low",
            "phi_affected": [],
            "notification_required": False,
            "notification_deadline": None,
            "recommendations": [],
        }

        # Phase 1: Basic breach detection
        # In production, would assess:
        # - Was PHI accessed?
        # - Was access authorized?
        # - Was encryption bypassed?
        # - How many records affected?

        phi_accessed = incident_data.get("phi_accessed", False)
        unauthorized = incident_data.get("unauthorized", False)
        encryption_bypassed = incident_data.get("encryption_bypassed", False)

        if phi_accessed and (unauthorized or encryption_bypassed):
            breach_assessment["is_breach"] = True
            breach_assessment["risk_level"] = "high"
            breach_assessment["notification_required"] = True
            breach_assessment["notification_deadline"] = (datetime.utcnow() + timedelta(days=60)).isoformat()
            breach_assessment["recommendations"] = [
                "Notify affected individuals within 60 days",
                "Notify HHS (Department of Health and Human Services) if >500 records",
                "Document breach and remediation steps",
                "Conduct risk assessment",
                "Implement additional safeguards",
            ]

        if breach_assessment["is_breach"]:
            logger.warning(f"HIPAA breach detected: {breach_assessment['risk_level']} risk")

        return breach_assessment

    async def generate_hipaa_compliance_report(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate HIPAA compliance report with database queries.

        Includes:
        - PHI access logs
        - Breach incidents
        - Access control compliance
        - Encryption status
        - BAA compliance

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report with actual statistics
        """
        logger.info(f"Generating HIPAA compliance report")

        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()

        report = {
            "report_period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
            "phi_access_events": 0,
            "breach_incidents": 0,
            "compliance_score": 0.0,
            "recommendations": [],
            "audit_log_summary": {},
            "breach_summary": {},
        }

        # Query database for actual statistics
        if self.db_session:
            try:
                from .hipaa_models import HIPAAAuditLog, HIPAABreachIncident

                # Count PHI access events
                phi_access_count = (
                    self.db_session.query(HIPAAAuditLog)
                    .filter(
                        HIPAAAuditLog.phi_accessed == True,
                        HIPAAAuditLog.created_at >= start_date,
                        HIPAAAuditLog.created_at <= end_date,
                    )
                    .count()
                )

                report["phi_access_events"] = phi_access_count

                # Count total audit events
                total_audit_events = (
                    self.db_session.query(HIPAAAuditLog)
                    .filter(HIPAAAuditLog.created_at >= start_date, HIPAAAuditLog.created_at <= end_date)
                    .count()
                )

                # Count breach incidents
                breach_count = (
                    self.db_session.query(HIPAABreachIncident)
                    .filter(HIPAABreachIncident.created_at >= start_date, HIPAABreachIncident.created_at <= end_date)
                    .count()
                )

                confirmed_breaches = (
                    self.db_session.query(HIPAABreachIncident)
                    .filter(
                        HIPAABreachIncident.is_breach == True,
                        HIPAABreachIncident.created_at >= start_date,
                        HIPAABreachIncident.created_at <= end_date,
                    )
                    .count()
                )

                report["breach_incidents"] = breach_count

                # Calculate compliance score
                # Base score: 100, deductions for:
                # - Missing audit logs
                # - Breaches
                # - Late notifications
                compliance_score = 100.0

                # Deduct for confirmed breaches
                compliance_score -= confirmed_breaches * 10.0

                # Check for overdue breach notifications
                overdue_breaches = (
                    self.db_session.query(HIPAABreachIncident)
                    .filter(
                        HIPAABreachIncident.notification_required == True,
                        HIPAABreachIncident.notification_deadline < datetime.utcnow(),
                        HIPAABreachIncident.notification_sent_at == None,
                    )
                    .count()
                )

                compliance_score -= overdue_breaches * 20.0

                # Ensure score doesn't go below 0
                compliance_score = max(0.0, compliance_score)

                report["compliance_score"] = compliance_score

                # Audit log summary
                report["audit_log_summary"] = {
                    "total_events": total_audit_events,
                    "phi_access_events": phi_access_count,
                    "successful_actions": self.db_session.query(HIPAAAuditLog)
                    .filter(
                        HIPAAAuditLog.success == True,
                        HIPAAAuditLog.created_at >= start_date,
                        HIPAAAuditLog.created_at <= end_date,
                    )
                    .count(),
                }

                # Breach summary
                report["breach_summary"] = {
                    "total_incidents": breach_count,
                    "confirmed_breaches": confirmed_breaches,
                    "notifications_required": self.db_session.query(HIPAABreachIncident)
                    .filter(
                        HIPAABreachIncident.notification_required == True,
                        HIPAABreachIncident.created_at >= start_date,
                        HIPAABreachIncident.created_at <= end_date,
                    )
                    .count(),
                    "notifications_sent": self.db_session.query(HIPAABreachIncident)
                    .filter(
                        HIPAABreachIncident.notification_sent_at != None,
                        HIPAABreachIncident.created_at >= start_date,
                        HIPAABreachIncident.created_at <= end_date,
                    )
                    .count(),
                    "overdue_notifications": overdue_breaches,
                }

                logger.info(f"Queried database: {phi_access_count} PHI accesses, {breach_count} incidents")

            except Exception as e:
                logger.error(f"Error querying database for compliance report: {e}")
                # Fall through to default recommendations

        # Generate recommendations
        recommendations = []

        if report.get("breach_summary", {}).get("overdue_notifications", 0) > 0:
            recommendations.append("URGENT: Send overdue breach notifications immediately")

        if report.get("breach_summary", {}).get("confirmed_breaches", 0) > 0:
            recommendations.append("Review and strengthen security controls to prevent future breaches")

        recommendations.extend(
            [
                "Maintain audit logs for 7 years (HIPAA requirement)",
                "Ensure all PHI is encrypted at rest and in transit",
                "Implement minimum necessary access controls",
                "Conduct regular breach risk assessments",
                "Maintain Business Associate Agreements (BAA)",
                "Review and update security policies regularly",
            ]
        )

        report["recommendations"] = recommendations

        logger.info(f"HIPAA compliance report generated: Score {report['compliance_score']}%")
        return report
