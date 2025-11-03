#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""Multipart upload HTTP endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from auth_utils import get_current_user
from dependencies import get_rate_limiter, get_upload_service
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from security.audit import SecurityEventType, security_alert_manager
from uploads import MultipartUploadService

if TYPE_CHECKING:  # pragma: no cover - imported only for type hints
    from redis_client import RateLimiter

router = APIRouter(prefix="/upload/multipart", tags=["uploads"])


RATE_LIMITS: dict[str, dict[str, int]] = {
    "multipart:start": {"limit": 5, "window": 60},
    "multipart:part-url": {"limit": 300, "window": 60},
    "multipart:register": {"limit": 600, "window": 60},
    "multipart:complete": {"limit": 30, "window": 60},
    "multipart:abort": {"limit": 30, "window": 60},
    "multipart:status": {"limit": 120, "window": 60},
}


class StartUploadRequest(BaseModel):
    object_key: str = Field(..., min_length=1)
    filename: str | None = Field(default=None, max_length=512)
    content_type: str | None = Field(default=None, max_length=255)
    metadata: Dict[str, str] | None = None
    total_size: int | None = Field(default=None, ge=0)
    part_size: int | None = Field(default=None, ge=5 * 1024 * 1024)
    part_count: int | None = Field(default=None, ge=1)
    acl: str | None = None
    initiated_by: str | None = None


class PartUrlRequest(BaseModel):
    part_number: int = Field(..., ge=1)
    expires_in: int | None = Field(default=None, ge=60, le=24 * 3600)
    extra_params: Dict[str, str] | None = None


class RegisterPartRequest(BaseModel):
    part_number: int = Field(..., ge=1)
    etag: str = Field(..., min_length=1)
    size: int | None = Field(default=None, ge=0)


def _to_iso(value) -> str | None:
    return value.isoformat() if value else None


def _extract_user_id(current_user: Dict[str, Any]) -> str:
    user_id = current_user.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication context")
    return str(user_id)


def _user_id_as_int(user_id: str) -> int | None:
    try:
        return int(user_id)
    except (TypeError, ValueError):  # pragma: no cover - non-numeric IDs allowed
        return None


async def _enforce_rate_limit(
    rate_limiter: "RateLimiter",
    user_id: str,
    endpoint: str,
) -> None:
    spec = RATE_LIMITS.get(endpoint, {"limit": 100, "window": 60})
    allowed, meta = await rate_limiter.is_allowed(user_id, endpoint, limit=spec["limit"], window=spec["window"])
    if allowed:
        return

    await security_alert_manager.log_security_event(
        SecurityEventType.RATE_LIMIT_EXCEEDED,
        user_id=_user_id_as_int(user_id),
        metadata={
            "endpoint": endpoint,
            "limit": spec["limit"],
            "window": spec["window"],
            "reset_at": meta.get("reset_at"),
        },
    )
    raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_multipart_upload(
    request: StartUploadRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limiter: "RateLimiter" = Depends(get_rate_limiter),
    service: MultipartUploadService = Depends(get_upload_service),
):
    """Initiate a new multipart upload session."""

    user_id = _extract_user_id(current_user)
    await _enforce_rate_limit(rate_limiter, user_id, "multipart:start")

    try:
        session = await service.start_session(
            object_key=request.object_key,
            filename=request.filename,
            content_type=request.content_type,
            metadata=request.metadata,
            acl=request.acl,
            total_size=request.total_size,
            part_size=request.part_size,
            part_count=request.part_count,
            initiated_by=request.initiated_by or user_id,
        )
    except Exception as exc:  # pragma: no cover - bubbled errors should be rare
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return {
        "session_id": session.session_id,
        "upload_id": session.upload_id,
        "bucket": session.bucket,
        "key": session.key,
        "status": session.status,
        "part_size": session.part_size,
        "part_count": session.part_count,
        "expires_at": _to_iso(session.expires_at),
    }


@router.post("/{session_id}/part-url", status_code=status.HTTP_200_OK)
async def get_part_upload_url(
    session_id: str,
    request: PartUrlRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limiter: "RateLimiter" = Depends(get_rate_limiter),
    service: MultipartUploadService = Depends(get_upload_service),
):
    """Get a presigned URL for uploading a specific part."""

    user_id = _extract_user_id(current_user)
    await _enforce_rate_limit(rate_limiter, user_id, "multipart:part-url")

    try:
        url = await service.get_part_upload_url(
            session_id,
            part_number=request.part_number,
            expires_in=request.expires_in,
            extra_params=request.extra_params,
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return {"upload_url": url, "part_number": request.part_number, "expires_in": request.expires_in}


@router.post("/{session_id}/parts", status_code=status.HTTP_200_OK)
async def register_uploaded_part(
    session_id: str,
    request: RegisterPartRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limiter: "RateLimiter" = Depends(get_rate_limiter),
    service: MultipartUploadService = Depends(get_upload_service),
):
    """Register a successfully uploaded part."""

    user_id = _extract_user_id(current_user)
    await _enforce_rate_limit(rate_limiter, user_id, "multipart:register")

    try:
        session = await service.register_part(
            session_id,
            part_number=request.part_number,
            etag=request.etag,
            size=request.size,
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return {
        "success": True,
        "part_number": request.part_number,
        "parts_uploaded": len(session.parts),
    }


@router.post("/{session_id}/complete", status_code=status.HTTP_200_OK)
async def complete_multipart_upload(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limiter: "RateLimiter" = Depends(get_rate_limiter),
    service: MultipartUploadService = Depends(get_upload_service),
):
    """Finalize the multipart upload."""

    user_id = _extract_user_id(current_user)
    await _enforce_rate_limit(rate_limiter, user_id, "multipart:complete")

    try:
        result = await service.complete_session(session_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return {
        "success": True,
        "bucket": result.get("bucket"),
        "key": result.get("key"),
        "etag": result.get("etag"),
        "location": result.get("location"),
    }


@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
async def abort_multipart_upload(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limiter: "RateLimiter" = Depends(get_rate_limiter),
    service: MultipartUploadService = Depends(get_upload_service),
):
    """Cancel and cleanup a multipart upload."""

    user_id = _extract_user_id(current_user)
    await _enforce_rate_limit(rate_limiter, user_id, "multipart:abort")

    try:
        session = await service.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")

    try:
        await service.abort_session(session_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    await security_alert_manager.log_security_event(
        SecurityEventType.ADMIN_ACTION,
        user_id=_user_id_as_int(user_id),
        metadata={
            "action": "multipart_upload_abort",
            "session_id": session.session_id,
            "upload_id": session.upload_id,
            "bucket": session.bucket,
            "object_key": session.key,
        },
    )

    return {"success": True, "message": "Upload aborted"}


@router.get("/{session_id}/status", status_code=status.HTTP_200_OK)
async def get_upload_status(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rate_limiter: "RateLimiter" = Depends(get_rate_limiter),
    service: MultipartUploadService = Depends(get_upload_service),
):
    """Get current status and progress of the upload session."""

    user_id = _extract_user_id(current_user)
    await _enforce_rate_limit(rate_limiter, user_id, "multipart:status")

    try:
        session = await service.store.get(session_id)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")

    progress = session.progress()
    return {
        "session_id": session.session_id,
        "status": session.status,
        "progress": progress,
        "parts_uploaded": len(session.parts),
        "created_at": _to_iso(session.created_at),
        "updated_at": _to_iso(session.updated_at),
        "expires_at": _to_iso(session.expires_at),
    }
