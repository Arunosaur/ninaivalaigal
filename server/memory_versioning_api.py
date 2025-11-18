#!/usr/bin/env python3
# SPDX-License-Identifier: Proprietary
# Copyright (c) 2025 Medhasys LLC
#
# This file contains proprietary code owned by Medhasys LLC.
# Unauthorized copying, modification, or distribution is prohibited.
# See LICENSE file in the server/ directory for details.
#
"""
SPEC-035: Memory Versioning API

FastAPI endpoints for memory version history tracking:
- Version history retrieval
- Version details
- Version comparison
- Version restore
- Snapshot management
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

import structlog
from database import User
from fastapi import APIRouter, Depends, HTTPException, Query
from memory_versioning.diff_engine import VersionDiffEngine, get_diff_engine
from memory_versioning.engine import (
    MemoryVersioningEngine,
    VersioningError,
    get_versioning_engine,
)
from pydantic import BaseModel, Field

from auth import get_current_user

logger = structlog.get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/memories/versions", tags=["Memory Versioning"])


# Request/Response Models
class VersionResponse(BaseModel):
    """Version response model"""

    id: str
    memory_id: str
    version_number: int
    parent_version_id: Optional[str] = None
    content: str
    content_hash: str
    metadata: dict[str, Any] = {}
    embedding: Optional[list[float]] = None
    created_by: Optional[str] = None
    created_at: datetime
    change_summary: Optional[str] = None
    change_type: Optional[str] = None
    is_current: bool
    is_snapshot: bool
    snapshot_label: Optional[str] = None


class VersionHistoryResponse(BaseModel):
    """Version history response model"""

    memory_id: str
    total_versions: int
    current_version_number: int
    versions: list[VersionResponse]
    pagination: dict[str, Any]


class VersionComparisonResponse(BaseModel):
    """Version comparison response model"""

    memory_id: str
    version1: VersionResponse
    version2: VersionResponse
    differences: dict[str, Any]
    similarity_score: Optional[float] = None
    compared_at: datetime


class DiffVisualizationResponse(BaseModel):
    """Diff visualization response model"""

    version1_id: str
    version2_id: str
    similarity_score: float
    has_changes: bool
    change_summary: str
    content_length_diff: int
    word_count_diff: int
    character_count_diff: int
    metadata_diff: dict[str, Any]
    visualization: dict[str, Any]
    calculated_at: datetime


class RestoreVersionRequest(BaseModel):
    """Restore version request model"""

    version_id: str = Field(..., description="Version ID to restore")
    restore_notes: Optional[str] = Field(None, description="Notes about the restore")


class RestoreVersionResponse(BaseModel):
    """Restore version response model"""

    success: bool
    restored_version: VersionResponse
    previous_version: Optional[VersionResponse] = None
    message: str


def get_versioning_engine_dep() -> MemoryVersioningEngine:
    """Dependency to get versioning engine"""
    return get_versioning_engine()


def version_to_response(version) -> VersionResponse:
    """Convert MemoryVersion model to response"""
    return VersionResponse(
        id=str(version.id),
        memory_id=str(version.memory_id),
        version_number=version.version_number,
        parent_version_id=str(version.parent_version_id) if version.parent_version_id else None,
        content=version.content,
        content_hash=version.content_hash,
        metadata=version.metadata_json or {},
        embedding=version.embedding,
        created_by=str(version.created_by) if version.created_by else None,
        created_at=version.created_at,
        change_summary=version.change_summary,
        change_type=version.change_type,
        is_current=version.is_current,
        is_snapshot=version.is_snapshot,
        snapshot_label=version.snapshot_label,
    )


@router.get("/{memory_id}/history", response_model=VersionHistoryResponse)
async def get_version_history(
    memory_id: UUID,
    limit: int = Query(100, ge=1, le=1000, description="Number of versions to return"),
    offset: int = Query(0, ge=0, description="Number of versions to skip"),
    include_snapshots_only: bool = Query(False, description="Include only snapshots"),
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Get version history for a memory"""
    try:
        logger.info(
            "Getting version history",
            memory_id=str(memory_id),
            user_id=current_user.id,
            limit=limit,
            offset=offset,
        )

        # Get version history
        versions = versioning_engine.get_version_history(
            memory_id=memory_id,
            limit=limit,
            offset=offset,
            include_snapshots_only=include_snapshots_only,
        )

        # Get current version
        current_version = versioning_engine.get_current_version(memory_id)
        current_version_number = current_version.version_number if current_version else 0

        # Get total count
        total_versions = versioning_engine.get_version_count(memory_id)

        # Convert to response
        version_responses = [version_to_response(v) for v in versions]

        response = VersionHistoryResponse(
            memory_id=str(memory_id),
            total_versions=total_versions,
            current_version_number=current_version_number,
            versions=version_responses,
            pagination={
                "limit": limit,
                "offset": offset,
                "total": total_versions,
                "has_more": (offset + limit) < total_versions,
            },
        )

        logger.info(
            "Version history retrieved",
            memory_id=str(memory_id),
            count=len(versions),
            user_id=current_user.id,
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to get version history",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get version history: {str(e)}")


# Alias for backward compatibility - redirects to /history endpoint
@router.get("/{memory_id}", response_model=VersionHistoryResponse)
async def get_version_history_alias(
    memory_id: UUID,
    limit: int = Query(100, ge=1, le=1000, description="Number of versions to return"),
    offset: int = Query(0, ge=0, description="Number of versions to skip"),
    include_snapshots_only: bool = Query(False, description="Include only snapshots"),
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Get version history for a memory (alias for /history endpoint)"""
    # Reuse the same implementation
    return await get_version_history(
        memory_id=memory_id,
        limit=limit,
        offset=offset,
        include_snapshots_only=include_snapshots_only,
        current_user=current_user,
        versioning_engine=versioning_engine,
    )


@router.get("/{memory_id}/current", response_model=VersionResponse)
async def get_current_version(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Get current version of a memory"""
    try:
        logger.info("Getting current version", memory_id=str(memory_id), user_id=current_user.id)

        current_version = versioning_engine.get_current_version(memory_id)

        if not current_version:
            raise HTTPException(status_code=404, detail="No version found for this memory")

        return version_to_response(current_version)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get current version",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get current version: {str(e)}")


@router.get("/{memory_id}/version/{version_id}", response_model=VersionResponse)
async def get_version(
    memory_id: UUID,
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Get a specific version by ID"""
    try:
        logger.info(
            "Getting version",
            memory_id=str(memory_id),
            version_id=str(version_id),
            user_id=current_user.id,
        )

        version = versioning_engine.get_version(version_id)

        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        if version.memory_id != memory_id:
            raise HTTPException(status_code=400, detail="Version does not belong to this memory")

        return version_to_response(version)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get version",
            memory_id=str(memory_id),
            version_id=str(version_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get version: {str(e)}")


@router.get("/{memory_id}/compare", response_model=VersionComparisonResponse)
async def compare_versions(
    memory_id: UUID,
    version1_id: UUID = Query(..., description="First version ID"),
    version2_id: UUID = Query(..., description="Second version ID"),
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Compare two versions"""
    try:
        logger.info(
            "Comparing versions",
            memory_id=str(memory_id),
            version1_id=str(version1_id),
            version2_id=str(version2_id),
            user_id=current_user.id,
        )

        # Get both versions
        v1 = versioning_engine.get_version(version1_id)
        v2 = versioning_engine.get_version(version2_id)

        if not v1 or not v2:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        if v1.memory_id != memory_id or v2.memory_id != memory_id:
            raise HTTPException(status_code=400, detail="Versions do not belong to this memory")

        # Calculate differences
        differences = {
            "content_changed": v1.content != v2.content,
            "content_hash_changed": v1.content_hash != v2.content_hash,
            "metadata_changed": v1.metadata != v2.metadata,
            "version_number_diff": v2.version_number - v1.version_number,
            "created_at_diff_seconds": (v2.created_at - v1.created_at).total_seconds(),
        }

        # Calculate similarity score (simple content comparison)
        if v1.content == v2.content:
            similarity_score = 1.0
        elif v1.content_hash == v2.content_hash:
            similarity_score = 1.0
        else:
            # Simple similarity based on content length and common substrings
            len1, len2 = len(v1.content), len(v2.content)
            if len1 == 0 and len2 == 0:
                similarity_score = 1.0
            elif len1 == 0 or len2 == 0:
                similarity_score = 0.0
            else:
                # Use simple ratio calculation
                from difflib import SequenceMatcher

                similarity_score = SequenceMatcher(None, v1.content, v2.content).ratio()

        response = VersionComparisonResponse(
            memory_id=str(memory_id),
            version1=version_to_response(v1),
            version2=version_to_response(v2),
            differences=differences,
            similarity_score=similarity_score,
            compared_at=datetime.utcnow(),
        )

        logger.info(
            "Versions compared",
            memory_id=str(memory_id),
            similarity_score=similarity_score,
            user_id=current_user.id,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to compare versions",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to compare versions: {str(e)}")


@router.get("/{memory_id}/diff", response_model=DiffVisualizationResponse)
async def get_version_diff(
    memory_id: UUID,
    version1_id: UUID = Query(..., description="First version ID (older)"),
    version2_id: UUID = Query(..., description="Second version ID (newer)"),
    format: str = Query("unified", description="Diff format: unified, side_by_side, inline, json"),
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
    diff_engine: VersionDiffEngine = Depends(lambda: get_diff_engine()),
):
    """Get detailed diff visualization between two versions"""
    try:
        logger.info(
            "Getting version diff",
            memory_id=str(memory_id),
            version1_id=str(version1_id),
            version2_id=str(version2_id),
            format=format,
            user_id=current_user.id,
        )

        # Get both versions
        v1 = versioning_engine.get_version(version1_id)
        v2 = versioning_engine.get_version(version2_id)

        if not v1 or not v2:
            raise HTTPException(status_code=404, detail="One or both versions not found")

        if v1.memory_id != memory_id or v2.memory_id != memory_id:
            raise HTTPException(status_code=400, detail="Versions do not belong to this memory")

        # Calculate comprehensive diff
        diff_result = diff_engine.calculate_diff(v1, v2)

        # Format for display
        visualization = diff_engine.format_diff_for_display(diff_result, format=format)

        response = DiffVisualizationResponse(
            version1_id=str(version1_id),
            version2_id=str(version2_id),
            similarity_score=diff_result.similarity_score,
            has_changes=diff_result.has_changes,
            change_summary=diff_result.change_summary,
            content_length_diff=diff_result.content_length_diff,
            word_count_diff=diff_result.word_count_diff,
            character_count_diff=diff_result.character_count_diff,
            metadata_diff=diff_result.metadata_diff,
            visualization=visualization,
            calculated_at=diff_result.calculated_at,
        )

        logger.info(
            "Version diff calculated",
            memory_id=str(memory_id),
            similarity_score=diff_result.similarity_score,
            has_changes=diff_result.has_changes,
            user_id=current_user.id,
        )

        return response

    except HTTPException:
        raise
    except ValueError as e:
        logger.error(
            "Invalid diff format",
            memory_id=str(memory_id),
            format=format,
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to get version diff",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get version diff: {str(e)}")


@router.get("/{memory_id}/lineage/{version_id}", response_model=list[VersionResponse])
async def get_version_lineage(
    memory_id: UUID,
    version_id: UUID,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Get version lineage (ancestors)"""
    try:
        logger.info(
            "Getting version lineage",
            memory_id=str(memory_id),
            version_id=str(version_id),
            user_id=current_user.id,
        )

        # Verify version belongs to memory
        version = versioning_engine.get_version(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="Version not found")

        if version.memory_id != memory_id:
            raise HTTPException(status_code=400, detail="Version does not belong to this memory")

        # Get lineage
        lineage = versioning_engine.get_version_lineage(version_id)

        return [version_to_response(v) for v in lineage]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get version lineage",
            memory_id=str(memory_id),
            version_id=str(version_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get version lineage: {str(e)}")


@router.post("/{memory_id}/restore", response_model=RestoreVersionResponse)
async def restore_version(
    memory_id: UUID,
    request: RestoreVersionRequest,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Restore a previous version"""
    try:
        logger.info(
            "Restoring version",
            memory_id=str(memory_id),
            version_id=request.version_id,
            user_id=current_user.id,
        )

        version_id = UUID(request.version_id)

        # Verify version belongs to memory
        old_version = versioning_engine.get_version(version_id)
        if not old_version:
            raise HTTPException(status_code=404, detail="Version not found")

        if old_version.memory_id != memory_id:
            raise HTTPException(status_code=400, detail="Version does not belong to this memory")

        # Get current version before restore
        current_version = versioning_engine.get_current_version(memory_id)

        # Restore version
        restored_version = versioning_engine.restore_version(
            version_id=version_id,
            restored_by=current_user.id,
            restore_notes=request.restore_notes,
        )

        response = RestoreVersionResponse(
            success=True,
            restored_version=version_to_response(restored_version),
            previous_version=version_to_response(current_version) if current_version else None,
            message=f"Version {old_version.version_number} restored successfully",
        )

        logger.info(
            "Version restored",
            memory_id=str(memory_id),
            restored_version_number=restored_version.version_number,
            user_id=current_user.id,
        )

        return response

    except HTTPException:
        raise
    except VersioningError as e:
        logger.error(
            "Versioning error during restore",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to restore version",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to restore version: {str(e)}")


@router.post("/{memory_id}/rollback", response_model=RestoreVersionResponse)
async def rollback_restore(
    memory_id: UUID,
    request: RestoreVersionRequest,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Rollback a restore operation"""
    try:
        logger.info(
            "Rolling back restore",
            memory_id=str(memory_id),
            restore_version_id=request.version_id,
            user_id=current_user.id,
        )

        restore_version_id = UUID(request.version_id)

        # Verify restore version belongs to memory
        restore_version = versioning_engine.get_version(restore_version_id)
        if not restore_version:
            raise HTTPException(status_code=404, detail="Restore version not found")

        if restore_version.memory_id != memory_id:
            raise HTTPException(status_code=400, detail="Restore version does not belong to this memory")

        if restore_version.change_type != "restore":
            raise HTTPException(status_code=400, detail="Version is not a restore operation")

        # Get current version before rollback
        current_version = versioning_engine.get_current_version(memory_id)

        # Rollback restore
        rolled_back_version = versioning_engine.rollback_restore(
            restore_version_id=restore_version_id,
            rolled_back_by=current_user.id,
            rollback_notes=request.restore_notes,
        )

        response = RestoreVersionResponse(
            success=True,
            restored_version=version_to_response(rolled_back_version),
            previous_version=version_to_response(current_version) if current_version else None,
            message=f"Restore rolled back successfully",
        )

        logger.info(
            "Restore rolled back",
            memory_id=str(memory_id),
            rolled_back_version_number=rolled_back_version.version_number,
            user_id=current_user.id,
        )

        return response

    except HTTPException:
        raise
    except VersioningError as e:
        logger.error(
            "Versioning error during rollback",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to rollback restore",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to rollback restore: {str(e)}")


@router.get("/{memory_id}/restore-history", response_model=list[VersionResponse])
async def get_restore_history(
    memory_id: UUID,
    limit: int = Query(100, ge=1, le=1000, description="Number of restore operations to return"),
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Get restore operation history for a memory"""
    try:
        logger.info(
            "Getting restore history",
            memory_id=str(memory_id),
            user_id=current_user.id,
        )

        restore_history = versioning_engine.get_restore_history(memory_id, limit=limit)

        return [version_to_response(v) for v in restore_history]

    except Exception as e:
        logger.error(
            "Failed to get restore history",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get restore history: {str(e)}")


@router.get("/{memory_id}/stats", response_model=dict[str, Any])
async def get_version_stats(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Get version statistics for a memory"""
    try:
        logger.info("Getting version stats", memory_id=str(memory_id), user_id=current_user.id)

        total_versions = versioning_engine.get_version_count(memory_id)
        snapshot_count = versioning_engine.get_snapshot_count(memory_id)
        current_version = versioning_engine.get_current_version(memory_id)

        stats = {
            "memory_id": str(memory_id),
            "total_versions": total_versions,
            "snapshot_count": snapshot_count,
            "current_version_number": current_version.version_number if current_version else None,
            "current_version_id": str(current_version.id) if current_version else None,
            "has_versions": total_versions > 0,
            "has_snapshots": snapshot_count > 0,
        }

        return stats

    except Exception as e:
        logger.error(
            "Failed to get version stats",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get version stats: {str(e)}")


# Enhanced Snapshot Management Endpoints
class CreateSnapshotRequest(BaseModel):
    """Create snapshot request model"""

    memory_id: str = Field(..., description="Memory ID")
    content: str = Field(..., description="Memory content")
    metadata: dict[str, Any] = Field(None, description="Memory metadata")
    embedding: list[float] = Field(None, description="Content embedding vector")
    snapshot_label: str = Field(None, description="Snapshot label")


class UpdateSnapshotLabelRequest(BaseModel):
    """Update snapshot label request model"""

    label: str = Field(..., description="New snapshot label")


class SnapshotResponse(BaseModel):
    """Snapshot response model"""

    snapshot: VersionResponse
    message: str


@router.post("/snapshots", response_model=SnapshotResponse)
async def create_snapshot(
    request: CreateSnapshotRequest,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Create a new snapshot"""
    try:
        logger.info(
            "Creating snapshot",
            memory_id=request.memory_id,
            label=request.snapshot_label,
            user_id=current_user.id,
        )

        memory_id = UUID(request.memory_id)

        snapshot = versioning_engine.create_snapshot(
            memory_id=memory_id,
            content=request.content,
            metadata=request.metadata,
            embedding=request.embedding,
            created_by=current_user.id,
            snapshot_label=request.snapshot_label,
        )

        response = SnapshotResponse(
            snapshot=version_to_response(snapshot),
            message=f"Snapshot '{request.snapshot_label or 'Unlabeled'}' created successfully",
        )

        logger.info(
            "Snapshot created",
            memory_id=str(memory_id),
            snapshot_id=str(snapshot.id),
            user_id=current_user.id,
        )

        return response

    except VersioningError as e:
        logger.error(
            "Versioning error creating snapshot",
            memory_id=request.memory_id,
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to create snapshot",
            memory_id=request.memory_id,
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to create snapshot: {str(e)}")


@router.get("/{memory_id}/snapshots", response_model=list[VersionResponse])
async def list_snapshots(
    memory_id: UUID,
    label: str = Query(None, description="Filter by snapshot label"),
    limit: int = Query(100, ge=1, le=1000, description="Number of snapshots to return"),
    offset: int = Query(0, ge=0, description="Number of snapshots to skip"),
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """List snapshots for a memory"""
    try:
        logger.info(
            "Listing snapshots",
            memory_id=str(memory_id),
            label=label,
            user_id=current_user.id,
        )

        snapshots = versioning_engine.get_snapshots(
            memory_id=memory_id,
            label=label,
            limit=limit,
            offset=offset,
        )

        return [version_to_response(s) for s in snapshots]

    except Exception as e:
        logger.error(
            "Failed to list snapshots",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to list snapshots: {str(e)}")


@router.get("/snapshots/{snapshot_id}", response_model=VersionResponse)
async def get_snapshot(
    snapshot_id: UUID,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Get a specific snapshot"""
    try:
        logger.info("Getting snapshot", snapshot_id=str(snapshot_id), user_id=current_user.id)

        snapshot = versioning_engine.get_snapshot(snapshot_id)

        if not snapshot:
            raise HTTPException(status_code=404, detail="Snapshot not found")

        return version_to_response(snapshot)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get snapshot",
            snapshot_id=str(snapshot_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get snapshot: {str(e)}")


@router.put("/snapshots/{snapshot_id}/label", response_model=VersionResponse)
async def update_snapshot_label(
    snapshot_id: UUID,
    request: UpdateSnapshotLabelRequest,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Update snapshot label"""
    try:
        logger.info(
            "Updating snapshot label",
            snapshot_id=str(snapshot_id),
            new_label=request.label,
            user_id=current_user.id,
        )

        snapshot = versioning_engine.update_snapshot_label(
            snapshot_id=snapshot_id,
            new_label=request.label,
        )

        return version_to_response(snapshot)

    except VersioningError as e:
        logger.error(
            "Versioning error updating snapshot label",
            snapshot_id=str(snapshot_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to update snapshot label",
            snapshot_id=str(snapshot_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to update snapshot label: {str(e)}")


@router.delete("/snapshots/{snapshot_id}")
async def delete_snapshot(
    snapshot_id: UUID,
    soft_delete: bool = Query(True, description="Soft delete (mark as deleted) or hard delete"),
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Delete a snapshot"""
    try:
        logger.info(
            "Deleting snapshot",
            snapshot_id=str(snapshot_id),
            soft_delete=soft_delete,
            user_id=current_user.id,
        )

        versioning_engine.delete_snapshot(
            snapshot_id=snapshot_id,
            soft_delete=soft_delete,
        )

        return {"success": True, "message": "Snapshot deleted successfully"}

    except VersioningError as e:
        logger.error(
            "Versioning error deleting snapshot",
            snapshot_id=str(snapshot_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            "Failed to delete snapshot",
            snapshot_id=str(snapshot_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to delete snapshot: {str(e)}")


@router.get("/{memory_id}/snapshots/stats", response_model=dict[str, Any])
async def get_snapshot_statistics(
    memory_id: UUID,
    current_user: User = Depends(get_current_user),
    versioning_engine: MemoryVersioningEngine = Depends(get_versioning_engine_dep),
):
    """Get snapshot statistics for a memory"""
    try:
        logger.info("Getting snapshot stats", memory_id=str(memory_id), user_id=current_user.id)

        stats = versioning_engine.get_snapshot_statistics(memory_id=memory_id)

        return stats

    except Exception as e:
        logger.error(
            "Failed to get snapshot stats",
            memory_id=str(memory_id),
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Failed to get snapshot stats: {str(e)}")
