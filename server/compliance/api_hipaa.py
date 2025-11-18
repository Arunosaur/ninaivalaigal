#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-011/US-121: HIPAA Compliance API Endpoints

FastAPI endpoints for HIPAA compliance functionality:
- PHI detection
- HIPAA audit trails
- Breach detection and notification
- Compliance reporting

Status: Phase 1 - In Progress
Assigned To: Developer G
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

try:
    from server.auth import get_current_user
    from server.database import DatabaseManager, User
except ImportError:
    # Fallback for different import paths
    try:
        from database import DatabaseManager, User

        from auth import get_current_user
    except ImportError:
        # Define stubs if imports fail
        def get_current_user():
            pass

        class User:
            id = None

        class DatabaseManager:
            def get_session(self):
                pass


from .hipaa import HIPAAComplianceManager, PHICategory
from .hipaa_notifications import HIPAAEmailNotifier

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/compliance/hipaa", tags=["hipaa-compliance"])


# Pydantic Request/Response Models
class PHIDetectionRequest(BaseModel):
    """Request model for PHI detection"""

    data: str = Field(..., description="Data to scan for PHI")


class PHIDetectionResponse(BaseModel):
    """Response model for PHI detection"""

    has_phi: bool
    categories: List[str]
    risk_level: str
    locations: List[Dict[str, Any]]


class PHIProtectionRequest(BaseModel):
    """Request model for PHI protection check"""

    data: Dict[str, Any] = Field(..., description="Data to check for PHI protection")


class PHIProtectionResponse(BaseModel):
    """Response model for PHI protection"""

    phi_detected: bool
    categories: List[str]
    protected: bool
    recommendations: List[str]


class AuditTrailRequest(BaseModel):
    """Request model for creating audit trail"""

    action: str = Field(..., description="Action performed (view, edit, delete, export)")
    resource_type: str = Field(..., description="Type of resource (memory, context, etc.)")
    resource_id: Optional[UUID] = None
    phi_accessed: bool = Field(default=False, description="Whether PHI was accessed")


class MinimumNecessaryRequest(BaseModel):
    """Request model for minimum necessary access"""

    requested_data: List[str] = Field(..., description="List of data fields requested")
    purpose: str = Field(..., description="Purpose of access (treatment, payment, operations)")


class MinimumNecessaryResponse(BaseModel):
    """Response model for minimum necessary access"""

    allowed: bool
    purpose_valid: bool
    allowed_fields: List[str]
    restricted_fields: List[str]
    reason: str


class BreachAssessmentRequest(BaseModel):
    """Request model for breach assessment"""

    incident_data: Dict[str, Any] = Field(..., description="Incident details")


class BreachAssessmentResponse(BaseModel):
    """Response model for breach assessment"""

    is_breach: bool
    risk_level: str
    phi_affected: List[str]
    notification_required: bool
    notification_deadline: Optional[str]
    recommendations: List[str]


class BreachNotificationRequest(BaseModel):
    """Request model for breach notification"""

    breach_incident_id: UUID = Field(..., description="ID of breach incident")
    affected_individuals: List[Dict[str, str]] = Field(
        ..., description="List of affected individuals with contact info"
    )
    notification_type: str = Field(default="individual", description="Type: individual, hhs, media")


# Database dependencies
def get_db():
    """Get DatabaseManager instance"""
    from database import DatabaseManager

    return DatabaseManager()


def get_db_session(db: DatabaseManager = Depends(get_db)):
    """Get SQLAlchemy database session"""
    session = db.get_session()
    try:
        yield session
    finally:
        session.close()


def get_hipaa_manager(db_session: Session = Depends(get_db_session)):
    """Get HIPAA Compliance Manager instance"""
    return HIPAAComplianceManager(db_session=db_session)


# HIPAA Compliance Endpoints


@router.post("/detect-phi", response_model=PHIDetectionResponse)
async def detect_phi(
    request_data: PHIDetectionRequest,
    current_user: User = Depends(get_current_user),
    hipaa_manager: HIPAAComplianceManager = Depends(get_hipaa_manager),
):
    """
    Detect Protected Health Information (PHI) in data.

    HIPAA defines 18 types of identifiers that constitute PHI.
    This endpoint scans data and identifies any PHI present.
    """
    try:
        detection_result = await hipaa_manager.detect_phi(request_data.data)

        return PHIDetectionResponse(
            has_phi=detection_result["has_phi"],
            categories=detection_result["categories"],
            risk_level=detection_result["risk_level"],
            locations=detection_result.get("locations", []),
        )
    except Exception as e:
        logger.error(f"Error detecting PHI: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to detect PHI: {str(e)}")


@router.post("/ensure-protection", response_model=PHIProtectionResponse)
async def ensure_phi_protection(
    request_data: PHIProtectionRequest,
    current_user: User = Depends(get_current_user),
    hipaa_manager: HIPAAComplianceManager = Depends(get_hipaa_manager),
):
    """
    Ensure PHI in data is properly protected.

    Checks encryption, access controls, audit logging, and minimum necessary principle.
    """
    try:
        protection_result = await hipaa_manager.ensure_phi_protection(request_data.data, current_user.id)

        return PHIProtectionResponse(
            phi_detected=protection_result["phi_detected"],
            categories=protection_result["categories"],
            protected=protection_result["protected"],
            recommendations=protection_result["recommendations"],
        )
    except Exception as e:
        logger.error(f"Error ensuring PHI protection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to ensure PHI protection: {str(e)}"
        )


@router.post("/audit-trail")
async def create_audit_trail(
    request_data: AuditTrailRequest,
    current_user: User = Depends(get_current_user),
    hipaa_manager: HIPAAComplianceManager = Depends(get_hipaa_manager),
):
    """
    Create HIPAA-compliant audit trail record.

    Logs who accessed PHI, when, and what action was performed.
    Required for HIPAA compliance.
    """
    try:
        audit_record = await hipaa_manager.generate_hipaa_audit_trail(
            user_id=current_user.id,
            action=request_data.action,
            resource_type=request_data.resource_type,
            resource_id=request_data.resource_id,
            phi_accessed=request_data.phi_accessed,
        )

        return {"success": True, "audit_record": audit_record, "message": "Audit trail created successfully"}
    except Exception as e:
        logger.error(f"Error creating audit trail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create audit trail: {str(e)}"
        )


@router.post("/minimum-necessary", response_model=MinimumNecessaryResponse)
async def enforce_minimum_necessary(
    request_data: MinimumNecessaryRequest,
    current_user: User = Depends(get_current_user),
    hipaa_manager: HIPAAComplianceManager = Depends(get_hipaa_manager),
):
    """
    Enforce HIPAA minimum necessary access principle.

    Users should only access PHI necessary for their job function.
    Returns allowed fields based on user role and purpose.
    """
    try:
        access_decision = await hipaa_manager.enforce_minimum_necessary_access(
            user_id=current_user.id, requested_data=request_data.requested_data, purpose=request_data.purpose
        )

        return MinimumNecessaryResponse(
            allowed=access_decision["allowed"],
            purpose_valid=access_decision["purpose_valid"],
            allowed_fields=access_decision["allowed_fields"],
            restricted_fields=access_decision["restricted_fields"],
            reason=access_decision["reason"],
        )
    except Exception as e:
        logger.error(f"Error enforcing minimum necessary access: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enforce minimum necessary access: {str(e)}",
        )


@router.get("/audit-trail")
async def get_audit_trail(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    hipaa_manager: HIPAAComplianceManager = Depends(get_hipaa_manager),
):
    """
    Get HIPAA audit trail.

    US-121: AC12 - Retrieve HIPAA-compliant audit trail records

    Returns audit trail records showing who accessed PHI, when, and what actions were performed.

    Query Parameters:
    - start_date: Start date for audit trail (ISO format, default: 30 days ago)
    - end_date: End date for audit trail (ISO format, default: now)
    """
    try:
        audit_trail = await hipaa_manager.generate_hipaa_audit_trail(
            user_id=current_user.id,
            action="view",
            resource_type="audit_trail",
            start_date=start_date,
            end_date=end_date,
        )
        return audit_trail
    except Exception as e:
        logger.error(f"Error retrieving HIPAA audit trail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve audit trail: {str(e)}",
        )


@router.post("/breach-assessment", response_model=BreachAssessmentResponse)
async def assess_breach(
    request_data: BreachAssessmentRequest,
    current_user: User = Depends(get_current_user),
    hipaa_manager: HIPAAComplianceManager = Depends(get_hipaa_manager),
):
    """
    Assess potential HIPAA breach.

    Determines if an incident constitutes a breach requiring notification.
    """
    try:
        breach_assessment = await hipaa_manager.detect_breach(request_data.incident_data)

        return BreachAssessmentResponse(
            is_breach=breach_assessment["is_breach"],
            risk_level=breach_assessment["risk_level"],
            phi_affected=breach_assessment["phi_affected"],
            notification_required=breach_assessment["notification_required"],
            notification_deadline=breach_assessment["notification_deadline"],
            recommendations=breach_assessment["recommendations"],
        )
    except Exception as e:
        logger.error(f"Error assessing breach: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to assess breach: {str(e)}"
        )


@router.get("/compliance-report")
async def get_compliance_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    hipaa_manager: HIPAAComplianceManager = Depends(get_hipaa_manager),
):
    """
    Generate HIPAA compliance report.

    Includes PHI access logs, breach incidents, and compliance score.
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        report = await hipaa_manager.generate_hipaa_compliance_report(start_date=start_dt, end_date=end_dt)

        return {"success": True, "report": report}
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate compliance report: {str(e)}"
        )


@router.post("/send-breach-notification")
async def send_breach_notification(
    request_data: BreachNotificationRequest,
    current_user: User = Depends(get_current_user),
    db_session: Session = Depends(get_db_session),
):
    """
    Send HIPAA breach notification emails.

    Sends individual notifications or HHS notification as required.
    """
    try:
        from .hipaa_models import HIPAABreachIncident
        from .hipaa_notifications import HIPAAEmailNotifier

        # Get breach incident
        breach_incident = (
            db_session.query(HIPAABreachIncident)
            .filter(HIPAABreachIncident.id == request_data.breach_incident_id)
            .first()
        )

        if not breach_incident:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Breach incident not found")

        # Prepare incident details
        incident_details = {
            "phi_records_affected": breach_incident.phi_records_affected,
            "is_breach": breach_incident.is_breach,
            "description": breach_incident.description,
            "created_at": breach_incident.created_at.isoformat() if breach_incident.created_at else None,
            "phi_affected": breach_incident.phi_affected,
        }

        # Send notification
        notifier = HIPAAEmailNotifier()
        result = await notifier.send_breach_notification(
            breach_incident_id=request_data.breach_incident_id,
            incident_details=incident_details,
            affected_individuals=request_data.affected_individuals,
            notification_type=request_data.notification_type,
        )

        # Update breach incident if notification sent
        if result.get("sent"):
            breach_incident.notification_sent_at = datetime.utcnow()
            breach_incident.status = "notified"
            db_session.commit()

        return {"success": result.get("sent", False), "notification_result": result}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending breach notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send breach notification: {str(e)}"
        )
