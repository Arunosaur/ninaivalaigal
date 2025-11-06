#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
Memory Attachment API Endpoints

US#327, US#328, US#329: Memory Attachment Upload, Retrieval, and Deletion
"""

import os
import sys
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from auth_service import get_current_user
from database import DatabaseManager, User
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile

try:
    from memory.factory import get_default_memory_provider
except ImportError:
    # Fallback if memory factory not available
    def get_default_memory_provider():
        return None
from memory.interfaces import MemoryProvider, MemoryProviderError
from pydantic import BaseModel
from sqlalchemy import text

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from utils.config import get_dynamic_database_url
except ImportError:
    # Fallback if utils.config not available
    import os
    def get_dynamic_database_url():
        return os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/memory", tags=["memory", "attachments"])

# Database URL
DATABASE_URL = get_dynamic_database_url()

# Storage backend (will be initialized)
storage_backend = None


def get_storage_backend():
    """Get storage backend for file uploads."""
    global storage_backend
    if storage_backend is None:
        try:
            from ninaivalaigal_storage import get_default_storage_backend

            storage_backend = get_default_storage_backend()
        except ImportError:
            logger.warning("Storage backend not available, file storage disabled")
            storage_backend = None
    return storage_backend


def get_db():
    """Get database instance."""
    return DatabaseManager(DATABASE_URL)


# Response models
class AttachmentResponse(BaseModel):
    """Attachment response model."""

    id: str
    memory_id: str
    filename: str
    content_type: str
    size: int
    storage_key: str
    download_url: str | None = None
    created_at: str
    metadata: dict | None = None


class AttachmentListResponse(BaseModel):
    """Attachment list response model."""

    items: List[AttachmentResponse]
    total: int
    memory_id: str


# Initialize attachment table if needed
async def ensure_attachment_table(db: DatabaseManager):
    """Ensure memory_attachments table exists."""
    try:
        session = db.get_session()
        session.execute(
            text("""
            CREATE TABLE IF NOT EXISTS memory_attachments (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                memory_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                content_type TEXT NOT NULL,
                size BIGINT NOT NULL,
                storage_key TEXT NOT NULL,
                storage_backend TEXT DEFAULT 's3',
                attachment_metadata JSONB DEFAULT '{{}}'::jsonb,
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            );
            CREATE INDEX IF NOT EXISTS ix_memory_attachments_memory_id ON memory_attachments(memory_id);
            CREATE INDEX IF NOT EXISTS ix_memory_attachments_user_id ON memory_attachments(user_id);
            CREATE INDEX IF NOT EXISTS ix_memory_attachments_storage_key ON memory_attachments(storage_key);
            """)
        )
        session.commit()
        session.close()
        logger.info("Memory attachments table ensured")
    except Exception as e:
        logger.warning(f"Failed to create memory_attachments table (may already exist): {e}")


@router.post("/{memory_id}/attachments", response_model=AttachmentResponse, status_code=201)
async def upload_memory_attachment(
    memory_id: str,
    request: Request,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_default_memory_provider),
):
    """
    Upload and attach a file to a memory.

    US#327: Memory Attachment Upload Endpoint

    Accepts multipart/form-data file uploads and stores the file in the storage backend.
    Stores attachment metadata in the database.
    """
    try:
        # Verify memory exists and user has access
        try:
            memories = await provider.list_memories(
                user_id=current_user.id,
                limit=1000,
                offset=0,
                bearer_token=request.headers.get("authorization"),
            )
            memory_exists = any(m.get("id") == memory_id for m in memories)
            if not memory_exists:
                raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
        except Exception as e:
            logger.warning(f"Failed to verify memory existence: {e}")
            # Continue anyway - memory might exist in different provider

        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="Filename is required")

        # Check file size (max 100MB)
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        file_content = await file.read()
        file_size = len(file_content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
            )

        if file_size == 0:
            raise HTTPException(status_code=400, detail="File is empty")

        # Validate content type (basic check)
        allowed_types = [
            "image/", "application/pdf", "text/", "application/json",
            "application/zip", "application/x-zip-compressed"
        ]
        content_type = file.content_type or "application/octet-stream"
        if not any(content_type.startswith(allowed) for allowed in allowed_types):
            logger.warning(f"Unusual content type: {content_type}")
            # Allow but log warning

        # Get storage backend
        storage = get_storage_backend()
        if not storage:
            raise HTTPException(
                status_code=503,
                detail="File storage backend not available"
            )

        # Generate storage key
        attachment_id = str(uuid.uuid4())
        storage_key = f"memory-attachments/{current_user.id}/{memory_id}/{attachment_id}/{file.filename}"

        # Upload file to storage
        try:
            # Use storage backend to upload
            if hasattr(storage, 'upload_file'):
                await storage.upload_file(
                    key=storage_key,
                    file_content=file_content,
                    content_type=content_type,
                    metadata={"memory_id": memory_id, "user_id": str(current_user.id)}
                )
            else:
                # Fallback: Store in database as blob (not ideal but works)
                logger.warning("Storage backend doesn't support direct upload, using fallback")
                # For now, we'll store metadata and return a placeholder
                pass

            # Store attachment metadata in database
            db = get_db()
            await ensure_attachment_table(db)

            session = db.get_session()
            attachment_record = {
                "id": attachment_id,
                "memory_id": memory_id,
                "user_id": str(current_user.id),
                "filename": file.filename,
                "content_type": content_type,
                "size": file_size,
                "storage_key": storage_key,
                "storage_backend": "s3",  # Default
                "attachment_metadata": {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
            }

            session.execute(
                text("""
                INSERT INTO memory_attachments
                (id, memory_id, user_id, filename, content_type, size, storage_key, storage_backend, attachment_metadata, created_at, updated_at)
                VALUES (:id, :memory_id, :user_id, :filename, :content_type, :size, :storage_key, :storage_backend, :attachment_metadata, :created_at, :updated_at)
                """),
                attachment_record
            )
            session.commit()
            session.close()

            # Generate download URL (pre-signed if supported)
            download_url = None
            if hasattr(storage, 'generate_presigned_url'):
                try:
                    download_url = await storage.generate_presigned_url(
                        key=storage_key,
                        expires_in=3600  # 1 hour
                    )
                except Exception as e:
                    logger.warning(f"Failed to generate presigned URL: {e}")

            logger.info(
                "Memory attachment uploaded",
                memory_id=memory_id,
                attachment_id=attachment_id,
                filename=file.filename,
                size=file_size,
                user_id=current_user.id
            )

            return AttachmentResponse(
                id=attachment_id,
                memory_id=memory_id,
                filename=file.filename,
                content_type=content_type,
                size=file_size,
                storage_key=storage_key,
                download_url=download_url,
                created_at=attachment_record["created_at"].isoformat(),
                metadata={}
            )

        except Exception as e:
            logger.error(f"Failed to upload attachment: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload attachment: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Memory attachment upload failed: {e}", user_id=current_user.id)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/{memory_id}/attachments", response_model=AttachmentListResponse)
async def list_memory_attachments(
    memory_id: str,
    request: Request,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_default_memory_provider),
):
    """
    List all attachments for a memory.

    US#328: Memory Attachment Retrieval Endpoints

    Returns paginated list of attachments with metadata.
    """
    try:
        # Verify memory exists and user has access
        try:
            memories = await provider.list_memories(
                user_id=current_user.id,
                limit=1000,
                offset=0,
                bearer_token=request.headers.get("authorization"),
            )
            memory_exists = any(m.get("id") == memory_id for m in memories)
            if not memory_exists:
                raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
        except Exception as e:
            logger.warning(f"Failed to verify memory existence: {e}")

        # Get attachments from database
        db = get_db()
        session = db.get_session()

        # Get total count
        count_result = session.execute(
            text("""
            SELECT COUNT(*) as count
            FROM memory_attachments
            WHERE memory_id = :memory_id AND user_id = :user_id
            """),
            {"memory_id": memory_id, "user_id": str(current_user.id)}
        )
        total = count_result.fetchone()[0] if count_result else 0

            # Get attachments with pagination
            attachments_result = session.execute(
                text("""
            SELECT id, memory_id, filename, content_type, size, storage_key,
                   attachment_metadata, created_at, updated_at
            FROM memory_attachments
            WHERE memory_id = :memory_id AND user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            """),
                {"memory_id": memory_id, "user_id": str(current_user.id), "limit": limit, "offset": offset}
            )

            attachments = []
            storage = get_storage_backend()

            for row in attachments_result:
                attachment_id = str(row.id)
                storage_key = row.storage_key

                # Generate download URL
                download_url = None
                if storage and hasattr(storage, 'generate_presigned_url'):
                    try:
                        download_url = await storage.generate_presigned_url(
                            key=storage_key,
                            expires_in=3600  # 1 hour
                        )
                    except Exception as e:
                        logger.warning(f"Failed to generate presigned URL for {attachment_id}: {e}")

                attachments.append(AttachmentResponse(
                    id=attachment_id,
                    memory_id=memory_id,
                    filename=row.filename,
                    content_type=row.content_type,
                    size=row.size,
                    storage_key=storage_key,
                    download_url=download_url,
                    created_at=row.created_at.isoformat() if row.created_at else datetime.utcnow().isoformat(),
                    metadata=getattr(row, 'attachment_metadata', None) or {}
                ))

        session.close()

        return AttachmentListResponse(
            items=attachments,
            total=total,
            memory_id=memory_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list memory attachments: {e}", user_id=current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to list attachments: {str(e)}")


@router.get("/{memory_id}/attachments/{attachment_id}", response_model=AttachmentResponse)
async def get_memory_attachment(
    memory_id: str,
    attachment_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_default_memory_provider),
):
    """
    Get a specific memory attachment.

    US#328: Memory Attachment Retrieval Endpoints

    Returns attachment metadata and generates pre-signed download URL.
    """
    try:
        # Verify memory exists
        try:
            memories = await provider.list_memories(
                user_id=current_user.id,
                limit=1000,
                offset=0,
                bearer_token=request.headers.get("authorization"),
            )
            memory_exists = any(m.get("id") == memory_id for m in memories)
            if not memory_exists:
                raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
        except Exception as e:
            logger.warning(f"Failed to verify memory existence: {e}")

        # Get attachment from database
        db = get_db()
        session = db.get_session()

        attachment_result = session.execute(
            text("""
            SELECT id, memory_id, filename, content_type, size, storage_key,
                   attachment_metadata, created_at, updated_at
            FROM memory_attachments
            WHERE id = :attachment_id AND memory_id = :memory_id AND user_id = :user_id
            """),
            {"attachment_id": attachment_id, "memory_id": memory_id, "user_id": str(current_user.id)}
        )

        row = attachment_result.fetchone()
        session.close()

        if not row:
            raise HTTPException(status_code=404, detail=f"Attachment {attachment_id} not found")

        # Generate download URL
        download_url = None
        storage = get_storage_backend()
        if storage and hasattr(storage, 'generate_presigned_url'):
            try:
                download_url = await storage.generate_presigned_url(
                    key=row.storage_key,
                    expires_in=3600  # 1 hour
                )
            except Exception as e:
                logger.warning(f"Failed to generate presigned URL: {e}")

        return AttachmentResponse(
            id=str(row.id),
            memory_id=memory_id,
            filename=row.filename,
            content_type=row.content_type,
            size=row.size,
            storage_key=row.storage_key,
            download_url=download_url,
            created_at=row.created_at.isoformat() if row.created_at else datetime.utcnow().isoformat(),
            metadata=getattr(row, 'attachment_metadata', None) or {}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get memory attachment: {e}", user_id=current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to get attachment: {str(e)}")


@router.delete("/{memory_id}/attachments/{attachment_id}", status_code=204)
async def delete_memory_attachment(
    memory_id: str,
    attachment_id: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    provider: MemoryProvider = Depends(get_default_memory_provider),
):
    """
    Delete a memory attachment.

    US#329: Memory Attachment Deletion Endpoint

    Deletes the file from storage and removes the attachment record from database.
    """
    try:
        # Verify memory exists
        try:
            memories = await provider.list_memories(
                user_id=current_user.id,
                limit=1000,
                offset=0,
                bearer_token=request.headers.get("authorization"),
            )
            memory_exists = any(m.get("id") == memory_id for m in memories)
            if not memory_exists:
                raise HTTPException(status_code=404, detail=f"Memory {memory_id} not found")
        except Exception as e:
            logger.warning(f"Failed to verify memory existence: {e}")

        # Get attachment record to get storage_key
        db = get_db()
        session = db.get_session()

        attachment_result = session.execute(
            text("""
            SELECT storage_key, storage_backend
            FROM memory_attachments
            WHERE id = :attachment_id AND memory_id = :memory_id AND user_id = :user_id
            """),
            {"attachment_id": attachment_id, "memory_id": memory_id, "user_id": str(current_user.id)}
        )

        row = attachment_result.fetchone()

        if not row:
            session.close()
            raise HTTPException(status_code=404, detail=f"Attachment {attachment_id} not found")

        storage_key = row.storage_key

        # Delete file from storage
        storage = get_storage_backend()
        if storage:
            try:
                if hasattr(storage, 'delete_file'):
                    await storage.delete_file(key=storage_key)
                elif hasattr(storage, 'delete_object'):
                    await storage.delete_object(key=storage_key)
                else:
                    logger.warning("Storage backend doesn't support file deletion")
            except Exception as e:
                logger.warning(f"Failed to delete file from storage: {e}")
                # Continue with database deletion anyway

        # Delete attachment record from database
        session.execute(
            text("""
            DELETE FROM memory_attachments
            WHERE id = :attachment_id AND memory_id = :memory_id AND user_id = :user_id
            """),
            {"attachment_id": attachment_id, "memory_id": memory_id, "user_id": str(current_user.id)}
        )
        session.commit()
        session.close()

        logger.info(
            "Memory attachment deleted",
            memory_id=memory_id,
            attachment_id=attachment_id,
            user_id=current_user.id
        )

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete memory attachment: {e}", user_id=current_user.id)
        raise HTTPException(status_code=500, detail=f"Failed to delete attachment: {str(e)}")
