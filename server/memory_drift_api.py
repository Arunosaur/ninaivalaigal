"""
SPEC-044: Memory Drift & Diff Detection API

FastAPI endpoints for memory drift detection and management:
- Drift detection and analysis
- Memory snapshot management
- Drift history and reporting
- Real-time drift monitoring
- Diff visualization

Endpoints:
- POST /drift/detect - Detect drift for memory
- GET /drift/history/{memory_id} - Get drift history
- GET /drift/report/{memory_id} - Generate drift report
- POST /drift/snapshot - Create memory snapshot
- GET /drift/stats - Get drift statistics
"""

from datetime import datetime
from typing import Any

import structlog
from auth import get_current_user
from database import User
from fastapi import APIRouter, Depends, HTTPException, Query
from memory_drift_engine import (
    MemoryDriftEngine,
    get_drift_engine,
)
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

# Create router
router = APIRouter(prefix="/drift", tags=["Memory Drift Detection"])


# Request/Response Models
class DriftDetectionRequest(BaseModel):
    memory_id: str = Field(..., description="Memory ID to analyze")
    content: str = Field(..., description="Current memory content")
    metadata: dict[str, Any] | None = Field(None, description="Memory metadata")
    embedding: list[float] | None = Field(
        None, description="Content embedding vector"
    )


class SnapshotRequest(BaseModel):
    memory_id: str = Field(..., description="Memory ID")
    content: str = Field(..., description="Memory content")
    metadata: dict[str, Any] | None = Field(None, description="Memory metadata")
    embedding: list[float] | None = Field(
        None, description="Content embedding vector"
    )


class DriftDetectionResponse(BaseModel):
    memory_id: str
    drift_count: int
    detections: list[dict[str, Any]]
    analysis_timestamp: datetime


class DriftHistoryResponse(BaseModel):
    memory_id: str
    total_drifts: int
    drift_history: list[dict[str, Any]]
    retrieved_at: datetime


class DriftReportResponse(BaseModel):
    memory_id: str
    report_period_days: int
    total_drifts: int
    drift_timeline: list[dict[str, Any]]
    summary_stats: dict[str, Any]
    generated_at: datetime


class DriftStatsResponse(BaseModel):
    total_memories_tracked: int
    total_drifts_detected: int
    drift_types_distribution: dict[str, int]
    severity_distribution: dict[str, int]
    recent_drift_rate: float
    stats_generated_at: datetime


class SnapshotResponse(BaseModel):
    memory_id: str
    version: int
    content_hash: str
    created_at: datetime
    snapshot_stored: bool


# Dependency to get drift engine
async def get_drift_engine_dep() -> MemoryDriftEngine:
    """Dependency to get the drift engine"""
    return await get_drift_engine()


@router.post("/detect", response_model=DriftDetectionResponse)
async def detect_memory_drift(
    request: DriftDetectionRequest,
    current_user: User = Depends(get_current_user),
    drift_engine: MemoryDriftEngine = Depends(get_drift_engine_dep),
):
    """Detect drift in memory content"""
    try:
        logger.info(
            "Detecting memory drift",
            memory_id=request.memory_id,
            user_id=current_user.id,
            content_length=len(request.content),
        )

        # Detect drift
        detections = await drift_engine.detect_drift(
            memory_id=request.memory_id,
            new_content=request.content,
            new_metadata=request.metadata,
            new_embedding=request.embedding,
        )

        # Convert detections to response format
        detection_data = []
        for detection in detections:
            detection_data.append(
                {
                    "drift_type": detection.drift_type.value,
                    "severity": detection.severity.value,
                    "confidence": detection.confidence,
                    "changes": detection.changes,
                    "detected_at": detection.detected_at.isoformat(),
                }
            )

        response = DriftDetectionResponse(
            memory_id=request.memory_id,
            drift_count=len(detections),
            detections=detection_data,
            analysis_timestamp=datetime.utcnow(),
        )

        logger.info(
            "Memory drift detection completed",
            memory_id=request.memory_id,
            drift_count=len(detections),
            user_id=current_user.id,
        )

        return response

    except Exception as e:
        logger.error(
            "Memory drift detection failed",
            memory_id=request.memory_id,
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=f"Drift detection failed: {str(e)}")


@router.get("/history/{memory_id}", response_model=DriftHistoryResponse)
async def get_drift_history(
    memory_id: str,
    limit: int = Query(
        50, ge=1, le=1000, description="Maximum number of drift records"
    ),
    current_user: User = Depends(get_current_user),
    drift_engine: MemoryDriftEngine = Depends(get_drift_engine_dep),
):
    """Get drift detection history for a memory"""
    try:
        logger.info(
            "Retrieving drift history",
            memory_id=memory_id,
            user_id=current_user.id,
            limit=limit,
        )

        # Get drift history
        drift_history = await drift_engine.get_drift_history(memory_id, limit)

        # Convert to response format
        history_data = []
        for drift in drift_history:
            history_data.append(
                {
                    "drift_type": drift.drift_type.value,
                    "severity": drift.severity.value,
                    "confidence": drift.confidence,
                    "changes": drift.changes,
                    "detected_at": drift.detected_at.isoformat(),
                }
            )

        response = DriftHistoryResponse(
            memory_id=memory_id,
            total_drifts=len(drift_history),
            drift_history=history_data,
            retrieved_at=datetime.utcnow(),
        )

        logger.info(
            "Drift history retrieved",
            memory_id=memory_id,
            total_drifts=len(drift_history),
            user_id=current_user.id,
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to retrieve drift history",
            memory_id=memory_id,
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve drift history: {str(e)}"
        )


@router.get("/report/{memory_id}", response_model=DriftReportResponse)
async def generate_drift_report(
    memory_id: str,
    days_back: int = Query(
        30, ge=1, le=365, description="Number of days to include in report"
    ),
    current_user: User = Depends(get_current_user),
    drift_engine: MemoryDriftEngine = Depends(get_drift_engine_dep),
):
    """Generate comprehensive drift report for a memory"""
    try:
        logger.info(
            "Generating drift report",
            memory_id=memory_id,
            user_id=current_user.id,
            days_back=days_back,
        )

        # Generate drift report
        report = await drift_engine.generate_drift_report(memory_id, days_back)

        response = DriftReportResponse(
            memory_id=report.memory_id,
            report_period_days=days_back,
            total_drifts=report.total_drifts,
            drift_timeline=report.drift_timeline,
            summary_stats=report.summary_stats,
            generated_at=report.generated_at,
        )

        logger.info(
            "Drift report generated",
            memory_id=memory_id,
            total_drifts=report.total_drifts,
            user_id=current_user.id,
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to generate drift report",
            memory_id=memory_id,
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to generate drift report: {str(e)}"
        )


@router.post("/snapshot", response_model=SnapshotResponse)
async def create_memory_snapshot(
    request: SnapshotRequest,
    current_user: User = Depends(get_current_user),
    drift_engine: MemoryDriftEngine = Depends(get_drift_engine_dep),
):
    """Create a memory snapshot for drift tracking"""
    try:
        logger.info(
            "Creating memory snapshot",
            memory_id=request.memory_id,
            user_id=current_user.id,
            content_length=len(request.content),
        )

        # Create snapshot
        snapshot = await drift_engine.create_memory_snapshot(
            memory_id=request.memory_id,
            content=request.content,
            metadata=request.metadata,
            embedding=request.embedding,
        )

        response = SnapshotResponse(
            memory_id=snapshot.memory_id,
            version=snapshot.version,
            content_hash=snapshot.content_hash,
            created_at=snapshot.created_at,
            snapshot_stored=True,
        )

        logger.info(
            "Memory snapshot created",
            memory_id=request.memory_id,
            version=snapshot.version,
            user_id=current_user.id,
        )

        return response

    except Exception as e:
        logger.error(
            "Failed to create memory snapshot",
            memory_id=request.memory_id,
            user_id=current_user.id,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to create snapshot: {str(e)}"
        )


@router.get("/stats", response_model=DriftStatsResponse)
async def get_drift_statistics(
    current_user: User = Depends(get_current_user),
    drift_engine: MemoryDriftEngine = Depends(get_drift_engine_dep),
):
    """Get overall drift detection statistics"""
    try:
        logger.info("Retrieving drift statistics", user_id=current_user.id)

        # This would normally aggregate stats from Redis
        # For now, return mock data structure
        stats = DriftStatsResponse(
            total_memories_tracked=0,
            total_drifts_detected=0,
            drift_types_distribution={
                "content": 0,
                "semantic": 0,
                "structural": 0,
                "metadata": 0,
            },
            severity_distribution={"low": 0, "medium": 0, "high": 0, "critical": 0},
            recent_drift_rate=0.0,
            stats_generated_at=datetime.utcnow(),
        )

        logger.info("Drift statistics retrieved", user_id=current_user.id)

        return stats

    except Exception as e:
        logger.error(
            "Failed to retrieve drift statistics", user_id=current_user.id, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.get("/system-status")
def drift_system_status():
    """Memory drift system status check"""
    return {
        "status": "healthy",
        "service": "memory-drift-api",
        "drift_capabilities": [
            "content_drift_detection",
            "semantic_drift_analysis",
            "metadata_change_tracking",
            "snapshot_versioning",
            "drift_reporting",
            "real_time_monitoring",
        ],
    }


@router.get("/ping")
def drift_ping():
    """Simple ping endpoint for drift system"""
    return {"ping": "pong", "service": "memory-drift"}
