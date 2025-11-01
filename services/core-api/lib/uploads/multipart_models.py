#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Mapping, Optional

DEFAULT_SESSION_TTL_SECONDS = 24 * 60 * 60
REFRESH_LOOKAHEAD_SECONDS = 300


def _utcnow() -> datetime:
    return datetime.utcnow()


@dataclass
class UploadedPart:
    part_number: int
    etag: str
    size: Optional[int] = None
    uploaded_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "part_number": self.part_number,
            "etag": self.etag,
            "size": self.size,
            "uploaded_at": self.uploaded_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UploadedPart":
        uploaded_at = data.get("uploaded_at")
        return cls(
            part_number=int(data["part_number"]),
            etag=str(data["etag"]),
            size=int(data["size"]) if data.get("size") is not None else None,
            uploaded_at=datetime.fromisoformat(str(uploaded_at)) if uploaded_at else _utcnow(),
        )


@dataclass
class MultipartUploadSession:
    session_id: str
    bucket: str
    key: str
    upload_id: str
    filename: Optional[str] = None
    content_type: Optional[str] = None
    status: str = "pending"
    part_size: Optional[int] = None
    part_count: Optional[int] = None
    total_size: Optional[int] = None
    metadata: Dict[str, str] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)
    initiated_by: Optional[str] = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)
    expires_at: Optional[datetime] = None
    parts: Dict[int, UploadedPart] = field(default_factory=dict)
    result_etag: Optional[str] = None
    result_location: Optional[str] = None
    completed_at: Optional[datetime] = None

    def __post_init__(self) -> None:
        if self.expires_at is None:
            self.expires_at = self.created_at + timedelta(seconds=DEFAULT_SESSION_TTL_SECONDS)

    def mark_started(
        self,
        *,
        upload_id: str,
        bucket: str,
        metadata: Mapping[str, str] | None = None,
        part_size: int | None = None,
        part_count: int | None = None,
        total_size: int | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> None:
        self.upload_id = upload_id
        self.bucket = bucket
        if metadata:
            self.metadata.update({str(k): str(v) for k, v in metadata.items()})
        if part_size is not None:
            self.part_size = part_size
        if part_count is not None:
            self.part_count = part_count
        if total_size is not None:
            self.total_size = total_size
        if filename is not None:
            self.filename = filename
        if content_type is not None:
            self.content_type = content_type
        self.status = "in_progress"
        self.updated_at = _utcnow()

    def register_part(self, part_number: int, etag: str, size: Optional[int] = None) -> None:
        self.parts[part_number] = UploadedPart(part_number=part_number, etag=etag, size=size)
        self.updated_at = _utcnow()

    def list_parts(self) -> list[dict[str, Any]]:
        return [part.to_dict() for part in sorted(self.parts.values(), key=lambda item: item.part_number)]

    def refresh(self, *, ttl_seconds: int | None = None) -> None:
        self.updated_at = _utcnow()
        if ttl_seconds:
            self.expires_at = self.updated_at + timedelta(seconds=ttl_seconds)

    @property
    def requires_refresh(self) -> bool:
        if not self.expires_at:
            return False
        return _utcnow() + timedelta(seconds=REFRESH_LOOKAHEAD_SECONDS) >= self.expires_at

    def progress(self) -> dict[str, Any]:
        uploaded_parts = len(self.parts)
        uploaded_bytes = sum(part.size or 0 for part in self.parts.values())
        total_parts = self.part_count
        if total_parts is None and self.total_size and self.part_size:
            total_parts = math.ceil(self.total_size / self.part_size)
        total_bytes = self.total_size
        percent_complete: Optional[float] = None
        if total_bytes:
            percent_complete = (min(uploaded_bytes, total_bytes) / total_bytes) * 100

        return {
            "uploaded_parts": uploaded_parts,
            "uploaded_bytes": uploaded_bytes,
            "total_parts": total_parts,
            "total_bytes": total_bytes,
            "percent_complete": percent_complete,
        }

    def mark_completed(self, *, etag: Optional[str], location: Optional[str]) -> None:
        self.status = "completed"
        self.completed_at = _utcnow()
        self.result_etag = etag
        self.result_location = location
        self.updated_at = self.completed_at

    def mark_aborted(self) -> None:
        self.status = "aborted"
        self.completed_at = _utcnow()
        self.updated_at = self.completed_at

    def is_active(self) -> bool:
        return self.status in {"pending", "in_progress"}

    def is_completed(self) -> bool:
        return self.status == "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "bucket": self.bucket,
            "key": self.key,
            "upload_id": self.upload_id,
            "filename": self.filename,
            "content_type": self.content_type,
            "status": self.status,
            "part_size": self.part_size,
            "part_count": self.part_count,
            "total_size": self.total_size,
            "metadata": self.metadata,
            "extra": self.extra,
            "initiated_by": self.initiated_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "parts": self.list_parts(),
            "result_etag": self.result_etag,
            "result_location": self.result_location,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MultipartUploadSession":
        created_at = datetime.fromisoformat(str(data.get("created_at", _utcnow().isoformat())))
        updated_at_raw = data.get("updated_at")
        updated_at = datetime.fromisoformat(str(updated_at_raw)) if updated_at_raw else created_at
        expires_at_raw = data.get("expires_at")
        expires_at = datetime.fromisoformat(str(expires_at_raw)) if expires_at_raw else None
        completed_at_raw = data.get("completed_at")
        completed_at = datetime.fromisoformat(str(completed_at_raw)) if completed_at_raw else None

        parts_payload = data.get("parts", []) or []
        parts = {int(item["part_number"]): UploadedPart.from_dict(item) for item in parts_payload}

        session = cls(
            session_id=str(data["session_id"]),
            bucket=str(data["bucket"]),
            key=str(data["key"]),
            upload_id=str(data["upload_id"]),
            filename=data.get("filename"),
            content_type=data.get("content_type"),
            status=str(data.get("status", "pending")),
            part_size=int(data["part_size"]) if data.get("part_size") is not None else None,
            part_count=int(data["part_count"]) if data.get("part_count") is not None else None,
            total_size=int(data["total_size"]) if data.get("total_size") is not None else None,
            metadata=dict(data.get("metadata", {})),
            extra=dict(data.get("extra", {})),
            initiated_by=data.get("initiated_by"),
            created_at=created_at,
            updated_at=updated_at,
            expires_at=expires_at,
            parts=parts,
            result_etag=data.get("result_etag"),
            result_location=data.get("result_location"),
            completed_at=completed_at,
        )
        return session
