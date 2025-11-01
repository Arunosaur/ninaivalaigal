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
import uuid
from typing import Any, Iterable, Mapping

import structlog
from ninaivalaigal_storage import (
    StorageMultipartError,
    create_storage_backend,
    get_default_storage_backend,
    load_storage_settings,
)

from .multipart_models import MultipartUploadSession
from .multipart_store import MultipartUploadSessionStore

logger = structlog.get_logger(__name__)


class MultipartUploadService:
    """Coordinate multipart upload workflow across storage and session store."""

    _REQUIRED_METHODS = {
        "create_multipart_upload",
        "generate_part_upload_url",
        "upload_part",
        "complete_multipart_upload",
        "abort_multipart_upload",
        "list_multipart_parts",
    }

    def __init__(
        self,
        *,
        backend: Any | None = None,
        store: MultipartUploadSessionStore | None = None,
        default_part_size: int = 5 * 1024 * 1024,
    ) -> None:
        self._backend = backend or self._resolve_backend()
        self._store = store or MultipartUploadSessionStore()
        self._default_part_size = default_part_size

    def _resolve_backend(self) -> Any:
        backend = get_default_storage_backend()
        self._validate_backend(backend)
        return backend

    def _validate_backend(self, backend: Any) -> None:
        missing = [name for name in self._REQUIRED_METHODS if not hasattr(backend, name)]
        if missing:
            raise RuntimeError(f"Storage backend missing multipart capabilities: {', '.join(missing)}")

    async def start_session(
        self,
        *,
        object_key: str,
        filename: str | None = None,
        content_type: str | None = None,
        metadata: Mapping[str, str] | None = None,
        acl: str | None = None,
        total_size: int | None = None,
        part_size: int | None = None,
        part_count: int | None = None,
        initiated_by: str | None = None,
        extra: Mapping[str, Any] | None = None,
        session_id: str | None = None,
    ) -> MultipartUploadSession:
        """Start a multipart upload and persist session metadata."""

        backend_response = self._backend.create_multipart_upload(
            object_key,
            content_type=content_type,
            metadata=metadata,
            acl=acl,
        )

        session_identifier = session_id or uuid.uuid4().hex
        derived_part_size = part_size or self._default_part_size
        derived_part_count = part_count
        if derived_part_count is None and total_size and derived_part_size:
            derived_part_count = math.ceil(total_size / derived_part_size)

        session = MultipartUploadSession(
            session_id=session_identifier,
            bucket=backend_response["bucket"],
            key=backend_response["key"],
            upload_id=backend_response["upload_id"],
            filename=filename,
            content_type=content_type,
            total_size=total_size,
            part_size=derived_part_size,
            part_count=derived_part_count,
            initiated_by=initiated_by,
            metadata={str(k): str(v) for k, v in (metadata or {}).items()},
            extra=dict(extra or {}),
        )
        session.mark_started(
            upload_id=backend_response["upload_id"],
            bucket=backend_response["bucket"],
            metadata=metadata,
            part_size=derived_part_size,
            part_count=derived_part_count,
            total_size=total_size,
            filename=filename,
            content_type=content_type,
        )

        await self._store.save(session)
        logger.debug("multipart session started", session_id=session.session_id, key=session.key)
        return session

    async def get_session(self, session_id: str, *, refresh_ttl: bool = True) -> MultipartUploadSession:
        session = await self._store.get(session_id)
        if not session:
            raise KeyError(f"Multipart session '{session_id}' not found")
        if refresh_ttl and session.requires_refresh:
            await self._store.save(session)
        return session

    async def generate_part_upload_url(
        self,
        session_id: str,
        part_number: int,
        *,
        expires_in: int | None = None,
        extra_params: Mapping[str, str] | None = None,
    ) -> str:
        session = await self.get_session(session_id)
        if not session.is_active():
            raise RuntimeError(f"Cannot generate part URL for session in state '{session.status}'")

        url = self._backend.generate_part_upload_url(
            session.key,
            session.upload_id,
            part_number,
            expires_in=expires_in,
            extra_params=extra_params,
        )
        return url

    async def register_uploaded_part(
        self,
        session_id: str,
        *,
        part_number: int,
        etag: str,
        size: int | None = None,
    ) -> MultipartUploadSession:
        session = await self.get_session(session_id)
        if not session.is_active():
            raise RuntimeError(f"Cannot register part on session in state '{session.status}'")
        session.register_part(part_number, etag, size)
        await self._store.save(session)
        logger.debug(
            "multipart part registered",
            session_id=session.session_id,
            part_number=part_number,
            etag=etag,
        )
        return session

    async def sync_remote_parts(self, session_id: str) -> Iterable[dict[str, Any]]:
        session = await self.get_session(session_id)
        try:
            parts = self._backend.list_multipart_parts(session.key, session.upload_id)
        except StorageMultipartError as err:
            logger.error("failed to list multipart parts", session_id=session_id, error=str(err))
            raise

        for part in parts:
            part_number = int(part.get("part_number") or part.get("PartNumber"))
            etag = str(part.get("etag") or part.get("ETag"))
            size = part.get("size") or part.get("Size")
            session.register_part(part_number, etag, size)

        await self._store.save(session)
        return parts

    async def complete_session(self, session_id: str) -> dict[str, Any]:
        session = await self.get_session(session_id)
        if session.status == "aborted":
            raise RuntimeError("Cannot complete an aborted multipart upload")
        if session.is_completed():
            return {
                "bucket": session.bucket,
                "key": session.key,
                "location": session.result_location,
                "etag": session.result_etag,
            }
        if not session.parts:
            raise RuntimeError("Cannot complete multipart upload without uploaded parts")

        ordered_parts = [
            {
                "PartNumber": part.part_number,
                "ETag": part.etag if str(part.etag).startswith('"') else f'"{part.etag}"',
            }
            for part in sorted(session.parts.values(), key=lambda p: p.part_number)
        ]
        result = self._backend.complete_multipart_upload(
            session.key,
            session.upload_id,
            ordered_parts,
        )

        session.mark_completed(etag=result.get("etag"), location=result.get("location"))
        await self._store.save(session)
        logger.debug("multipart session completed", session_id=session.session_id, result=result)
        return result

    async def abort_session(self, session_id: str) -> None:
        session = await self.get_session(session_id)
        try:
            self._backend.abort_multipart_upload(session.key, session.upload_id)
        except StorageMultipartError as err:
            logger.warning("abort multipart upload failed", session_id=session_id, error=str(err))
            raise
        finally:
            session.mark_aborted()
            await self._store.save(session)
            logger.debug("multipart session aborted", session_id=session.session_id)

    async def delete_session(self, session_id: str) -> None:
        await self._store.delete(session_id)

    async def get_uploaded_parts(self, session_id: str) -> list[dict[str, Any]]:
        session = await self.get_session(session_id)
        return session.list_parts()


def build_service_from_env() -> MultipartUploadService:
    """Factory helper used by FastAPI dependency wiring."""

    settings = load_storage_settings()
    backend = create_storage_backend(settings=settings)
    service = MultipartUploadService(backend=backend)
    return service
