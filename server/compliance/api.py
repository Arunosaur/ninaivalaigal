#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-074: GDPR Compliance API Endpoints

FastAPI endpoints for GDPR compliance functionality:
- Data Subject Access Requests (DSAR)
- Right to Erasure
- Data Portability
- Request status tracking

Status: Phase 1 - In Progress
Assigned To: Developer G
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from database import DatabaseManager, User
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from auth import get_current_user

from .export import EncryptedDataExporter, ExportFormat
from .gdpr import DataSubjectRequestType, GDPRComplianceManager
from .gdpr_models import DataExport, DataSubjectRequest, ExportStatus, RequestStatus

logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(prefix="/api/v1/compliance", tags=["gdpr-compliance"])


# Pydantic Request/Response Models
class DSARRequest(BaseModel):
    """Request model for Data Subject Access Request (DSAR)"""

    description: Optional[str] = Field(None, description="Optional description or notes")


class ErasureRequest(BaseModel):
    """Request model for Right to Erasure"""

    description: Optional[str] = Field(None, description="Optional description or notes")
    confirm_erasure: bool = Field(..., description="Must be True to confirm erasure request")


class PortabilityRequest(BaseModel):
    """Request model for Data Portability"""

    format: str = Field("json", description="Export format: json, xml, csv")
    description: Optional[str] = Field(None, description="Optional description or notes")


class RectificationRequest(BaseModel):
    """Request model for Right to Rectification"""

    data_updates: dict = Field(..., description="Data fields to update")
    description: Optional[str] = Field(None, description="Optional description or notes")


class RestrictionRequest(BaseModel):
    """Request model for Right to Restrict Processing"""

    description: Optional[str] = Field(None, description="Reason for restriction request")


class ObjectionRequest(BaseModel):
    """Request model for Right to Object"""

    description: Optional[str] = Field(..., description="Reason for objecting to processing")


class DataSubjectRequestResponse(BaseModel):
    """Response model for data subject requests"""

    id: UUID
    user_id: UUID
    request_type: str
    status: str
    description: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]
    response_data: Optional[dict]
    rejection_reason: Optional[str]


class DataExportResponse(BaseModel):
    """Response model for data exports"""

    id: UUID
    user_id: UUID
    format: str
    status: str
    download_url: Optional[str]
    expires_at: Optional[datetime]
    file_size: Optional[int]
    created_at: datetime


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


def get_gdpr_manager(db_session: Session = Depends(get_db_session)):
    """Get GDPR Compliance Manager instance"""
    exporter = EncryptedDataExporter(db_session=db_session)
    return GDPRComplianceManager(db_session=db_session, export_manager=exporter)


def get_export_manager(db_session: Session = Depends(get_db_session)):
    """Get Encrypted Data Exporter instance"""
    return EncryptedDataExporter(db_session=db_session)


# GDPR Compliance Endpoints


@router.post("/dsar", response_model=DataSubjectRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_dsar(
    request_data: DSARRequest,
    current_user: User = Depends(get_current_user),
    gdpr_manager: GDPRComplianceManager = Depends(get_gdpr_manager),
):
    """
    Submit Data Subject Access Request (DSAR).

    GDPR Article 15: Right of Access
    Allows users to request all personal data held by the platform.

    Returns a request ID that can be used to track status.
    """
    try:
        request = await gdpr_manager.handle_data_subject_request(
            user_id=current_user.id, request_type=DataSubjectRequestType.ACCESS, description=request_data.description
        )

        return DataSubjectRequestResponse(
            id=request.id,
            user_id=request.user_id,
            request_type=request.request_type,
            status=request.status,
            description=request.description,
            created_at=request.created_at,
            completed_at=request.completed_at,
            response_data=request.response_data,
            rejection_reason=request.rejection_reason,
        )
    except Exception as e:
        logger.error(f"Error submitting DSAR for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to submit DSAR request: {str(e)}"
        )


@router.post("/erasure", response_model=DataSubjectRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_erasure(
    request_data: ErasureRequest,
    current_user: User = Depends(get_current_user),
    gdpr_manager: GDPRComplianceManager = Depends(get_gdpr_manager),
):
    """
    Submit Right to Erasure request ("Right to be Forgotten").

    GDPR Article 17: Right to Erasure
    Allows users to request deletion of all their personal data.

    WARNING: This action is irreversible. Some data may be retained
    due to legal obligations (e.g., financial records).
    """
    if not request_data.confirm_erasure:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm erasure by setting 'confirm_erasure' to True",
        )

    try:
        request = await gdpr_manager.handle_data_subject_request(
            user_id=current_user.id, request_type=DataSubjectRequestType.ERASURE, description=request_data.description
        )

        return DataSubjectRequestResponse(
            id=request.id,
            user_id=request.user_id,
            request_type=request.request_type,
            status=request.status,
            description=request.description,
            created_at=request.created_at,
            completed_at=request.completed_at,
            response_data=request.response_data,
            rejection_reason=request.rejection_reason,
        )
    except Exception as e:
        logger.error(f"Error submitting erasure request for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to submit erasure request: {str(e)}"
        )


@router.post("/portability", response_model=DataExportResponse, status_code=status.HTTP_201_CREATED)
async def request_data_portability(
    request_data: PortabilityRequest,
    current_user: User = Depends(get_current_user),
    export_manager: EncryptedDataExporter = Depends(get_export_manager),
):
    """
    Request Data Portability (encrypted export).

    GDPR Article 20: Right to Data Portability
    Allows users to receive their data in a machine-readable format.

    Supported formats: json, xml, csv
    """
    try:
        # Validate format
        try:
            export_format = ExportFormat(request_data.format.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid format: {request_data.format}. Supported: json, xml, csv",
            )

        export = await export_manager.create_export(user_id=current_user.id, format=export_format, expiry_days=30)

        return DataExportResponse(
            id=export.id,
            user_id=export.user_id,
            format=export.format,
            status=export.status,
            download_url=export.download_url,
            expires_at=export.expires_at,
            file_size=export.file_size,
            created_at=export.created_at,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating data export for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create data export: {str(e)}"
        )


@router.get("/requests/{request_id}", response_model=DataSubjectRequestResponse)
async def get_request_status(
    request_id: UUID,
    current_user: User = Depends(get_current_user),
    gdpr_manager: GDPRComplianceManager = Depends(get_gdpr_manager),
):
    """
    Get status of a data subject request.

    Returns the current status and any response data.
    """
    request = await gdpr_manager.get_request_status(request_id)

    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Request {request_id} not found")

    # Verify user owns this request
    if request.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this request")

    return DataSubjectRequestResponse(
        id=request.id,
        user_id=request.user_id,
        request_type=request.request_type,
        status=request.status,
        description=request.description,
        created_at=request.created_at,
        completed_at=request.completed_at,
        response_data=request.response_data,
        rejection_reason=request.rejection_reason,
    )


@router.get("/requests", response_model=List[DataSubjectRequestResponse])
async def list_user_requests(
    current_user: User = Depends(get_current_user),
    gdpr_manager: GDPRComplianceManager = Depends(get_gdpr_manager),
):
    """
    List all data subject requests for the current user.

    Returns a list of all GDPR requests (DSAR, erasure, etc.) submitted by the user.
    """
    requests = await gdpr_manager.list_user_requests(current_user.id)

    return [
        DataSubjectRequestResponse(
            id=req.id,
            user_id=req.user_id,
            request_type=req.request_type,
            status=req.status,
            description=req.description,
            created_at=req.created_at,
            completed_at=req.completed_at,
            response_data=req.response_data,
            rejection_reason=req.rejection_reason,
        )
        for req in requests
    ]


@router.get("/exports/{export_id}", response_model=DataExportResponse)
async def get_export_status(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    export_manager: EncryptedDataExporter = Depends(get_export_manager),
):
    """
    Get status of a data export.

    Returns the current status and download URL if ready.
    """
    export = await export_manager.get_export(export_id)

    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Export {export_id} not found")

    # Verify user owns this export
    if export.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this export")

    return DataExportResponse(
        id=export.id,
        user_id=export.user_id,
        format=export.format,
        status=export.status,
        download_url=export.download_url,
        expires_at=export.expires_at,
        file_size=export.file_size,
        created_at=export.created_at,
    )


@router.get("/exports/{export_id}/download")
async def download_export(
    export_id: UUID,
    current_user: User = Depends(get_current_user),
    export_manager: EncryptedDataExporter = Depends(get_export_manager),
):
    """
    Download encrypted data export.

    Returns the export file with appropriate headers.
    Downloads are tracked (downloaded_at timestamp updated).
    """
    export = await export_manager.get_export(export_id)

    if not export:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Export {export_id} not found")

    # Verify user owns this export
    if export.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to this export")

    # Check if export is ready
    if export.status != ExportStatus.READY.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Export is not ready. Current status: {export.status}"
        )

    # Check if expired
    if export.expires_at and export.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Export download link has expired")

    # Phase 2: Retrieve encrypted export from storage
    encrypted_data = await export_manager._retrieve_export(export_id)
    if not encrypted_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Export file not found in storage")

    # Phase 2: Decrypt export
    try:
        decrypted_data = await export_manager.decrypt_export(encrypted_data, export.encryption_key_id)
        decrypted_content = decrypted_data.decode("utf-8")
    except Exception as e:
        logger.error(f"Error decrypting export {export_id}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to decrypt export")

    # Update downloaded_at timestamp
    from database import DatabaseManager
    from sqlalchemy import text

    db = DatabaseManager()
    session = db.get_session()
    try:
        session.execute(
            text("UPDATE public.data_exports SET downloaded_at = CURRENT_TIMESTAMP WHERE id = :export_id"),
            {"export_id": export_id},
        )
        session.commit()
    finally:
        session.close()

    # Determine media type
    media_type_map = {"json": "application/json", "xml": "application/xml", "csv": "text/csv"}
    media_type = media_type_map.get(export.format, "application/octet-stream")

    from fastapi.responses import Response

    return Response(
        content=decrypted_content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="gdpr_export_{export_id}.{export.format}"'},
    )


@router.post("/rectification", response_model=DataSubjectRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_rectification(
    request_data: RectificationRequest,
    current_user: User = Depends(get_current_user),
    gdpr_manager: GDPRComplianceManager = Depends(get_gdpr_manager),
):
    """
    Submit Right to Rectification request.

    GDPR Article 16: Right to Rectification
    Allows users to correct inaccurate personal data.
    """
    try:
        # Phase 2: Pass data_updates to handler
        request = await gdpr_manager.handle_data_subject_request(
            user_id=current_user.id,
            request_type=DataSubjectRequestType.RECTIFICATION,
            description=request_data.description,
            data_updates=request_data.data_updates,
        )

        # Trigger processing
        request = await gdpr_manager._handle_rectification_request(request)

        return DataSubjectRequestResponse(
            id=request.id,
            user_id=request.user_id,
            request_type=request.request_type,
            status=request.status,
            description=request.description,
            created_at=request.created_at,
            completed_at=request.completed_at,
            response_data=request.response_data,
            rejection_reason=request.rejection_reason,
        )
    except Exception as e:
        logger.error(f"Error submitting rectification request for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit rectification request: {str(e)}",
        )


@router.post("/restriction", response_model=DataSubjectRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_restriction(
    request_data: RestrictionRequest,
    current_user: User = Depends(get_current_user),
    gdpr_manager: GDPRComplianceManager = Depends(get_gdpr_manager),
):
    """
    Submit Right to Restrict Processing request.

    GDPR Article 18: Right to Restrict Processing
    Allows users to temporarily halt data processing while data is preserved.
    """
    try:
        # Phase 2: Create and process restriction request
        request = await gdpr_manager.handle_data_subject_request(
            user_id=current_user.id,
            request_type=DataSubjectRequestType.RESTRICTION,
            description=request_data.description,
        )

        # Trigger processing
        request = await gdpr_manager._handle_restriction_request(request)

        return DataSubjectRequestResponse(
            id=request.id,
            user_id=request.user_id,
            request_type=request.request_type,
            status=request.status,
            description=request.description,
            created_at=request.created_at,
            completed_at=request.completed_at,
            response_data=request.response_data,
            rejection_reason=request.rejection_reason,
        )
    except Exception as e:
        logger.error(f"Error submitting restriction request for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to submit restriction request: {str(e)}"
        )


@router.post("/objection", response_model=DataSubjectRequestResponse, status_code=status.HTTP_201_CREATED)
async def submit_objection(
    request_data: ObjectionRequest,
    current_user: User = Depends(get_current_user),
    gdpr_manager: GDPRComplianceManager = Depends(get_gdpr_manager),
):
    """
    Submit Right to Object request.

    GDPR Article 21: Right to Object
    Allows users to object to processing of their personal data.

    For direct marketing objections, processing stops immediately (absolute right).
    For other processing, objection is recorded and evaluated.
    """
    try:
        # Phase 2: Create and process objection request
        request = await gdpr_manager.handle_data_subject_request(
            user_id=current_user.id, request_type=DataSubjectRequestType.OBJECTION, description=request_data.description
        )

        # Trigger processing
        request = await gdpr_manager._handle_objection_request(request)

        return DataSubjectRequestResponse(
            id=request.id,
            user_id=request.user_id,
            request_type=request.request_type,
            status=request.status,
            description=request.description,
            created_at=request.created_at,
            completed_at=request.completed_at,
            response_data=request.response_data,
            rejection_reason=request.rejection_reason,
        )
    except Exception as e:
        logger.error(f"Error submitting objection request for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to submit objection request: {str(e)}"
        )


@router.get("/reports", status_code=status.HTTP_200_OK)
async def get_gdpr_compliance_report(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    gdpr_manager: GDPRComplianceManager = Depends(get_gdpr_manager),
):
    """
    Get GDPR compliance report.

    US-121: AC6 - Generate comprehensive GDPR compliance report

    Returns compliance metrics including:
    - Data subject request statistics
    - SLA compliance rates
    - Export statistics
    - Overall compliance status

    Query Parameters:
    - start_date: Start date for report period (ISO format, default: 30 days ago)
    - end_date: End date for report period (ISO format, default: now)
    """
    try:
        report = await gdpr_manager.generate_gdpr_compliance_report(start_date=start_date, end_date=end_date)
        return report
    except Exception as e:
        logger.error(f"Error generating GDPR compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate compliance report: {str(e)}",
        )
